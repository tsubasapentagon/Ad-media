"""広告分析データ加工の実行入口。各マスターは1回だけ読み込む。"""
from __future__ import annotations

from collections.abc import Callable

from ad_master import load_all_ad_records
from click_data import load_all_click_records
from cv import load_all_cv_records
from daily_metrics import build_daily_metrics
from pv import load_all_pv_records


def run_pipeline(spread_init: Callable, get_ga4: Callable, start_date: str, end_date: str, targets: set[str] | None = None):
    targets = targets or {"all"}
    # 実績は期間指定だが、広告マスターは必ず3メディア全件を毎回読み直す。
    ads = load_all_ad_records(spread_init)
    if targets == {"ad_master"}:
        return {"ads": ads, "pv": [], "clicks": [], "cv": [], "daily_metrics": [], "cv_by_grad": []}
    full = "all" in targets
    pv = load_all_pv_records(spread_init, get_ga4, start_date, end_date) if full or "pv" in targets else []
    clicks = load_all_click_records(spread_init, get_ga4, start_date, end_date, ad_records=ads) if full or "clicks" in targets else []
    cvs = load_all_cv_records(spread_init, start_date, end_date, ad_records=ads) if full or "cv" in targets else []
    daily_metrics, cv_by_grad = build_daily_metrics(ads, pv, clicks, cvs)
    return {
        "ads": ads,
        "pv": pv,
        "clicks": clicks,
        "cv": cvs,
        "daily_metrics": daily_metrics,
        "cv_by_grad": cv_by_grad,
    }
