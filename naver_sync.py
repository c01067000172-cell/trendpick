"""maspick.co.kr -> 가비아 중계 서버 -> 네이버 스마트스토어 (항상 전시중지로 등록).

요청은 NAVER_SYNC_SECRET으로 서명(HMAC-SHA256)해서 보내며, 비밀값 자체는 전송하지 않습니다.
"""
import hashlib
import hmac
import json
import os
import secrets
import time

import requests

import seo_server as _backend

RELAY_URL = os.getenv("NAVER_RELAY_URL", "http://1.201.116.28").strip().rstrip("/")
SECRET = os.getenv("NAVER_SYNC_SECRET", "").strip()

DELIVERY_COMPANIES = {
    "CJGLS": "CJ대한통운",
    "HYUNDAI": "롯데택배",
    "HANJIN": "한진택배",
    "KGB": "로젠택배",
    "EPOST": "우체국택배",
}
FIELD_KEYS = (
    "category", "origin", "importer", "manufacturer", "company", "shipping", "returning",
    "fee", "free_over", "return_fee", "exchange_fee", "phone", "as_guide", "material", "color",
    "size", "caution", "packDateText", "warrantyPolicy", "afterServiceDirector", "stock",
    "policy_confirm", "condition",
)
_catalog_cache = {}


class NaverSyncError(Exception):
    pass


def enabled():
    return len(SECRET) >= 32


def _message(detail):
    if isinstance(detail, list):
        return " / ".join(str(x) for x in detail[:8])
    if isinstance(detail, dict):
        for key in ("message", "detail"):
            if detail.get(key):
                inner = detail[key]
                text = _message(inner) if not isinstance(inner, str) else inner
                invalid = detail.get("invalidInputs")
                if isinstance(invalid, list) and invalid:
                    text += " · " + ", ".join(
                        str(i.get("message") or i.get("name") or i) for i in invalid[:5] if isinstance(i, dict)
                    )
                return text
        return json.dumps(detail, ensure_ascii=False)[:400]
    return str(detail)


def _call(method, path, payload=None, timeout=120):
    if not enabled():
        raise NaverSyncError("NAVER_SYNC_SECRET이 설정되지 않았습니다.")
    body = b"" if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ts = str(int(time.time()))
    nonce = secrets.token_hex(16)
    signature = hmac.new(
        SECRET.encode(), f"{method}\n{path}\n{ts}\n{nonce}\n".encode() + body, hashlib.sha256
    ).hexdigest()
    try:
        response = requests.request(
            method,
            RELAY_URL + path,
            data=body if payload is not None else None,
            headers={
                "Content-Type": "application/json",
                "X-TJR-Timestamp": ts,
                "X-TJR-Nonce": nonce,
                "X-TJR-Signature": signature,
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise NaverSyncError("가비아 중계 서버에 연결하지 못했습니다. 잠시 후 다시 시도하세요.") from exc
    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text[:300]}
    if response.status_code >= 400:
        detail = data.get("detail", data) if isinstance(data, dict) else data
        raise NaverSyncError(_message(detail))
    return data


def catalog(kind):
    hit = _catalog_cache.get(kind)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    rows = _call("GET", f"/site/v1/catalog/{kind}", timeout=60)
    _catalog_cache[kind] = (time.time(), rows)
    return rows


def remote_status(product_id):
    return _call("GET", f"/site/v1/products/{product_id}", timeout=30)


# ------------------------------------------------------------------ DB

def _db():
    return _backend.db_client()


def load_setting(product_id):
    rows = (
        _db().table("naver_product_settings").select("*")
        .eq("product_id", str(product_id)).limit(1).execute().data
    ) or []
    return rows[0] if rows else None


def latest_fields():
    rows = (
        _db().table("naver_product_settings").select("fields")
        .order("updated_at", desc=True).limit(1).execute().data
    ) or []
    return dict(rows[0].get("fields") or {}) if rows else {}


def save_setting(product_id, fields, enabled_flag, status=None, origin_no=None, error=None):
    row = {
        "product_id": str(product_id),
        "fields": {k: fields.get(k) for k in FIELD_KEYS if k in fields},
        "sync_enabled": bool(enabled_flag),
        "naver_category_id": str(fields.get("category") or "") or None,
        "manufacturer": fields.get("manufacturer") or None,
        "shipping_fee": int(fields.get("fee") or 0),
        "return_phone": fields.get("phone") or None,
    }
    if status:
        row["sync_status"] = status
    if origin_no is not None:
        row["naver_origin_product_no"] = str(origin_no)
    if error is not None or status in ("synced", "sending"):
        row["sync_error"] = error
    _db().table("naver_product_settings").upsert(row, on_conflict="product_id").execute()


# ------------------------------------------------------------------ publish

def publish(product_id, product_payload, fields):
    """사이트에 저장된 상품을 네이버에 전시중지로 등록합니다. (state, message) 반환."""
    current = load_setting(product_id) or {}
    if current.get("sync_status") == "synced":
        return "synced", f"이미 네이버에 등록된 상품입니다 · 상품번호 {current.get('naver_origin_product_no')}"
    if current.get("sync_status") in ("sending", "unknown"):
        return "unknown", "이전 네이버 전송 결과 확인이 필요합니다. 스마트스토어센터에서 등록 여부를 확인하세요."
    save_setting(product_id, fields, True, status="sending")
    try:
        result = _call("POST", f"/site/v1/products/{product_id}", {"fields": fields, "product": product_payload})
    except NaverSyncError as exc:
        save_setting(product_id, fields, True, status="error", error=str(exc)[:1000])
        return "error", str(exc)
    state = result.get("state")
    detail = result.get("result") or {}
    if state == "published":
        origin_no = detail.get("originProductNo")
        save_setting(product_id, fields, True, status="synced", origin_no=origin_no)
        return "synced", f"네이버 등록 완료 · 상품번호 {origin_no} (전시중지)"
    if state == "error":
        message = _message(detail.get("detail", detail))
        save_setting(product_id, fields, True, status="error", error=message[:1000])
        return "error", message
    save_setting(product_id, fields, True, status="unknown", error="네이버 응답을 확인하지 못했습니다.")
    return "unknown", "네이버 응답을 확인하지 못했습니다. 스마트스토어센터에서 등록 여부를 확인하세요."
