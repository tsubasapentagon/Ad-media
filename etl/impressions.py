"""記事PVを同じ小カテゴリの広告へSP 70%・PC 30%で日別配賦する。"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

OUTPUT_COLUMNS = (
    "date", "media", "ad_id", "category", "subcategory", "placement",
    "device", "impressions", "allocation_status",
)


def _allocate_integer(total: int, ad_ids: list[str]) -> dict[str, int]:
    """整数の合計を維持し、端数は広告ID順へ1ずつ配る。"""
    if not ad_ids:
        return {}
    ordered = sorted(ad_ids)
    each, remainder = divmod(total, len(ordered))
    return {ad_id: each + (1 if index < remainder else 0) for index, ad_id in enumerate(ordered)}


def is_ad_active_on(ad: dict[str, Any], date: str) -> bool:
    start_date = ad.get("start_date")
    end_date = ad.get("end_date")
    return (not start_date or date >= start_date) and (not end_date or date <= end_date)


def allocate_daily_impressions(
    pv_records: Iterable[dict[str, Any]],
    ad_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """PVを日付・媒体・小カテゴリごとにまとめて対象広告へ割り当てる。"""
    ads = list(ad_records)
    pv_records = list(pv_records)
    pv_totals: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in pv_records:
        key = (row["date"], row["media"], row["category"], row["subcategory"])
        pv_totals[key] += int(row["page_views"])

    output: list[dict[str, Any]] = []
    allocated_keys: set[tuple[str, str]] = set()
    for (date, media, category, subcategory), page_views in sorted(pv_totals.items()):
        matching = [
            ad for ad in ads
            if ad["media"] == media
            and ad["subcategory"].casefold() == subcategory.casefold()
            and is_ad_active_on(ad, date)
        ]
        by_device = {
            "SP": [ad for ad in matching if ad["device"] == "SP"],
            "PC": [ad for ad in matching if ad["device"] == "PC"],
        }
        device_totals = {"SP": round(page_views * 0.7), "PC": page_views - round(page_views * 0.7)}
        for device in ("SP", "PC"):
            allocation = _allocate_integer(device_totals[device], [ad["ad_id"] for ad in by_device[device]])
            for ad in by_device[device]:
                allocated_keys.add((date, f'{ad["media"]}\0{ad["ad_id"]}'))
                output.append({
                    "date": date,
                    "media": media,
                    "ad_id": ad["ad_id"],
                    "category": category,
                    "subcategory": subcategory,
                    "placement": ad["placement"],
                    "device": device,
                    "impressions": allocation[ad["ad_id"]],
                    "allocation_status": "配賦済み",
                })

    # PVと一致しなかった広告や端末不明広告も一覧から消さない。
    dates = sorted({row["date"] for row in pv_records})
    for date in dates:
        for ad in ads:
            allocation_key = (date, f'{ad["media"]}\0{ad["ad_id"]}')
            if allocation_key in allocated_keys:
                continue
            if not is_ad_active_on(ad, date):
                reason = "掲載期間外"
            elif ad["device"] == "不明":
                reason = "端末不明"
            else:
                reason = "対象PVなし"
            output.append({
                "date": date,
                "media": ad["media"],
                "ad_id": ad["ad_id"],
                "category": ad["category"],
                "subcategory": ad["subcategory"],
                "placement": ad["placement"],
                "device": ad["device"],
                "impressions": 0,
                "allocation_status": reason,
            })

    return sorted(output, key=lambda row: (
        row["date"], row["media"], row["category"], row["subcategory"],
        row["placement"], row["device"], row["ad_id"],
    ))
