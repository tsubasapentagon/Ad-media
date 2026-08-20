"""GA4と記事マスターから日別・記事別PVの基礎テーブルを作る。"""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from ad_master import CATEGORY_SHEET, CATEGORY_SPREADSHEET_ID, normalize_category_mapping

PROPERTY_IDS = {
    "Digmedia": "250888928",
    "就活市場": "250950712",
    "ベンチャー就活": "282499967",
}

ARTICLE_CONFIG = (
    {"media": "Digmedia", "sheet": "digmedia", "id_column": "id", "category_column": "Category"},
    {"media": "就活市場", "sheet": "就活市場", "id_column": "ID", "category_column": "カテゴリ"},
    {"media": "ベンチャー就活", "sheet": "ベンチャー就活ナビ", "id_column": "ID", "category_column": "カテゴリ"},
)

OUTPUT_COLUMNS = ("date", "media", "article_id", "category", "subcategory", "page_views")
ARTICLE_ID_PATTERN = re.compile(r"/article/(\d+)(?:/|$)")


def extract_article_id(page_path: str) -> str | None:
    match = ARTICLE_ID_PATTERN.search(str(page_path))
    return match.group(1) if match else None


def normalize_article_master(values: Sequence[Sequence[Any]], config: dict[str, str]) -> dict[str, str]:
    """記事IDをキー、小カテゴリを値にした記事マスターを作る。"""
    if not values:
        raise ValueError(f'{config["sheet"]}: 記事マスターが空です')
    headers = [str(value).strip() for value in values[0]]
    required = (config["id_column"], config["category_column"])
    missing = [column for column in required if column not in headers]
    if missing:
        raise ValueError(f'{config["sheet"]}: 必須カラムがありません: {", ".join(missing)}')
    id_index = headers.index(config["id_column"])
    category_index = headers.index(config["category_column"])
    articles: dict[str, str] = {}
    for row in values[1:]:
        article_id = str(row[id_index]).strip() if id_index < len(row) else ""
        subcategory = str(row[category_index]).strip() if category_index < len(row) else ""
        if not article_id:
            continue
        if article_id in articles and articles[article_id] != subcategory:
            raise ValueError(f'{config["sheet"]}: 記事IDのカテゴリが競合しています: {article_id}')
        articles[article_id] = subcategory
    return articles


def build_pv_records(
    media: str,
    ga4_rows: Iterable[dict[str, Any]],
    article_master: dict[str, str],
    category_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """GA4行を日別・記事別にまとめ、カテゴリを付与する。"""
    totals: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in ga4_rows:
        article_id = extract_article_id(str(row.get("pagePath", "")))
        if not article_id:
            continue
        date = str(row.get("date", "")).strip()
        if not date:
            continue
        try:
            page_views = int(float(str(row.get("screenPageViews", "0")).replace(",", "")))
        except ValueError as error:
            raise ValueError(f"{media}: PVが数値ではありません: {row.get('screenPageViews')}") from error
        subcategory = article_master.get(article_id, "未設定") or "未設定"
        category = category_mapping.get(subcategory.casefold(), "未設定")
        totals[(date, article_id, category, subcategory)] += page_views

    return [
        {
            "date": date,
            "media": media,
            "article_id": article_id,
            "category": category,
            "subcategory": subcategory,
            "page_views": page_views,
        }
        for (date, article_id, category, subcategory), page_views in sorted(totals.items())
    ]


def load_all_pv_records(
    spread_init: Callable[[str, str], Sequence[Sequence[Any]]],
    get_ga4: Callable[..., Any],
    start_date: str,
    end_date: str,
    spreadsheet_id: str = CATEGORY_SPREADSHEET_ID,
) -> list[dict[str, Any]]:
    category_mapping = normalize_category_mapping(spread_init(spreadsheet_id, CATEGORY_SHEET))
    records: list[dict[str, Any]] = []
    for config in ARTICLE_CONFIG:
        article_master = normalize_article_master(spread_init(spreadsheet_id, config["sheet"]), config)
        frame = get_ga4(
            property_id=PROPERTY_IDS[config["media"]],
            metrics=["screenPageViews", "totalUsers"],
            dimensions=["date", "pagePath"],
            start_date=start_date,
            end_date=end_date,
            limit=100000,
        )
        ga4_rows = frame.to_dict("records") if hasattr(frame, "to_dict") else frame
        records.extend(build_pv_records(config["media"], ga4_rows, article_master, category_mapping))
    return records


def load_all_pv_dataframe(spread_init: Callable, get_ga4: Callable, start_date: str, end_date: str):
    import pandas as pd

    return pd.DataFrame(
        load_all_pv_records(spread_init, get_ga4, start_date, end_date),
        columns=OUTPUT_COLUMNS,
    )
