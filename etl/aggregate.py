"""Pure aggregation rules shared by the scheduled importer and tests."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Ad:
    media: str
    ad_id: str
    device: str

def allocate_impressions(page_views: int, ads: Iterable[Ad]) -> dict[tuple[str, str], int]:
    """Allocate page PV to matching ads: SP 70%, PC 30%, evenly per device."""
    ads = list(ads)
    result: dict[tuple[str, str], int] = {}
    for device, ratio in (("SP", .7), ("PC", .3)):
        matching = [ad for ad in ads if ad.device == device]
        if not matching:
            continue
        total = round(page_views * ratio)
        each, remainder = divmod(total, len(matching))
        for index, ad in enumerate(sorted(matching, key=lambda x: (x.media, x.ad_id))):
            result[(ad.media, ad.ad_id)] = each + (1 if index < remainder else 0)
    return result

def count_submissions(rows: Iterable[dict]) -> dict[tuple[str, str], int]:
    """Each submission is one CV; repeated submissions are intentionally retained."""
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        counts[(row["media"], row["ad_id"])] += 1
    return dict(counts)
