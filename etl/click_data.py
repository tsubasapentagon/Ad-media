"""GA4の広告クリックイベントへ広告マスター情報を付与する。"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from ad_master import load_all_ad_records
from pv import PROPERTY_IDS, extract_article_id

EVENT_NAME = "SPARKクリック"
OUTPUT_COLUMNS = (
    "date",
    "media",
    "ad_id",
    "article_id",
    "category",
    "subcategory",
    "placement",
    "device",
    "clicks",
)


def build_click_records(
    media: str,
    ga4_rows: Iterable[dict[str, Any]],
    ad_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """クリック行を広告IDで広告マスターへ結合し、日別に合算する。"""
    ads = {
        str(ad["ad_id"]).strip(): ad
        for ad in ad_records
        if ad.get("media") == media and str(ad.get("ad_id", "")).strip()
    }
    totals: dict[tuple[str, str, str | None], int] = defaultdict(int)
    for row in ga4_rows:
        ad_id = str(row.get("customEvent:広告ID", row.get("ID", ""))).strip()
        if not ad_id or ad_id == "(not set)":
            continue
        date = str(row.get("date", "")).strip()
        if not date:
            continue
        try:
            clicks = int(float(str(row.get("eventCount", "0")).replace(",", "")))
        except ValueError as error:
            raise ValueError(f"{media}: クリック数が数値ではありません: {row.get('eventCount')}") from error
        article_id = extract_article_id(str(row.get("pagePath", "")))
        totals[(date, ad_id, article_id)] += clicks

    records: list[dict[str, Any]] = []
    for (date, ad_id, article_id), clicks in sorted(
        totals.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] or "")
    ):
        ad = ads.get(ad_id)
        records.append(
            {
                "date": date,
                "media": media,
                "ad_id": ad_id,
                "article_id": article_id,
                "category": ad["category"] if ad else "未設定",
                "subcategory": ad["subcategory"] if ad else "未設定",
                "placement": ad["placement"] if ad else "未設定",
                "device": ad["device"] if ad else "不明",
                "clicks": clicks,
            }
        )
    return records


def load_all_click_records(
    spread_init: Callable[[str, str], Sequence[Sequence[Any]]],
    get_ga4: Callable[..., Any],
    start_date: str,
    end_date: str,
    ad_records: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    ad_records = list(ad_records) if ad_records is not None else load_all_ad_records(spread_init)
    records: list[dict[str, Any]] = []
    for media, property_id in PROPERTY_IDS.items():
        frame = get_ga4(
            property_id=property_id,
            metrics=["eventCount"],
            dimensions=["date", "customEvent:広告ID", "pagePath"],
            filter_field="eventName",
            filter_value=EVENT_NAME,
            start_date=start_date,
            end_date=end_date,
            limit=100000,
        )
        ga4_rows = frame.to_dict("records") if hasattr(frame, "to_dict") else frame
        records.extend(build_click_records(media, ga4_rows, ad_records))
    return records


def load_all_click_dataframe(
    spread_init: Callable,
    get_ga4: Callable,
    start_date: str,
    end_date: str,
):
    import pandas as pd

    return pd.DataFrame(
        load_all_click_records(spread_init, get_ga4, start_date, end_date),
        columns=OUTPUT_COLUMNS,
    )
