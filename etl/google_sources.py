"""Google SheetsとGA4の本番データ取得アダプター。"""
from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any


def load_service_account_info() -> dict[str, Any]:
    """環境変数のJSONを優先し、ローカル開発時だけ明示ファイルを許可する。"""
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        try:
            info = json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSONが正しいJSONではありません") from error
    else:
        filename = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
        if not filename:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSONが設定されていません")
        try:
            info = json.loads(Path(filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Googleサービスアカウントファイルを読み込めません") from error

    required = ("client_email", "private_key", "token_uri")
    missing = [key for key in required if not str(info.get(key, "")).strip()]
    if missing:
        raise RuntimeError("Google認証情報に必須項目がありません: " + ", ".join(missing))
    return info


@lru_cache(maxsize=1)
def sheets_client():
    import gspread

    return gspread.service_account_from_dict(load_service_account_info())


def spread_init(spreadsheet_id: str, sheet_name: str) -> list[list[str]]:
    """既存コード互換: 指定タブの全セルを二次元配列で返す。"""
    for attempt in range(5):
        try:
            return sheets_client().open_by_key(spreadsheet_id).worksheet(sheet_name).get_all_values()
        except Exception as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            if status not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


@lru_cache(maxsize=1)
def analytics_client():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_info(
        load_service_account_info(),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def get_ga4(
    property_id: str,
    metrics: list[str],
    dimensions: list[str],
    start_date: str,
    end_date: str,
    filter_field: str | None = None,
    filter_value: str | None = None,
    timeout: int = 120,
    limit: int = 100000,
) -> list[dict[str, str]]:
    """GA4をページ分割して全件取得する。limitは1回あたりの取得件数。"""
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Filter,
        FilterExpression,
        Metric,
        RunReportRequest,
    )

    page_size = max(1, min(int(limit), 100000))
    dimension_filter = None
    if filter_field and filter_value:
        dimension_filter = FilterExpression(
            filter=Filter(
                field_name=filter_field,
                string_filter=Filter.StringFilter(
                    value=filter_value,
                    match_type=Filter.StringFilter.MatchType.EXACT,
                ),
            )
        )

    rows: list[dict[str, str]] = []
    offset = 0
    while True:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=name) for name in metrics],
            dimensions=[Dimension(name=name) for name in dimensions],
            dimension_filter=dimension_filter,
            limit=page_size,
            offset=offset,
        )
        response = analytics_client().run_report(request, timeout=timeout)
        page = [
            dict(zip(
                dimensions + metrics,
                [value.value for value in row.dimension_values]
                + [value.value for value in row.metric_values],
            ))
            for row in response.rows
        ]
        rows.extend(page)
        offset += len(page)
        if not page or offset >= response.row_count:
            break
    return rows
