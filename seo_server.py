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

BRAND = "투제이로드 TWO J ROAD"
PHONE = os.getenv("MASPICK_PHONE", "").strip()
LABEL_TO_KIND = {label: kind for kind, label in CATEGORIES.items()}

CATEGORY_INFO = {
    "bike": {
        "heading": "포천 중고 바이크 · 중고 오토바이",
        "title": "포천 중고 바이크·중고 오토바이 매물 | " + BRAND,
        "summary": "경기 포천 투제이로드(TWO J ROAD)의 중고 바이크·중고 오토바이 매물과 가격, 판매 상태를 확인하세요.",
        "intro": (
            "경기 포천 투제이로드(TWO J ROAD)에 등록된 중고 바이크 매물입니다. "
            "매물별 사진과 가격, 판매 상태를 확인한 뒤 매장 방문이나 문의에 참고하세요."
        ),
    },
    "wear": {
        "heading": "바이크 의류 · 라이딩 자켓·장갑·바지·신발",
        "title": "바이크 의류·오토바이 자켓·장갑 | " + BRAND,
        "summary": "투제이로드(TWO J ROAD)의 바이크 의류. 오토바이 자켓, 바이크 장갑, 라이딩 바지, 바이크 신발을 확인하세요.",
        "intro": (
            "투제이로드(TWO J ROAD)에서 판매하는 바이크 의류입니다. "
            "라이딩 자켓, 오토바이 장갑, 바이크 바지와 신발을 종류별로 나눠 두었습니다."
        ),
    },
    "gear": {
        "heading": "바이크 용품 · 오토바이 헬멧·라이딩 기어",
        "title": "바이크 용품·오토바이 헬멧 | " + BRAND,
        "summary": "투제이로드(TWO J ROAD)의 바이크 용품. 오토바이 헬멧과 라이딩 용품의 가격을 확인하세요.",
        "intro": (
            "투제이로드(TWO J ROAD)에서 판매하는 바이크 용품입니다. "
            "오토바이 헬멧과 라이딩에 필요한 용품을 확인하세요."
        ),
    },
}

# slug -> 상품 subcategory 값과 검색용 문구. subcategory 값은 app.py 등록 화면의 선택지와 같아야 합니다.
SUBCATEGORIES = {
    "wear": {
        "jacket": {
            "label": "자켓",
            "heading": "바이크 자켓 · 오토바이 자켓",
            "title": "바이크 자켓·오토바이 자켓·라이딩 자켓 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 바이크 자켓, 오토바이 자켓, 라이딩 자켓 상품과 가격을 확인하세요.",
            "intro": "라이딩할 때 입는 바이크 자켓(오토바이 자켓, 라이딩 자켓) 상품입니다.",
        },
        "gloves": {
            "label": "장갑",
            "heading": "오토바이 장갑 · 바이크 장갑",
            "title": "오토바이 장갑·바이크 장갑 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 오토바이 장갑, 바이크 장갑 상품과 가격을 확인하세요.",
            "intro": "라이딩용 오토바이 장갑(바이크 장갑) 상품입니다.",
        },
        "pants": {
            "label": "하의",
            "heading": "바이크 바지 · 라이딩 팬츠",
            "title": "바이크 바지·라이딩 팬츠 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 바이크 바지, 라이딩 팬츠 상품과 가격을 확인하세요.",
            "intro": "라이딩용 바이크 바지(라이딩 팬츠) 상품입니다.",
        },
        "shoes": {
            "label": "신발",
            "heading": "바이크 신발 · 바이크 부츠",
            "title": "바이크 신발·바이크 부츠 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 바이크 신발, 바이크 부츠 상품과 가격을 확인하세요.",
            "intro": "라이딩용 바이크 신발과 바이크 부츠 상품입니다.",
        },
        "tops": {
            "label": "상의",
            "heading": "바이크 상의 · 라이딩 의류",
            "title": "바이크 상의·라이딩 의류 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 바이크 상의와 라이딩 의류를 확인하세요.",
            "intro": "라이딩할 때 입는 바이크 상의 상품입니다.",
        },
    },
    "gear": {
        "helmet": {
            "label": "헬멧",
            "heading": "오토바이 헬멧 · 바이크 헬멧",
            "title": "오토바이 헬멧·바이크 헬멧 | " + BRAND,
            "summary": "투제이로드(TWO J ROAD)의 오토바이 헬멧, 바이크 헬멧 상품과 가격을 확인하세요.",
            "intro": "오토바이 헬멧(바이크 헬멧) 상품입니다.",
        },
    },
}

# Official Toss Payments documentation test keys. They cannot charge real money.
# When both merchant keys are added as Render env vars, those values take priority.
# TOSS_MODE=live 로 설정하면 실결제 키가 아닐 때 결제를 막습니다(테스트 키로 조용히 운영되는 것 방지).
DOCS_TEST_CLIENT_KEY = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"
DOCS_TEST_SECRET_KEY = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"
_env_client_key = os.getenv("TOSS_CLIENT_KEY", "").strip()
_env_secret_key = os.getenv("TOSS_SECRET_KEY", "").strip()
TOSS_MODE = os.getenv("TOSS_MODE", "test").strip().lower()
if _env_client_key and _env_secret_key:
    TOSS_CLIENT_KEY = _env_client_key
    TOSS_SECRET_KEY = _env_secret_key
else:
    TOSS_CLIENT_KEY = DOCS_TEST_CLIENT_KEY
    TOSS_SECRET_KEY = DOCS_TEST_SECRET_KEY
TOSS_TEST_MODE = TOSS_CLIENT_KEY.startswith("test_") or TOSS_SECRET_KEY.startswith("test_")

PAYMENT_DISABLED_REASON = ""
if TOSS_CLIENT_KEY.startswith("test_") != TOSS_SECRET_KEY.startswith("test_"):
    PAYMENT_DISABLED_REASON = "토스 클라이언트 키와 시크릿 키의 모드(테스트/라이브)가 서로 다릅니다."
elif TOSS_MODE == "live" and TOSS_TEST_MODE:
    PAYMENT_DISABLED_REASON = "TOSS_MODE=live 이지만 라이브 결제 키가 설정되지 않았습니다."
PAYMENT_ENABLED = not PAYMENT_DISABLED_REASON
print(
    "[PAYMENT] mode=" + ("test" if TOSS_TEST_MODE else "live")
    + " enabled=" + str(PAYMENT_ENABLED)
    + (" reason=" + PAYMENT_DISABLED_REASON if PAYMENT_DISABLED_REASON else ""),
    flush=True,
)

PENDING_EXPIRE_MINUTES = 60      # 결제창만 열고 끝나지 않은 주문을 실패 처리하는 기준
RECONCILE_INTERVAL_SECONDS = 300 # 토스 결제 상태와 주문 상태를 맞추는 주기

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
                "image,images,description,demo,year,mileage,cc,region,accident,updated_at"
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
            "image,images,description,demo,year,mileage,cc,region,accident,updated_at"
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


def product_kind(p):
    return LABEL_TO_KIND.get(str(p.get("category") or "").strip()) or str(p.get("type") or "")


def product_sub_slug(p):
    label = str(p.get("subcategory") or "").strip()
    for slug, info in SUBCATEGORIES.get(product_kind(p), {}).items():
        if info["label"] == label:
            return slug
    return None


def display_name(p):
    """브랜드 + 상품명. 상품명이 이미 브랜드로 시작하면 브랜드를 다시 붙이지 않습니다."""
    brand = str(p.get("brand") or "").strip()
    name = str(p.get("name") or "상품").strip()
    if not brand or name.lower().startswith(brand.lower()):
        return name
    return brand + " " + name


def first_image(p):
    pics = p.get("images") or [p.get("image")]
    if not isinstance(pics, list):
        pics = [pics]
    return next(
        (u for u in pics if isinstance(u, str) and u.startswith(("https://", "http://"))),
        "",
    )


def product_url(p):
    return "/products/" + quote(str(p["id"]), safe="")


def _jsonld(data):
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">' + text.replace("</", "<\\/") + "</script>"


def _breadcrumb(crumbs):
    html = '<nav class="crumbs" aria-label="현재 위치">'
    html += " › ".join(
        f'<a href="{esc(path, quote=True)}">{esc(name)}</a>' for name, path in crumbs
    )
    html += "</nav>"
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": SITE + path}
            for i, (name, path) in enumerate(crumbs, 1)
        ],
    }
    return html, data


def page(title, summary, path, body, image_url="", schemas=None, crumbs=None):
    url = esc(SITE + path, quote=True)
    schemas = list(schemas or [])
    crumb_html = ""
    if crumbs:
        crumb_html, crumb_data = _breadcrumb(crumbs)
        schemas.append(crumb_data)
    og_image = image_url or (SITE + "/app/static/jinbike_banner.webp")
    sub_links = " · ".join(
        f'<a href="/catalog/{kind}/{slug}">{esc(info["label"])}</a>'
        for kind, subs in SUBCATEGORIES.items()
        for slug, info in subs.items()
    )
    phone_html = f" · 문의 {esc(PHONE)}" if PHONE else ""
    map_url = "https://map.naver.com/p/search/" + quote(STORE_ADDRESS, safe="")
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(summary, quote=True)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}"><meta property="og:title" content="{esc(title, quote=True)}">
<meta property="og:description" content="{esc(summary, quote=True)}"><meta property="og:url" content="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="TWO J ROAD (투제이로드)">
<meta property="og:locale" content="ko_KR"><meta property="og:image" content="{esc(og_image, quote=True)}">
{"".join(_jsonld(item) for item in schemas)}
<style>
body{{background:#080808;color:#eee;font:16px/1.7 sans-serif;max-width:1100px;margin:auto;padding:24px}}
a{{color:#ff8a24}}nav.main{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px;font-weight:700}}
nav.sub{{font-size:14px;margin-bottom:18px}}.crumbs{{font-size:13px;color:#aaa;margin-bottom:8px}}
img{{display:block;max-width:100%;max-height:700px;object-fit:contain;margin:12px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:20px}}
.card{{border:1px solid #333;padding:16px}}.card img{{width:100%;height:220px}}
.card h2{{font-size:17px;margin:8px 0}}.state{{color:#ffb36b;font-size:14px}}
.chips a{{display:inline-block;border:1px solid #444;padding:4px 12px;margin:0 8px 8px 0;border-radius:16px}}
.text{{white-space:pre-wrap}}h1{{font-size:28px;margin:8px 0}}.intro{{color:#ccc}}
.buy{{display:inline-block;background:#ff6900;color:#fff;padding:12px 20px;font-weight:800;border-radius:4px}}
.notice{{border:1px solid #4a3420;background:#1b120b;padding:12px 14px;margin:18px 0}}
footer{{margin-top:40px;border-top:1px solid #333;padding-top:16px;font-size:14px;color:#aaa}}
</style></head><body>
<nav class="main"><a href="/">투제이로드 TWO J ROAD</a><a href="/catalog/bike">중고 바이크</a><a href="/catalog/wear">바이크 의류</a><a href="/catalog/gear">바이크 용품</a><a href="/?page=store">오프라인매장</a></nav>
<nav class="sub">{sub_links}</nav>
{crumb_html}
{body}
<footer><p>포천 투제이로드(TWO J ROAD) · {esc(STORE_ADDRESS)}{phone_html}<br>
중고 오토바이 · 바이크 의류 · 오토바이 헬멧 · 라이딩 용품<br>
<a href="{esc(map_url, quote=True)}" rel="noopener">네이버 지도에서 위치 보기</a> · <a href="/sitemap.xml">사이트맵</a></p></footer>
</body></html>'''


def product_page(p):
    name = str(p.get("name") or "상품")
    brand = str(p.get("brand") or "")
    state = str(p.get("condition") or "")
    price = int(p.get("price") or 0)
    kind = product_kind(p)
    sub = product_sub_slug(p)
    text, files = description(p)
    full_name = display_name(p)
    summary = " ".join(" ".join((full_name, state, text)).split())[:150] or name
    pics = p.get("images") or [p.get("image")]
    if not isinstance(pics, list):
        pics = [pics]

    body = f'<h1>{esc(full_name)}</h1>'
    if brand:
        body += f'<p>브랜드: {esc(brand)}</p>'
    body += f'<p>{price:,}원' + (f' · {esc(state)}' if state else "") + '</p>'
    if kind == "bike":
        specs = [
            (label, str(p.get(key) or "").strip())
            for label, key in (
                ("연식", "year"), ("주행거리", "mileage"), ("배기량", "cc"),
                ("지역", "region"), ("사고 여부", "accident"),
            )
        ]
        specs = [(label, value) for label, value in specs if value]
        if specs:
            body += "<ul>" + "".join(
                f"<li>{esc(label)}: {esc(value)}</li>" for label, value in specs
            ) + "</ul>"
    body += "".join(image(url, full_name) for url in pics)
    body += f'<div class="text">{esc(text)}</div>'
    for item in files:
        if not isinstance(item, dict):
            continue
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
    if PAYMENT_ENABLED and state == "판매중" and price > 0:
        label = "테스트 결제" if TOSS_TEST_MODE else "구매하기"
        body += (
            f'<p><a class="buy" href="/checkout/{quote(str(p["id"]), safe="")}">'
            f'{label}</a></p>'
        )
        if TOSS_TEST_MODE:
            body += '<div class="notice">현재 테스트 결제 모드이며 실제 금액은 청구되지 않습니다.</div>'

    crumbs = [("투제이로드 홈", "/")]
    section = ""
    if kind in CATEGORIES:
        crumbs.append((CATEGORIES[kind], "/catalog/" + kind))
        section = CATEGORIES[kind]
        if sub:
            info = SUBCATEGORIES[kind][sub]
            crumbs.append((info["label"], f"/catalog/{kind}/{sub}"))
            section = info["heading"].split(" · ")[0]
    crumbs.append((name, product_url(p)))

    hero = first_image(p)
    product_data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": full_name,
        "url": SITE + product_url(p),
        "description": summary,
    }
    image_list = [u for u in pics if isinstance(u, str) and u.startswith(("http://", "https://"))]
    if image_list:
        product_data["image"] = image_list[:10]
    if brand:
        product_data["brand"] = {"@type": "Brand", "name": brand}
    if price > 0:
        offer = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": "KRW",
            "url": SITE + product_url(p),
            "seller": {"@type": "Organization", "name": "TWO J ROAD"},
        }
        if kind == "bike":
            offer["itemCondition"] = "https://schema.org/UsedCondition"
        if state == "판매중":
            offer["availability"] = "https://schema.org/InStock"
        elif state in ("판매완료", "품절"):
            offer["availability"] = "https://schema.org/SoldOut"
        product_data["offers"] = offer

    title_parts = [full_name]
    if section:
        title_parts.append(section)
    title_parts.append(BRAND)
    return page(
        " | ".join(title_parts),
        summary,
        product_url(p),
        body,
        image_url=hero,
        schemas=[product_data],
        crumbs=crumbs,
    )


def _card(p):
    name = display_name(p)
    state = str(p.get("condition") or "")
    return (
        f'<article class="card"><a href="{product_url(p)}">{image(first_image(p), name)}'
        f'<h2>{esc(name)}</h2></a><p>{int(p.get("price") or 0):,}원'
        + (f' <span class="state">{esc(state)}</span>' if state else "")
        + '</p></article>'
    )


def catalog_page(kind, rows, sub=None):
    info = CATEGORY_INFO[kind]
    in_kind = [p for p in rows if product_kind(p) == kind]
    path = "/catalog/" + kind
    crumbs = [("투제이로드 홈", "/"), (CATEGORIES[kind], path)]
    if sub:
        sub_info = SUBCATEGORIES[kind][sub]
        filtered = [
            p for p in in_kind
            if str(p.get("subcategory") or "").strip() == sub_info["label"]
        ]
        path += "/" + sub
        crumbs.append((sub_info["label"], path))
        heading, title, summary, intro = (
            sub_info["heading"], sub_info["title"], sub_info["summary"], sub_info["intro"]
        )
    else:
        filtered = in_kind
        heading, title, summary, intro = (
            info["heading"], info["title"], info["summary"], info["intro"]
        )

    body = f'<h1>{esc(heading)}</h1><p class="intro">{esc(intro)}</p>'
    subs = SUBCATEGORIES.get(kind, {})
    if subs:
        body += '<p class="chips">'
        for slug, s in subs.items():
            count = sum(
                str(p.get("subcategory") or "").strip() == s["label"] for p in in_kind
            )
            body += f'<a href="/catalog/{kind}/{slug}">{esc(s["label"])} ({count})</a>'
        body += "</p>"
    if filtered:
        body += f'<p>등록 상품 {len(filtered)}개</p><div class="grid">'
        body += "".join(_card(p) for p in filtered)
        body += "</div>"
    else:
        body += "<p>현재 등록된 상품이 없습니다. 입고 문의는 매장으로 연락해 주세요.</p>"

    schemas = [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": heading,
        "url": SITE + path,
        "description": summary,
    }]
    hero = next((first_image(p) for p in filtered if first_image(p)), "")
    return page(title, summary, path, body, image_url=hero, schemas=schemas, crumbs=crumbs)


def sitemap(rows):
    urls = [SITE + "/"] + [SITE + "/catalog/" + kind for kind in CATEGORIES]
    for kind, subs in SUBCATEGORIES.items():
        for slug, info in subs.items():
            has_items = any(
                product_kind(p) == kind
                and str(p.get("subcategory") or "").strip() == info["label"]
                for p in rows
            )
            if has_items:
                urls.append(SITE + f"/catalog/{kind}/{slug}")
    product_entries = [(SITE + product_url(p), _lastmod(p)) for p in rows]
    newest = max((mod for _, mod in product_entries if mod), default="")
    entries = [(url, newest) for url in urls] + product_entries
    xml = "".join(
        "<url><loc>" + xml_escape(url) + "</loc>"
        + ("<lastmod>" + mod + "</lastmod>" if mod else "")
        + "</url>"
        for url, mod in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><urlset '
        'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + xml
        + "</urlset>"
    )


def _lastmod(p):
    match = re.match(r"(\d{4}-\d{2}-\d{2})", str(p.get("updated_at") or "").strip())
    return match.group(1) if match else ""


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


ACTIVE_ORDER_STATUSES = ("paid", "awaiting_deposit", "partial_canceled")

TOSS_STATUS_MAP = {
    "DONE": "paid",
    "WAITING_FOR_DEPOSIT": "awaiting_deposit",
    "CANCELED": "canceled",
    "PARTIAL_CANCELED": "partial_canceled",
    "ABORTED": "failed",
    "EXPIRED": "failed",
}


def _log(message):
    print("[PAYMENT] " + str(message)[:800], flush=True)


def _require_payment_enabled():
    if not PAYMENT_ENABLED:
        raise RuntimeError("현재 온라인 결제를 사용할 수 없습니다. 매장으로 문의해 주세요.")


def _is_bike(product_or_order):
    kind = str(
        product_or_order.get("product_type") or product_or_order.get("type") or ""
    )
    return kind == "bike" or str(product_or_order.get("category") or "") == "중고 바이크"


def _active_order_exists(product_id, exclude_order_id=None):
    rows = (
        db_client()
        .table("orders")
        .select("order_id,status,stock_reserved")
        .eq("product_id", str(product_id))
        .execute()
        .data
    ) or []
    for row in rows:
        if exclude_order_id and row.get("order_id") == exclude_order_id:
            continue
        if row.get("status") in ACTIVE_ORDER_STATUSES:
            return True
        if row.get("status") == "pending" and row.get("stock_reserved"):
            return True
    return False


def create_order(payload):
    _require_payment_enabled()
    data = _validate_order_payload(payload)
    product = product_by_id(data["product_id"])
    if product is None:
        raise ValueError("판매 상품을 찾을 수 없습니다.")
    if str(product.get("condition") or "") != "판매중":
        raise ValueError("현재 결제할 수 없는 상품입니다.")
    price = int(product.get("price") or 0)
    if price <= 0:
        raise ValueError("결제 가능한 상품 가격이 설정되지 않았습니다.")
    if _is_bike(product) and _active_order_exists(product["id"]):
        raise ValueError("이미 다른 고객이 결제했거나 결제 진행 중인 매물입니다.")

    quantity = 1
    amount = price * quantity
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


def _toss_request(method, path, payload=None, idempotency_key=None):
    headers = {"Authorization": _basic_auth(TOSS_SECRET_KEY)}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    try:
        response = requests.request(
            method,
            "https://api.tosspayments.com" + path,
            headers=headers,
            json=payload,
            timeout=15,
        )
    except requests.RequestException as exc:
        return 599, {"code": "NETWORK_ERROR", "message": str(exc)[:300]}
    try:
        body = response.json()
    except ValueError:
        body = {"code": "INVALID_RESPONSE", "message": response.text[:500]}
    if not isinstance(body, dict):
        body = {"code": "INVALID_RESPONSE", "message": str(body)[:500]}
    return response.status_code, body


def _toss_post(path, payload, idempotency_key=None):
    return _toss_request("POST", path, payload, idempotency_key)


def _toss_get(path):
    return _toss_request("GET", path)


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


def _reserve_bike(order):
    """중고 바이크는 승인 요청 전에 '판매중 → 예약중'으로 먼저 잡아 중복 판매를 막습니다."""
    if not _is_bike(order) or order.get("stock_reserved"):
        return True
    if _active_order_exists(order.get("product_id"), exclude_order_id=order.get("order_id")):
        return False
    claimed = (
        db_client()
        .table("products")
        .update({"condition": "예약중"})
        .eq("id", order.get("product_id"))
        .eq("condition", "판매중")
        .execute()
        .data
    )
    if not claimed:
        return False
    db_client().table("orders").update({"stock_reserved": True}).eq(
        "order_id", order["order_id"]
    ).execute()
    order["stock_reserved"] = True
    _cache.update(time=0, rows=None)
    return True


def _release_bike(order):
    """이 주문이 잡아둔 바이크 예약만 풀어 '판매중'으로 되돌립니다."""
    if not order.get("stock_reserved"):
        return
    client = db_client()
    if not _active_order_exists(order.get("product_id"), exclude_order_id=order.get("order_id")):
        client.table("products").update({"condition": "판매중"}).eq(
            "id", order.get("product_id")
        ).eq("condition", "예약중").execute()
    client.table("orders").update({"stock_reserved": False}).eq(
        "order_id", order["order_id"]
    ).execute()
    order["stock_reserved"] = False
    _cache.update(time=0, rows=None)


def _apply_toss_payment(order, result):
    """토스 결제 객체를 기준으로 orders/payments를 맞춥니다. 금액·주문번호 불일치는 반영하지 않습니다."""
    order_id = order["order_id"]
    db_amount = int(order.get("amount") or 0)
    if str(result.get("orderId") or "") != order_id:
        raise RuntimeError("토스페이먼츠 주문번호 검증에 실패했습니다.")
    if int(result.get("totalAmount") or 0) != db_amount:
        raise RuntimeError("토스페이먼츠 결제 금액 검증에 실패했습니다.")

    payment_key = str(result.get("paymentKey") or "").strip()
    stored_key = str(order.get("payment_key") or "").strip()
    if stored_key and payment_key and stored_key != payment_key:
        raise RuntimeError("이미 다른 결제로 처리된 주문입니다.")

    toss_status = str(result.get("status") or "")
    order_status = TOSS_STATUS_MAP.get(toss_status, "pending")
    method = str(result.get("method") or "")
    easy = result.get("easyPay")
    provider = str(easy.get("provider") or "") if isinstance(easy, dict) else ""
    approved_at = result.get("approvedAt")
    canceled_at = None
    cancels = result.get("cancels")
    if isinstance(cancels, list) and cancels and isinstance(cancels[-1], dict):
        canceled_at = cancels[-1].get("canceledAt")

    client = db_client()
    if payment_key:
        client.table("payments").upsert(
            {
                "order_id": order_id,
                "payment_key": payment_key,
                "amount": db_amount,
                "status": toss_status or order_status,
                "method": method or None,
                "easy_pay_provider": provider or None,
                "approved_at": approved_at,
                "canceled_at": canceled_at,
                "raw_response": result,
                "is_test": bool(order.get("is_test")),
            },
            on_conflict="payment_key",
        ).execute()

    update = {"status": order_status}
    if payment_key:
        update["payment_key"] = payment_key
    if method:
        update["payment_method"] = method
    if provider:
        update["easy_pay_provider"] = provider
    if approved_at:
        update["approved_at"] = approved_at
    if canceled_at:
        update["canceled_at"] = canceled_at
    if order_status in ("paid", "awaiting_deposit"):
        update["failure_code"] = None
        update["failure_message"] = None
    elif order_status == "failed":
        failure = result.get("failure") if isinstance(result.get("failure"), dict) else {}
        update["failure_code"] = str(failure.get("code") or toss_status)[:100]
        update["failure_message"] = str(failure.get("message") or "결제가 완료되지 않았습니다.")[:500]
    client.table("orders").update(update).eq("order_id", order_id).execute()
    order.update(update)

    if order_status in ("canceled", "failed"):
        _release_bike(order)

    return {
        "order_id": order_id,
        "amount": db_amount,
        "status": order_status,
        "method": method,
        "provider": provider,
        "is_test": bool(order.get("is_test")),
    }


def sync_order_from_toss(order_id):
    """토스에 저장된 실제 결제 상태로 주문을 맞춥니다(웹훅·자동 점검용)."""
    order = _order_row(order_id)
    if order is None:
        return None
    if bool(order.get("is_test")) != TOSS_TEST_MODE:
        return None  # 다른 모드(테스트/라이브) 키로는 조회할 수 없음
    status_code, result = _toss_get("/v1/payments/orders/" + quote(str(order_id), safe=""))
    if status_code == 404:
        return {"order_id": order_id, "status": order.get("status"), "not_found": True}
    if status_code < 200 or status_code >= 300:
        _log(f"sync failed order={order_id} http={status_code} code={result.get('code')}")
        return None
    toss_status = str(result.get("status") or "")
    if toss_status not in TOSS_STATUS_MAP:
        return {"order_id": order_id, "status": order.get("status"), "toss_status": toss_status}
    if order.get("status") == "canceled" and toss_status != "CANCELED":
        return {"order_id": order_id, "status": "canceled"}
    return _apply_toss_payment(order, result)


def confirm_order(payment_key, order_id, redirected_amount):
    _require_payment_enabled()
    payment_key = str(payment_key or "").strip()
    order_id = str(order_id or "").strip()
    if not payment_key or not order_id:
        raise ValueError("결제 정보가 올바르지 않습니다.")
    try:
        redirected_amount = int(redirected_amount)
    except (TypeError, ValueError):
        raise ValueError("결제 금액 정보가 올바르지 않습니다.")

    order = _order_row(order_id)
    if order is None:
        raise ValueError("주문을 찾을 수 없습니다.")
    if bool(order.get("is_test")) != TOSS_TEST_MODE:
        raise ValueError("현재 결제 모드와 다른 주문입니다.")
    db_amount = int(order.get("amount") or 0)

    if order.get("status") in ACTIVE_ORDER_STATUSES:
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
    if order.get("status") == "failed":
        raise ValueError("만료되었거나 실패 처리된 주문입니다. 다시 주문해 주세요.")

    if redirected_amount != db_amount:
        db_client().table("orders").update(
            {
                "status": "failed",
                "failure_code": "AMOUNT_MISMATCH",
                "failure_message": "결제 요청 금액과 주문 금액이 다릅니다.",
            }
        ).eq("order_id", order_id).execute()
        _release_bike(order)
        raise ValueError("결제 금액 검증에 실패했습니다.")

    if not _reserve_bike(order):
        db_client().table("orders").update(
            {
                "status": "failed",
                "failure_code": "ALREADY_RESERVED",
                "failure_message": "다른 고객이 먼저 결제한 매물입니다.",
            }
        ).eq("order_id", order_id).execute()
        raise ValueError("다른 고객이 먼저 결제한 매물입니다. 결제는 승인되지 않았습니다.")

    status_code, result = _toss_post(
        "/v1/payments/confirm",
        {"paymentKey": payment_key, "orderId": order_id, "amount": db_amount},
        idempotency_key="confirm-" + order_id,
    )

    if status_code < 200 or status_code >= 300:
        code = str(result.get("code") or "PAYMENT_CONFIRM_FAILED")[:100]
        message = str(result.get("message") or "결제 승인에 실패했습니다.")[:500]
        if code == "ALREADY_PROCESSED_PAYMENT" or status_code >= 500:
            # 승인 응답을 못 받았거나 이미 승인된 경우: 토스 실제 상태로 맞춥니다.
            synced = sync_order_from_toss(order_id)
            if synced and synced.get("status") in ACTIVE_ORDER_STATUSES:
                return synced
            db_client().table("orders").update(
                {"failure_code": code, "failure_message": message}
            ).eq("order_id", order_id).execute()
            _log(f"confirm pending order={order_id} http={status_code} code={code}")
            raise RuntimeError(
                "결제 승인 결과를 아직 확인하지 못했습니다. 잠시 후 자동으로 확인되며, "
                "결제가 되지 않았다면 청구되지 않습니다."
            )
        db_client().table("orders").update(
            {"status": "failed", "failure_code": code, "failure_message": message}
        ).eq("order_id", order_id).execute()
        _release_bike(order)
        raise RuntimeError(message)

    return _apply_toss_payment(order, result)


def mark_failed_order(order_id, code, message):
    if not order_id:
        return
    try:
        order = _order_row(order_id)
        if order is None or order.get("status") != "pending" or order.get("stock_reserved"):
            return
        db_client().table("orders").update(
            {
                "status": "failed",
                "failure_code": str(code or "")[:100],
                "failure_message": str(message or "")[:500],
            }
        ).eq("order_id", str(order_id)).eq("status", "pending").execute()
    except Exception:
        pass


def reconcile_orders():
    """결제 대기·입금 대기 주문을 토스 상태와 맞추고, 오래된 미결제 주문을 만료 처리합니다."""
    if not PAYMENT_ENABLED:
        return
    client = db_client()
    cutoff_recent = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 10 * 60)
    )
    cutoff_expire = time.time() - PENDING_EXPIRE_MINUTES * 60
    rows = (
        client.table("orders")
        .select("order_id,status,created_at,is_test,stock_reserved")
        .in_("status", ["pending", "awaiting_deposit"])
        .eq("is_test", TOSS_TEST_MODE)
        .lt("created_at", cutoff_recent)
        .order("created_at")
        .limit(50)
        .execute()
        .data
    ) or []
    for row in rows:
        order_id = row.get("order_id")
        try:
            synced = sync_order_from_toss(order_id)
            if row.get("status") != "pending":
                continue
            if synced is None:
                continue  # 토스 조회 실패 시에는 다음 주기에 다시 확인
            still_pending = (
                synced.get("status") == "pending"
                or synced.get("not_found")
                or synced.get("toss_status")
            )
            if still_pending and _created_ts(row.get("created_at")) < cutoff_expire:
                order = _order_row(order_id)
                if order and order.get("status") == "pending":
                    client.table("orders").update(
                        {
                            "status": "failed",
                            "failure_code": "EXPIRED",
                            "failure_message": "결제가 완료되지 않아 주문이 만료되었습니다.",
                        }
                    ).eq("order_id", order_id).eq("status", "pending").execute()
                    _release_bike(order)
                    _log(f"expired order={order_id}")
        except Exception as exc:
            _log(f"reconcile error order={order_id} {type(exc).__name__}: {exc}")
    now = time.monotonic()
    for ip in list(_order_rate):
        if not [t for t in _order_rate[ip] if now - t < 600]:
            _order_rate.pop(ip, None)


def _created_ts(value):
    from datetime import datetime, timezone
    text = str(value or "").strip().replace("Z", "+00:00").replace(" ", "T", 1)
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        # 소수점 자릿수가 6자리가 아닌 경우 등
        moment = datetime.fromisoformat(re.sub(r"\.\d+", "", text))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def handle_toss_webhook(body):
    """토스 웹훅은 내용만 믿지 않고, 토스 API로 실제 결제 상태를 다시 조회해 반영합니다."""
    if not isinstance(body, dict):
        return
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    order_id = str(data.get("orderId") or body.get("orderId") or "").strip()
    if not order_id or not order_id.startswith("TJR_"):
        return
    result = sync_order_from_toss(order_id)
    _log(
        f"webhook event={body.get('eventType') or 'DEPOSIT_CALLBACK'} "
        f"order={order_id} result={result.get('status') if result else 'skip'}"
    )


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
    if bool(order.get("is_test")) != TOSS_TEST_MODE:
        raise ValueError("현재 결제 모드와 다른 주문이라 취소할 수 없습니다.")
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
        if str(result.get("code") or "") == "ALREADY_CANCELED_PAYMENT":
            sync_order_from_toss(order_id)
        raise RuntimeError(str(result.get("message") or "결제 취소에 실패했습니다."))

    _apply_toss_payment(order, result)
    if order.get("status") == "canceled" and _is_bike(order) and not order.get("stock_reserved"):
        # 이전 버전으로 결제된 주문(예약 표시 없음)도 바이크 예약을 풀어 줍니다.
        order["stock_reserved"] = True
        _release_bike(order)
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
    for header in ("CF-Connecting-IP", "True-Client-IP"):
        value = request.headers.get(header, "").strip()
        if value:
            return value
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
                if ident is not None and ident not in SUBCATEGORIES.get(kind, {}):
                    raise tornado.web.HTTPError(404)
                self.set_header("Content-Type", "text/html; charset=utf-8")
                self.finish(catalog_page(kind, rows, ident))
            else:
                product = next((p for p in rows if str(p["id"]) == str(kind)), None)
                if product is None:
                    raise tornado.web.HTTPError(404)
                self.set_header("Content-Type", "text/html; charset=utf-8")
                self.finish(product_page(product))

        async def head(self, kind=None, ident=None):
            # 검색로봇의 HEAD 요청에도 405 대신 정상 응답 (본문은 Tornado가 생략)
            await self.get(kind, ident)

    class Checkout(tornado.web.RequestHandler):
        async def get(self, product_id):
            self.set_header("Cache-Control", "no-store")
            self.set_header("X-Robots-Tag", "noindex")
            if not PAYMENT_ENABLED:
                self.set_status(503)
                self.set_header("Content-Type", "text/html; charset=utf-8")
                self.finish(payment_result_page(
                    "결제 일시 중지",
                    "현재 온라인 결제를 사용할 수 없습니다. 매장으로 문의해 주세요.",
                    False,
                ))
                return
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
        def options(self):
            origin = self.request.headers.get("Origin", "")
            if origin and (urlparse(origin).hostname or "").lower() in ALLOWED_HOSTS:
                self.set_header("Access-Control-Allow-Origin", origin)
                self.set_header("Access-Control-Allow-Headers", "Content-Type")
                self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.set_header("Vary", "Origin")
            self.set_status(204)
            self.finish()

        async def post(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "application/json; charset=utf-8")
            if not _same_origin(self.request):
                self.set_status(403)
                self.finish(json.dumps({"message": "허용되지 않은 요청입니다."}, ensure_ascii=False))
                return
            if not PAYMENT_ENABLED:
                self.set_status(503)
                self.finish(json.dumps({"message": "현재 온라인 결제를 사용할 수 없습니다."}, ensure_ascii=False))
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
            except RuntimeError as exc:
                self.set_status(503)
                self.finish(json.dumps({"message": str(exc)}, ensure_ascii=False))
            except Exception as exc:
                _log(f"create order error {type(exc).__name__}: {exc}")
                self.set_status(500)
                self.finish(json.dumps({"message": "주문 생성 중 오류가 발생했습니다."}, ensure_ascii=False))

    class PaymentSuccess(tornado.web.RequestHandler):
        async def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.set_header("X-Robots-Tag", "noindex")
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
            except (ValueError, RuntimeError) as exc:
                self.finish(
                    payment_result_page(
                        "결제 확인 실패",
                        str(exc) or "결제 승인 결과를 확인하지 못했습니다.",
                        False,
                    )
                )
            except Exception as exc:
                _log(f"confirm error {type(exc).__name__}: {exc}")
                self.finish(
                    payment_result_page(
                        "결제 확인 실패",
                        "결제 승인 결과를 확인하지 못했습니다. 잠시 후 자동으로 다시 확인됩니다.",
                        False,
                    )
                )

    class PaymentFail(tornado.web.RequestHandler):
        async def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.set_header("X-Robots-Tag", "noindex")
            order_id = self.get_query_argument("orderId", default="")
            code = self.get_query_argument("code", default="PAYMENT_FAILED")
            message = self.get_query_argument("message", default="결제가 취소되었거나 실패했습니다.")
            await asyncio.to_thread(mark_failed_order, order_id, code, message)
            self.finish(payment_result_page("결제 실패", message, False))

    class TossWebhook(tornado.web.RequestHandler):
        async def post(self):
            self.set_header("Content-Type", "application/json; charset=utf-8")
            if len(self.request.body or b"") > 65536:
                self.set_status(413)
                self.finish("{}")
                return
            try:
                body = json.loads((self.request.body or b"{}").decode("utf-8"))
            except ValueError:
                self.set_status(400)
                self.finish("{}")
                return
            try:
                await asyncio.to_thread(handle_toss_webhook, body)
            except Exception as exc:
                _log(f"webhook error {type(exc).__name__}: {exc}")
                self.set_status(500)  # 토스가 나중에 다시 보내도록
                self.finish("{}")
                return
            self.finish("{}")

    async def _reconcile_once():
        try:
            await asyncio.to_thread(reconcile_orders)
        except Exception as exc:
            _log(f"reconcile loop error {type(exc).__name__}: {exc}")

    reconcile_state = {"started": False}

    def _start_reconcile():
        if reconcile_state["started"]:
            return
        reconcile_state["started"] = True
        from tornado.ioloop import PeriodicCallback

        timer = PeriodicCallback(
            lambda: asyncio.ensure_future(_reconcile_once()),
            RECONCILE_INTERVAL_SECONDS * 1000,
        )
        timer.start()
        _log("reconcile timer started")

    original = Server._create_app

    def create_app(server):
        application = original(server)
        application.add_handlers(
            r".*",
            [
                (r"/robots\.txt", Public),
                (r"/(?:app/static/)?sitemap\.xml", Public),
                (r"/catalog/([^/]+)", Public),
                (r"/catalog/([^/]+)/([^/]+)", Public),
                (r"/products/([^/]+)", Public),
                (r"/checkout/([^/]+)", Checkout),
                (r"/api/orders/create", CreateOrder),
                (r"/payment/success", PaymentSuccess),
                (r"/payment/fail", PaymentFail),
                (r"/api/toss/webhook", TossWebhook),
            ],
        )
        try:
            _start_reconcile()
        except Exception as exc:
            _log(f"reconcile timer not started {type(exc).__name__}: {exc}")
        return application

    Server._create_app = create_app
    cli.main()


if __name__ == "__main__":
    main()
