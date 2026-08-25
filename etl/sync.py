"""毎朝・手動更新で使う広告分析データ同期の入口。"""
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from google_sources import get_ga4, spread_init
from pipeline import run_pipeline
from supabase_writer import SupabaseWriter

REQUIRED = ("SUPABASE_URL", "SUPABASE_SECRET_KEY", "GOOGLE_SERVICE_ACCOUNT_JSON")


def default_sync_range(today: date | None = None) -> tuple[str, str]:
    """先月1日から昨日まで。日付はGA4互換のYYYY-MM-DD。"""
    today = today or datetime.now(ZoneInfo("Asia/Tokyo")).date()
    yesterday = today - timedelta(days=1)
    previous_month_end = today.replace(day=1) - timedelta(days=1)
    start = previous_month_end.replace(day=1)
    return start.isoformat(), yesterday.isoformat()


def sync_range_from_environment(today: date | None = None) -> tuple[str, str]:
    default_start, default_end = default_sync_range(today)
    start = os.getenv("SYNC_START_DATE") or default_start
    end = os.getenv("SYNC_END_DATE") or default_end
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError as error:
        raise RuntimeError("SYNC_START_DATE/END_DATEはYYYY-MM-DDで指定してください") from error
    if end_date < start_date:
        raise RuntimeError("同期終了日は開始日以降にしてください")
    return start_date.isoformat(), end_date.isoformat()

def main() -> None:
    missing = [name for name in REQUIRED if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing required secrets: " + ", ".join(missing))
    start_date, end_date = sync_range_from_environment()
    trigger = os.getenv("SYNC_TRIGGER", "schedule")
    targets = {value.strip() for value in os.getenv("SYNC_TARGETS", "all").split(",") if value.strip()}
    if not targets or not targets <= {"all", "ad_master", "pv", "clicks", "cv"} or ("all" in targets and len(targets)>1):
        raise RuntimeError("SYNC_TARGETSが不正です")
    print(f"広告データ更新: targets={','.join(sorted(targets))} / {start_date} 〜 {end_date}")
    result = run_pipeline(spread_init, get_ga4, start_date, end_date, targets)
    if "all" in targets and not result["daily_metrics"]:
        raise RuntimeError("分析データが0件のため、既存データを保護して更新を中止しました")
    run_id = SupabaseWriter.from_environment().save(result, start_date, end_date, trigger, targets)
    print(f"広告データ更新完了: run_id={run_id}")

if __name__ == "__main__": main()
