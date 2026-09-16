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
BIZ_NAME = "투제이-로드(2J-ROAD)"
BIZ_OWNER = "전선옥"
BIZ_REG_NO = "505-48-00676"
BIZ_ADDRESS = "경기도 포천시 내촌면 금강로3224번길 11-7, 다동 1층"
BIZ_MAIL_ORDER_NO = os.getenv("MASPICK_MAIL_ORDER_NO", "").strip() or "2024-경기포천-0754"


def business_info_html():
    check_url = "https://www.ftc.go.kr/bizCommPop.do?wrkr_no=" + BIZ_REG_NO.replace("-", "")
    parts = [
        f"<b>{esc(BIZ_NAME)}</b>",
        f"대표 {esc(BIZ_OWNER)}",
        f'사업자등록번호 {esc(BIZ_REG_NO)} (<a href="{esc(check_url, quote=True)}" '
        'target="_blank" rel="noopener noreferrer">사업자정보확인</a>)',
    ]
    if BIZ_MAIL_ORDER_NO:
        parts.append(f"통신판매업신고 {esc(BIZ_MAIL_ORDER_NO)}")
    line2 = esc(BIZ_ADDRESS) + (f" · 전화 {esc(PHONE)}" if PHONE else "")
    links = ('<a href="/terms">이용약관</a> · <a href="/privacy"><b>개인정보처리방침</b></a> · '
             '<a href="/refund">교환·환불 안내</a>')
    return " · ".join(parts) + "<br>" + line2 + "<br>" + links
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

VISITOR_COOKIE = "twoj_vid"
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
<footer><p>{business_info_html()}<br>
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
    if kind == "bike" and state == "판매중":
        body += '<div class="notice">중고 바이크는 온라인 결제 없이 매장 방문·전화 상담 후 거래합니다.</div>'
    if PAYMENT_ENABLED and kind != "bike" and state == "판매중" and price > 0:
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
    if not product_id and not payload.get("items"):
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


MAX_CART_LINES = 20
MAX_LINE_QTY = 20


def product_options(product_id):
    """상품 옵션(이름·추가금액·재고). 옵션이 없으면 빈 목록."""
    rows = (
        db_client()
        .table("product_options")
        .select("name,extra_price,stock,sort")
        .eq("product_id", str(product_id))
        .order("sort")
        .execute()
        .data
    ) or []
    return sorted(rows, key=lambda r: (int(r.get("sort") or 0), str(r.get("name") or "")))


def order_items(order_or_id):
    order = order_or_id if isinstance(order_or_id, dict) else _order_row(order_or_id)
    if not order:
        return []
    rows = (
        db_client()
        .table("order_items")
        .select("product_id,product_type,product_name,option_name,unit_price,quantity,amount")
        .eq("order_id", order["order_id"])
        .order("id")
        .execute()
        .data
    ) or []
    if rows:
        return rows
    # 장바구니 도입 전 주문(단일 상품)
    return [{
        "product_id": order.get("product_id"),
        "product_type": order.get("product_type") or "",
        "product_name": order.get("product_name") or "",
        "option_name": None,
        "unit_price": int(order.get("unit_price") or 0),
        "quantity": int(order.get("quantity") or 1),
        "amount": int(order.get("amount") or 0),
    }]


def _is_bike(product_or_order):
    kind = str(
        product_or_order.get("product_type") or product_or_order.get("type") or ""
    )
    return kind == "bike" or str(product_or_order.get("category") or "") == "중고 바이크"


def _active_order_exists(product_id, exclude_order_id=None):
    """이 상품을 포함한 결제완료·입금대기·예약중(승인 진행) 주문이 있는지."""
    client = db_client()
    order_ids = {
        row.get("order_id")
        for row in (
            client.table("order_items").select("order_id")
            .eq("product_id", str(product_id)).execute().data or []
        )
    }
    legacy = (
        client.table("orders").select("order_id")
        .eq("product_id", str(product_id)).execute().data or []
    )
    order_ids.update(row.get("order_id") for row in legacy)
    order_ids.discard(None)
    order_ids.discard(exclude_order_id)
    if not order_ids:
        return False
    rows = (
        client.table("orders").select("order_id,status,stock_reserved")
        .in_("order_id", sorted(order_ids)).execute().data or []
    )
    for row in rows:
        if row.get("status") in ACTIVE_ORDER_STATUSES:
            return True
        if row.get("status") == "pending" and row.get("stock_reserved"):
            return True
    return False


def _parse_cart_items(raw_items):
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("주문할 상품이 없습니다.")
    merged = {}
    for raw in raw_items[: MAX_CART_LINES * 2]:
        if not isinstance(raw, dict):
            continue
        product_id = str(raw.get("product_id") or raw.get("p") or "").strip()[:64]
        option = str(raw.get("option") or raw.get("o") or "").strip()[:60]
        try:
            qty = int(raw.get("qty") or raw.get("q") or 0)
        except (TypeError, ValueError):
            qty = 0
        if not product_id or qty <= 0:
            continue
        key = (product_id, option)
        merged[key] = min(MAX_LINE_QTY, merged.get(key, 0) + qty)
    if not merged:
        raise ValueError("주문할 상품이 없습니다.")
    if len(merged) > MAX_CART_LINES:
        raise ValueError(f"한 번에 최대 {MAX_CART_LINES}개 상품까지 주문할 수 있습니다.")
    return [{"product_id": k[0], "option": k[1], "qty": v} for k, v in merged.items()]


def quote_items(raw_items, strict=True):
    """장바구니 항목을 DB 기준 가격·재고로 검증합니다. strict=False면 문제 항목도 사유와 함께 돌려줍니다."""
    items = _parse_cart_items(raw_items)
    lines, total, problems = [], 0, []
    product_cache, option_cache = {}, {}
    for item in items:
        pid, option, qty = item["product_id"], item["option"], item["qty"]
        if pid not in product_cache:
            product_cache[pid] = product_by_id(pid)
            option_cache[pid] = product_options(pid) if product_cache[pid] else []
        product = product_cache[pid]
        line = {"product_id": pid, "option": option, "qty": qty, "ok": False, "error": ""}
        if product is None:
            line["error"] = "판매하지 않는 상품입니다."
        else:
            options = option_cache[pid]
            unit = int(product.get("price") or 0)
            line.update({
                "name": display_name(product),
                "type": str(product.get("type") or ""),
                "image": first_image(product),
                "unit_price": unit,
                "max_qty": MAX_LINE_QTY,
            })
            if str(product.get("condition") or "") != "판매중":
                line["error"] = "현재 " + (str(product.get("condition") or "구매 불가")) + " 상품입니다."
            elif unit <= 0:
                line["error"] = "가격이 설정되지 않은 상품입니다."
            elif options and not option:
                line["error"] = "옵션을 선택해 주세요."
            elif _is_bike(product):
                line["error"] = "중고 바이크는 온라인 결제 없이 매장 상담 후 거래합니다."
            elif option and not options:
                line["error"] = "선택한 옵션이 없는 상품입니다."
            else:
                if options:
                    match = next((o for o in options if str(o.get("name")) == option), None)
                    if match is None:
                        line["error"] = "선택한 옵션을 찾을 수 없습니다."
                    else:
                        unit += int(match.get("extra_price") or 0)
                        line["unit_price"] = unit
                        stock = match.get("stock")
                        if stock is not None:
                            line["max_qty"] = min(MAX_LINE_QTY, int(stock))
                            if int(stock) <= 0:
                                line["error"] = "품절된 옵션입니다."
                            elif qty > int(stock):
                                line["error"] = f"재고가 {int(stock)}개 남았습니다."
                if not line["error"] and _is_bike(product):
                    line["max_qty"] = 1
                    if qty != 1:
                        line["qty"] = qty = 1
                    if _active_order_exists(pid):
                        line["error"] = "다른 고객이 결제했거나 결제 진행 중인 매물입니다."
            if not line["error"]:
                line["ok"] = True
                line["amount"] = unit * qty
                total += unit * qty
        if not line["ok"]:
            problems.append((line.get("name") or pid) + ": " + line["error"])
        lines.append(line)
    if strict and problems:
        raise ValueError(" / ".join(problems[:3]))
    return {"lines": lines, "total": total, "ok": not problems}


def create_order(payload):
    _require_payment_enabled()
    data = _validate_order_payload(payload)
    raw_items = payload.get("items")
    if not raw_items:
        raw_items = [{"product_id": data["product_id"], "qty": 1}]
    quote_result = quote_items(raw_items, strict=True)
    lines = quote_result["lines"]
    amount = int(quote_result["total"])
    if amount <= 0:
        raise ValueError("결제할 금액이 없습니다.")
    try:
        client_total = int(payload.get("expected_amount") or 0)
    except (TypeError, ValueError):
        client_total = 0
    if client_total and client_total != amount:
        raise ValueError("상품 가격이나 재고가 바뀌었습니다. 장바구니를 새로고침해 주세요.")

    first = lines[0]
    total_qty = sum(line["qty"] for line in lines)
    order_name = first["name"] + (f" {first['option']}" if first["option"] else "")
    if len(lines) > 1:
        order_name += f" 외 {len(lines) - 1}건"
    order_id = "TJR_" + time.strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:12]
    row = {
        "order_id": order_id,
        "product_id": first["product_id"],
        "product_name": order_name[:200],
        "product_type": first["type"][:30],
        "unit_price": int(first["unit_price"]),
        "quantity": total_qty,
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
    client = db_client()
    client.table("orders").insert(row).execute()
    try:
        client.table("order_items").insert([
            {
                "order_id": order_id,
                "product_id": line["product_id"],
                "product_type": line["type"][:30],
                "product_name": line["name"][:200],
                "option_name": line["option"] or None,
                "unit_price": int(line["unit_price"]),
                "quantity": int(line["qty"]),
                "amount": int(line["amount"]),
            }
            for line in lines
        ]).execute()
    except Exception:
        client.table("orders").update({
            "status": "failed",
            "failure_code": "ITEMS_SAVE_FAILED",
            "failure_message": "주문 상품 저장에 실패했습니다.",
        }).eq("order_id", order_id).execute()
        raise
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
    """승인 요청 전에 재고를 먼저 잡습니다. 중고 바이크는 '판매중→예약중', 옵션은 재고 차감.

    하나라도 실패하면 이미 잡은 것을 되돌리고 False를 돌려줍니다.
    """
    if order.get("stock_reserved"):
        return True
    client = db_client()
    done = []
    ok = True
    for item in order_items(order):
        pid = item.get("product_id")
        qty = int(item.get("quantity") or 1)
        option = item.get("option_name")
        if _is_bike(item):
            if _active_order_exists(pid, exclude_order_id=order.get("order_id")):
                ok = False
                break
            claimed = (
                client.table("products").update({"condition": "예약중"})
                .eq("id", pid).eq("condition", "판매중").execute().data
            )
            if not claimed:
                ok = False
                break
            done.append(("bike", pid, None, 1))
        elif option:
            reserved = client.rpc(
                "reserve_option_stock",
                {"p_product_id": pid, "p_name": option, "p_qty": qty},
            ).execute().data
            if reserved is not True:
                ok = False
                break
            done.append(("option", pid, option, qty))
    if not ok:
        _undo_reservations(done)
        return False
    client.table("orders").update({"stock_reserved": True}).eq(
        "order_id", order["order_id"]
    ).execute()
    order["stock_reserved"] = True
    _cache.update(time=0, rows=None)
    return True


def _undo_reservations(done):
    client = db_client()
    for kind, pid, option, qty in done:
        try:
            if kind == "bike":
                client.table("products").update({"condition": "판매중"}).eq(
                    "id", pid
                ).eq("condition", "예약중").execute()
            else:
                client.rpc(
                    "release_option_stock",
                    {"p_product_id": pid, "p_name": option, "p_qty": qty},
                ).execute()
        except Exception as exc:
            _log(f"undo reservation failed {pid} {type(exc).__name__}: {exc}")
    _cache.update(time=0, rows=None)


def _release_bike(order):
    """이 주문이 잡아둔 재고(바이크 예약·옵션 재고)만 되돌립니다."""
    if not order.get("stock_reserved"):
        return
    done = []
    for item in order_items(order):
        pid = item.get("product_id")
        if _is_bike(item):
            if not _active_order_exists(pid, exclude_order_id=order.get("order_id")):
                done.append(("bike", pid, None, 1))
        elif item.get("option_name"):
            done.append(("option", pid, item.get("option_name"), int(item.get("quantity") or 1)))
    # 먼저 플래그를 내려 중복 복원을 막습니다.
    db_client().table("orders").update({"stock_reserved": False}).eq(
        "order_id", order["order_id"]
    ).eq("stock_reserved", True).execute()
    order["stock_reserved"] = False
    _undo_reservations(done)


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
                "failure_code": "OUT_OF_STOCK",
                "failure_message": "재고가 부족하거나 다른 고객이 먼저 결제한 상품이 있습니다.",
            }
        ).eq("order_id", order_id).execute()
        raise ValueError("재고가 부족하거나 다른 고객이 먼저 결제한 상품이 있습니다. 결제는 승인되지 않았습니다.")

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
    return result


SHOP_CSS = """
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{margin:0;background:#080808;color:#eee;font-family:Arial,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;overflow-x:hidden}
img,iframe{max-width:100%}
a{color:#ff8a24;text-decoration:none}.wrap{max-width:980px;margin:0 auto;padding:24px 18px 60px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;gap:12px}
.logo{font-size:26px;font-weight:900;color:#ff6900}.panel{background:#111;border:1px solid #2a2a2a;padding:20px;border-radius:6px}
.grid{display:grid;grid-template-columns:1.1fr 1fr;gap:24px}
.line{display:grid;grid-template-columns:72px 1fr auto;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid #222}
.line img{width:72px;height:72px;object-fit:cover;background:#1a1a1a;border-radius:4px}
.line .nm{font-weight:700}.line .op{color:#aaa;font-size:13px}.line .er{color:#ff7a7a;font-size:13px;margin-top:4px}
.qty{display:inline-flex;align-items:center;border:1px solid #333;border-radius:4px;overflow:hidden}
.qty button{width:30px;height:30px;border:0;background:#1b1b1b;color:#fff;cursor:pointer;font-size:16px;padding:0;margin:0}
.qty span{min-width:34px;text-align:center}.rm{background:none;border:0;color:#999;cursor:pointer;font-size:13px;margin-top:6px;padding:0}
.price{font-weight:800;text-align:right;white-space:nowrap}.total{display:flex;justify-content:space-between;font-size:20px;font-weight:900;margin:18px 0}
.btn{display:block;width:100%;border:0;background:#ff6900;color:#fff;font-size:17px;font-weight:900;padding:15px;margin-top:12px;cursor:pointer;border-radius:4px;text-align:center}
.btn.sub{background:#222;border:1px solid #444}.btn:disabled{opacity:.45;cursor:not-allowed}
label{display:block;margin:12px 0 6px;color:#bbb}input,select,textarea{width:100%;padding:13px;background:#0b0b0b;border:1px solid #3a3a3a;color:#fff;border-radius:4px;font-size:16px}
.addr-row{display:grid;grid-template-columns:130px 1fr;gap:8px}.small{font-size:13px;color:#aaa;line-height:1.6}
.agree{display:flex;gap:8px;align-items:flex-start;margin:18px 0}.agree input{width:auto;margin-top:4px}
#msg{min-height:24px;margin-top:10px;color:#ffb36b}.test-banner{background:#2b190b;border:1px solid #7d491c;padding:12px;margin-bottom:18px;border-radius:4px}
#payment-method,#agreement{background:white;border-radius:6px;margin-top:16px;overflow:hidden;min-height:60px}
.panel,.grid>section{min-width:0}.empty{padding:40px 0;text-align:center;color:#aaa}
@media(max-width:760px){.grid{grid-template-columns:1fr}.addr-row{grid-template-columns:1fr}}
"""

SHOP_JS = r"""
const CART_KEY = "twoj_cart_v1";
const BUY_KEY = "twoj_buynow_v1";
function readList(storage, key){
  try { const v = JSON.parse(storage.getItem(key) || "[]"); return Array.isArray(v) ? v : []; }
  catch(e){ return []; }
}
function writeList(storage, key, list){ storage.setItem(key, JSON.stringify(list.slice(0, 20))); }
function getCart(){ return readList(localStorage, CART_KEY); }
function setCart(list){ writeList(localStorage, CART_KEY, list); }
function won(n){ return Number(n || 0).toLocaleString("ko-KR") + "원"; }
function esc(t){ const d = document.createElement("div"); d.textContent = t == null ? "" : String(t); return d.innerHTML; }
async function quote(items){
  const r = await fetch("/api/cart/quote?items=" + encodeURIComponent(JSON.stringify(items)), {cache:"no-store"});
  const body = await r.json();
  if (!r.ok) throw new Error(body.message || "상품 정보를 불러오지 못했습니다.");
  return body;
}
"""


def _shop_shell(title, body, script="", head_extra=""):
    mode_badge = (
        '<div class="test-banner"><b>TEST 결제</b> · 실제 금액은 청구되지 않습니다.</div>'
        if TOSS_TEST_MODE else ""
    )
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{esc(title)} | TWO J ROAD</title>{head_extra}
<style>{SHOP_CSS}</style></head><body><div class="wrap">
<div class="top"><a class="logo" href="/">TWO J ROAD</a><a href="/">쇼핑 계속하기</a></div>
{mode_badge}{body}
<footer style="margin-top:40px;border-top:1px solid #2a2a2a;padding-top:14px;font-size:13px;color:#999;line-height:1.7">{business_info_html()}</footer></div>
<script>{SHOP_JS}</script><script>{script}</script></body></html>'''


def cart_add_page():
    """팝업의 '장바구니/구매하기' 링크가 도착하는 곳. 브라우저에 담고 다음 화면으로 이동합니다."""
    script = r"""
(function(){
  const q = new URLSearchParams(location.search);
  const pid = (q.get("product") || "").slice(0, 64);
  let items = [];
  try { items = JSON.parse(q.get("items") || "[]"); } catch(e) { items = []; }
  if (!Array.isArray(items) || !items.length) items = [{o: q.get("option") || "", q: Number(q.get("qty") || 1)}];
  const picked = items
    .map(i => ({product_id: pid, option: String(i.o || "").slice(0, 60), qty: Math.max(0, Math.min(20, parseInt(i.q, 10) || 0))}))
    .filter(i => i.product_id && i.qty > 0);
  if (!picked.length) { location.replace("/?page=detail&id=" + encodeURIComponent(pid)); return; }
  if (q.get("next") === "buy") {
    writeList(sessionStorage, BUY_KEY, picked);
    location.replace("/checkout?mode=buy");
    return;
  }
  const cart = getCart();
  for (const it of picked) {
    const found = cart.find(c => c.product_id === it.product_id && (c.option || "") === it.option);
    if (found) found.qty = Math.min(20, (parseInt(found.qty, 10) || 0) + it.qty);
    else cart.push(it);
  }
  setCart(cart);
  location.replace("/cart");
})();
"""
    return _shop_shell("장바구니 담는 중", '<p class="empty">장바구니에 담는 중입니다…</p>', script)


def cart_page():
    body = '''<h1>장바구니</h1>
<div class="panel"><div id="lines"><p class="empty">불러오는 중…</p></div>
<div class="total"><span>총 결제금액</span><span id="total">0원</span></div>
<div id="msg"></div>
<button class="btn" id="order" disabled>주문하기</button>
<a class="btn sub" href="/">쇼핑 계속하기</a></div>'''
    script = r"""
async function render(){
  const cart = getCart();
  const box = document.getElementById("lines");
  const btn = document.getElementById("order");
  if (!cart.length) {
    box.innerHTML = '<p class="empty">장바구니가 비어 있습니다.</p>';
    document.getElementById("total").textContent = "0원";
    btn.disabled = true; return;
  }
  let data;
  try { data = await quote(cart); }
  catch(e) { document.getElementById("msg").textContent = e.message; return; }
  box.innerHTML = data.lines.map((l, i) => `
    <div class="line">
      ${l.image ? `<img src="${esc(l.image)}" alt="">` : '<img alt="">'}
      <div>
        <div class="nm">${esc(l.name || "판매 종료 상품")}</div>
        ${l.option ? `<div class="op">옵션: ${esc(l.option)}</div>` : ""}
        <div class="qty"><button data-i="${i}" data-d="-1" aria-label="수량 빼기">−</button><span>${l.qty}</span><button data-i="${i}" data-d="1" aria-label="수량 더하기">+</button></div>
        ${l.error ? `<div class="er">${esc(l.error)}</div>` : ""}
        <div><button class="rm" data-rm="${i}">삭제</button></div>
      </div>
      <div class="price">${l.ok ? won(l.amount) : "-"}</div>
    </div>`).join("");
  document.getElementById("total").textContent = won(data.total);
  document.getElementById("msg").textContent = data.ok ? "" : "구매할 수 없는 상품을 삭제하거나 수량을 조정해 주세요.";
  btn.disabled = !data.ok || data.total <= 0;
  box.querySelectorAll("button[data-d]").forEach(b => b.onclick = () => {
    const list = getCart(); const i = +b.dataset.i;
    const max = (data.lines[i] && data.lines[i].max_qty) || 20;
    list[i].qty = Math.max(1, Math.min(max, (parseInt(list[i].qty, 10) || 1) + (+b.dataset.d)));
    setCart(list); render();
  });
  box.querySelectorAll("button[data-rm]").forEach(b => b.onclick = () => {
    const list = getCart(); list.splice(+b.dataset.rm, 1); setCart(list); render();
  });
}
document.getElementById("order").onclick = () => { location.href = "/checkout?mode=cart"; };
render();
"""
    return _shop_shell("장바구니", body, script)


POLICY_EFFECTIVE_DATE = "2026년 9월 16일"


def _policy_contact():
    return f"{BIZ_NAME} · 대표 {BIZ_OWNER} · {BIZ_ADDRESS}" + (f" · 전화 {PHONE}" if PHONE else "")


def _policy_sections(kind):
    contact = _policy_contact()
    if kind == "terms":
        return "이용약관", [
            ("제1조 (목적)", f"이 약관은 {BIZ_NAME}(이하 \"회사\")가 운영하는 온라인 쇼핑몰 TWO J ROAD(www.maspick.co.kr, 이하 \"몰\")에서 제공하는 상품 판매 및 관련 서비스의 이용 조건과 절차, 회사와 이용자의 권리·의무를 정하는 것을 목적으로 합니다."),
            ("제2조 (정의)", "\"이용자\"란 몰에 접속하여 이 약관에 따라 회사가 제공하는 서비스를 받는 자를 말하며, 몰은 별도의 회원가입 없이 비회원 주문으로 운영됩니다."),
            ("제3조 (약관의 게시와 변경)", "회사는 이 약관을 몰의 초기화면 하단에 게시합니다. 회사는 관련 법령을 위반하지 않는 범위에서 약관을 변경할 수 있으며, 변경 시 적용일자와 변경 사유를 적용일 7일 전부터 몰에 공지합니다."),
            ("제4조 (서비스의 제공)", "회사는 바이크 의류·용품 등 재화의 정보 제공 및 판매, 주문에 따른 배송, 상품 문의 응대 등의 서비스를 제공합니다. 중고 바이크(오토바이)는 온라인 결제 대상이 아니며, 매장 방문 또는 전화 상담을 통해 별도로 거래합니다."),
            ("제5조 (구매신청)", "이용자는 몰에서 상품과 옵션·수량을 선택하고, 주문자 정보(이름, 휴대폰 번호, 배송지 등)를 입력한 뒤 개인정보 수집·이용 및 결제 조건에 동의하여 구매를 신청합니다."),
            ("제6조 (계약의 성립)", "회사는 구매신청에 대해 결제가 정상적으로 승인되면 이를 승낙한 것으로 봅니다. 다만 신청 내용에 허위·누락이 있거나 재고가 없는 경우 등에는 승낙하지 않거나 계약을 취소할 수 있으며, 이 경우 결제 금액을 지체 없이 환불합니다."),
            ("제7조 (결제방법)", "상품 대금은 회사가 계약한 결제대행사(토스페이먼츠)를 통해 신용·체크카드, 간편결제(네이버페이, 카카오페이, 토스페이 등), 계좌이체 등 몰에서 안내하는 방법으로 지급할 수 있습니다."),
            ("제8조 (배송)", "회사는 결제 완료일로부터 영업일 기준 7일 이내에 상품을 발송하도록 노력하며, 재고 사정 등으로 지연될 경우 이용자에게 연락드립니다. 매장 방문 수령을 원하시면 주문 전 문의해 주세요."),
            ("제9조 (청약철회 등)", "청약철회, 교환 및 환불에 관한 사항은 몰 하단의 「교환·환불 안내」에 따릅니다."),
            ("제10조 (개인정보보호)", "회사는 이용자의 개인정보를 관련 법령과 몰 하단의 「개인정보처리방침」에 따라 보호합니다."),
            ("제11조 (회사의 의무)", "회사는 법령과 이 약관이 금지하는 행위를 하지 않으며, 지속적이고 안정적으로 재화를 제공하기 위해 노력합니다."),
            ("제12조 (이용자의 의무)", "이용자는 주문 시 허위 정보를 입력하거나 타인의 정보를 도용해서는 안 되며, 몰의 운영을 방해하는 행위를 해서는 안 됩니다."),
            ("제13조 (분쟁해결)", f"회사는 이용자의 불만과 피해를 신속히 처리하기 위해 노력합니다. 문의처: {contact}. 분쟁이 해결되지 않는 경우 이용자는 한국소비자원, 전자거래분쟁조정위원회 등에 조정을 신청할 수 있습니다."),
            ("제14조 (재판권 및 준거법)", "회사와 이용자 간 분쟁에 관한 소송은 민사소송법에 따른 관할 법원에 제기하며, 대한민국 법을 적용합니다."),
            ("부칙", f"이 약관은 {POLICY_EFFECTIVE_DATE}부터 시행합니다."),
        ]
    if kind == "privacy":
        return "개인정보처리방침", [
            ("1. 총칙", f"{BIZ_NAME}(이하 \"회사\")는 「개인정보 보호법」 등 관련 법령을 준수하며, 이용자의 개인정보를 아래와 같이 처리합니다."),
            ("2. 수집하는 개인정보 항목과 목적",
             "· 주문·결제·배송: 주문자 이름, 휴대폰 번호, 이메일(선택), 우편번호·주소, 결제 기록(결제수단, 승인 정보)\n"
             "· 상품 문의: 작성자 이름, 문의 내용, 비밀번호(암호화하여 저장)\n"
             "· 상품 후기: 주문번호, 휴대폰 번호(본인 주문 확인용, 후기에는 가려진 이름만 표시), 후기 내용\n"
             "· 서비스 운영: 찜 기능용 익명 방문자 식별값(쿠키), 접속 기록\n"
             "회사는 회원가입을 받지 않으며, 위 목적 외의 용도로 개인정보를 이용하지 않습니다."),
            ("3. 보유 및 이용 기간",
             "목적이 달성되면 지체 없이 파기합니다. 다만 「전자상거래 등에서의 소비자보호에 관한 법률」에 따라 다음 기간 동안 보관합니다.\n"
             "· 계약 또는 청약철회 등에 관한 기록: 5년\n"
             "· 대금결제 및 재화 등의 공급에 관한 기록: 5년\n"
             "· 소비자의 불만 또는 분쟁처리에 관한 기록: 3년\n"
             "· 표시·광고에 관한 기록: 6개월"),
            ("4. 개인정보의 제3자 제공", "회사는 이용자의 동의 또는 법령에 근거한 경우를 제외하고 개인정보를 제3자에게 제공하지 않습니다. 상품 배송을 위해 택배사에 수령인 이름, 연락처, 주소를 제공하며, 배송 완료 후 해당 목적 범위에서만 이용됩니다."),
            ("5. 개인정보 처리의 위탁",
             "· 토스페이먼츠(주): 결제 처리 및 결제 도용 방지\n"
             "· Supabase Inc.: 주문·상품 데이터 보관(클라우드 데이터베이스)\n"
             "· Render Services, Inc.: 웹사이트 호스팅\n"
             "해외에 위치한 클라우드 사업자에 대한 위탁은 서비스 제공을 위해 필요한 범위로 한정하며, 암호화된 통신으로 전송됩니다."),
            ("6. 개인정보의 파기", "보유 기간이 지나거나 처리 목적이 달성된 개인정보는 복구할 수 없는 방법으로 지체 없이 삭제합니다."),
            ("7. 이용자의 권리", f"이용자는 언제든지 자신의 개인정보 열람, 정정, 삭제, 처리정지를 요청할 수 있으며, 회사는 법령에서 정한 기간 내에 조치합니다. 요청은 아래 개인정보 보호책임자에게 해 주세요."),
            ("8. 안전성 확보 조치", "회사는 주문 데이터에 대한 접근 권한을 관리자로 제한하고, 전송 구간을 암호화(HTTPS)하며, 문의 비밀번호는 복호화할 수 없는 방식으로 저장합니다. 카드번호 등 결제수단 정보는 회사가 저장하지 않고 결제대행사가 처리합니다."),
            ("9. 쿠키의 사용", "찜 기능 제공을 위해 개인을 식별하지 않는 익명 방문자 식별값을 쿠키로 저장합니다. 이용자는 브라우저 설정에서 쿠키 저장을 거부할 수 있으며, 이 경우 찜 기능 이용이 제한될 수 있습니다."),
            ("10. 개인정보 보호책임자", f"성명: {BIZ_OWNER} (대표) · 연락처: {BIZ_ADDRESS}" + (f", 전화 {PHONE}" if PHONE else "") + "\n개인정보 침해에 대한 신고·상담은 개인정보침해신고센터(privacy.kisa.or.kr, 국번없이 118)에 문의하실 수 있습니다."),
            ("11. 시행일", f"이 개인정보처리방침은 {POLICY_EFFECTIVE_DATE}부터 적용됩니다."),
        ]
    return "교환·환불 안내", [
        ("청약철회(반품) 기간", "상품을 받은 날부터 7일 이내에 교환·반품을 신청할 수 있습니다. 상품의 내용이 표시·광고와 다르거나 계약 내용과 다르게 이행된 경우에는 상품을 받은 날부터 3개월 이내, 그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 신청할 수 있습니다."),
        ("신청 방법", f"주문번호와 사유를 적어 매장으로 연락해 주세요. {_policy_contact()}"),
        ("교환·반품이 제한되는 경우",
         "· 이용자의 책임 있는 사유로 상품이 멸실·훼손된 경우(내용 확인을 위한 포장 훼손은 제외)\n"
         "· 착용·사용 흔적이 있거나 세탁·수선한 경우 등 사용으로 상품 가치가 현저히 줄어든 경우\n"
         "· 시간이 지나 다시 판매하기 곤란할 정도로 상품 가치가 줄어든 경우\n"
         "· 복제가 가능한 상품의 포장을 훼손한 경우\n"
         "· 중고 상품으로서 상품 상세에 고지한 사용감·하자를 이유로 하는 경우"),
        ("배송비", "단순 변심에 의한 교환·반품은 왕복 배송비를 구매자가 부담합니다. 상품 불량이나 오배송 등 회사의 사유인 경우 배송비는 회사가 부담합니다."),
        ("환불", "반품 상품이 회사에 도착해 확인된 날부터 3영업일 이내에 결제 취소를 진행합니다. 카드·간편결제는 결제대행사와 카드사 사정에 따라 실제 환불 반영까지 며칠이 더 걸릴 수 있습니다."),
        ("중고 바이크", "중고 바이크(오토바이)는 온라인 결제 대상이 아니며, 매장에서 차량 상태를 직접 확인하고 계약하는 방식으로 거래합니다. 거래 조건은 매장 계약서에 따릅니다."),
        ("시행일", f"이 안내는 {POLICY_EFFECTIVE_DATE}부터 적용됩니다."),
    ]


def policy_page(kind):
    title, sections = _policy_sections(kind)
    body = f"<h1>{esc(title)}</h1>"
    for heading, text in sections:
        body += f'<h2 style="font-size:18px;margin-top:26px">{esc(heading)}</h2><p class="text">{esc(text)}</p>'
    path = {"terms": "/terms", "privacy": "/privacy", "refund": "/refund"}[kind]
    return page(f"{title} | {BRAND}", f"{BIZ_NAME} {title}", path, body)


def checkout_page():
    body = f'''<div class="grid">
<section class="panel"><h2>주문 상품</h2><div id="lines"><p class="empty">불러오는 중…</p></div>
<div class="total"><span>총 결제금액</span><span id="total">0원</span></div>
<div class="small">배송·교환·환불 관련 문의는 매장으로 연락해 주세요.</div></section>
<section class="panel"><h2>주문 정보</h2>
<label for="buyer_name">주문자명</label><input id="buyer_name" maxlength="50" autocomplete="name">
<label for="buyer_phone">휴대폰</label><input id="buyer_phone" inputmode="tel" placeholder="01012345678" autocomplete="tel">
<label for="buyer_email">이메일 (선택)</label><input id="buyer_email" type="email" maxlength="120" autocomplete="email">
<label>배송지</label>
<div class="addr-row"><input id="postal_code" maxlength="20" placeholder="우편번호" autocomplete="postal-code"><input id="address1" maxlength="200" placeholder="기본 주소" autocomplete="address-line1"></div>
<input id="address2" maxlength="200" placeholder="상세 주소" style="margin-top:8px" autocomplete="address-line2">
<div class="agree"><input id="privacy" type="checkbox"><label for="privacy" style="margin:0">
주문·결제·배송·환불 처리를 위한 개인정보 수집 및 이용에 동의합니다.
<span class="small">주문 처리에 필요한 최소 정보만 저장합니다.</span></label></div>
<div id="payment-method"></div><div id="agreement"></div>
<button class="btn" id="payment-button" disabled>{"테스트 결제하기" if TOSS_TEST_MODE else "결제하기"}</button>
<div id="msg"></div></section></div>'''
    script = r"""
const CLIENT_KEY = __CLIENT_KEY__;
const MODE = new URLSearchParams(location.search).get("mode") === "buy" ? "buy" : "cart";
function items(){ return MODE === "buy" ? readList(sessionStorage, BUY_KEY) : getCart(); }
function value(id){ return document.getElementById(id).value.trim(); }
function message(t){ document.getElementById("msg").textContent = t || ""; }
async function main(){
  const list = items();
  const box = document.getElementById("lines");
  if (!list.length) { box.innerHTML = '<p class="empty">주문할 상품이 없습니다. <a href="/">쇼핑하러 가기</a></p>'; return; }
  let data;
  try { data = await quote(list); } catch(e) { message(e.message); return; }
  box.innerHTML = data.lines.map(l => `
    <div class="line">
      ${l.image ? `<img src="${esc(l.image)}" alt="">` : '<img alt="">'}
      <div><div class="nm">${esc(l.name || "판매 종료 상품")}</div>
      ${l.option ? `<div class="op">옵션: ${esc(l.option)}</div>` : ""}
      <div class="op">수량 ${l.qty}개</div>
      ${l.error ? `<div class="er">${esc(l.error)}</div>` : ""}</div>
      <div class="price">${l.ok ? won(l.amount) : "-"}</div>
    </div>`).join("");
  document.getElementById("total").textContent = won(data.total);
  if (!data.ok) {
    message("구매할 수 없는 상품이 있습니다. " + (MODE === "cart" ? "장바구니에서 정리해 주세요." : "상품을 다시 선택해 주세요."));
    return;
  }
  const button = document.getElementById("payment-button");
  try {
    const tossPayments = TossPayments(CLIENT_KEY);
    const widgets = tossPayments.widgets({customerKey: TossPayments.ANONYMOUS});
    await widgets.setAmount({currency: "KRW", value: data.total});
    await Promise.all([
      widgets.renderPaymentMethods({selector: "#payment-method", variantKey: "DEFAULT"}),
      widgets.renderAgreement({selector: "#agreement", variantKey: "AGREEMENT"}),
    ]);
    button.disabled = false;
    button.addEventListener("click", async () => {
      if (!document.getElementById("privacy").checked) { message("개인정보 수집 동의가 필요합니다."); return; }
      button.disabled = true;
      message("주문 정보를 확인하고 있습니다.");
      try {
        const response = await fetch("/api/orders/create", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            items: list,
            expected_amount: data.total,
            buyer_name: value("buyer_name"),
            buyer_phone: value("buyer_phone"),
            buyer_email: value("buyer_email"),
            postal_code: value("postal_code"),
            address1: value("address1"),
            address2: value("address2"),
            privacy_agreed: true
          })
        });
        const order = await response.json();
        if (!response.ok) throw new Error(order.message || "주문 생성에 실패했습니다.");
        if (Number(order.amount) !== Number(data.total)) throw new Error("상품 금액이 변경되었습니다. 페이지를 새로고침해 주세요.");
        localStorage.setItem("twoj_last_checkout", JSON.stringify({mode: MODE, order_id: order.order_id}));
        message("");
        await widgets.requestPayment({
          orderId: order.order_id,
          orderName: order.order_name,
          successUrl: location.origin + "/payment/success",
          failUrl: location.origin + "/payment/fail",
          customerName: order.buyer_name,
          customerEmail: order.buyer_email || undefined,
          customerMobilePhone: order.buyer_phone
        });
      } catch (error) {
        console.error(error);
        message(error && error.message ? error.message : "결제를 시작하지 못했습니다.");
        button.disabled = false;
      }
    });
  } catch (error) {
    console.error(error);
    message("결제 모듈을 불러오지 못했습니다.");
  }
}
main();
""".replace("__CLIENT_KEY__", json.dumps(TOSS_CLIENT_KEY))
    return _shop_shell(
        "주문·결제", body, script,
        head_extra='<script src="https://js.tosspayments.com/v2/standard"></script>',
    )


CLEAR_CART_SCRIPT = r"""<script>
try {
  const last = JSON.parse(localStorage.getItem("twoj_last_checkout") || "null");
  const oid = new URLSearchParams(location.search).get("orderId");
  if (last && last.order_id === oid) {
    if (last.mode === "cart") localStorage.removeItem("twoj_cart_v1");
    else sessionStorage.removeItem("twoj_buynow_v1");
    localStorage.removeItem("twoj_last_checkout");
  }
} catch (e) {}
</script>"""


def payment_result_page(title, message, ok=True, details="", script=""):
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
</div>{script}</body></html>'''


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

    def _payment_off(handler):
        handler.set_status(503)
        handler.set_header("Content-Type", "text/html; charset=utf-8")
        handler.finish(payment_result_page(
            "결제 일시 중지",
            "현재 온라인 결제를 사용할 수 없습니다. 매장으로 문의해 주세요.",
            False,
        ))

    class Checkout(tornado.web.RequestHandler):
        """예전 단일상품 결제 주소 → 바로구매 흐름으로 연결"""
        def get(self, product_id):
            self.set_header("Cache-Control", "no-store")
            self.redirect(
                "/cart/add?" + urlencode({"product": product_id, "qty": 1, "next": "buy"}),
                permanent=False,
            )

    class ShopPage(tornado.web.RequestHandler):
        def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("X-Robots-Tag", "noindex")
            if not PAYMENT_ENABLED:
                _payment_off(self)
                return
            self.set_header("Content-Type", "text/html; charset=utf-8")
            path = self.request.path.rstrip("/")
            if path == "/cart/add":
                self.finish(cart_add_page())
            elif path == "/cart":
                self.finish(cart_page())
            else:
                self.finish(checkout_page())

    class CartQuote(tornado.web.RequestHandler):
        async def get(self):
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "application/json; charset=utf-8")
            raw = self.get_query_argument("items", default="[]")
            if len(raw) > 8000:
                self.set_status(413)
                self.finish(json.dumps({"message": "요청 데이터가 너무 큽니다."}, ensure_ascii=False))
                return
            try:
                items = json.loads(raw)
                result = await asyncio.to_thread(quote_items, items, False)
                self.finish(json.dumps(result, ensure_ascii=False))
            except ValueError as exc:
                self.set_status(400)
                self.finish(json.dumps({"message": str(exc)}, ensure_ascii=False))
            except Exception as exc:
                _log(f"quote error {type(exc).__name__}: {exc}")
                self.set_status(500)
                self.finish(json.dumps({"message": "상품 정보를 불러오지 못했습니다."}, ensure_ascii=False))

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
                self.finish(payment_result_page("결제 완료", status_message, True, details, CLEAR_CART_SCRIPT))
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

    class Policy(tornado.web.RequestHandler):
        def get(self, kind):
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.set_header("Cache-Control", "public, max-age=600")
            self.finish(policy_page(kind))

        head = get

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

    from tornado.web import OutputTransform

    class VisitorCookie(OutputTransform):
        """찜 기능용 익명 방문자 ID 쿠키(개인정보 없음)를 처음 방문 시 발급합니다."""
        def __init__(self, request):
            super().__init__(request)
            cookie = request.headers.get("Cookie", "")
            self._needs = VISITOR_COOKIE + "=" not in cookie and request.method == "GET"

        def transform_first_chunk(self, status_code, headers, chunk, finishing):
            if self._needs and status_code < 400 and "text/html" in str(headers.get("Content-Type", "")):
                headers.add(
                    "Set-Cookie",
                    f"{VISITOR_COOKIE}={uuid.uuid4().hex}; Path=/; Max-Age=31536000; "
                    "HttpOnly; Secure; SameSite=Lax",
                )
            return super().transform_first_chunk(status_code, headers, chunk, finishing)

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
                (r"/checkout/?", ShopPage),
                (r"/cart/?", ShopPage),
                (r"/cart/add", ShopPage),
                (r"/api/cart/quote", CartQuote),
                (r"/api/orders/create", CreateOrder),
                (r"/payment/success", PaymentSuccess),
                (r"/payment/fail", PaymentFail),
                (r"/(terms|privacy|refund)", Policy),
                (r"/api/toss/webhook", TossWebhook),
            ],
        )
        try:
            application.add_transform(VisitorCookie)
        except Exception as exc:
            _log(f"visitor cookie not installed {type(exc).__name__}: {exc}")
        try:
            _start_reconcile()
        except Exception as exc:
            _log(f"reconcile timer not started {type(exc).__name__}: {exc}")
        return application

    Server._create_app = create_app
    cli.main()


if __name__ == "__main__":
    main()
