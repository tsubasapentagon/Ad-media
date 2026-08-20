"""LINEと会員登録の個人情報リストを、PIIを含まない日別CVへ統合する。"""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from typing import Any

from ad_master import load_all_ad_records

LINE_SPREADSHEET_ID = "1lyzLKsi4FzIvhehg2EmCMFnPaSIfROrZLkoaD_xyghU"
DIGMEDIA_SPREADSHEET_ID = "1FAXjcSg44nxeBJD6lAT2go__zkoJUmbQHAmVnQ6otCw"
MIN_DATE = "20240101"

MEMBER_SOURCES = (
    {"media": "就活市場", "spreadsheet_id": LINE_SPREADSHEET_ID, "sheet": "貼付：就活市場"},
    {"media": "Digmedia", "spreadsheet_id": DIGMEDIA_SPREADSHEET_ID, "sheet": "貼付：新Digmedia"},
    {"media": "ベンチャー就活", "spreadsheet_id": LINE_SPREADSHEET_ID, "sheet": "貼付：ベンチャー就活"},
)

OUTPUT_COLUMNS = (
    "date", "media", "ad_id", "graduation_year", "category", "subcategory",
    "placement", "device", "cv_source", "cv_count",
)

MEDIA_ALIASES = {
    "digmedia": "Digmedia",
    "digmeida": "Digmedia",
    "就活市場": "就活市場",
    "ベンチャー就活": "ベンチャー就活",
    "ベンチャー就活ナビ": "ベンチャー就活",
}


def normalize_media(value: Any) -> str:
    text = str(value).strip()
    return MEDIA_ALIASES.get(text.casefold(), "未設定")


def normalize_date(value: Any) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 8:
        candidate = digits[:8]
        try:
            datetime.strptime(candidate, "%Y%m%d")
            return candidate
        except ValueError:
            pass
    normalized = text.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
    try:
        return datetime.fromisoformat(normalized).strftime("%Y%m%d")
    except ValueError:
        return None


def normalize_graduation_year(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(20\d{2}|\d{2})", text)
    if not match:
        return None
    year = int(match.group(1))
    return year + 2000 if year < 100 else year


def rows_from_values(
    values: Sequence[Sequence[Any]], header_row: int, sheet: str, required: Sequence[str] = ()
) -> list[dict[str, str]]:
    if len(values) <= header_row:
        raise ValueError(f"{sheet}: ヘッダー行が見つかりません")
    headers = [str(value).strip() for value in values[header_row]]
    missing = [column for column in required if column not in headers]
    if missing:
        raise ValueError(f'{sheet}: 必須カラムがありません: {", ".join(missing)}')
    rows: list[dict[str, str]] = []
    for values_row in values[header_row + 1:]:
        rows.append({header: str(values_row[index]).strip() if index < len(values_row) else "" for index, header in enumerate(headers) if header})
    return rows


def normalize_line_records(values: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    """電話番号入力済みのLINE行だけをCVにする。電話番号自体は返さない。"""
    sheet = "貼付：Liny"
    required = ("友だち追加日", "流入経路", "流入経路詳細", "卒業年度", "電話番号")
    rows = rows_from_values(values, header_row=1, sheet=sheet, required=required)
    records: list[dict[str, Any]] = []
    for row in rows:
        date = normalize_date(row["友だち追加日"])
        if not row["電話番号"].strip() or not date or date < MIN_DATE:
            continue
        records.append({
            "date": date,
            "media": normalize_media(row["流入経路"]),
            "ad_id": row["流入経路詳細"].strip() or "未設定",
            "graduation_year": normalize_graduation_year(row["卒業年度"]),
            "cv_source": "LINE",
        })
    return records


def normalize_member_records(values: Sequence[Sequence[Any]], media: str, sheet: str) -> list[dict[str, Any]]:
    required = ("登録日時", "電話番号", "卒業予定［年］", "経由点(バナー)")
    rows = rows_from_values(values, header_row=0, sheet=sheet, required=required)
    records: list[dict[str, Any]] = []
    seen_phone_numbers: set[str] = set()
    for row in rows:
        date = normalize_date(row["登録日時"])
        if not date or date < MIN_DATE:
            continue
        phone_number = row["電話番号"].strip()
        if phone_number in seen_phone_numbers:
            continue
        seen_phone_numbers.add(phone_number)
        records.append({
            "date": date,
            "media": media,
            "ad_id": row["経由点(バナー)"].strip() or "未設定",
            "graduation_year": normalize_graduation_year(row["卒業予定［年］"]),
            "cv_source": "会員登録",
        })
    return records


def enrich_and_aggregate_cv_records(
    cv_records: Iterable[dict[str, Any]],
    ad_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    ads = {(ad["media"], ad["ad_id"]): ad for ad in ad_records}
    totals: dict[tuple[Any, ...], int] = defaultdict(int)
    for record in cv_records:
        key = (
            record["date"], record["media"], record["ad_id"],
            record["graduation_year"], record["cv_source"],
        )
        totals[key] += 1

    output: list[dict[str, Any]] = []
    for (date, media, ad_id, graduation_year, cv_source), count in sorted(
        totals.items(), key=lambda item: tuple("" if value is None else str(value) for value in item[0])
    ):
        ad = ads.get((media, ad_id))
        output.append({
            "date": date,
            "media": media,
            "ad_id": ad_id,
            "graduation_year": graduation_year,
            "category": ad["category"] if ad else "未設定",
            "subcategory": ad["subcategory"] if ad else "未設定",
            "placement": ad["placement"] if ad else "未設定",
            "device": ad["device"] if ad else "不明",
            "cv_source": cv_source,
            "cv_count": count,
        })
    return output


def load_all_cv_records(
    spread_init: Callable[[str, str], Sequence[Sequence[Any]]],
    start_date: str | None = None,
    end_date: str | None = None,
    ad_records: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    submissions = normalize_line_records(spread_init(LINE_SPREADSHEET_ID, "貼付：Liny"))
    for source in MEMBER_SOURCES:
        submissions.extend(normalize_member_records(
            spread_init(source["spreadsheet_id"], source["sheet"]), source["media"], source["sheet"]
        ))
    normalized_start = normalize_date(start_date) if start_date else None
    normalized_end = normalize_date(end_date) if end_date else None
    submissions = [
        row for row in submissions
        if (not normalized_start or row["date"] >= normalized_start)
        and (not normalized_end or row["date"] <= normalized_end)
    ]
    ads = list(ad_records) if ad_records is not None else load_all_ad_records(spread_init)
    return enrich_and_aggregate_cv_records(submissions, ads)


def load_all_cv_dataframe(spread_init: Callable, start_date: str | None = None, end_date: str | None = None):
    import pandas as pd
    return pd.DataFrame(load_all_cv_records(spread_init, start_date, end_date), columns=OUTPUT_COLUMNS)
