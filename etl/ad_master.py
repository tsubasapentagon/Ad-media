"""3メディアの広告マスターを共通カラムへ正規化する。"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
import re
from typing import Any

SPREADSHEET_ID = "1_5eKLVYJEkkv6U8zOXg3XoYAWNPPEu9Fwckev0SBIQY"
CATEGORY_SPREADSHEET_ID = "1DXQ6pxd4UhUOXtx2AdJjLhL9Tac1tU5i8lW1HyTndL8"
CATEGORY_SHEET = "カテゴリ小林"
OUTPUT_COLUMNS = (
    "media",
    "ad_id",
    "category",
    "subcategory",
    "placement",
    "cv_point",
    "lp_number",
    "device",
    "status",
    "start_date",
    "end_date",
    "comment",
)

SOURCE_CONFIG = (
    {
        "media": "Digmedia",
        "sheet": "digmediaデータ",
        "header_row": 3,
        "data_start_row": 4,
        "columns": {
            "ID": "ad_id",
            "カテゴリ": "subcategory",
            "詳細": "placement",
            "CVポイント": "cv_point",
            "LP番号": "lp_number",
            "進捗": "status",
            "開始日": "start_date",
            "終了日": "end_date",
        },
        "optional_columns": {},
    },
    {
        "media": "就活市場",
        "sheet": "マスターデータ",
        "header_row": 0,
        "data_start_row": 1,
        "columns": {
            "ID": "ad_id",
            "カテゴリ": "subcategory",
            "詳細": "placement",
            "CVポイント": "cv_point",
            "LP": "lp_number",
            "進捗": "status",
            "開始日": "start_date",
            "終了日": "end_date",
        },
        "optional_columns": {},
    },
    {
        "media": "ベンチャー就活",
        "sheet": "ベンチャー就活ナビ",
        "header_row": 0,
        "data_start_row": 1,
        "columns": {
            "ID": "ad_id",
            "カテゴリ": "subcategory",
            "位置": "placement",
            "CVポイント": "cv_point",
            "LP": "lp_number",
            "進捗": "status",
            "開始日": "start_date",
            "終了日": "end_date",
        },
        "optional_columns": {"コンテンツ": "comment"},
    },
)


def device_from_ad_id(ad_id: str) -> str:
    normalized = ad_id.strip().lower()
    if normalized.endswith("_sp"):
        return "SP"
    if normalized.endswith("_pc"):
        return "PC"
    return "不明"


def normalize_optional_date(value: Any) -> str | None:
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
            return None
    return None


def normalize_sheet_values(values: Sequence[Sequence[Any]], config: dict[str, Any]) -> list[dict[str, str]]:
    """get_all_values() の結果を媒体共通の辞書へ変換する。"""
    if len(values) <= config["header_row"]:
        raise ValueError(f'{config["sheet"]}: ヘッダー行が見つかりません')

    headers = [str(value).strip() for value in values[config["header_row"]]]
    missing = [source for source in config["columns"] if source not in headers]
    if missing:
        raise ValueError(f'{config["sheet"]}: 必須カラムがありません: {", ".join(missing)}')

    indexes = {target: headers.index(source) for source, target in config["columns"].items()}
    optional_indexes = {
        target: headers.index(source)
        for source, target in config.get("optional_columns", {}).items()
        if source in headers
    }
    records: list[dict[str, str]] = []
    for row in values[config["data_start_row"] :]:
        def cell(target: str) -> str:
            index = indexes.get(target, optional_indexes.get(target))
            if index is None:
                return ""
            return str(row[index]).strip() if index < len(row) else ""

        ad_id = cell("ad_id")
        if not ad_id:
            continue
        records.append(
            {
                "media": config["media"],
                "ad_id": ad_id,
                "category": "",
                "subcategory": cell("subcategory"),
                "placement": cell("placement"),
                "cv_point": cell("cv_point"),
                "lp_number": cell("lp_number"),
                "device": device_from_ad_id(ad_id),
                "status": cell("status"),
                "start_date": normalize_optional_date(cell("start_date")),
                "end_date": normalize_optional_date(cell("end_date")),
                "comment": cell("comment"),
            }
        )
    return records


def normalize_category_mapping(values: Sequence[Sequence[Any]]) -> dict[str, str]:
    """カテゴリ設定をキーに、細分化（共通カテゴリ）を返す。"""
    if not values:
        raise ValueError(f"{CATEGORY_SHEET}: データがありません")
    headers = [str(value).strip() for value in values[0]]
    required = ("カテゴリ設定", "細分化")
    missing = [column for column in required if column not in headers]
    if missing:
        raise ValueError(f'{CATEGORY_SHEET}: 必須カラムがありません: {", ".join(missing)}')
    indexes = {column: headers.index(column) for column in required}
    mapping: dict[str, str] = {}
    for row in values[1:]:
        def value(column: str) -> str:
            index = indexes[column]
            return str(row[index]).strip() if index < len(row) else ""

        source_category = value("カテゴリ設定")
        if not source_category:
            continue
        key = source_category.casefold()
        mapped = value("細分化")
        if key in mapping and mapping[key] != mapped:
            raise ValueError(f"{CATEGORY_SHEET}: カテゴリ設定が競合しています: {source_category}")
        mapping[key] = mapped
    return mapping


def load_all_ad_records(
    spread_init: Callable[[str, str], Sequence[Sequence[Any]]],
    spreadsheet_id: str = SPREADSHEET_ID,
    category_spreadsheet_id: str = CATEGORY_SPREADSHEET_ID,
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for config in SOURCE_CONFIG:
        values = spread_init(spreadsheet_id, config["sheet"])
        records.extend(normalize_sheet_values(values, config))

    category_values = spread_init(category_spreadsheet_id, CATEGORY_SHEET)
    category_mapping = normalize_category_mapping(category_values)
    for record in records:
        record["category"] = category_mapping.get(record["subcategory"].casefold(), "未設定")

    duplicate_keys: set[tuple[str, str]] = set()
    seen: set[tuple[str, str]] = set()
    for record in records:
        key = (record["media"], record["ad_id"])
        if key in seen:
            duplicate_keys.add(key)
        seen.add(key)
    if duplicate_keys:
        duplicates = ", ".join(f"{media}/{ad_id}" for media, ad_id in sorted(duplicate_keys))
        raise ValueError(f"広告IDが重複しています: {duplicates}")
    return records


def load_all_ad_dataframe(
    spread_init: Callable,
    spreadsheet_id: str = SPREADSHEET_ID,
    category_spreadsheet_id: str = CATEGORY_SPREADSHEET_ID,
):
    """既存コードから利用するpandas DataFrame版の入口。"""
    import pandas as pd

    return pd.DataFrame(
        load_all_ad_records(spread_init, spreadsheet_id, category_spreadsheet_id),
        columns=OUTPUT_COLUMNS,
    )
