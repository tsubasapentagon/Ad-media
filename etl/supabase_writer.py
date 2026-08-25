"""加工済みデータをSupabaseへ1トランザクションで保存する。"""
from __future__ import annotations

import os
import json
import time
from datetime import datetime, timedelta
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class HttpResponse:
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.text = body
        self.ok = 200 <= status_code < 300

    def json(self) -> Any:
        return json.loads(self.text) if self.text else None


def standard_post(url: str, *, json: dict[str, Any], headers: dict[str, str], timeout: int) -> HttpResponse:
    request = Request(
        url,
        data=__import__("json").dumps(json).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return HttpResponse(response.status, response.read().decode("utf-8"))
    except HTTPError as error:
        return HttpResponse(error.code, error.read().decode("utf-8"))


def iso_date(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    for date_format in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"日付形式が不正です: {value}")


def build_ingest_payload(result: dict[str, Any], start_date: str, end_date: str, trigger: str) -> dict[str, Any]:
    ads = []
    known_ads: set[tuple[str, str]] = set()
    issues: list[dict[str, str]] = []
    for row in result["ads"]:
        key = (row["media"], row["ad_id"])
        known_ads.add(key)
        ads.append({
            "media": row["media"], "ad_id": row["ad_id"], "device": row["device"],
            "placement": row["placement"], "placement_detail": row.get("placement_detail", row["placement"]),
            "cv_point": row.get("cv_point"),
            "lp_number": row.get("lp_number"), "destination": row.get("destination"),
            "comment": row.get("comment"), "category": row.get("category"),
            "subcategory": row.get("subcategory"), "status": row.get("status", ""),
            "start_date": iso_date(row.get("start_date")), "end_date": iso_date(row.get("end_date")),
        })
        if row.get("category") == "未設定":
            issues.append({"issue_type":"category_unmapped","media":row["media"],"source_id":row["ad_id"],"details":row.get("subcategory", "")})
        if row.get("device") == "不明":
            issues.append({"issue_type":"device_unknown","media":row["media"],"source_id":row["ad_id"],"details":"広告ID末尾に_sp/_pcがありません"})

    metrics = []
    for row in result["daily_metrics"]:
        key = (row["media"], row["ad_id"])
        if key not in known_ads:
            issues.append({"issue_type":"ad_not_found","media":row["media"],"source_id":row["ad_id"],"details":"日別実績を保存対象から除外"})
            continue
        metrics.append({
            "metric_date": iso_date(row["date"]), "media": row["media"], "ad_id": row["ad_id"],
            "impressions": int(row["impressions"]), "clicks": int(row["clicks"]),
            "cv": int(row["cv"]), "allocation_status": row["allocation_status"],
        })

    grad_metrics = []
    for row in result["cv_by_grad"]:
        key = (row["media"], row["ad_id"])
        if key not in known_ads:
            continue
        grad_metrics.append({
            "metric_date": iso_date(row["date"]), "media": row["media"], "ad_id": row["ad_id"],
            "graduation_year": int(row["graduation_year"]), "cv": int(row["cv"]),
        })
    return {
        "p_start_date": iso_date(start_date), "p_end_date": iso_date(end_date), "p_trigger": trigger,
        "p_ads": ads, "p_metrics": metrics, "p_grad_metrics": grad_metrics, "p_issues": issues,
    }


class SupabaseWriter:
    def __init__(self, url: str, secret_key: str, post: Callable[..., Any] = standard_post, sleep: Callable[[float], None] = time.sleep):
        self.url = url.rstrip("/")
        self.secret_key = secret_key
        self.post = post
        self.sleep = sleep

    @classmethod
    def from_environment(cls):
        return cls(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    def _rpc(self, function: str, payload: dict[str, Any]) -> Any:
        response = self.post(
            f"{self.url}/rest/v1/rpc/{function}", json=payload, timeout=120,
            headers={"apikey":self.secret_key,"Authorization":f"Bearer {self.secret_key}","Content-Type":"application/json"},
        )
        if not response.ok:
            raise RuntimeError(f"Supabase {function} failed ({response.status_code}): {response.text[:2000]}")
        return response.json()

    def _idempotent_rpc(self, function: str, payload: dict[str, Any]) -> Any:
        """ネットワーク系の一時エラーだけを指数バックオフで再試行する。"""
        for attempt in range(3):
            try:
                return self._rpc(function, payload)
            except RuntimeError as error:
                retryable = any(f"failed ({status})" in str(error) for status in (408, 520, 502, 503, 504))
                if not retryable or attempt == 2:
                    raise
                self.sleep(2 ** attempt)
        raise AssertionError("unreachable")

    def save(self, result: dict[str, Any], start_date: str, end_date: str, trigger: str = "schedule", targets: set[str] | None = None) -> Any:
        targets = targets or {"all"}
        payload = build_ingest_payload(result, start_date, end_date, trigger)
        try:
            # 広告マスターは毎回全件更新する。日別実績とは分離し、巨大な
            # JSON/長時間トランザクションで無料枠DBを圧迫しないようにする。
            if "all" in targets or "ad_master" in targets:
                self._idempotent_rpc("sync_ad_master", {"p_ads": payload["p_ads"]})

            metrics_by_date: dict[str, list[dict[str, Any]]] = {}
            for row in payload["p_metrics"]:
                metrics_by_date.setdefault(row["metric_date"], []).append(row)
            grad_by_date: dict[str, list[dict[str, Any]]] = {}
            for row in payload["p_grad_metrics"]:
                grad_by_date.setdefault(row["metric_date"], []).append(row)

            if "all" in targets:
                current = datetime.strptime(payload["p_start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(payload["p_end_date"], "%Y-%m-%d").date()
                while current <= end:
                    day = current.isoformat()
                    self._idempotent_rpc("replace_ad_metrics", {
                        "p_start_date": day,
                        "p_end_date": day,
                        "p_metrics": metrics_by_date.get(day, []),
                        "p_grad_metrics": grad_by_date.get(day, []),
                    })
                    current += timedelta(days=1)
            elif targets & {"pv", "clicks", "cv"}:
                current = datetime.strptime(payload["p_start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(payload["p_end_date"], "%Y-%m-%d").date()
                while current <= end:
                    day = current.isoformat()
                    self._idempotent_rpc("replace_ad_metric_components", {
                        "p_metric_date": day,
                        "p_components": sorted(targets & {"pv", "clicks", "cv"}),
                        "p_metrics": metrics_by_date.get(day, []),
                        "p_grad_metrics": grad_by_date.get(day, []),
                    })
                    current += timedelta(days=1)

            return self._rpc("record_sync_success", {
                "p_trigger": trigger,
                "p_ads_count": len(payload["p_ads"]) if ("all" in targets or "ad_master" in targets) else 0,
                "p_metrics_count": len(payload["p_metrics"]) if targets & {"all", "pv", "clicks", "cv"} else 0,
                "p_issues": payload["p_issues"],
            })
        except Exception as error:
            try:
                self._rpc("log_failed_sync", {"p_trigger":trigger,"p_error":str(error)})
            except Exception:
                pass
            raise
