"""Public HTML, SEO, and payment routes alongside the existing Streamlit storefront."""
import asyncio
import base64
import json
import os
import re
import time
import uuid
from html import escape as esc
from urllib.parse import quote, urlencode, urlparse
from xml.sax.saxutils import escape as xml_escape

import requests

SITE = "https://www.maspick.co.kr"
STORE_NAME = "TWO J ROAD"
STORE_ADDRESS = "경기 포천시 내촌면 금강로3224번길 11-7"
CATEGORIES = {"bike": "중고 바이크", "wear": "바이크 의류", "gear": "바이크 용품"}

# Official Toss Payments documentation test keys. They cannot charge real money.
# When both merchant keys are added as Render env vars, those values take priority.
DOCS_TEST_CLIENT_KEY = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"
DOCS_TEST_SECRET_KEY = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"
_env_client_key = os.getenv("TOSS_CLIENT_KEY", "").strip()
_env_secret_key = os.getenv("TOSS_SECRET_KEY", "").strip()
if _env_client_key and _env_secret_key:
    TOSS_CLIENT_KEY = _env_client_key
    TOSS_SECRET_KEY = _env_secret_key
else:
    TOSS_CLIENT_KEY = DOCS_TEST_CLIENT_KEY
    TOSS_SECRET_KEY = DOCS_TEST_SECRET_KEY
TOSS_TEST_MODE = TOSS_CLIENT_KEY.startswith("test_") or TOSS_SECRET_KEY.startswith("test_")

_cache = {"time": 0, "rows": None}
_client_cache = {"client": None, "sig": None}
_order_rate = {}


def db_client():
    from supabase import create_client
    from jinbike_supabase_storage import _validate_server_key

    url = os.environ["SUPABASE_URL"].strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    _validate_server_key(key)
    sig = (url, key)
    if _client_cache["client"] is None or _client_cache["sig"] != sig:
        _client_cache["client"] = create_client(url, key)
        _client_cache["sig"] = sig
    return _client_cache["client"]


def products():
    if _cache["rows"] is not None and time.monotonic() - _cache["time"] < 30:
        return _cache["rows"]
    client = db_client()
    rows = []
    offset = 0
    while True:
        batch = (
            client.table("products")
            .select(
                "id,type,category,subcategory,brand,name,price,condition,"
                "image,images,description,demo"
            )
            .order("id")
            .range(offset, offset + 999)
            .execute()
            .data
        )
        if not isinstance(batch, list):
            raise ValueError("Invalid products response")
        rows.extend(row for row in batch if not row.get("demo"))
        if len(batch) < 1000:
            break
        offset += 1000
    _cache.update(time=time.monotonic(), rows=rows)
    return rows


def product_by_id(product_id):
    product_id = str(product_id or "").strip()
    if not product_id:
        return None
    row = (
        db_client()
        .table("products")
        .select(
            "id,type,category,subcategory,brand,name,price,condition,"
            "image,images,description,demo"
        )
        .eq("id", product_id)
        .limit(1)
        .execute()
        .data
    )
    if not isinstance(row, list) or not row:
        return None
    product = row[0]
    if product.get("demo"):
        return None
    return product


def description(product):
    value = str(product.get("description") or "")
    if value.startswith("DOOJAY_DETAIL_V1:"):
        try:
            data = json.loads(value.split(":", 1)[1])
            return str(data.get("text", "")), data.get("files", [])
        except (ValueError, AttributeError):
            return "", []
    return value, []


def image(url, alt):
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        return ""
    return (
        f'<img src="{esc(url, quote=True)}" alt="{esc(alt, quote=True)}" '
        'loading="lazy">'
    )


def page(title, summary, path, body):
    url = esc(SITE + path, quote=True)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(summary, quote=True)}">
<link rel="canonical" href="{url}"><meta property="og:title" content="{esc(title, quote=True)}">
<meta property="og:description" content="{esc(summary, quote=True)}"><meta property="og:url" content="{url}">
<meta property="og:type" content="website"><style>
body{{background:#080808;color:#eee;font:16px/1.7 sans-serif;max-width:1100px;margin:auto;padding:24px}}
a{{color:#ff8a24}}nav{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:24px}}
img{{display:block;max-width:100%;max-height:700px;object-fit:contain;margin:12px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:20px}}
.card{{border:1px solid #333;padding:16px}}.card img{{width:100%;height:220px}}
.text{{white-space:pre-wrap}}h1{{font-size:28px}}
.buy{{display:inline-block;background:#ff6900;color:#fff;padding:12px 20px;font-weight:800;border-radius:4px}}
.notice{{border:1px solid #4a3420;background:#1b120b;padding:12px 14px;margin:18px 0}}
</style></head><body>
<nav><a href="/">TWO J ROAD</a><a href="/catalog/bike">중고 바이크</a><a href="/catalog/wear">바이크 의류</a><a href="/catalog/gear">바이크 용품</a></nav>
{body}<footer><p>포천 TWO J ROAD · {esc(STORE_ADDRESS)}</p></footer></body></html>'''


def product_page(p):
    name = str(p.get("name") or "상품")
    text, files = description(p)
    summary = " ".join(
        (str(p.get("brand") or ""), name, str(p.get("condition") or ""), text)
    ).strip()
    summary = " ".join(summary.split())[:150] or name
    pics = p.get("images") or [p.get("image")]
    body = f'<h1>{esc(name)}</h1><p>{esc(str(p.get("brand") or ""))}</p>'
    body += f'<p>{int(p.get("price") or 0):,}원 · {esc(str(p.get("condition") or ""))}</p>'
    body += "".join(image(url, name) for url in pics)
    body += f'<div class="text">{esc(text)}</div>'
    for item in files:
        url = item.get("url", "")
        if item.get("kind") == "image":
            body += image(url, item.get("name", name))
        elif isinstance(url, str) and url.startswith(("http://", "https://")):
            body += (
                f'<p><a href="{esc(url, quote=True)}">'
                f'{esc(item.get("name", "상세 자료"))}</a></p>'
            )
    detail = "/?" + urlencode({"page": "detail", "id": p["id"]})
    body += f'<p><a href="{esc(detail, quote=True)}">상품 상세 보기</a></p>'
    if str(p.get("condition") or "") == "판매중" and int(p.get("price") or 0) > 0:
        label = "테스트 결제" if TOSS_TEST_MODE else "구매하기"
        body += (
            f'<p><a class="buy" href="/checkout/{quote(str(p["id"]), safe="")}">'
            f'{label}</a></p>'
        )
        if TOSS_TEST_MODE:
            body += '<div class="notice">현재 테스트 결제 모드이며 실제 금액은 청구되지 않습니다.</div>'
    return page(
        name + " | TWO J ROAD",
        summary,
        "/products/" + quote(str(p["id"]), safe=""),
        body,
    )


def catalog_page(kind, rows):
    label = CATEGORIES[kind]
    filtered = [p for p in rows if p.get("type") == kind]
    body = f'<h1>{label}</h1><div class="grid">'
    for p in filtered:
        name = str(p.get("name") or "상품")
        url = "/products/" + quote(str(p["id"]), safe="")
        body += (
            f'<article class="card"><a href="{url}">{image(p.get("image"), name)}'
            f'<h2>{esc(name)}</h2></a><p>{int(p.get("price") or 0):,}원</p></article>'
        )
    body += "</div>" if filtered else "</div><p>등록된 상품이 없습니다.</p>"
    return page(
        label + " | TWO J ROAD",
        "TWO J ROAD의 " + label + " 상품과 가격을 확인하세요.",
        "/catalog/" + kind,
        body,
    )


def sitemap(rows):
    urls = [SITE + "/"] + [SITE + "/catalog/" + kind for kind in CATEGORIES]
    urls += [SITE + "/products/" + quote(str(p["id"]), safe="") for p in rows]
    return (
        '<?xml version="1.0" encoding="UTF-8"?><urlset '
        'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join("<url><loc>" + xml_escape(url) + "</loc></url>" for url in urls)
        + "</urlset>"
    )


def _clean_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) not in (10, 11) or not digits.startswith("01"):
        raise ValueError("휴대폰 번호를 정확히 입력해 주세요.")
    return digits


def _clean_email(value):
    value = str(value or "").strip()
    if not value:
        return None
    if len(value) > 120 or "@" not in value or "." not in value.rsplit("@", 1)[-1]:
        raise ValueError("이메일 형식을 확인해 주세요.")
    return value


def _validate_order_payload(payload):
    product_id = str(payload.get("product_id") or "").strip()
    buyer_name = str(payload.get("buyer_name") or "").strip()
    buyer_phone = _clean_phone(payload.get("buyer_phone"))
    buyer_email = _clean_email(payload.get("buyer_email"))
    postal_code = str(payload.get("postal_code") or "").strip()[:20]
    address1 = str(payload.get("address1") or "").strip()
    address2 = str(payload.get("address2") or "").strip()[:200]
    if not product_id:
        raise ValueError("상품 정보가 없습니다.")
    if not 2 <= len(buyer_name) <= 50:
        raise ValueError("주문자 이름을 2~50자로 입력해 주세요.")
    if not 3 <= len(address1) <= 200:
        raise ValueError("배송 주소를 입력해 주세요.")
    if payload.get("privacy_agreed") is not True:
        raise ValueError("주문 처리를 위한 개인정보 수집 동의가 필요합니다.")
    return {
        "product_id": product_id,
        "buyer_name": buyer_name,
        "buyer_phone": buyer_phone,
        "buyer_email": buyer_email,
        "postal_code": postal_code or None,
        "address1": address1,
        "address2": address2 or None,
    }


def create_order(payload):
    data = _validate_order_payload(payload)
    product = product_by_id(data["product_id"])
    if product is None:
        raise ValueError("판매 상품을 찾을 수 없습니다.")
    if str(product.get("condition") or "") != "판매중":
        raise ValueError("현재 결제할 수 없는 상품입니다.")
    price = int(product.get("price") or 0)
    if price <= 0:
        raise ValueError("결제 가능한 상품 가격이 설정되지 않았습니다.")

    quantity = 1
    amount = price
    order_id = "TJR_" + time.strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:12]
    row = {
        "order_id": order_id,
        "product_id": str(product["id"]),
        "product_name": str(product.get("name") or "상품")[:200],
        "product_type": str(product.get("type") or "")[:30],
        "unit_price": price,
        "quantity": quantity,
        "amount": amount,
        "buyer_name": data["buyer_name"],
        "buyer_phone": data["buyer_phone"],
        "buyer_email": data["buyer_email"],
        "postal_code": data["postal_code"],
        "address1": data["address1"],
        "address2": data["address2"],
        "status": "pending",
        "is_test": TOSS_TEST_MODE,
    }
    db_client().table("orders").insert(row).execute()
    return {
        "order_id": order_id,
        "order_name": row["product_name"][:100],
        "amount": amount,
        "buyer_name": row["buyer_name"],
        "buyer_phone": row["buyer_phone"],
        "buyer_email": row["buyer_email"],
        "is_test": TOSS_TEST_MODE,
    }


def _basic_auth(secret_key):
    token = base64.b64encode((secret_key + ":").encode("utf-8")).decode("ascii")
    return "Basic " + token


def _toss_post(path, payload, idempotency_key=None):
    headers = {
        "Authorization": _basic_auth(TOSS_SECRET_KEY),
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    response = requests.post(
        "https://api.tosspayments.com" + path,
        headers=headers,
        json=payload,
        timeout=15,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"code": "INVALID_RESPONSE", "message": response.text[:500]}
    return response.status_code, body


def _order_row(order_id):
    rows = (
        db_client()
        .table("orders")
        .select("*")
        .eq("order_id", str(order_id))
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if isinstance(rows, list) and rows else None


def confirm_order(payment_key, order_id, redirected_amount):
    payment_key = str(payment_key or "").strip()
    order_id = str(order_id or "").strip()
    try:
        redirected_amount = int(redirected_amount)
    except (TypeError, ValueError):
        raise ValueError("결제 금액 정보가 올바르지 않습니다.")

    order = _order_row(order_id)
    if order is None:
        raise ValueError("주문을 찾을 수 없습니다.")
    db_amount = int(order.get("amount") or 0)
    if redirected_amount != db_amount:
        db_client().table("orders").update(
            {
                "status": "failed",
                "failure_code": "AMOUNT_MISMATCH",
                "failure_message": "결제 요청 금액과 주문 금액이 다릅니다.",
            }
        ).eq("order_id", order_id).execute()
        raise ValueError("결제 금액 검증에 실패했습니다.")

    if order.get("status") in ("paid", "awaiting_deposit"):
        if str(order.get("payment_key") or "") != payment_key:
            raise ValueError("이미 다른 결제로 처리된 주문입니다.")
        return {
            "order_id": order_id,
            "amount": db_amount,
            "status": str(order.get("status")),
            "method": str(order.get("payment_method") or ""),
            "provider": str(order.get("easy_pay_provider") or ""),
            "is_test": bool(order.get("is_test")),
        }

    if order.get("status") == "canceled":
        raise ValueError("이미 취소된 주문입니다.")

    status_code, result = _toss_post(
        "/v1/payments/confirm",
        {
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": db_amount,
        },
    )

    if status_code < 200 or status_code >= 300:
        code = str(result.get("code") or "PAYMENT_CONFIRM_FAILED")[:100]
        message = str(result.get("message") or "결제 승인에 실패했습니다.")[:500]
        new_status = "pending" if status_code >= 500 else "failed"
        db_client().table("orders").update(
            {
                "status": new_status,
                "failure_code": code,
                "failure_message": message,
            }
        ).eq("order_id", order_id).execute()
        raise RuntimeError(message)

    if str(result.get("orderId") or "") != order_id:
        raise RuntimeError("토스페이먼츠 주문번호 검증에 실패했습니다.")
    if int(result.get("totalAmount") or 0) != db_amount:
        raise RuntimeError("토스페이먼츠 승인 금액 검증에 실패했습니다.")

    toss_status = str(result.get("status") or "")
    if toss_status == "DONE":
        order_status = "paid"
    elif toss_status == "WAITING_FOR_DEPOSIT":
        order_status = "awaiting_deposit"
    else:
        order_status = "pending"

    method = str(result.get("method") or "")
    easy = result.get("easyPay")
    provider = str(easy.get("provider") or "") if isinstance(easy, dict) else ""
    approved_at = result.get("approvedAt")

    client = db_client()
    client.table("payments").upsert(
        {
            "order_id": order_id,
            "payment_key": payment_key,
            "amount": db_amount,
            "status": toss_status or order_status,
            "method": method or None,
            "easy_pay_provider": provider or None,
            "approved_at": approved_at,
            "raw_response": result,
            "is_test": TOSS_TEST_MODE,
        },
        on_conflict="payment_key",
    ).execute()
    client.table("orders").update(
        {
            "status": order_status,
            "payment_key": payment_key,
            "payment_method": method or None,
            "easy_pay_provider": provider or None,
            "approved_at": approved_at,
            "failure_code": None,
            "failure_message": None,
        }
    ).eq("order_id", order_id).execute()

    if order_status == "paid" and str(order.get("product_type") or "") == "bike":
        client.table("products").update({"condition": "예약중"}).eq(
            "id", order.get("product_id")
        ).eq("condition", "판매중").execute()
        _cache.update(time=0, rows=None)

    return {
        "order_id": order_id,
        "amount": db_amount,
        "status": order_status,
        "method": method,
        "provider": provider,
        "is_test": TOSS_TEST_MODE,
    }


def mark_failed_order(order_id, code, message):
    if not order_id:
        return
    try:
        db_client().table("orders").update(
            {
                "status": "failed",
                "failure_code": str(code or "")[:100],
                "failure_message": str(message or "")[:500],
            }
        ).eq("order_id", str(order_id)).eq("status", "pending").execute()
    except Exception:
        pass


def admin_orders(limit=100):
    rows = (
        db_client()
        .table("orders")
        .select(
            "order_id,product_id,product_name,product_type,unit_price,quantity,"
            "amount,buyer_name,buyer_phone,buyer_email,postal_code,address1,address2,"
            "status,payment_key,payment_method,easy_pay_provider,approved_at,canceled_at,"
            "failure_code,failure_message,is_test,created_at,updated_at"
        )
        .order("created_at", desc=True)
        .limit(max(1, min(int(limit), 500)))
        .execute()
        .data
    )
    return rows if isinstance(rows, list) else []


def cancel_order(order_id, reason):
    order = _order_row(order_id)
    if order is None:
        raise ValueError("주문을 찾을 수 없습니다.")
    if order.get("status") not in ("paid", "partial_canceled"):
        raise ValueError("결제완료 주문만 취소할 수 있습니다.")
    payment_key = str(order.get("payment_key") or "").strip()
    if not payment_key:
        raise ValueError("결제키가 없는 주문입니다.")
    if "가상계좌" in str(order.get("payment_method") or ""):
        raise ValueError("가상계좌 환불은 환불계좌 정보가 필요해 관리자 자동취소에서 제외했습니다.")
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("취소 사유를 입력해 주세요.")
    status_code, result = _toss_post(
        f'/v1/payments/{quote(payment_key, safe="")}/cancel',
        {"cancelReason": reason[:200]},
        idempotency_key="cancel-" + str(order_id),
    )
    if status_code < 200 or status_code >= 300:
        raise RuntimeError(str(result.get("message") or "결제 취소에 실패했습니다."))

    toss_status = str(result.get("status") or "CANCELED")
    canceled_at = None
    cancels = result.get("cancels")
    if isinstance(cancels, list) and cancels:
        canceled_at = cancels[-1].get("canceledAt")

    client = db_client()
    client.table("orders").update(
        {
            "status": "canceled" if toss_status == "CANCELED" else "partial_canceled",
            "canceled_at": canceled_at,
        }
    ).eq("order_id", str(order_id)).execute()
    client.table("payments").update(
        {
            "status": toss_status,
            "canceled_at": canceled_at,
            "raw_response": result,
        }
    ).eq("payment_key", payment_key).execute()

    if toss_status == "CANCELED" and str(order.get("product_type") or "") == "bike":
        client.table("products").update({"condition": "판매중"}).eq(
            "id", order.get("product_id")
        ).eq("condition", "예약중").execute()
        _cache.update(time=0, rows=None)

    return result


def checkout_page(product):
    name = str(product.get("name") or "상품")
    brand = str(product.get("brand") or "")
    amount = int(product.get("price") or 0)
    product_id = str(product.get("id") or "")
    pics = product.get("images") or [product.get("image")]
    hero = next(
        (u for u in pics if isinstance(u, str) and u.startswith(("http://", "https://"))),
        "",
    )
    mode_badge = (
        '<div class="test-banner"><b>TEST 결제</b> · 실제 금액은 청구되지 않습니다. 실제 고객 주문에는 사용하지 마세요.</div>'
        if TOSS_TEST_MODE
        else ""
    )
    client_key_js = json.dumps(TOSS_CLIENT_KEY)
    product_id_js = json.dumps(product_id)
    amount_js = json.dumps(amount)
    name_js = json.dumps(name)
    image_html = image(hero, name) if hero else ""
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} 결제 | TWO J ROAD</title>
<script src="https://js.tosspayments.com/v2/standard"></script>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#080808;color:#eee;font-family:Arial,sans-serif}}
.wrap{{max-width:920px;margin:0 auto;padding:24px 18px 60px}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}}
.logo{{font-size:28px;font-weight:900;color:#ff6900}}a{{color:#ff8a24;text-decoration:none}}
.grid{{display:grid;grid-template-columns:1fr 1.15fr;gap:24px}}.panel{{background:#111;border:1px solid #2a2a2a;padding:20px}}
.product img{{width:100%;height:300px;object-fit:contain;background:#090909}}
.price{{font-size:28px;font-weight:900;margin:8px 0 18px}}label{{display:block;margin:12px 0 6px;color:#bbb}}
input{{width:100%;padding:13px;background:#0b0b0b;border:1px solid #3a3a3a;color:#fff;border-radius:4px}}
.addr-row{{display:grid;grid-template-columns:130px 1fr;gap:8px}}
button{{width:100%;border:0;background:#ff6900;color:#fff;font-size:17px;font-weight:900;padding:15px;margin-top:18px;cursor:pointer;border-radius:4px}}
button:disabled{{opacity:.45;cursor:not-allowed}}.test-banner{{background:#2b190b;border:1px solid #7d491c;padding:12px;margin-bottom:18px}}
.small{{font-size:13px;color:#aaa;line-height:1.6}}.agree{{display:flex;gap:8px;align-items:flex-start;margin:18px 0}}
.agree input{{width:auto;margin-top:4px}}#msg{{min-height:24px;margin-top:10px;color:#ffb36b}}
#payment-method,#agreement{{background:white;border-radius:6px;margin-top:16px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr}}.product img{{height:220px}}}}
</style></head><body><div class="wrap">
<div class="top"><div class="logo">TWO J ROAD</div><a href="/?page=detail&id={esc(product_id, quote=True)}">상품으로 돌아가기</a></div>
{mode_badge}
<div class="grid">
<section class="panel product">
{image_html}
<div class="small">{esc(brand)}</div><h1>{esc(name)}</h1>
<div class="price">{amount:,}원</div>
<div class="small">현재 결제 연동 단계에서는 1회 주문 수량이 1개로 고정됩니다.</div>
</section>
<section class="panel">
<h2>주문 정보</h2>
<label for="buyer_name">주문자명</label><input id="buyer_name" maxlength="50" autocomplete="name">
<label for="buyer_phone">휴대폰</label><input id="buyer_phone" inputmode="tel" placeholder="01012345678" autocomplete="tel">
<label for="buyer_email">이메일 (선택)</label><input id="buyer_email" type="email" maxlength="120" autocomplete="email">
<label>배송지</label>
<div class="addr-row"><input id="postal_code" maxlength="20" placeholder="우편번호"><input id="address1" maxlength="200" placeholder="기본 주소"></div>
<input id="address2" maxlength="200" placeholder="상세 주소" style="margin-top:8px">
<div class="agree"><input id="privacy" type="checkbox"><label for="privacy" style="margin:0">
주문·결제·배송·환불 처리를 위한 개인정보 수집 및 이용에 동의합니다.
<span class="small">주문 처리에 필요한 최소 정보만 저장합니다.</span></label></div>
<div id="payment-method"></div>
<div id="agreement"></div>
<button id="payment-button" disabled>{"테스트 결제하기" if TOSS_TEST_MODE else "결제하기"}</button>
<div id="msg"></div>
</section></div></div>
<script>
const PRODUCT_ID = {product_id_js};
const PRODUCT_NAME = {name_js};
const AMOUNT = {amount_js};
const CLIENT_KEY = {client_key_js};
function value(id) {{ return document.getElementById(id).value.trim(); }}
function message(text) {{ document.getElementById("msg").textContent = text || ""; }}
async function main() {{
  const button = document.getElementById("payment-button");
  try {{
    const tossPayments = TossPayments(CLIENT_KEY);
    const widgets = tossPayments.widgets({{customerKey: TossPayments.ANONYMOUS}});
    await widgets.setAmount({{currency:"KRW", value:AMOUNT}});
    await Promise.all([
      widgets.renderPaymentMethods({{selector:"#payment-method", variantKey:"DEFAULT"}}),
      widgets.renderAgreement({{selector:"#agreement", variantKey:"AGREEMENT"}}),
    ]);
    button.disabled = false;
    button.addEventListener("click", async () => {{
      if (!document.getElementById("privacy").checked) {{
        message("개인정보 수집 동의가 필요합니다.");
        return;
      }}
      button.disabled = true;
      message("주문 정보를 확인하고 있습니다.");
      try {{
        const response = await fetch("/api/orders/create", {{
          method:"POST",
          headers:{{"Content-Type":"application/json"}},
          body:JSON.stringify({{
            product_id:PRODUCT_ID,
            buyer_name:value("buyer_name"),
            buyer_phone:value("buyer_phone"),
            buyer_email:value("buyer_email"),
            postal_code:value("postal_code"),
            address1:value("address1"),
            address2:value("address2"),
            privacy_agreed:true
          }})
        }});
        const order = await response.json();
        if (!response.ok) throw new Error(order.message || "주문 생성에 실패했습니다.");
        if (Number(order.amount) !== AMOUNT) {{
          throw new Error("상품 금액이 변경되었습니다. 페이지를 새로고침해 주세요.");
        }}
        message("");
        await widgets.requestPayment({{
          orderId: order.order_id,
          orderName: order.order_name || PRODUCT_NAME,
          successUrl: window.location.origin + "/payment/success",
          failUrl: window.location.origin + "/payment/fail",
          customerName: order.buyer_name,
          customerEmail: order.buyer_email || undefined,
          customerMobilePhone: order.buyer_phone
        }});
      }} catch (error) {{
        console.error(error);
        message(error && error.message ? error.message : "결제를 시작하지 못했습니다.");
        button.disabled = false;
      }}
    }});
  }} catch (error) {{
    console.error(error);
    message("결제 모듈을 불러오지 못했습니다.");
  }}
}}
main();
</script></body></html>'''


def payment_result_page(title, message, ok=True, details=""):
    tone = "#17351f" if ok else "#3a1717"
    border = "#2e7542" if ok else "#8d3333"
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | TWO J ROAD</title>
<style>body{{background:#080808;color:#eee;font-family:Arial,sans-serif;margin:0}}
.box{{max-width:650px;margin:70px auto;padding:28px;background:#111;border:1px solid #333}}
.result{{background:{tone};border:1px solid {border};padding:18px;margin:18px 0}}
a{{display:inline-block;background:#ff6900;color:#fff;text-decoration:none;padding:12px 18px;font-weight:800}}
small{{color:#aaa}}</style></head><body><div class="box"><h1>{esc(title)}</h1>
<div class="result">{esc(message)}</div>{details}
<p><a href="/">TWO J ROAD 홈으로</a></p>
<small>{"테스트 결제 모드 · 실제 청구 없음" if TOSS_TEST_MODE else STORE_NAME}</small>
</div></body></html>'''


def _request_ip(request):
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",", 1)[0].strip() if forwarded else request.remote_ip) or "unknown"


def _allow_order_attempt(ip):
    now = time.monotonic()
    recent = [t for t in _order_rate.get(ip, []) if now - t < 600]
    if len(recent) >= 10:
        _order_rate[ip] = recent
        return False
    recent.append(now)
    _order_rate[ip] = recent
    return True


ALLOWED_HOSTS = {
    "www.maspick.co.kr",
    "maspick.co.kr",
}

def _same_origin(request):
    origin = request.headers.get("Origin")
    if not origin:
        return True
    try:
        origin_host = (urlparse(origin).hostname or "").lower()
        forwarded_host = (
            request.headers.get("X-Forwarded-Host")
            or request.headers.get("Host")
            or ""
        ).split(",",1)[0].strip().lower()
        return origin_host in ALLOWED_HOSTS and forwarded_host in ALLOWED_HOSTS
    except Exception:
        return False


def main():
    import tornado.web
    from streamlit.web.server.server import Server
    from streamlit.web import cli

    class Public(tornado.web.RequestHandler):
        async def get(self, kind=None, ident=None):
            path = self.request.path
            self.set_header("Cache-Control", "no-cache")
            if path == "/robots.txt":
                self.set_header("Content-Type", "text/plain; charset=utf-8")
                self.finish("User-agent: *\nAllow: /\nSitemap: " + SITE + "/sitemap.xml\n")
                return
            try:
                rows = await asyncio.to_thread(products)
            except Exception:
                self.set_status(503)
                self.set_header("Retry-After", "60")
                self.finish("상품 정보를 일시적으로 불러올 수 없습니다.")
                return
            if path.endswith("sitemap.xml"):
                self.set_header("Content-Type", "application/xml; charset=utf-8")
                self.finish(sitemap(rows))
            elif path.startswith("/catalog/"):
                if kind not in CATEGORIES:
                    raise tornado.web.HTTPError(404)
                self.set_header("Content-Type", "text/html; charset=utf-8")
                self.finish(catalog_page(kind, rows))
            else:
                product = next((p for p in rows if str(p["id"]) == str(kind)), None)
                if product is None:
                    raise tornado.web.HTTPError(404)
                self.set_header("Content-Type", "text/html; charset=utf-8")
                self.finish(product_page(product))

    class Checkout(tornado.web.RequestHandler):
        async def get(self, product_id):
            self.set_header("Cache-Control", "no-store")
            try:
                product = await asyncio.to_thread(product_by_id, product_id)
            except Exception:
                product = None
            if (
                product is None
                or str(product.get("condition") or "") != "판매중"
                or int(product.get("price") or 0) <= 0
            ):
                raise tornado.web.HTTPError(404)
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish(checkout_page(product))

    class CreateOrder(tornado.web.RequestHandler):
        async def post(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "application/json; charset=utf-8")
            if not _same_origin(self.request):
                self.set_status(403)
                self.finish(json.dumps({"message": "허용되지 않은 요청입니다."}, ensure_ascii=False))
                return
            if not _allow_order_attempt(_request_ip(self.request)):
                self.set_status(429)
                self.finish(json.dumps({"message": "주문 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."}, ensure_ascii=False))
                return
            if len(self.request.body or b"") > 16384:
                self.set_status(413)
                self.finish(json.dumps({"message": "요청 데이터가 너무 큽니다."}, ensure_ascii=False))
                return
            try:
                payload = json.loads((self.request.body or b"{}").decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("주문 요청 형식이 올바르지 않습니다.")
                order = await asyncio.to_thread(create_order, payload)
                self.finish(json.dumps(order, ensure_ascii=False))
            except ValueError as exc:
                self.set_status(400)
                self.finish(json.dumps({"message": str(exc)}, ensure_ascii=False))
            except Exception:
                self.set_status(500)
                self.finish(json.dumps({"message": "주문 생성 중 오류가 발생했습니다."}, ensure_ascii=False))

    class PaymentSuccess(tornado.web.RequestHandler):
        async def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "text/html; charset=utf-8")
            payment_key = self.get_query_argument("paymentKey", default="")
            order_id = self.get_query_argument("orderId", default="")
            amount = self.get_query_argument("amount", default="")
            try:
                result = await asyncio.to_thread(confirm_order, payment_key, order_id, amount)
                method_text = " · ".join(
                    part for part in [result.get("method"), result.get("provider")] if part
                )
                details = (
                    f'<p>주문번호: <b>{esc(str(result["order_id"]))}</b></p>'
                    f'<p>결제금액: <b>{int(result["amount"]):,}원</b></p>'
                    + (f'<p>결제수단: {esc(method_text)}</p>' if method_text else "")
                )
                status_message = (
                    "입금 확인을 기다리고 있습니다."
                    if result.get("status") == "awaiting_deposit"
                    else "결제가 정상적으로 승인되었습니다."
                )
                self.finish(payment_result_page("결제 완료", status_message, True, details))
            except Exception as exc:
                self.finish(
                    payment_result_page(
                        "결제 확인 실패",
                        str(exc) or "결제 승인 결과를 확인하지 못했습니다.",
                        False,
                    )
                )

    class PaymentFail(tornado.web.RequestHandler):
        async def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "text/html; charset=utf-8")
            order_id = self.get_query_argument("orderId", default="")
            code = self.get_query_argument("code", default="PAYMENT_FAILED")
            message = self.get_query_argument("message", default="결제가 취소되었거나 실패했습니다.")
            await asyncio.to_thread(mark_failed_order, order_id, code, message)
            self.finish(payment_result_page("결제 실패", message, False))

    original = Server._create_app

    def create_app(server):
        application = original(server)
        application.add_handlers(
            r".*",
            [
                (r"/robots\.txt", Public),
                (r"/(?:app/static/)?sitemap\.xml", Public),
                (r"/catalog/([^/]+)", Public),
                (r"/products/([^/]+)", Public),
                (r"/checkout/([^/]+)", Checkout),
                (r"/api/orders/create", CreateOrder),
                (r"/payment/success", PaymentSuccess),
                (r"/payment/fail", PaymentFail),
            ],
        )
        return application

    Server._create_app = create_app
    cli.main()


if __name__ == "__main__":
    main()
