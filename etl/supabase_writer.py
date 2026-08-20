"""加工済みデータをSupabaseへ1トランザクションで保存する。"""
from __future__ import annotations

import os
import json
from datetime import datetime
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
            "placement": row["placement"], "cv_point": row.get("cv_point"),
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
    def __init__(self, url: str, secret_key: str, post: Callable[..., Any] = standard_post):
        self.url = url.rstrip("/")
        self.secret_key = secret_key
        self.post = post

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

    def save(self, result: dict[str, Any], start_date: str, end_date: str, trigger: str = "schedule") -> Any:
        payload = build_ingest_payload(result, start_date, end_date, trigger)
        try:
            return self._rpc("ingest_ad_analysis", payload)
        except Exception as error:
            try:
                self._rpc("log_failed_sync", {"p_trigger":trigger,"p_error":str(error)})
            except Exception:
                pass
            raise
