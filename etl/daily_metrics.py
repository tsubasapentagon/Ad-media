"""広告・PV・クリック・CVを日付×媒体×広告IDへ統合する。"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from impressions import allocate_daily_impressions

DAILY_COLUMNS = (
    "date", "media", "ad_id", "category", "subcategory", "placement", "device",
    "impressions", "clicks", "cv", "allocation_status",
)
GRAD_COLUMNS = ("date", "media", "ad_id", "graduation_year", "cv")


def build_daily_metrics(
    ad_records: Iterable[dict[str, Any]],
    pv_records: Iterable[dict[str, Any]],
    click_records: Iterable[dict[str, Any]],
    cv_records: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ads = list(ad_records)
    pv_records = list(pv_records)
    click_records = list(click_records)
    cv_records = list(cv_records)
    metadata = {(ad["media"], ad["ad_id"]): ad for ad in ads}
    values: dict[tuple[str, str, str], dict[str, Any]] = {}

    def metric_row(date: str, media: str, ad_id: str, fallback: dict[str, Any]) -> dict[str, Any]:
        key = (date, media, ad_id)
        if key not in values:
            ad = metadata.get((media, ad_id), fallback)
            values[key] = {
                "date": date,
                "media": media,
                "ad_id": ad_id,
                "category": ad.get("category", "未設定"),
                "subcategory": ad.get("subcategory", "未設定"),
                "placement": ad.get("placement", "未設定"),
                "device": ad.get("device", "不明"),
                "impressions": 0,
                "clicks": 0,
                "cv": 0,
                "allocation_status": "対象PVなし",
            }
        return values[key]

    for row in allocate_daily_impressions(pv_records, ads):
        target = metric_row(row["date"], row["media"], row["ad_id"], row)
        target["impressions"] += int(row["impressions"])
        target["allocation_status"] = row["allocation_status"]

    for row in click_records:
        target = metric_row(row["date"], row["media"], row["ad_id"], row)
        target["clicks"] += int(row["clicks"])

    graduation_totals: dict[tuple[str, str, str, int], int] = defaultdict(int)
    for row in cv_records:
        target = metric_row(row["date"], row["media"], row["ad_id"], row)
        count = int(row["cv_count"])
        target["cv"] += count
        graduation_year = row.get("graduation_year")
        if graduation_year is not None:
            graduation_totals[(row["date"], row["media"], row["ad_id"], int(graduation_year))] += count

    daily = sorted(values.values(), key=lambda row: (
        row["date"], row["media"], row["category"], row["subcategory"],
        row["placement"], row["device"], row["ad_id"],
    ))
    by_grad = [
        {"date": date, "media": media, "ad_id": ad_id, "graduation_year": year, "cv": count}
        for (date, media, ad_id, year), count in sorted(graduation_totals.items())
    ]
    return daily, by_grad


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator * 100 if denominator else None


def summarize_metrics(
    daily_records: Iterable[dict[str, Any]],
    graduation_records: Iterable[dict[str, Any]],
    selected_graduation_year: int,
) -> dict[str, Any]:
    daily_records = list(daily_records)
    impressions = sum(int(row["impressions"]) for row in daily_records)
    clicks = sum(int(row["clicks"]) for row in daily_records)
    cv = sum(int(row["cv"]) for row in daily_records)
    graduation_cv = sum(
        int(row["cv"])
        for row in graduation_records
        if int(row["graduation_year"]) == selected_graduation_year
    )
    return {
        "impressions": impressions,
        "clicks": clicks,
        "ctr": safe_rate(clicks, impressions),
        "cv": cv,
        "cvr": safe_rate(cv, clicks),
        "graduation_year": selected_graduation_year,
        "graduation_cv": graduation_cv,
        "graduation_cv_rate": safe_rate(graduation_cv, cv),
    }


def build_daily_dataframes(ad_records, pv_records, click_records, cv_records):
    import pandas as pd
    daily, by_grad = build_daily_metrics(ad_records, pv_records, click_records, cv_records)
    return pd.DataFrame(daily, columns=DAILY_COLUMNS), pd.DataFrame(by_grad, columns=GRAD_COLUMNS)
