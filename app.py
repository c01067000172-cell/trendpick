import streamlit as st
import os
import json
import uuid
import time
import base64
import mimetypes
from pathlib import Path
from html import escape
from textwrap import dedent
from urllib.parse import urlencode

SITE_URL = "https://www.maspick.co.kr"
STORE_NAME = "포천 TWO J ROAD"
STORE_ADDRESS = "경기 포천시 내촌면 금강로3224번길 11-7"

# =========================================================
# PAGE / SEO
# =========================================================

def initial_query_value(name, default=""):
    value = st.query_params.get(name, default)
    return value[0] if isinstance(value, list) else value


def seo_page_info():
    page = initial_query_value("page", "home")
    category = initial_query_value("cat", "전체상품")

    if page == "store":
        return ("TWO J ROAD | 오프라인매장", "TWO J ROAD 매장 위치와 방문 안내")

    subcategory = initial_query_value("sub", "")
    category_titles = {
        "자켓": ("바이크 자켓·오토바이 자켓 | TWO J ROAD", "TWO J ROAD의 바이크 자켓과 오토바이 라이딩 자켓을 확인하세요."),
        "장갑": ("오토바이 장갑·바이크 장갑 | TWO J ROAD", "TWO J ROAD의 오토바이 장갑과 바이크 장갑을 확인하세요."),
        "하의": ("바이크 바지·라이딩 팬츠 | TWO J ROAD", "TWO J ROAD의 바이크 바지와 라이딩 팬츠를 확인하세요."),
        "신발": ("바이크 신발·부츠 | TWO J ROAD", "TWO J ROAD의 바이크 신발과 부츠를 확인하세요."),
        "상의": ("바이크 의류·상의 | TWO J ROAD", "TWO J ROAD의 바이크 상의를 확인하세요."),
    }
    if page == "shop" and category == "바이크 의류" and subcategory in category_titles:
        return category_titles[subcategory]
    if page == "shop" and category == "바이크 용품" and subcategory == "헬멧":
        return ("오토바이 헬멧·바이크 헬멧 | TWO J ROAD", "TWO J ROAD의 오토바이 헬멧을 확인하세요.")

    if page == "shop" and category == "바이크 의류":
        return (
            "바이크 의류 | 라이딩 자켓·팬츠·글러브 | 포천 TWO J ROAD",
            "포천 TWO J ROAD의 바이크 의류를 확인하세요.",
        )

    if page == "shop" and category == "중고 바이크":
        return (
            "포천 중고 바이크 | 할리데이비슨·중고 오토바이 | TWO J ROAD",
            "포천 TWO J ROAD의 중고 바이크 매물을 확인하세요.",
        )

    if page == "shop" and category == "바이크 용품":
        return (
            "바이크 용품 | 헬멧·오토바이 용품 | 포천 TWO J ROAD",
            "포천 TWO J ROAD의 바이크 용품을 확인하세요.",
        )

    return (
        "포천 TWO J ROAD | 중고 오토바이·바이크 의류·라이딩 용품",
        "포천 TWO J ROAD. 중고 오토바이와 바이크 의류, 라이딩 용품을 확인하세요.",
    )


SEO_TITLE, SEO_DESCRIPTION = seo_page_info()

st.set_page_config(
    page_title=SEO_TITLE,
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_original_markdown = st.markdown


def safe_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        body = dedent(body).strip()

    if kwargs.get("unsafe_allow_html"):
        return st.html(body)

    return _original_markdown(body, *args, **kwargs)


# =========================================================
# STORAGE
# =========================================================

DATA_DIR = Path(
    os.getenv(
        "TRENDPICK_DATA_DIR",
        str(Path(__file__).parent / "data")
    )
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_FILE = DATA_DIR / "products.json"

IMAGE_DIR = DATA_DIR / "product_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

BANNER_FILE = (
    Path(__file__).parent
    / "assets"
    / "jinbike_banner.png"
)

ADMIN_PASSWORD = os.getenv("MASPICK_ADMIN_PASSWORD", "")
MASPICK_PHONE = os.getenv("MASPICK_PHONE", "").strip()
MASPICK_KAKAO_URL = os.getenv("MASPICK_KAKAO_URL", "").strip()


DEMO_PRODUCTS = [
    {
        "id": "bike-001",
        "type": "bike",
        "category": "중고 바이크",
        "subcategory": "투어링",
        "brand": "HARLEY-DAVIDSON",
        "name": "Street Glide Special",
        "price": 31500000,
        "year": "2021",
        "mileage": "18,200km",
        "cc": "1,868cc",
        "condition": "판매중",
        "region": "경기 포천",
        "accident": "상담문의",
        "badge": "추천매물",
        "image": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=1200&q=85",
        "description": "화면 구성 확인용 샘플 중고 바이크입니다.",
        "demo": True,
    },
    {
        "id": "bike-002",
        "type": "bike",
        "category": "중고 바이크",
        "subcategory": "크루저",
        "brand": "HARLEY-DAVIDSON",
        "name": "Fat Boy 114",
        "price": 26800000,
        "year": "2020",
        "mileage": "21,400km",
        "cc": "1,868cc",
        "condition": "판매중",
        "region": "경기 포천",
        "accident": "상담문의",
        "badge": "인기",
        "image": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?auto=format&fit=crop&w=1200&q=85",
        "description": "화면 구성 확인용 샘플 중고 바이크입니다.",
        "demo": True,
    },
    {
        "id": "wear-001",
        "type": "wear",
        "category": "바이크 의류",
        "subcategory": "자켓",
        "brand": "HARLEY-DAVIDSON",
        "name": "라이딩 레더 재킷",
        "price": 489000,
        "condition": "판매중",
        "badge": "BEST",
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=1200&q=85",
        "description": "화면 구성 확인용 샘플 의류입니다.",
        "demo": True,
    },
    {
        "id": "gear-001",
        "type": "gear",
        "category": "바이크 용품",
        "subcategory": "헬멧",
        "brand": "BELL",
        "name": "Custom 500 Helmet",
        "price": 259000,
        "condition": "판매중",
        "badge": "BEST",
        "image": "https://images.unsplash.com/photo-1558980394-0c7c9299fe96?auto=format&fit=crop&w=1200&q=85",
        "description": "화면 구성 확인용 샘플 용품입니다.",
        "demo": True,
    },
]


def save_products(products):
    tmp = PRODUCT_FILE.with_suffix(".tmp")

    tmp.write_text(
        json.dumps(
            products,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    tmp.replace(PRODUCT_FILE)


def load_products():
    if not PRODUCT_FILE.exists():
        save_products([])
        return []

    try:
        data = json.loads(
            PRODUCT_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def get_product(products, product_id):
    for product in products:
        if product.get("id") == product_id:
            return product

    return None


def money(value):
    try:
        return f"{int(value):,}원"
    except Exception:
        return "가격문의"


def get_param(name, default=""):
    try:
        value = st.query_params.get(name, default)

        if isinstance(value, list):
            return value[0] if value else default

        return value

    except Exception:
        return default


def product_images(product):
    images = product.get("images")

    if isinstance(images, list) and images:
        return images

    image = str(product.get("image", "")).strip()

    if image:
        return [image]

    return []


def local_image_path(value):
    value = str(value or "").strip()

    if not value:
        return None

    if value.startswith(("http://", "https://", "data:")):
        return None

    p = Path(value)

    if not p.is_absolute():
        p = DATA_DIR / p

    return p


def image_src(value):
    value = str(value or "").strip()

    if not value:
        return ""

    if value.startswith(("http://", "https://", "data:")):
        return value

    p = local_image_path(value)

    if not p or not p.exists():
        return ""

    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"

    try:
        encoded = base64.b64encode(
            p.read_bytes()
        ).decode("ascii")

        return f"data:{mime};base64,{encoded}"

    except Exception:
        return ""


def main_image_src(product):
    images = product_images(product)

    if not images:
        return ""

    return image_src(images[0])


def save_uploaded_images(uploaded_files, product_id):
    saved = []

    if not uploaded_files:
        return saved

    mime_ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }

    for index, uploaded in enumerate(uploaded_files[:8], start=1):
        ext = mime_ext.get(
            getattr(uploaded, "type", ""),
            ""
        )

        if not ext:
            original_ext = Path(
                getattr(uploaded, "name", "")
            ).suffix.lower()

            if original_ext in (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ):
                ext = ".jpg" if original_ext == ".jpeg" else original_ext
            else:
                ext = ".jpg"

        filename = (
            f"{product_id}_{index}_"
            f"{uuid.uuid4().hex[:8]}{ext}"
        )

        target = IMAGE_DIR / filename
        target.write_bytes(uploaded.getbuffer())

        saved.append(
            f"product_images/{filename}"
        )

    return saved


def delete_local_images(product):
    for value in product_images(product):
        p = local_image_path(value)

        if not p:
            continue

        try:
            if p.exists() and IMAGE_DIR in p.parents:
                p.unlink()

        except Exception:
            pass


def banner_image_src():
    if not BANNER_FILE.exists():
        return ""

    try:
        mime = (
            mimetypes.guess_type(BANNER_FILE.name)[0]
            or "image/jpeg"
        )

        encoded = base64.b64encode(
            BANNER_FILE.read_bytes()
        ).decode("ascii")

        return f"data:{mime};base64,{encoded}"

    except Exception:
        return ""


PRODUCTS = load_products()


# =========================================================
# CSS
# =========================================================

safe_markdown("""
<style>

#MainMenu, footer, header {
    visibility:hidden;
}

[data-testid="stSidebar"] {
    display:none;
}

html, body, .stApp {
    background:#080808;
    color:#f4f4f4;
}

.stApp {
    background:
        radial-gradient(
            circle at top,
            #171717 0,
            #080808 520px
        );
}

.block-container {
    max-width:1480px;
    padding-top:0 !important;
    padding-left:28px !important;
    padding-right:28px !important;
    padding-bottom:70px !important;
}

* {
    box-sizing:border-box;
}

a {
    text-decoration:none !important;
}

.header {
    position:relative;
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    align-items:center;
    min-height:90px;
    border-bottom:1px solid #242424;
}

.header-center {
    grid-column:2;
    text-align:center;
}

.header-right {
    grid-column:3;
    text-align:right;
}

.admin-link {
    display:inline-block;
    color:#777 !important;
    font-size:11px;
    font-weight:700;
    letter-spacing:.5px;
    padding:8px 10px;
    border:1px solid #282828;
    background:#0d0d0d;
}

.admin-link:hover {
    color:#ff6900 !important;
    border-color:#ff6900;
}

.logo {
    min-height:44px;
    font-size:36px;
    letter-spacing:-1px;
    font-style:italic;
}

.logo::before {
    content:"TWO J";
    color:#ff6900;
    font-weight:1000;
}

.logo::after {
    content:" ROAD";
    color:#fff;
    font-weight:1000;
}

.logo-small {
    font-size:12px;
    letter-spacing:2px;
    color:#aaa;
}

.navbar {
    min-height:48px;
    display:flex;
    justify-content:center;
    align-items:center;
    gap:32px;
    border-bottom:1px solid #252525;
    white-space:nowrap;
    overflow-x:auto;
}

.navbar a {
    color:#e5e5e5;
    font-weight:800;
    font-size:14px;
}

.navbar a:hover {
    color:#ff6900;
}

.hero {
    width:100%;
    margin-top:28px;
    border:1px solid #222;
    overflow:hidden;
    line-height:0;
    background:#080808;
}
.hero img {
    display:block;
    width:100%;
    height:auto;
    max-width:100%;
}

.catalog-layout {
    display:grid;
    grid-template-columns:180px minmax(0,1fr);
    gap:24px;
    margin-top:18px;
}

.catalog-sidebar {
    border-top:2px solid #eee;
    font-size:14px;
}

.catalog-sidebar summary {
    padding:16px 0;
    font-weight:800;
    cursor:pointer;
}

.catalog-sidebar a {
    display:block;
    color:#bbb;
    padding:9px 8px;
    border-bottom:1px solid #242424;
    overflow-wrap:anywhere;
}

.catalog-sidebar a:hover,
.catalog-sidebar a.active {
    color:#ff6900;
    background:#191919;
}

.category-node {
    border-bottom:1px solid #242424;
}

.category-node summary {
    list-style:none;
    padding:9px 8px;
    color:#bbb;
    cursor:pointer;
}

.category-node summary::-webkit-details-marker {
    display:none;
}

.category-node summary::after {
    content:'+';
    float:right;
    color:#777;
}

.category-node[open] summary {
    color:#ff6900;
    background:#191919;
}

.category-node[open] summary::after {
    content:'−';
}

.category-children {
    border-bottom:1px solid #242424;
    padding:4px 0;
}

.category-children a {
    border-bottom:0;
    padding-left:28px;
    color:#b9c7d4;
}

.category-children a::before {
    content:'ㄴ';
    margin-right:7px;
    color:#777;
}

.catalog-results {
    min-width:0;
}

.grid {
    display:grid;
    grid-template-columns:repeat(5,minmax(0,1fr));
    gap:24px 12px;
}

.grid > a {
    min-width:0;
    color:inherit;
}

.card {
    background:transparent;
    border:0;
    min-width:0;
}

.card-imgbox {
    position:relative;
    width:100%;
    aspect-ratio:1 / 1;
    overflow:hidden;
    background:#eee;
    border:1px solid #292929;
}

.card-img {
    width:100%;
    height:100%;
    object-fit:contain;
}

.badge {
    position:absolute;
    left:6px;
    top:6px;
    padding:4px 6px;
    background:#ff6900;
    color:#fff;
    font-size:12px;
    font-weight:900;
}

.demo {
    position:absolute;
    right:6px;
    top:6px;
    padding:4px 6px;
    background:#333;
    color:#aaa;
    font-size:12px;
}

.card-body {
    padding:12px 2px;
    text-align:center;
}

.card-brand {
    font-size:12px;
    color:#bdbdbd;
}

.card-name {
    color:#eee;
    font-size:14px;
    font-weight:600;
    line-height:1.5;
    min-height:42px;
    margin-top:7px;
}

.card-info {
    font-size:12px;
    color:#aaa;
    margin-top:7px;
    line-height:1.5;
}

.card-price {
    font-size:16px;
    margin-top:9px;
    color:#fff;
    font-weight:1000;
}

.page-title {
    margin-top:22px;
    font-size:22px;
    font-weight:1000;
}

.page-subtitle {
    font-size:14px;
    color:#aaa;
    margin-top:7px;
    margin-bottom:16px;
}

.detail-photo {
    width:100%;
    max-height:650px;
    object-fit:contain;
    border:1px solid #252525;
    background:#eee;
}

.detail-gallery {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin-top:9px;
}

.detail-thumb {
    width:100%;
    aspect-ratio:1 / 1;
    object-fit:contain;
    border:1px solid #292929;
    background:#eee;
}

.detail-brand {
    color:#777;
    font-size:11px;
    letter-spacing:2px;
    font-weight:900;
}

.detail-name {
    font-size:35px;
    font-weight:1000;
    color:#fff;
    margin-top:10px;
}

.detail-price {
    color:#ff6900;
    font-size:31px;
    font-weight:1000;
    margin-top:22px;
    padding-bottom:22px;
    border-bottom:1px solid #333;
}

.spec-row {
    display:grid;
    grid-template-columns:110px 1fr;
    padding:13px 0;
    border-bottom:1px solid #222;
    font-size:13px;
}

.spec-label {
    color:#707070;
}

.spec-value {
    color:#ddd;
}

.contact-actions {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:22px;
}

.contact-btn {
    min-height:52px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:14px;
    font-weight:900;
    border:1px solid #333;
    color:#fff !important;
    background:#151515;
}

.contact-btn:hover {
    border-color:#ff6900;
}

.contact-btn.primary {
    background:#ff6900;
    border-color:#ff6900;
}

.contact-disabled {
    margin-top:18px;
    padding:15px;
    border:1px solid #292929;
    color:#777;
    font-size:12px;
    background:#101010;
}

.admin-product {
    padding:18px;
    border:1px solid #252525;
    margin-bottom:12px;
    background:#0d0d0d;
}

.admin-product-name {
    color:#fff;
    font-size:16px;
    font-weight:900;
}

.admin-product-meta {
    color:#777;
    font-size:11px;
    margin-top:5px;
}

.footer-block {
    border-top:1px solid #252525;
    margin-top:65px;
    padding:40px 0 15px;
    text-align:center;
    color:#555;
    font-size:10px;
    line-height:1.9;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {
    background:#111 !important;
    color:#eee !important;
    border:1px solid #333 !important;
    border-radius:0 !important;
}

div[data-testid="stSelectbox"] > div > div {
    background:#111 !important;
    border-color:#333 !important;
    border-radius:0 !important;
}

.stButton > button {
    border-radius:0 !important;
    background:#ff6900 !important;
    color:#fff !important;
    border:0 !important;
    font-weight:900 !important;
}

a:focus-visible,
summary:focus-visible {
    outline:2px solid #ff6900;
    outline-offset:3px;
}

@media(max-width:1100px) {
    .catalog-layout {
        grid-template-columns:150px minmax(0,1fr);
        gap:16px;
    }

    .grid {
        grid-template-columns:repeat(3,minmax(0,1fr));
    }
}

@media(max-width:600px) {
    .block-container {
        padding-left:14px !important;
        padding-right:14px !important;
    }

    .header {
        grid-template-columns:1fr 1fr;
        gap:12px;
        padding:16px 0;
    }

    .header-center {
        grid-column:1;
        text-align:left;
    }

    .header-right {
        grid-column:2;
        display:block;
    }

    .logo {
        font-size:30px;
    }

    .navbar {
        justify-content:flex-start;
        gap:24px;
    }

    .catalog-layout {
        grid-template-columns:1fr;
    }

    .catalog-sidebar:not([open]) > :not(summary) {
        display:none;
    }

    .grid {
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:20px 10px;
    }
}

@media(min-width:601px) {
    .catalog-sidebar:not([open]) > :not(summary) {
        display:block;
    }
}



</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# 관리자 버튼은 우측 상단
# =========================================================

safe_markdown("""
<div class="header">

    <div class="header-center">
        <a href="?page=home">
            <div
                class="logo"
                translate="no"
                aria-label="TWO J ROAD"
            ></div>
            <div class="logo-small">
                MOTORCYCLE CULTURE
            </div>
        </a>
    </div>

    <div class="header-right">
        <a
            class="admin-link"
            href="?page=admin"
        >
            관리자
        </a>
    </div>

</div>

<div class="navbar">
    <a href="?page=shop&cat=중고 바이크">
        중고 바이크
    </a>
    <a href="?page=shop&cat=바이크 의류">
        바이크 의류
    </a>
    <a href="?page=shop&cat=바이크 용품">
        바이크 용품
    </a>
    <a href="?page=store" target="_self">
        오프라인매장
    </a>
</div>
""", unsafe_allow_html=True)


# =========================================================
# PRODUCT CARD
# =========================================================

def card_html(product):
    if product.get("type") == "bike":
        info = (
            f"{escape(str(product.get('year','')))} · "
            f"{escape(str(product.get('mileage','')))} · "
            f"{escape(str(product.get('cc','')))}"
        )
    else:
        info = escape(
            str(product.get("subcategory", ""))
        )

    badge_text = str(product.get("badge") or "")
    badge_html = (
        '<div class="badge" translate="no">' + escape(badge_text) + '</div>'
        if badge_text.strip() else ""
    )
    demo_badge = ""

    if product.get("demo"):
        demo_badge = '<div class="demo">DEMO</div>'

    image = escape(
        main_image_src(product),
        quote=True
    )

    return dedent(f"""
    <a href="{escape(detail_href(product.get('id','')), quote=True)}" target="_self">
        <div class="card">

            <div class="card-imgbox">
                <img
                    class="card-img"
                    loading="lazy"
                    alt="{escape(str(product.get('name','상품')), quote=True)}"
                    src="{image}"
                >

                {badge_html}

                {demo_badge}
            </div>

            <div class="card-body">

                <div class="card-brand">
                    {escape(str(product.get('brand','')))}
                </div>

                <div class="card-name">
                    {escape(str(product.get('name','')))}
                </div>

                <div class="card-info">
                    {info}
                </div>

                <div class="card-price">
                    {money(product.get('price',0))}
                </div>

            </div>

        </div>
    </a>
    """).strip()


def render_grid(products):
    if not products:
        st.info("등록된 상품이 없습니다.")
        return

    html = '<div class="grid">'

    for product in products:
        html += card_html(product)

    html += "</div>"

    safe_markdown(
        html,
        unsafe_allow_html=True
    )


# =========================================================
# HOME
# =========================================================

def render_home():
    banner = banner_image_src()

    safe_markdown(
        f"""
        <div class="hero">
            <img
                src="{escape(banner, quote=True)}"
                alt="포천 TWO J ROAD 매장 전경"
            >
        </div>
        """,
        unsafe_allow_html=True
    )

    safe_markdown("""
    <style>
    .home-products{margin:28px 0 36px;min-width:0;}
    .home-products h2{font-size:20px;margin:0 0 14px;color:#fff;}
    .home-slider{display:flex;gap:12px;overflow-x:auto;overflow-y:hidden;
        scroll-snap-type:x mandatory;scroll-behavior:smooth;
        padding:0 0 14px;scrollbar-color:#ff7900 #222;scrollbar-width:auto;}
    .home-slider>a{flex:0 0 calc((100% - 48px)/5);min-width:0;
        scroll-snap-align:start;color:inherit;}
    .home-slider:focus-visible{outline:2px solid #ff7900;outline-offset:4px;}
    .home-slider::-webkit-scrollbar{height:10px;}
    .home-slider::-webkit-scrollbar-track{background:#222;border-radius:8px;}
    .home-slider::-webkit-scrollbar-thumb{background:#ff7900;border-radius:8px;}
    @media(max-width:768px){
        .home-slider>a{flex-basis:calc((100% - 12px)/2);}
    }
    @media(prefers-reduced-motion:reduce){.home-slider{scroll-behavior:auto;}}
    </style>
    """, unsafe_allow_html=True)

    def home_category_link(label, category, sub=None):
        params = {"page": "shop", "cat": category}
        if sub:
            params["sub"] = sub
        url = escape("?" + urlencode(params), quote=True)
        return f'<a href="{url}" target="_self">{escape(label)}</a>'

    sidebar = '<details class="catalog-sidebar" open><summary>카테고리</summary><nav aria-label="상품 분류">'
    sidebar += home_category_link("전체상품", "전체상품")
    sidebar += home_category_link("중고 바이크", "중고 바이크")
    for label, children in [("바이크 의류", ["상의", "하의", "자켓", "장갑", "신발"]),
                            ("바이크 용품", ["헬멧"])]:
        sidebar += f'<details class="category-node"><summary>{label}</summary><div class="category-children">'
        sidebar += ''.join(home_category_link(child, label, child) for child in children)
        sidebar += '</div></details>'
    sidebar += '</nav></details>'
    sections = []

    for category, type_code in [
        ("중고 바이크", "bike"),
        ("바이크 의류", "wear"),
        ("바이크 용품", "gear"),
    ]:
        items = [p for p in reversed(PRODUCTS)
                 if p.get("category") == category
                 or (not p.get("category") and p.get("type") == type_code)]
        if items:
            content = (
                f'<div class="home-slider" tabindex="0" role="region" '
                f'aria-label="{category} 상품, 좌우로 넘겨보기">'
                + ''.join(card_html(p) for p in items) + '</div>'
            )
        else:
            content = '<p style="color:#aaa;">등록된 상품이 없습니다.</p>'
        sections.append(
            f'<section class="home-products"><h2>{category}</h2>'
            + content + '</section>'
        )
    safe_markdown(
        '<div class="catalog-layout">' + sidebar
        + '<div class="catalog-results">' + ''.join(sections) + '</div></div>',
        unsafe_allow_html=True
    )



# =========================================================
# SHOP
# =========================================================

def render_shop():
    category = get_param("cat", "전체상품")
    subcategory = get_param("sub", "")

    if category == "전체상품":
        items = PRODUCTS.copy()
    else:
        items = [
            p for p in PRODUCTS
            if p.get("category") == category
        ]

    # 사용자 요청:
    # 전체상품 제목 / HOME › SHOP / 설명문 전부 제거

    c1, c2 = st.columns([3, 1])

    with c1:
        keyword = st.text_input(
            "검색",
            placeholder="상품명 또는 브랜드 검색",
            label_visibility="collapsed",
        )

    with c2:
        sort = st.selectbox(
            "정렬",
            [
                "등록순",
                "낮은 가격순",
                "높은 가격순"
            ],
            label_visibility="collapsed",
        )

    if subcategory:
        sub_filters = {
            "상의": {
                "상의",
                "티셔츠",
                "셔츠",
                "후드",
                "맨투맨",
            },
            "하의": {
                "하의",
                "바지",
                "팬츠",
                "청바지",
            },
            "자켓": {
                "자켓",
                "재킷",
                "라이딩 재킷",
            },
            "장갑": {
                "장갑",
                "글러브",
            },
            "신발": {
                "신발",
                "부츠",
                "라이딩 부츠",
            },
            "헬멧": {
                "헬멧",
            },
        }

        allowed = sub_filters.get(
            subcategory,
            {subcategory}
        )

        items = [
            p for p in items
            if p.get("subcategory") in allowed
        ]

    if keyword:
        k = keyword.lower().strip()

        items = [
            p for p in items
            if (
                k in str(p.get("name", "")).lower()
                or
                k in str(p.get("brand", "")).lower()
                or
                k in str(p.get("subcategory", "")).lower()
            )
        ]

    if sort == "낮은 가격순":
        items.sort(
            key=lambda x: int(x.get("price", 0))
        )

    elif sort == "높은 가격순":
        items.sort(
            key=lambda x: int(x.get("price", 0)),
            reverse=True
        )

    else:
        items = list(reversed(items))

    st.caption(
        f"총 {len(items)}개의 상품"
    )

    def filter_link(label, **params):
        url = "?" + urlencode(
            {
                "page": "shop",
                **params
            }
        )

        active = (
            params.get("cat") == category
            and
            params.get("sub", "") == subcategory
        )

        active_class = (
            "active"
            if active
            else ""
        )

        return (
            f'<a class="{active_class}" '
            f'href="{escape(url, quote=True)}" target="_self">'
            f'{escape(str(label))}</a>'
        )

    is_wear = category == "바이크 의류"
    is_gear = category == "바이크 용품"

    sidebar = (
        f'<details class="catalog-sidebar" open>'
        f'<summary>카테고리</summary>'
        f'<nav aria-label="상품 분류">'
    )

    for cat in [
        "전체상품",
        "중고 바이크",
        "바이크 의류",
        "바이크 용품",
    ]:

        if cat == "바이크 의류":
            sidebar += (
                f'<details class="category-node" '
                f'{"open" if is_wear else ""}>'
                f'<summary>바이크 의류</summary>'
                f'<div class="category-children">'
            )

            for sub in [
                "상의",
                "하의",
                "자켓",
                "장갑",
                "신발",
            ]:
                sidebar += filter_link(
                    sub,
                    cat="바이크 의류",
                    sub=sub
                )

            sidebar += "</div></details>"

        elif cat == "바이크 용품":
            sidebar += (
                f'<details class="category-node" '
                f'{"open" if is_gear else ""}>'
                f'<summary>바이크 용품</summary>'
                f'<div class="category-children">'
            )

            sidebar += filter_link(
                "헬멧",
                cat="바이크 용품",
                sub="헬멧"
            )

            sidebar += "</div></details>"

        else:
            sidebar += filter_link(
                cat,
                cat=cat
            )

    sidebar += "</nav></details>"

    if items:
        results = (
            '<div class="grid">'
            + "".join(
                card_html(p)
                for p in items
            )
            + "</div>"
        )
    else:
        results = (
            '<p role="status">'
            '조건에 맞는 상품이 없습니다.'
            '</p>'
        )

    safe_markdown(
        '<div class="catalog-layout">'
        + sidebar
        + '<section class="catalog-results" aria-label="상품 목록">'
        + results
        + "</section></div>",
        unsafe_allow_html=True
    )


# =========================================================
# DETAIL
# =========================================================

DETAIL_PREFIX = "DOOJAY_DETAIL_V1:"


def unpack_detail(value):
    value = str(value or "")
    if value.startswith(DETAIL_PREFIX):
        try:
            data = json.loads(value[len(DETAIL_PREFIX):])
            if isinstance(data, dict) and isinstance(data.get("files"), list):
                return str(data.get("text", "")), data["files"]
        except (ValueError, TypeError):
            pass
    return value, []


def pack_detail(text, files, extras=None):
    extras = {k: v for k, v in (extras or {}).items() if str(v or "").strip()}
    if not files and not extras:
        return text
    data = {"text": text, "files": files or []}
    data.update(extras)
    return DETAIL_PREFIX + json.dumps(data, ensure_ascii=False)


def unpack_extras(value):
    """상품 설명에 함께 저장한 사이즈표(size_table)·세탁정보(care)."""
    value = str(value or "")
    if value.startswith(DETAIL_PREFIX):
        try:
            data = json.loads(value[len(DETAIL_PREFIX):])
            if isinstance(data, dict):
                return {k: str(data.get(k) or "") for k in EXTRA_KEYS}
        except (ValueError, TypeError):
            pass
    return {k: "" for k in EXTRA_KEYS}


EXTRA_KEYS = ("size_table", "size_table_m", "size_table_w", "care", "fabric")

FABRIC_ATTRS = [
    ("두께감", ["얇음", "보통", "두꺼움"]),
    ("비침", ["없음", "보통", "있음"]),
    ("신축성", ["없음", "보통", "좋음"]),
    ("안감", ["있음", "없음", "기모안감"]),
]


def parse_fabric(value):
    result = {}
    for part in str(value or "").split("|"):
        if ":" in part:
            key, val = part.split(":", 1)
            result[key.strip()] = val.strip()
    return result


def fabric_to_text(values):
    return "|".join(f"{k}:{v}" for k, v in values.items() if v)


def upload_detail_files(files, product_id):
    files = files or []
    if len(files) > 8:
        raise ValueError("상세 첨부파일은 최대 8개까지 등록할 수 있습니다.")
    for file in files:
        if Path(file.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
            raise ValueError("상세 첨부파일은 JPG, PNG, WEBP, PDF만 가능합니다.")
        if file.size > 20 * 1024 * 1024:
            raise ValueError("상세 첨부파일은 파일당 20MB 이하로 올려 주세요.")
    paths = save_uploaded_images(files, product_id + "-detail")
    return [{"name": file.name, "url": path,
             "kind": "pdf" if Path(file.name).suffix.lower() == ".pdf" else "image"}
            for file, path in zip(files, paths)]


def render_detail_files(files):
    for item in files:
        src = image_src(item.get("url", ""))
        if not src or not src.startswith(("https://", "http://", "data:image/", "data:application/pdf")):
            continue
        name = escape(str(item.get("name", "상세 첨부파일")))
        url = escape(src, quote=True)
        if item.get("kind") == "image":
            safe_markdown(f'<img src="{url}" alt="{name}" loading="lazy" '
                          'style="display:block;width:100%;height:auto;margin:12px 0;">',
                          unsafe_allow_html=True)
        else:
            safe_markdown(f'<p><a href="{url}" target="_blank" rel="noopener noreferrer">'
                          f'📎 {name} — PDF 열기</a></p>', unsafe_allow_html=True)


def render_detail():
    product_id = get_param("id", "")

    product = get_product(
        PRODUCTS,
        product_id
    )

    if not product:
        st.error("상품을 찾을 수 없습니다.")
        return

    safe_markdown(
        '<div class="page-title">PRODUCT DETAIL</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(
        [1.15, .85],
        gap="large"
    )

    with left:
        images = product_images(product)

        sources = [image_src(value) for value in images]
        sources = [src for src in sources if src]
        if sources:
            # Native radio controls switch photos without navigation or a rerun.
            gallery_id = "gallery-" + uuid.uuid4().hex
            controls, photos, thumbs, rules = [], [], [], []
            for index, src in enumerate(sources):
                photo_id = f"{gallery_id}-{index}"
                escaped_src = escape(src, quote=True)
                checked = " checked" if index == 0 else ""
                controls.append(
                    f'<input class="gallery-choice" type="radio" '
                    f'name="{gallery_id}" id="{photo_id}" '
                    f'aria-label="상품 사진 {index + 1}"{checked}>'
                )
                photos.append(
                    f'<img class="gallery-main photo-{index}" '
                    f'src="{escaped_src}" alt="상품 사진 {index + 1}">'
                )
                thumbs.append(
                    f'<label class="gallery-thumb thumb-{index}" '
                    f'for="{photo_id}" title="사진 {index + 1} 보기">'
                    f'<img src="{escaped_src}" alt="사진 {index + 1}"></label>'
                )
                rules.append(
                    f'#{photo_id}:checked ~ .gallery-stage .photo-{index}'
                    '{display:block;}'
                    f'#{photo_id}:checked ~ .gallery-thumbs .thumb-{index}'
                    '{border-color:#ff7900;}'
                    f'#{photo_id}:focus-visible ~ .gallery-thumbs .thumb-{index}'
                    '{outline:3px solid white;outline-offset:2px;}'
                )
            safe_markdown(
                '<style>'
                '.product-gallery{position:relative;width:100%;}'
                '.gallery-choice{position:absolute;width:1px;height:1px;'
                'opacity:0;overflow:hidden;}'
                '.gallery-stage{width:100%;aspect-ratio:1;background:#111;}'
                '.gallery-main{display:none;width:100%;height:100%;object-fit:contain;}'
                '.gallery-thumbs{display:flex;gap:8px;overflow-x:auto;padding:10px 3px;}'
                '.gallery-thumb{display:block;flex:0 0 72px;height:72px;cursor:pointer;'
                'border:2px solid #444;border-radius:3px;overflow:hidden;}'
                '.gallery-thumb img{width:100%;height:100%;object-fit:cover;}'
                + ''.join(rules) + '</style>'
                + '<div class="product-gallery" role="group" aria-label="상품 사진">'
                + ''.join(controls)
                + '<div class="gallery-stage">' + ''.join(photos) + '</div>'
                + ('<div class="gallery-thumbs">' + ''.join(thumbs) + '</div>'
                   if len(sources) > 1 else '')
                + '</div>',
                unsafe_allow_html=True
            )
        else:
            st.info(
                "등록된 상품 사진이 없습니다."
            )

    with right:
        safe_markdown(
            f"""
            <div class="detail-brand">
                {escape(str(product.get('brand','')))}
            </div>

            <div class="detail-name">
                {escape(str(product.get('name','')))}
            </div>

            <div class="detail-price">
                {money(product.get('price',0))}
            </div>
            """,
            unsafe_allow_html=True
        )

        if product.get("type") == "bike":
            specs = [
                ("상태", product.get("condition", "")),
                ("연식", product.get("year", "")),
                ("주행거리", product.get("mileage", "")),
                ("배기량", product.get("cc", "")),
                ("지역", product.get("region", "")),
                ("사고유무", product.get("accident", "")),
            ]
        else:
            specs = [
                ("상품구분", product.get("category", "")),
                ("종류", product.get("subcategory", "")),
                ("브랜드", product.get("brand", "")),
                ("상태", product.get("condition", "")),
            ]

        html = ""

        for label, value in specs:
            html += f"""
            <div class="spec-row">
                <div class="spec-label">
                    {escape(str(label))}
                </div>
                <div class="spec-value">
                    {escape(str(value))}
                </div>
            </div>
            """

        safe_markdown(
            html,
            unsafe_allow_html=True
        )

        st.write("")
        detail_text, detail_files = unpack_detail(product.get("description", ""))
        st.write(detail_text)
        render_detail_files(detail_files)

        contact_buttons = ""

        if MASPICK_PHONE:
            tel_number = "".join(
                c for c in MASPICK_PHONE
                if c.isdigit() or c == "+"
            )

            contact_buttons += f"""
            <a
                class="contact-btn primary"
                href="tel:{escape(tel_number, quote=True)}"
            >
                ☎ 전화 문의
            </a>
            """

        if MASPICK_KAKAO_URL:
            contact_buttons += f"""
            <a
                class="contact-btn"
                href="{escape(MASPICK_KAKAO_URL, quote=True)}"
                target="_blank"
                rel="noopener noreferrer"
            >
                카카오톡 문의
            </a>
            """

        if contact_buttons:
            safe_markdown(
                f"""
                <div class="contact-actions">
                    {contact_buttons}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            safe_markdown(
                """
                <div class="contact-disabled">
                    관리자에게 문의 연락처가 아직 설정되지 않았습니다.
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# PRODUCT POPUP (상품 팝업 · 옵션 · 장바구니 · 찜 · 문의 · 후기)
# =========================================================

def _shop_features():
    try:
        import shop_features
        return shop_features
    except Exception as exc:
        print("[SHOP] features unavailable: " + type(exc).__name__ + ": " + str(exc)[:200], flush=True)
        return None


def detail_href(product_id):
    params = {}
    for key in ("page", "cat", "sub", "q", "sort", "brand"):
        value = get_param(key, "")
        if value:
            params[key] = value
    if params.get("page") in ("detail", "admin"):
        params = {"page": "home"}
    params["detail"] = str(product_id)
    return "?" + urlencode(params)


def close_popup_href():
    params = {}
    for key in ("page", "cat", "sub", "q", "sort", "brand"):
        value = get_param(key, "")
        if value:
            params[key] = value
    if params.get("page") == "detail":
        params = {}
    return "?" + urlencode(params) if params else "?page=home"


def _close_popup():
    try:
        for key in ("detail", "id"):
            if key in st.query_params:
                del st.query_params[key]
        if st.query_params.get("page") == "detail":
            st.query_params["page"] = "home"
    except Exception:
        pass


def _visitor_id():
    try:
        value = str(st.context.cookies.get("twoj_vid", "") or "")
        if 8 <= len(value) <= 64 and value.isalnum():
            return value
    except Exception:
        pass
    return ""


def _gallery_html(sources, name):
    gallery_id = "pg-" + uuid.uuid4().hex[:10]
    total = len(sources)
    controls, photos, thumbs, rules = [], [], [], []
    for index, src in enumerate(sources):
        photo_id = f"{gallery_id}-{index}"
        esc_src = escape(src, quote=True)
        checked = " checked" if index == 0 else ""
        controls.append(
            f'<input class="pg-choice" type="radio" name="{gallery_id}" id="{photo_id}" '
            f'aria-label="상품 사진 {index + 1}"{checked}>'
        )
        nav = ""
        if total > 1:
            prev_id = f"{gallery_id}-{(index - 1) % total}"
            next_id = f"{gallery_id}-{(index + 1) % total}"
            nav = (
                f'<label class="pg-nav pg-prev" for="{prev_id}" role="button" aria-label="이전 사진">&#8249;</label>'
                f'<label class="pg-nav pg-next" for="{next_id}" role="button" aria-label="다음 사진">&#8250;</label>'
            )
        photos.append(
            f'<div class="pg-slide s-{index}"><img src="{esc_src}" '
            f'alt="{escape(name, quote=True)} 사진 {index + 1}">{nav}'
            f'<span class="pg-count">{index + 1} / {total}</span></div>'
        )
        thumbs.append(
            f'<label class="pg-thumb t-{index}" for="{photo_id}" title="사진 {index + 1}">'
            f'<img src="{esc_src}" alt=""></label>'
        )
        rules.append(
            f'#{photo_id}:checked ~ .pg-stage .s-{index}{{display:block;}}'
            f'#{photo_id}:checked ~ .pg-thumbs .t-{index}{{border-color:#ff7900;}}'
        )
    return (
        "<style>"
        ".pg{position:relative}.pg-choice{position:absolute;opacity:0;width:1px;height:1px}"
        ".pg-stage{position:relative;width:100%;aspect-ratio:1;background:#111;border-radius:6px;overflow:hidden}"
        ".pg-slide{display:none;width:100%;height:100%;position:relative}"
        ".pg-slide img{width:100%;height:100%;object-fit:contain}"
        ".pg-count{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.65);color:#fff;"
        "font-size:12px;padding:3px 9px;border-radius:12px}"
        ".pg-nav{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;"
        "border-radius:50%;background:rgba(0,0,0,.55);color:#fff;font-size:30px;line-height:40px;"
        "text-align:center;cursor:pointer;user-select:none;-webkit-user-select:none;z-index:2;"
        "-webkit-tap-highlight-color:transparent}"
        ".pg-nav:hover{background:rgba(255,105,0,.9)}"
        ".pg-prev{left:8px}.pg-next{right:8px}"
        ".pg-thumbs{display:flex;gap:6px;overflow-x:auto;padding:8px 2px}"
        ".pg-thumb{flex:0 0 58px;height:58px;border:2px solid #333;border-radius:4px;overflow:hidden;cursor:pointer}"
        ".pg-thumb img{width:100%;height:100%;object-fit:cover}"
        + "".join(rules) + "</style>"
        + '<div class="pg" role="group" aria-label="상품 사진">' + "".join(controls)
        + '<div class="pg-stage">' + "".join(photos) + "</div>"
        + ('<div class="pg-thumbs">' + "".join(thumbs) + "</div>" if total > 1 else "")
        + "</div>"
    )


def _related_html(product):
    related = [
        p for p in PRODUCTS
        if p.get("id") != product.get("id")
        and not p.get("demo")
        and p.get("category") == product.get("category")
    ][:12]
    if not related:
        return ""
    cards = []
    for p in related:
        cards.append(
            f'<a class="rel-card" href="{escape(detail_href(p.get("id", "")), quote=True)}" target="_self">'
            f'<img src="{escape(main_image_src(p), quote=True)}" alt="" loading="lazy">'
            f'<span class="rel-name">{escape(str(p.get("name", "")))}</span>'
            f'<span class="rel-price">{money(p.get("price", 0))}</span></a>'
        )
    return (
        "<style>.rel h4{margin:18px 0 8px;font-size:15px}"
        ".rel-row{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px;scroll-snap-type:x mandatory}"
        ".rel-card{flex:0 0 31%;min-width:110px;color:inherit!important;text-decoration:none;scroll-snap-align:start}"
        ".rel-card img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:4px;background:#1a1a1a}"
        ".rel-name{display:block;font-size:12px;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
        ".rel-price{display:block;font-size:12px;font-weight:700}</style>"
        '<div class="rel"><h4>연관 추천 상품</h4><div class="rel-row">' + "".join(cards) + "</div></div>"
    )


def _spec_table_html(rows):
    body = "".join(
        f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>"
        for k, v in rows if str(v or "").strip()
    )
    return (
        "<style>.pp-spec{width:100%;border-collapse:collapse;font-size:13px}"
        ".pp-spec th{width:34%;text-align:left;color:#999;font-weight:400;padding:6px 0;vertical-align:top}"
        ".pp-spec td{padding:6px 0}</style>"
        f'<table class="pp-spec">{body}</table>'
    )


def _size_table_html(header, rows):
    head = "".join(f"<th>{escape(c)}</th>" for c in header)
    body = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in r) + "</tr>" for r in rows)
    return (
        "<style>.pp-size{width:100%;border-collapse:collapse;font-size:13px;text-align:center}"
        ".pp-size th{background:rgba(128,128,128,.18);color:inherit;padding:7px 4px;font-weight:700}"
        ".pp-size td{border-bottom:1px solid rgba(128,128,128,.3);color:inherit;padding:7px 4px}</style>"
        f'<div style="overflow-x:auto"><table class="pp-size"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def _fabric_table_html(values):
    rows = []
    for attr, choices in FABRIC_ATTRS:
        current = values.get(attr, "")
        cells = "".join(
            f'<td class="{"on" if c == current else ""}">{escape(c)}</td>' for c in choices
        )
        rows.append(f"<tr><th>{escape(attr)}</th>{cells}</tr>")
    return (
        "<style>.pp-fabric{width:100%;border-collapse:collapse;font-size:14px;"
        "border-top:1px solid rgba(128,128,128,.6);color:inherit}"
        ".pp-fabric th{text-align:left;padding:14px 8px;width:28%;font-weight:700;color:inherit}"
        ".pp-fabric td{padding:14px 8px;color:inherit;opacity:.38}"
        ".pp-fabric td.on{opacity:1;font-weight:800;color:#ff6900}"
        ".pp-fabric tr{border-bottom:1px solid rgba(128,128,128,.25)}</style>"
        f'<table class="pp-fabric">{"".join(rows)}</table>'
    )


def _stars(value):
    value = max(0, min(5, int(round(float(value or 0)))))
    return "★" * value + "☆" * (5 - value)


def _rate_limited(key, limit=5, window=600):
    now = time.time()
    stamps = [t for t in st.session_state.get(key, []) if now - t < window]
    if len(stamps) >= limit:
        st.session_state[key] = stamps
        return True
    stamps.append(now)
    st.session_state[key] = stamps
    return False


def _render_purchase_box(product, features):
    pid = str(product.get("id", ""))
    price = int(product.get("price", 0) or 0)
    status = str(product.get("condition", ""))
    payment_on = globals().get("PAYMENT_ENABLED", True)
    can_buy = payment_on and status == "판매중" and price > 0 and not product.get("demo")
    if not can_buy:
        if status and status != "판매중":
            st.warning(f"현재 {status} 상품입니다.")
        elif not payment_on:
            st.info("현재 온라인 결제를 사용할 수 없습니다. 매장으로 문의해 주세요.")
        return

    options = features.get_options(pid) if features else []
    is_bike = product.get("type") == "bike"
    picked = []

    if options:
        st.markdown("**사이즈 · 옵션 선택**")
        names = [str(o.get("name")) for o in options]
        by_name = {str(o.get("name")): o for o in options}

        def _option_label(name):
            opt = by_name[name]
            extra = int(opt.get("extra_price") or 0)
            stock = opt.get("stock")
            label = name
            if extra:
                label += f" (+{extra:,}원)"
            if stock is not None and int(stock) <= 0:
                label += " · 품절"
            return label

        chosen = st.pills(
            "옵션", names, selection_mode="single", format_func=_option_label,
            key=f"pp_opt_{pid}", label_visibility="collapsed",
        )
        if chosen:
            opt = by_name[chosen]
            stock = opt.get("stock")
            extra = int(opt.get("extra_price") or 0)
            if stock is not None and int(stock) <= 0:
                st.warning("품절된 옵션입니다. 다른 옵션을 선택해 주세요.")
            else:
                max_qty = min(20, int(stock)) if stock is not None else 20
                c1, c2 = st.columns([3, 2], vertical_alignment="center")
                c1.markdown(f"**{escape(chosen)}**  \n<span style='color:#999;font-size:12px'>"
                            f"{money(price + extra)}"
                            f"{' · 재고 ' + str(int(stock)) if stock is not None else ''}</span>",
                            unsafe_allow_html=True)
                qty = c2.number_input("수량", min_value=1, max_value=max_qty, value=1, step=1,
                                      key=f"pp_qty_{pid}_{chosen}", label_visibility="collapsed")
                picked.append({"o": chosen, "q": int(qty), "unit": price + extra})
    else:
        st.markdown("**수량**")
        qty = 1
        if not is_bike:
            qty = st.number_input("수량", min_value=1, max_value=20, value=1, step=1,
                                  key=f"pp_qty_{pid}", label_visibility="collapsed")
        else:
            st.caption("중고 바이크는 1대씩 구매할 수 있습니다.")
        picked.append({"o": "", "q": int(qty), "unit": price})

    total = sum(p["unit"] * p["q"] for p in picked)
    safe_markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'border-top:1px solid #333;margin-top:10px;padding-top:12px">'
        f'<span>총 금액 <span style="color:#999;font-size:12px">(VAT 포함)</span></span>'
        f'<b style="font-size:22px">{money(total)}</b></div>',
        unsafe_allow_html=True,
    )
    if not picked:
        st.caption("사이즈·옵션을 선택하면 장바구니·구매 버튼이 활성화됩니다.")
        safe_markdown(
            '<div class="contact-actions"><span class="contact-btn" style="opacity:.45">장바구니</span>'
            '<span class="contact-btn primary" style="opacity:.45">구매하기</span></div>',
            unsafe_allow_html=True,
        )
        return
    items = json.dumps([{"o": p["o"], "q": p["q"]} for p in picked], ensure_ascii=False)
    base = {"product": pid, "items": items}
    cart_url = "/cart/add?" + urlencode(dict(base, next="cart"))
    buy_url = "/cart/add?" + urlencode(dict(base, next="buy"))
    label = "테스트 구매하기" if globals().get("PAYMENT_TEST_MODE", True) else "구매하기"
    safe_markdown(
        f'<div class="contact-actions">'
        f'<a class="contact-btn" href="{escape(cart_url, quote=True)}" target="_self">장바구니 담기</a>'
        f'<a class="contact-btn primary" href="{escape(buy_url, quote=True)}" target="_self">{label}</a>'
        f'</div><div style="text-align:right;margin-top:6px">'
        f'<a href="/cart" target="_self" style="font-size:13px">장바구니 보기 →</a></div>',
        unsafe_allow_html=True,
    )
    if globals().get("PAYMENT_TEST_MODE", True):
        st.caption("현재 TEST 결제 모드 · 실제 금액은 청구되지 않습니다.")


def _render_reviews(product, features):
    pid = str(product.get("id", ""))
    try:
        reviews = features.list_reviews(pid)
    except Exception:
        st.caption("후기를 불러오지 못했습니다.")
        return
    avg, count = features.review_summary(reviews)
    if count:
        st.markdown(f"**{_stars(avg)} {avg}** · 후기 {count}개")
    else:
        st.caption("아직 작성된 후기가 없습니다.")
    for review in reviews:
        option = f" · {review.get('option_name')}" if review.get("option_name") else ""
        safe_markdown(
            f'<div style="border-bottom:1px solid #262626;padding:10px 0">'
            f'<div style="color:#ffb400">{_stars(review.get("rating"))}</div>'
            f'<div style="color:#999;font-size:12px">{escape(str(review.get("author", "")))}'
            f'{escape(option)} · {escape(str(review.get("created_at", ""))[:10])}</div>'
            f'<div style="white-space:pre-wrap;margin-top:4px">{escape(str(review.get("content", "")))}</div></div>',
            unsafe_allow_html=True,
        )
    with st.form(f"pp_review_{pid}", clear_on_submit=True):
        st.caption("구매하신 분만 작성할 수 있어요. 결제 완료 화면의 주문번호와 주문 시 휴대폰 번호를 입력해 주세요.")
        c1, c2 = st.columns(2)
        order_id = c1.text_input("주문번호", placeholder="TJR_...")
        phone = c2.text_input("휴대폰 번호", placeholder="01012345678")
        rating = st.select_slider("별점", options=[1, 2, 3, 4, 5], value=5)
        content = st.text_area("후기 내용", max_chars=1000, height=90)
        if st.form_submit_button("후기 등록"):
            if _rate_limited("pp_review_rate"):
                st.error("잠시 후 다시 시도해 주세요.")
            else:
                try:
                    features.add_review(pid, order_id, phone, rating, content)
                    st.success("후기가 등록되었습니다.")
                    st.rerun(scope="fragment")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("후기 저장 중 오류가 발생했습니다.")


def _render_qna(product, features):
    pid = str(product.get("id", ""))
    try:
        questions = features.list_qna(pid)
    except Exception:
        st.caption("상품 문의를 불러오지 못했습니다.")
        return
    if not questions:
        st.caption("아직 등록된 문의가 없습니다.")
    for q in questions:
        state = "답변완료" if q.get("answer") else "답변대기"
        head = (f"{'🔒 ' if q.get('is_secret') else ''}{state} · {q.get('author', '')} · "
                f"{str(q.get('created_at', ''))[:10]}")
        with st.expander(head):
            if q.get("is_secret"):
                pw = st.text_input("비밀번호", type="password", key=f"pp_qpw_{q.get('id')}")
                if st.button("비밀글 보기", key=f"pp_qbtn_{q.get('id')}"):
                    try:
                        row = features.read_secret_qna(q.get("id"), pw)
                        st.text(row.get("question", ""))
                        if row.get("answer"):
                            st.info("답변: " + str(row.get("answer")))
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                st.text(q.get("question", ""))
                if q.get("answer"):
                    st.info("답변: " + str(q.get("answer")))
    with st.form(f"pp_qna_{pid}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        author = c1.text_input("작성자", max_chars=20)
        password = c2.text_input("비밀번호 (4자 이상)", type="password", max_chars=30)
        question = st.text_area("문의 내용", max_chars=1000, height=90)
        secret = st.checkbox("비밀글로 문의하기")
        st.caption("연락처 등 개인정보는 비밀글로 남겨 주세요.")
        if st.form_submit_button("문의 등록"):
            if _rate_limited("pp_qna_rate"):
                st.error("잠시 후 다시 시도해 주세요.")
            else:
                try:
                    features.add_qna(pid, author, password, question, secret)
                    st.success("문의가 등록되었습니다. 답변은 이 화면에서 확인할 수 있어요.")
                    st.rerun(scope="fragment")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("문의 저장 중 오류가 발생했습니다.")


def _product_popup_body(product_id):
    product = get_product(PRODUCTS, product_id)
    if not product:
        st.error("상품을 찾을 수 없습니다.")
        return
    features = _shop_features()
    pid = str(product.get("id", ""))
    name = str(product.get("name", ""))
    detail_text, detail_files = unpack_detail(product.get("description", ""))
    extras = unpack_extras(product.get("description", ""))

    safe_markdown(
        f'<div style="font-size:12px;color:#999">{escape(str(product.get("category", "")))}'
        f'{" › " + escape(str(product.get("subcategory", ""))) if product.get("subcategory") else ""}</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([1, 1], gap="large")

    with left:
        sources = [s for s in (image_src(v) for v in product_images(product)) if s]
        if sources:
            safe_markdown(_gallery_html(sources, name), unsafe_allow_html=True)
        else:
            st.info("등록된 상품 사진이 없습니다.")
        related = _related_html(product)
        if related:
            safe_markdown(related, unsafe_allow_html=True)

    with right:
        safe_markdown(
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
            '<div style="width:38px;height:38px;border-radius:50%;background:#ff6900;color:#fff;'
            'display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12px">TJR</div>'
            '<div><div style="font-weight:700">TWO J ROAD</div>'
            f'<div style="font-size:12px;color:#999">{escape(STORE_NAME)} · 오프라인 매장</div></div></div>'
            f'<div style="color:#aaa;font-size:13px">{escape(str(product.get("brand", "")))}</div>'
            f'<div style="font-size:20px;font-weight:800;line-height:1.35">{escape(name)}</div>',
            unsafe_allow_html=True,
        )
        pc, lc = st.columns([3, 1], vertical_alignment="center")
        pc.markdown(f"<div style='font-size:26px;font-weight:900'>{money(product.get('price', 0))}</div>",
                    unsafe_allow_html=True)
        if features:
            visitor = _visitor_id()
            liked = features.is_liked(pid, visitor)
            count = features.like_count(pid)
            if lc.button(("♥" if liked else "♡") + f" {count}", key=f"pp_like_{pid}",
                         help="찜하기", use_container_width=True):
                try:
                    features.toggle_like(pid, visitor)
                    st.rerun(scope="fragment")
                except ValueError as exc:
                    st.warning(str(exc))
                except Exception:
                    st.warning("찜 저장 중 오류가 발생했습니다.")

        if product.get("type") == "bike":
            specs = [("판매상태", product.get("condition")), ("연식", product.get("year")),
                     ("주행거리", product.get("mileage")), ("배기량", product.get("cc")),
                     ("지역", product.get("region")), ("사고유무", product.get("accident"))]
        else:
            specs = [("판매상태", product.get("condition")), ("브랜드", product.get("brand")),
                     ("상품구분", product.get("category")), ("종류", product.get("subcategory")),
                     ("배송", "택배 · 매장 픽업 문의")]
        with st.expander("상세정보", expanded=True):
            safe_markdown(_spec_table_html(specs), unsafe_allow_html=True)

        size_tables = []
        if features:
            for label, key in (("남성", "size_table_m"), ("여성", "size_table_w"), ("공용", "size_table")):
                if extras.get(key):
                    header, rows = features.parse_size_table(extras.get(key))
                    if header:
                        size_tables.append((label, header, rows))
        fabric = parse_fabric(extras.get("fabric"))
        if size_tables or extras.get("care") or fabric:
            with st.expander("사이즈 및 세탁 주의사항", expanded=True):
                if size_tables:
                    st.markdown("**사이즈 정보** (단위: cm)")
                    chosen = size_tables[0]
                    if len(size_tables) > 1:
                        labels = [t[0] for t in size_tables]
                        picked_label = st.segmented_control(
                            "사이즈표 구분", labels, default=labels[0],
                            key=f"pp_size_gender_{pid}", label_visibility="collapsed",
                        ) or labels[0]
                        chosen = next(t for t in size_tables if t[0] == picked_label)
                    elif chosen[0] != "공용":
                        st.caption(chosen[0] + " 사이즈")
                    safe_markdown(_size_table_html(chosen[1], chosen[2]), unsafe_allow_html=True)
                if fabric:
                    st.markdown("**소재 정보**")
                    safe_markdown(_fabric_table_html(fabric), unsafe_allow_html=True)
                if extras.get("care"):
                    st.markdown("**세탁 정보**")
                    st.text(extras.get("care"))

        with st.expander("제품 설명", expanded=True):
            if detail_text:
                st.text(detail_text)
            render_detail_files(detail_files)

        if product.get("type") == "bike":
            st.info("중고 바이크는 온라인 결제 없이 매장 방문·전화 상담 후 거래합니다. 아래 버튼으로 문의해 주세요.")
        elif features:
            with st.container(border=True):
                _render_purchase_box(product, features)

        if MASPICK_PHONE or MASPICK_KAKAO_URL:
            links = ""
            if MASPICK_PHONE:
                tel = "".join(c for c in MASPICK_PHONE if c.isdigit() or c == "+")
                links += f'<a class="contact-btn" href="tel:{escape(tel, quote=True)}">☎ 전화 문의</a>'
            if MASPICK_KAKAO_URL:
                links += (f'<a class="contact-btn" href="{escape(MASPICK_KAKAO_URL, quote=True)}" '
                          'target="_blank" rel="noopener noreferrer">카카오톡 문의</a>')
            safe_markdown(f'<div class="contact-actions">{links}</div>', unsafe_allow_html=True)

        if features:
            try:
                review_count = len(features.list_reviews(pid))
            except Exception:
                review_count = 0
            with st.expander(f"상품 후기 ({review_count})"):
                _render_reviews(product, features)
            with st.expander("상품 문의"):
                _render_qna(product, features)


POPUP_HOOK_JS = r"""
(function () {
  var P = window.parent;
  if (!P || P.__tjrPopupHook) return;
  var code = "(" + function () {
    if (window.__tjrPopupHook) return;
    window.__tjrPopupHook = true;
    document.addEventListener("click", function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a) return;
      var url;
      try { url = new URL(a.getAttribute("href"), location.href); } catch (err) { return; }
      if (url.origin !== location.origin || url.pathname !== location.pathname) return;
      var pid = url.searchParams.get("detail");
      if (!pid || !/^[A-Za-z0-9_-]{1,64}$/.test(pid)) return;
      var btn = document.querySelector(".st-key-tjr_open_" + pid + " button");
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      btn.click();
    }, true);
  } + ")();";
  var s = P.document.createElement("script");
  s.textContent = code;
  P.document.head.appendChild(s);
})();
"""


def _open_popup(product_id):
    try:
        if "id" in st.query_params:
            del st.query_params["id"]
        if st.query_params.get("page") == "detail":
            st.query_params["page"] = "home"
        st.query_params["detail"] = str(product_id)
    except Exception:
        pass


def render_popup_triggers():
    """상품 카드를 눌렀을 때 페이지를 새로 불러오지 않고 팝업을 여는 숨은 버튼과 연결 스크립트.

    스크립트가 동작하지 않는 환경에서는 카드 링크가 원래대로 페이지 이동으로 동작합니다.
    """
    safe_markdown(
        "<style>.st-key-tjr_popup_hook{display:none!important}</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="tjr_popup_hook"):
        for product in PRODUCTS:
            pid = str(product.get("id", ""))
            if not pid or not all(c.isalnum() or c in "_-" for c in pid) or len(pid) > 64:
                continue
            st.button(
                "open " + pid, key=f"tjr_open_{pid}",
                on_click=_open_popup, args=(pid,),
            )
        try:
            import streamlit.components.v1 as components
            components.html("<script>" + POPUP_HOOK_JS + "</script>", height=0)
        except Exception:
            pass


def render_product_popup(product_id):
    import inspect
    product = get_product(PRODUCTS, product_id)
    title = str(product.get("name", "상품 상세"))[:40] if product else "상품 상세"
    try:
        params = inspect.signature(st.dialog).parameters
    except (TypeError, ValueError):
        params = {}
    kwargs = {"width": "large"}
    if "on_dismiss" in params:
        kwargs["on_dismiss"] = _close_popup
    dialog = st.dialog(title, **kwargs)(_product_popup_body)
    dialog(product_id)
    if "on_dismiss" not in params:
        safe_markdown(
            f'<a href="{escape(close_popup_href(), quote=True)}" target="_self">✕ 상품 창 닫기</a>',
            unsafe_allow_html=True,
        )


OPTION_HELP = (
    "한 줄에 옵션 하나: 옵션명, 재고, 추가금액\n"
    "예) S, 3, 0\n    M, 5, 0\n    XL, , 2000   ← 재고를 비우면 수량 제한 없음\n"
    "옵션을 하나라도 넣으면 고객은 옵션을 골라야 구매할 수 있습니다."
)
SIZE_HELP = (
    "첫 줄은 제목, 칸은 쉼표로 구분 (단위 cm)\n"
    "예) 사이즈, 총장, 허리, 엉덩이\n    M, 100, 30, 52\n    L, 102, 32, 54"
)


def render_product_extras_inputs(key_prefix, options_text="", extras=None):
    extras = extras or {}
    filled = bool(options_text or any(extras.get(k) for k in EXTRA_KEYS))
    with st.expander("옵션 · 사이즈표 · 소재 · 세탁정보", expanded=filled):
        options_value = st.text_area("사이즈·옵션 (옵션명, 재고, 추가금액)", value=options_text, height=120,
                                     help=OPTION_HELP, key=f"{key_prefix}_options",
                                     placeholder="S, 3, 0\nM, 5, 0\nL, 2, 0")
        c1, c2 = st.columns(2)
        size_m = c1.text_area("남성 사이즈표", value=extras.get("size_table_m", ""), height=120,
                              help=SIZE_HELP, key=f"{key_prefix}_size_m",
                              placeholder="사이즈, 가슴, 총장\nS, 50, 68\nM, 52, 70")
        size_w = c2.text_area("여성 사이즈표", value=extras.get("size_table_w", ""), height=120,
                              help=SIZE_HELP, key=f"{key_prefix}_size_w",
                              placeholder="사이즈, 가슴, 총장\nS, 46, 62\nM, 48, 64")
        size_common = extras.get("size_table", "")
        if size_common:
            size_common = st.text_area("공용 사이즈표 (기존 입력)", value=size_common, height=90,
                                       help=SIZE_HELP, key=f"{key_prefix}_size")
        st.markdown("**소재 정보**")
        current = parse_fabric(extras.get("fabric"))
        fabric = {}
        for attr, choices in FABRIC_ATTRS:
            fabric[attr] = st.segmented_control(
                attr, choices, default=current.get(attr) if current.get(attr) in choices else None,
                key=f"{key_prefix}_fabric_{attr}",
            ) or ""
        care_value = st.text_area("세탁 정보", value=extras.get("care", ""), height=80,
                                  key=f"{key_prefix}_care", placeholder="손세탁 권장 / 표백제 사용 금지")
    return options_value, {
        "size_table": (size_common or "").strip(),
        "size_table_m": size_m.strip(),
        "size_table_w": size_w.strip(),
        "care": care_value.strip(),
        "fabric": fabric_to_text(fabric),
    }


def validate_product_options(options_text):
    features = _shop_features()
    if features is None:
        if str(options_text or "").strip():
            raise ValueError("옵션 기능을 불러오지 못해 옵션을 저장할 수 없습니다.")
        return None, None
    return features, features.parse_options_text(options_text)


def render_feedback_admin():
    st.subheader("상품 문의 · 후기 관리")
    features = _shop_features()
    if features is None:
        st.error("문의·후기 기능을 불러오지 못했습니다.")
        return
    names = {str(p.get("id")): str(p.get("name", "")) for p in PRODUCTS}
    qna_tab, review_tab = st.tabs(["상품 문의", "상품 후기"])

    with qna_tab:
        try:
            questions = features.admin_list_qna()
        except Exception:
            st.error("상품 문의를 불러오지 못했습니다.")
            questions = []
        waiting = [q for q in questions if not q.get("answer") and not q.get("hidden")]
        st.caption(f"전체 {len(questions)}건 · 답변 대기 {len(waiting)}건")
        only_waiting = st.checkbox("답변 대기만 보기", value=True, key="fb_only_waiting")
        for q in (waiting if only_waiting else questions):
            qid = q.get("id")
            title = (f"{'[숨김] ' if q.get('hidden') else ''}{'🔒 ' if q.get('is_secret') else ''}"
                     f"{names.get(str(q.get('product_id')), q.get('product_id'))} · {q.get('author')} · "
                     f"{str(q.get('created_at', ''))[:16].replace('T', ' ')}")
            with st.expander(title):
                st.text(q.get("question", ""))
                answer = st.text_area("답변", value=str(q.get("answer") or ""), key=f"fb_answer_{qid}")
                c1, c2 = st.columns(2)
                if c1.button("답변 저장", key=f"fb_save_{qid}", use_container_width=True):
                    try:
                        features.admin_answer_qna(qid, answer)
                        st.success("답변을 저장했습니다.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("답변 저장에 실패했습니다.")
                hide_label = "다시 보이기" if q.get("hidden") else "숨기기"
                if c2.button(hide_label, key=f"fb_hide_q_{qid}", use_container_width=True):
                    features.admin_set_qna_hidden(qid, not q.get("hidden"))
                    st.rerun()

    with review_tab:
        try:
            reviews = features.admin_list_reviews()
        except Exception:
            st.error("상품 후기를 불러오지 못했습니다.")
            reviews = []
        st.caption(f"전체 {len(reviews)}건")
        for r in reviews:
            rid = r.get("id")
            title = (f"{'[숨김] ' if r.get('hidden') else ''}{'★' * int(r.get('rating') or 0)} · "
                     f"{names.get(str(r.get('product_id')), r.get('product_id'))} · {r.get('author')}")
            with st.expander(title):
                st.caption(f"주문번호 {r.get('order_id')} · {r.get('option_name') or '옵션 없음'} · "
                           f"{str(r.get('created_at', ''))[:10]}")
                st.text(r.get("content", ""))
                hide_label = "다시 보이기" if r.get("hidden") else "숨기기"
                if st.button(hide_label, key=f"fb_hide_r_{rid}"):
                    features.admin_set_review_hidden(rid, not r.get("hidden"))
                    st.rerun()


MAX_PRODUCT_IMAGES = 20


def _thumb_data_uri(data, cache_key):
    cache = st.session_state.setdefault("_img_thumb_cache", {})
    if cache_key in cache:
        return cache[cache_key]
    try:
        from io import BytesIO
        from PIL import Image as _PILImage, ImageOps as _PILImageOps
        with _PILImage.open(BytesIO(data)) as im:
            im = _PILImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((320, 320))
            buf = BytesIO()
            im.save(buf, "JPEG", quality=78)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        uri = ""
    if len(cache) > 200:
        cache.clear()
    cache[cache_key] = uri
    return uri


def uploaded_image_entries(files):
    entries = []
    for f in files or []:
        file_id = str(getattr(f, "file_id", "") or f"{f.name}-{f.size}")
        entries.append({"id": "up:" + file_id, "src": _thumb_data_uri(f.getvalue(), file_id), "file": f})
    return entries


def _image_order_action(key, widget_key, item_id):
    choice = st.session_state.get(widget_key)
    st.session_state[widget_key] = None
    state = st.session_state.get(key) or {"order": [], "removed": []}
    order, removed = list(state["order"]), list(state["removed"])
    if item_id not in order:
        return
    idx = order.index(item_id)
    if choice == "◀" and idx > 0:
        order[idx - 1], order[idx] = order[idx], order[idx - 1]
    elif choice == "▶" and idx < len(order) - 1:
        order[idx + 1], order[idx] = order[idx], order[idx + 1]
    elif choice == "★" and idx > 0:
        order.insert(0, order.pop(idx))
    elif choice == "✕":
        removed.append(order.pop(idx))
    st.session_state[key] = {"order": order, "removed": removed}


def render_image_order_editor(key, entries, allow_remove=False, per_row=5):
    """사진 미리보기 + 순서 변경(◀ ★ ▶) + 빼기(✕). 정렬된 항목 목록을 돌려줍니다.

    버튼 줄은 한 개의 위젯이라, 이미 칸(column) 안에서 호출해도 겹침 제한에 걸리지 않습니다.
    """
    by_id = {e["id"]: e for e in entries}
    state = st.session_state.get(key) or {"order": [], "removed": []}
    removed = [i for i in state["removed"] if i in by_id]
    order = [i for i in state["order"] if i in by_id and i not in removed]
    order += [e["id"] for e in entries if e["id"] not in order and e["id"] not in removed]
    st.session_state[key] = {"order": order, "removed": removed}
    if not order:
        return []

    st.caption(f"사진 {len(order)}장 · 첫 번째가 대표 사진입니다. ◀ ▶ 순서 이동, ★ 대표로, ✕ 빼기")
    actions = ["◀", "★", "▶", "✕"] if allow_remove else ["◀", "★", "▶"]
    for row_start in range(0, len(order), per_row):
        cols = st.columns(per_row, gap="small")
        for offset, item_id in enumerate(order[row_start:row_start + per_row]):
            idx = row_start + offset
            item = by_id[item_id]
            with cols[offset]:
                border = "#ff6900" if idx == 0 else "#333"
                src = item.get("src") or ""
                img = (f'<img src="{escape(src, quote=True)}" alt="사진 {idx + 1}" '
                       f'style="width:100%;aspect-ratio:1;object-fit:cover;display:block">') if src else (
                       '<div style="aspect-ratio:1;display:flex;align-items:center;justify-content:center;'
                       'color:#888;font-size:12px">미리보기 없음</div>')
                safe_markdown(
                    f'<div style="border:2px solid {border};border-radius:6px;overflow:hidden;background:#111">'
                    f'{img}<div style="font-size:12px;padding:3px 6px;background:#161616">'
                    f'{idx + 1}{" · 대표" if idx == 0 else ""}</div></div>',
                    unsafe_allow_html=True,
                )
                widget_key = f"{key}_act_{item_id}"
                st.segmented_control(
                    f"사진 {idx + 1} 이동",
                    actions,
                    key=widget_key,
                    label_visibility="collapsed",
                    on_change=_image_order_action,
                    args=(key, widget_key, item_id),
                )
    return [by_id[i] for i in st.session_state[key]["order"]]


def _naver_sync():
    try:
        import naver_sync
        return naver_sync
    except Exception as exc:
        print("[NAVER] sync unavailable: " + type(exc).__name__ + ": " + str(exc)[:200], flush=True)
        return None


NAVER_WARRANTY_DEFAULT = "제품 이상 시 공정거래위원회 고시 소비자분쟁해결기준에 의거 보상합니다."


def _naver_pick(label, rows, current, key, placeholder):
    ids = [""] + [r["id"] for r in rows]
    names = {r["id"]: r["name"] for r in rows}
    index = ids.index(current) if current in ids else 0
    return st.selectbox(
        label, ids, index=index, key=key,
        format_func=lambda v: names.get(v, placeholder) if v else placeholder,
    ) or ""


def render_naver_fields(key_prefix, defaults, existing=None, show_stock=True):
    """네이버 동시 등록 입력칸. (사용 여부, 입력값) 반환. 중고 바이크에는 호출하지 않습니다."""
    sync = _naver_sync()
    existing = existing or {}
    with st.expander("네이버 스마트스토어 동시 등록 (전시중지)", expanded=bool(existing)):
        if sync is None or not sync.enabled():
            st.info("네이버 연동 비밀키(NAVER_SYNC_SECRET)가 아직 설정되지 않아 동시 등록을 사용할 수 없습니다.")
            return False, {}
        use = st.checkbox(
            "이 상품을 네이버 스마트스토어에도 등록 (항상 전시중지 상태로 생성)",
            value=bool(existing), key=f"{key_prefix}_use",
        )
        if not use:
            return False, {}
        base = dict(sync.latest_fields())
        base.update({k: v for k, v in (existing or {}).items() if v not in (None, "")})
        for k, v in defaults.items():
            if not base.get(k) or (k in ("size", "caution") and not existing.get(k)):
                if v:
                    base[k] = v
        try:
            categories = sync.catalog("categories")
            origins = sync.catalog("origins")
            addresses = sync.catalog("addresses")
        except Exception as exc:
            st.error("네이버 목록을 불러오지 못했습니다: " + str(exc))
            return False, {}

        f = {}
        f["category"] = _naver_pick("네이버 카테고리 (입력해서 검색)", categories, str(base.get("category") or ""),
                                    f"{key_prefix}_category", "카테고리 선택")
        c1, c2 = st.columns(2)
        with c1:
            f["origin"] = _naver_pick("원산지", origins, str(base.get("origin") or ""), f"{key_prefix}_origin", "원산지 선택")
            f["manufacturer"] = st.text_input("제조사", value=str(base.get("manufacturer") or ""), key=f"{key_prefix}_manufacturer")
            company_codes = [""] + list(sync.DELIVERY_COMPANIES)
            cur = str(base.get("company") or "")
            f["company"] = st.selectbox(
                "택배사", company_codes, index=company_codes.index(cur) if cur in company_codes else 0,
                format_func=lambda v: sync.DELIVERY_COMPANIES.get(v, "택배사 선택"), key=f"{key_prefix}_company",
            ) or ""
            f["fee"] = str(st.number_input("배송비(원) · 0이면 무료배송", min_value=0, step=500,
                                           value=int(base.get("fee") or 3000), key=f"{key_prefix}_fee"))
            f["return_fee"] = str(st.number_input("반품 배송비(원)", min_value=0, step=500,
                                                  value=int(base.get("return_fee") or 3000), key=f"{key_prefix}_return_fee"))
            f["phone"] = st.text_input("A/S 연락처", value=str(base.get("phone") or ""), key=f"{key_prefix}_phone")
        with c2:
            f["importer"] = st.text_input("수입사 (수입품만)", value=str(base.get("importer") or ""), key=f"{key_prefix}_importer")
            f["shipping"] = _naver_pick("출고지", addresses, str(base.get("shipping") or ""), f"{key_prefix}_shipping", "출고지 선택")
            f["returning"] = _naver_pick("반품지", addresses, str(base.get("returning") or ""), f"{key_prefix}_returning", "반품지 선택")
            f["free_over"] = str(st.number_input("무료배송 기준금액(원) · 없으면 0", min_value=0, step=10000,
                                                 value=int(base.get("free_over") or 0), key=f"{key_prefix}_free_over"))
            f["exchange_fee"] = str(st.number_input("교환 배송비(원)", min_value=0, step=500,
                                                    value=int(base.get("exchange_fee") or 6000), key=f"{key_prefix}_exchange_fee"))
            f["as_guide"] = st.text_input("A/S 안내", value=str(base.get("as_guide") or "구매 매장으로 문의해 주세요."),
                                          key=f"{key_prefix}_as_guide")
        st.markdown("**의류 필수 고시정보**")
        c3, c4 = st.columns(2)
        with c3:
            f["material"] = st.text_input("소재·혼용률", value=str(base.get("material") or ""), key=f"{key_prefix}_material",
                                          placeholder="예: 면 100%")
            f["color"] = st.text_input("색상", value=str(base.get("color") or ""), key=f"{key_prefix}_color")
            f["size"] = st.text_input("치수", value=str(base.get("size") or ""), key=f"{key_prefix}_size")
            f["packDateText"] = st.text_input("제조연월", value=str(base.get("packDateText") or ""),
                                              key=f"{key_prefix}_pack", placeholder="예: 2026-09")
        with c4:
            f["caution"] = st.text_input("세탁방법·취급 주의", value=str(base.get("caution") or ""), key=f"{key_prefix}_caution")
            f["warrantyPolicy"] = st.text_input("품질보증기준", value=str(base.get("warrantyPolicy") or NAVER_WARRANTY_DEFAULT),
                                                key=f"{key_prefix}_warranty")
            f["afterServiceDirector"] = st.text_input("A/S 책임자와 전화번호", value=str(base.get("afterServiceDirector") or ""),
                                                      key=f"{key_prefix}_as_director")
            if show_stock:
                f["stock"] = str(st.number_input("네이버 재고 (사이즈 옵션이 없을 때만 사용)", min_value=1, step=1,
                                                 value=int(base.get("stock") or 1), key=f"{key_prefix}_stock"))
        f["condition"] = "NEW"
        f["policy_confirm"] = "yes" if st.checkbox(
            "청약철회·반품·환불은 네이버 기본 고지를 사용하며, 입력한 정보가 실제 상품과 같음을 확인했습니다.",
            value=base.get("policy_confirm") == "yes", key=f"{key_prefix}_policy",
        ) else ""
        st.caption("사이트에 등록한 사진(JPG·PNG), 설명, 가격, 사이즈별 재고가 네이버로 함께 전송됩니다. "
                   "네이버에는 항상 전시중지로 만들어지니, 스마트스토어센터에서 확인 후 직접 전시해 주세요.")
    return True, f


def naver_product_payload(product):
    text, files = unpack_detail(product.get("description", ""))
    brand = str(product.get("brand") or "").strip()
    name = str(product.get("name") or "").strip()
    if brand and not name.lower().startswith(brand.lower()):
        name = f"{brand} {name}"
    options = []
    features = _shop_features()
    if features is not None:
        try:
            options = features._backend.product_options(str(product.get("id")))
        except Exception:
            options = []
    return {
        "name": name[:100],
        "price": int(product.get("price") or 0),
        "description": text,
        "images": [u for u in product_images(product) if str(u).startswith("https://")][:10],
        "detail_images": [
            f.get("url") for f in files
            if isinstance(f, dict) and f.get("kind") == "image" and str(f.get("url", "")).startswith("https://")
        ][:20],
        "options": [
            {"name": o.get("name"), "stock": o.get("stock"), "extra_price": o.get("extra_price")}
            for o in options
        ],
    }


def naver_defaults_for(product, options_text="", extras=None):
    extras = extras or {}
    sizes = []
    for line in str(options_text or "").splitlines():
        head = line.split(",")[0].strip()
        if head:
            sizes.append(head)
    return {
        "manufacturer": str(product.get("brand") or "").strip() or "투제이로드",
        "size": ", ".join(sizes) if sizes else "FREE",
        "caution": " ".join(str(extras.get("care") or "").split())[:200],
        "phone": MASPICK_PHONE,
    }


def run_naver_publish(product, fields):
    sync = _naver_sync()
    if sync is None:
        return "error", "네이버 연동 모듈을 불러오지 못했습니다."
    try:
        return sync.publish(str(product.get("id")), naver_product_payload(product), fields)
    except Exception as exc:
        return "error", f"네이버 등록 중 오류: {type(exc).__name__}: {str(exc)[:300]}"


def render_naver_status_and_publish(product):
    """상품 수정 화면: 네이버 등록 상태 표시와 전시중지 등록 버튼."""
    if product.get("type") == "bike":
        return
    sync = _naver_sync()
    if sync is None or not sync.enabled():
        return
    pid = str(product.get("id"))
    try:
        setting = sync.load_setting(pid) or {}
    except Exception:
        setting = {}
    status = setting.get("sync_status")
    st.markdown("#### 네이버 스마트스토어")
    if status == "synced":
        st.success(f"네이버 등록 완료 · 상품번호 {setting.get('naver_origin_product_no')} (전시중지로 생성). "
                   "사이트에서 수정한 내용은 네이버에 자동 반영되지 않으니 스마트스토어센터에서 수정해 주세요.")
        return
    if status == "sending" or status == "unknown":
        st.warning("이전 네이버 전송 결과를 확인하지 못했습니다. 스마트스토어센터에서 등록 여부를 먼저 확인해 주세요.")
    if status == "error" and setting.get("sync_error"):
        st.error("지난 네이버 등록 실패: " + str(setting.get("sync_error")))
    current_extras = unpack_extras(product.get("description", ""))
    options_text = ""
    features = _shop_features()
    if features is not None:
        try:
            options_text = features.options_to_text(features._backend.product_options(pid))
        except Exception:
            pass
    use, fields = render_naver_fields(
        f"naver_edit_{pid}", naver_defaults_for(product, options_text, current_extras),
        existing=setting.get("fields") or {},
    )
    if not use:
        return
    st.caption("먼저 '수정 저장'으로 사이트 내용을 저장한 뒤 눌러주세요. 저장된 사이트 상품 기준으로 전송됩니다.")
    if status in ("sending", "unknown"):
        return
    if st.button("네이버에 전시중지로 등록", key=f"naver_publish_{pid}", use_container_width=True):
        with st.spinner("네이버에 등록하는 중입니다. 사진이 많으면 1분 정도 걸릴 수 있어요..."):
            state, message = run_naver_publish(product, fields)
        if state == "synced":
            st.session_state["product_action_notice"] = message
            st.rerun()
        else:
            st.error(message)


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login():
    safe_markdown(
        """
        <div class="page-title">
            TWO J ROAD 관리자
        </div>

        <div class="page-subtitle">
            상품 등록 · 수정 · 삭제
        </div>
        """,
        unsafe_allow_html=True
    )

    if not ADMIN_PASSWORD:
        st.error(
            "관리자 비밀번호가 아직 서버에 설정되지 않았습니다."
        )

        st.code(
            "Render 환경변수: MASPICK_ADMIN_PASSWORD"
        )

        return False

    if st.session_state.get(
        "admin_logged_in"
    ):
        return True

    password = st.text_input(
        "관리자 비밀번호",
        type="password"
    )

    if st.button(
        "관리자 로그인",
        use_container_width=True
    ):
        if password == ADMIN_PASSWORD:
            st.session_state[
                "admin_logged_in"
            ] = True

            st.rerun()

        else:
            st.error(
                "비밀번호가 올바르지 않습니다."
            )

    return False


# =========================================================
# ADMIN - ADD PRODUCT
# =========================================================

def render_add_product():
    st.subheader("상품 등록")

    product_type = st.selectbox(
        "상품 종류",
        [
            "중고 바이크",
            "바이크 의류",
            "바이크 용품",
        ],
        key="add_type"
    )

    category_options = {
        "바이크 의류": [
            "상의",
            "하의",
            "자켓",
            "장갑",
            "신발",
        ],
        "바이크 용품": [
            "헬멧",
            "기타",
        ],
    }

    subcategory = ""
    if product_type != "중고 바이크":
        subcategory = st.selectbox(
            "카테고리 선택",
            category_options[product_type],
            key=f"add_subcategory_{product_type}",
            help="선택한 카테고리의 상품 목록에 표시됩니다."
        )

    c1, c2 = st.columns(2)

    with c1:
        brand = st.text_input(
            "브랜드",
            key="add_brand"
        )

        name = st.text_input(
            "상품명",
            key="add_name"
        )

        price = st.number_input(
            "가격",
            min_value=0,
            step=10000,
            key="add_price"
        )

        badge = st.text_input(
            "상품 배지",
            value="",
            placeholder="예: 신상품, 할인중, 추천매물",
            help="입력한 문구가 그대로 표시됩니다. 비워두면 표시하지 않습니다.",
            key="add_badge"
        )

    with c2:
        condition = st.selectbox(
            "판매상태",
            [
                "판매중",
                "예약중",
                "판매완료",
            ],
            key="add_condition"
        )

        add_ver = st.session_state.get("add_upload_ver", 0)
        uploaded_images = st.file_uploader(
            "상품 사진 직접 업로드 (여러 장 한 번에 선택 가능)",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            accept_multiple_files=True,
            help=f"최대 {MAX_PRODUCT_IMAGES}장까지 등록할 수 있습니다.",
            key=f"add_uploaded_images_{add_ver}"
        )
        add_image_entries = render_image_order_editor(
            f"add_img_order_{add_ver}",
            uploaded_image_entries(uploaded_images),
            allow_remove=True,
            per_row=3,
        )
        uploaded_images = [e["file"] for e in add_image_entries]

        image = st.text_input(
            "또는 대표 이미지 URL",
            placeholder="직접 업로드하면 비워두어도 됩니다.",
            key="add_image"
        )

        description = st.text_area(
            "상품 설명",
            height=150,
            key="add_description"
        )
        detail_uploads = st.file_uploader(
            "상세내용 첨부파일",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
            accept_multiple_files=True,
            help="상세 이미지 또는 PDF · 최대 8개, 파일당 20MB",
            key="add_detail_files"
        )

    year = ""
    mileage = ""
    cc = ""
    region = ""
    accident = ""

    if product_type == "중고 바이크":
        safe_markdown(
            "#### 중고 바이크 정보"
        )

        b1, b2, b3 = st.columns(3)

        with b1:
            year = st.text_input(
                "연식",
                placeholder="2021",
                key="add_year"
            )

            region = st.text_input(
                "지역",
                value="경기 포천",
                key="add_region"
            )

        with b2:
            mileage = st.text_input(
                "주행거리",
                placeholder="18,200km",
                key="add_mileage"
            )

            accident = st.text_input(
                "사고유무",
                placeholder="무사고 / 단순교환 / 상담문의",
                key="add_accident"
            )

        with b3:
            cc = st.text_input(
                "배기량",
                placeholder="1,868cc",
                key="add_cc"
            )

    add_options_text, add_extras = "", {}
    add_naver_use, add_naver_fields = False, {}
    if product_type != "중고 바이크":
        add_options_text, add_extras = render_product_extras_inputs("add_extras")
        add_naver_use, add_naver_fields = render_naver_fields(
            "naver_add",
            naver_defaults_for({"brand": brand}, add_options_text, add_extras),
        )

    if st.button(
        "상품 등록하기",
        use_container_width=True
    ):
        try:
            add_features, add_option_rows = validate_product_options(add_options_text)
        except ValueError as exc:
            st.error(str(exc))
            return

        if not name.strip():
            st.error(
                "상품명을 입력해 주세요."
            )
            return

        if len(uploaded_images or []) > MAX_PRODUCT_IMAGES:
            st.error(
                f"상품 사진은 최대 {MAX_PRODUCT_IMAGES}장까지 등록할 수 있습니다."
            )
            return

        if (
            not uploaded_images
            and
            not image.strip()
        ):
            st.error(
                "상품 사진을 직접 업로드하거나 이미지 URL을 입력해 주세요."
            )
            return

        type_code = {
            "중고 바이크": "bike",
            "바이크 의류": "wear",
            "바이크 용품": "gear",
        }[product_type]

        product_id = uuid.uuid4().hex[:12]

        try:
            saved_detail_files = upload_detail_files(detail_uploads, product_id)
        except Exception:
            st.error("상세 첨부파일 저장에 실패했습니다. 파일 수·크기와 저장소 연결을 확인해 주세요.")
            return

        saved_images = save_uploaded_images(
            uploaded_images,
            product_id
        )

        if (
            not saved_images
            and
            image.strip()
        ):
            saved_images = [
                image.strip()
            ]

        new_product = {
            "id": product_id,
            "type": type_code,
            "category": product_type,
            "subcategory": subcategory.strip(),
            "brand": brand.strip(),
            "name": name.strip(),
            "price": int(price),
            "condition": condition,
            "badge": badge,
            "image": (
                saved_images[0]
                if saved_images
                else ""
            ),
            "images": saved_images,
            "description": pack_detail(
                description.strip(),
                saved_detail_files,
                add_extras,
            ),
            "demo": False,
        }

        if product_type == "중고 바이크":
            new_product.update({
                "year": year.strip(),
                "mileage": mileage.strip(),
                "cc": cc.strip(),
                "region": region.strip(),
                "accident": accident.strip(),
            })

        PRODUCTS.append(
            new_product
        )

        save_products(
            PRODUCTS
        )

        option_notice = ""
        if add_features is not None and add_option_rows:
            try:
                add_features.save_options(product_id, add_option_rows)
            except Exception:
                option_notice = " (옵션 저장 실패 · 상품 수정에서 다시 저장해 주세요)"

        st.session_state["product_action_notice"] = (
            f"상품 등록 완료 · {new_product['name']}" + option_notice
        )
        if add_naver_use and product_type != "중고 바이크":
            with st.spinner("사이트 등록 완료. 네이버 스마트스토어에 전시중지로 등록하는 중..."):
                naver_state, naver_message = run_naver_publish(new_product, add_naver_fields)
            if naver_state == "synced":
                st.session_state["product_action_notice"] += " · " + naver_message
            else:
                st.session_state["naver_action_notice"] = (
                    "사이트 등록은 완료됐지만 네이버 등록은 실패했습니다: " + naver_message
                    + " → 상품 수정 화면에서 입력을 고친 뒤 '네이버에 전시중지로 등록'을 눌러주세요."
                )
        st.session_state.pop(f"add_img_order_{add_ver}", None)
        st.session_state["add_upload_ver"] = add_ver + 1

        st.rerun()


# =========================================================
# ADMIN - EDIT / DELETE
# =========================================================

def render_manage_products():
    st.subheader(
        f"등록 상품 관리 ({len(PRODUCTS)}개)"
    )

    if not PRODUCTS:
        st.info(
            "등록된 상품이 없습니다."
        )
        return

    options = {
        (
            f"{p.get('name','상품')} | "
            f"{money(p.get('price',0))} | "
            f"{p.get('id','')}"
        ): p.get("id", "")
        for p in PRODUCTS
    }

    selected_label = st.selectbox(
        "수정할 상품 선택",
        list(options.keys())
    )

    selected_id = options[
        selected_label
    ]

    product = get_product(
        PRODUCTS,
        selected_id
    )

    if not product:
        return

    safe_markdown(
        f"""
        <div class="admin-product">
            <div class="admin-product-name">
                {escape(str(product.get('name','')))}
            </div>

            <div class="admin-product-meta">
                {escape(str(product.get('category','')))}
                ·
                {escape(str(product.get('brand','')))}
                ·
                {money(product.get('price',0))}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    edit_brand = st.text_input(
        "브랜드",
        value=str(
            product.get("brand", "")
        ),
        key=f"edit_brand_{selected_id}"
    )

    edit_name = st.text_input(
        "상품명",
        value=str(
            product.get("name", "")
        ),
        key=f"edit_name_{selected_id}"
    )

    edit_price = st.number_input(
        "가격",
        min_value=0,
        value=int(
            product.get("price", 0)
        ),
        step=10000,
        key=f"edit_price_{selected_id}"
    )

    edit_category_options = {
        "바이크 의류": [
            "상의",
            "하의",
            "자켓",
            "장갑",
            "신발",
        ],
        "바이크 용품": [
            "헬멧",
            "기타",
        ],
    }

    current_category = product.get(
        "category",
        "바이크 용품"
    )

    edit_options = list(
        edit_category_options.get(
            current_category,
            ["기타"]
        )
    )

    current_subcategory = str(
        product.get(
            "subcategory",
            ""
        )
    )

    if (
        current_subcategory
        and
        current_subcategory not in edit_options
    ):
        edit_options.insert(
            0,
            current_subcategory
        )

    edit_subcategory = ""
    if product.get("type") != "bike" and current_category != "중고 바이크":
        edit_subcategory = st.selectbox(
            "카테고리",
            edit_options,
            index=(
                edit_options.index(current_subcategory)
                if current_subcategory in edit_options
                else 0
            ),
            key=f"edit_subcategory_{selected_id}"
        )

    conditions = [
        "판매중",
        "예약중",
        "판매완료",
    ]

    current_condition = product.get(
        "condition",
        "판매중"
    )

    edit_condition = st.selectbox(
        "판매상태",
        conditions,
        index=(
            conditions.index(current_condition)
            if current_condition in conditions
            else 0
        ),
        key=f"edit_condition_{selected_id}"
    )

    edit_badge = st.text_input(
        "상품 배지",
        value=str(
            product.get("badge", "")
        ),
        key=f"edit_badge_{selected_id}"
    )

    current_images = product_images(
        product
    )

    edit_ver = st.session_state.get(f"edit_upload_ver_{selected_id}", 0)
    st.markdown("#### 상품 사진 · 순서 변경")
    added_images = st.file_uploader(
        "사진 추가 (여러 장 한 번에 선택 가능)",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        accept_multiple_files=True,
        help=f"추가한 사진은 뒤에 붙습니다. 전체 최대 {MAX_PRODUCT_IMAGES}장.",
        key=f"edit_uploaded_images_{selected_id}_{edit_ver}"
    )
    edit_image_entries = render_image_order_editor(
        f"edit_img_order_{selected_id}_{edit_ver}",
        [
            {"id": f"cur:{i}:{v}", "src": image_src(v), "url": v}
            for i, v in enumerate(current_images)
        ] + uploaded_image_entries(added_images),
        allow_remove=True,
    )
    if current_images and not edit_image_entries:
        st.warning("사진을 모두 뺐습니다. 저장하려면 사진을 1장 이상 남기거나 추가해 주세요.")

    edit_image = st.text_input(
        "이미지 URL로 추가 (선택)",
        value="",
        placeholder="https://...",
        key=f"edit_image_{selected_id}_{edit_ver}"
    )

    current_detail_text, current_detail_files = unpack_detail(product.get("description", ""))
    edit_description = st.text_area(
        "상품 설명", value=current_detail_text, height=140,
        key=f"edit_description_{selected_id}"
    )
    if current_detail_files:
        st.caption("현재 상세 첨부파일: " + ", ".join(item.get("name", "파일") for item in current_detail_files))
    remove_detail_files = st.checkbox("기존 상세 첨부파일 삭제", key=f"remove_detail_{selected_id}")
    replacement_detail_files = st.file_uploader(
        "상세내용 첨부파일 추가 / 교체",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
        help="새 파일을 올리면 기존 상세 첨부파일을 교체합니다. 최대 8개, 파일당 20MB",
        key=f"edit_detail_files_{selected_id}"
    )

    current_extras = unpack_extras(product.get("description", ""))
    options_loaded = False
    edit_options_text, edit_extras = "", dict(current_extras)
    if product.get("type") != "bike":
        _edit_features = _shop_features()
        current_options_text = ""
        if _edit_features is not None:
            try:
                current_options_text = _edit_features.options_to_text(
                    _edit_features._backend.product_options(str(selected_id))
                )
                options_loaded = True
            except Exception:
                st.warning("현재 옵션을 불러오지 못했습니다. 이번 저장에서는 옵션을 변경하지 않습니다.")
        edit_options_text, edit_extras = render_product_extras_inputs(
            f"edit_extras_{selected_id}",
            current_options_text,
            current_extras,
        )

    render_naver_status_and_publish(product)

    bike_values = {}

    if product.get("type") == "bike":
        safe_markdown(
            "#### 차량 정보"
        )

        e1, e2, e3 = st.columns(3)

        with e1:
            bike_values["year"] = st.text_input(
                "연식",
                value=str(
                    product.get("year", "")
                ),
                key=f"edit_year_{selected_id}"
            )

            bike_values["region"] = st.text_input(
                "지역",
                value=str(
                    product.get("region", "")
                ),
                key=f"edit_region_{selected_id}"
            )

        with e2:
            bike_values["mileage"] = st.text_input(
                "주행거리",
                value=str(
                    product.get("mileage", "")
                ),
                key=f"edit_mileage_{selected_id}"
            )

            bike_values["accident"] = st.text_input(
                "사고유무",
                value=str(
                    product.get("accident", "")
                ),
                key=f"edit_accident_{selected_id}"
            )

        with e3:
            bike_values["cc"] = st.text_input(
                "배기량",
                value=str(
                    product.get("cc", "")
                ),
                key=f"edit_cc_{selected_id}"
            )

    b1, b2 = st.columns(2)

    with b1:
        if st.button(
            "수정 저장",
            use_container_width=True
        ):
            try:
                edit_features, edit_option_rows = validate_product_options(edit_options_text)
            except ValueError as exc:
                st.error(str(exc))
                return

            product["brand"] = edit_brand.strip()
            product["name"] = edit_name.strip()
            product["price"] = int(edit_price)
            product["subcategory"] = edit_subcategory.strip()
            product["condition"] = edit_condition
            product["badge"] = edit_badge

            final_entries = list(edit_image_entries)
            if edit_image.strip():
                final_entries.append({"id": "url:new", "url": edit_image.strip()})
            if not final_entries:
                st.error("상품 사진을 1장 이상 남기거나 추가해 주세요.")
                return
            if len(final_entries) > MAX_PRODUCT_IMAGES:
                st.error(f"상품 사진은 최대 {MAX_PRODUCT_IMAGES}장까지 등록할 수 있습니다.")
                return

            new_files = [e["file"] for e in final_entries if e.get("file") is not None]
            saved_new = []
            if new_files:
                saved_new = save_uploaded_images(
                    new_files,
                    product.get("id", uuid.uuid4().hex[:12])
                ) or []
                if len(saved_new) != len(new_files):
                    st.error("추가한 사진 저장에 실패했습니다. 다시 시도해 주세요.")
                    return
            saved_iter = iter(saved_new)
            updated_images = []
            for entry in final_entries:
                if entry.get("file") is not None:
                    updated_images.append(next(saved_iter))
                else:
                    updated_images.append(entry["url"])

            kept = set(updated_images)
            removed_images = [v for v in current_images if v not in kept]
            if removed_images:
                delete_local_images({"images": removed_images})

            product["images"] = updated_images
            product["image"] = updated_images[0]

            detail_files = [] if remove_detail_files else current_detail_files
            if replacement_detail_files:
                try:
                    detail_files = upload_detail_files(replacement_detail_files, str(selected_id))
                except Exception:
                    st.error("상세 첨부파일 저장에 실패했습니다. 파일 수·크기와 저장소 연결을 확인해 주세요.")
                    return
            if replacement_detail_files or remove_detail_files:
                delete_local_images({"images": [item["url"] for item in current_detail_files]})
            product["description"] = pack_detail(
                edit_description.strip(),
                detail_files,
                edit_extras,
            )

            for key, value in bike_values.items():
                product[key] = value.strip()

            product["demo"] = False

            save_products(
                PRODUCTS
            )

            option_notice = ""
            if edit_features is not None and options_loaded and product.get("type") != "bike":
                try:
                    edit_features.save_options(str(selected_id), edit_option_rows)
                except Exception:
                    option_notice = " (옵션 저장 실패 · 다시 시도해 주세요)"

            st.session_state["product_action_notice"] = (
                f"상품 수정 완료 · {product.get('name', '')}" + option_notice
            )
            st.session_state.pop(f"edit_img_order_{selected_id}_{edit_ver}", None)
            st.session_state[f"edit_upload_ver_{selected_id}"] = edit_ver + 1

            st.rerun()

    with b2:
        confirm_delete = st.checkbox(
            "삭제 확인",
            key=f"delete_confirm_{selected_id}"
        )

        if st.button(
            "상품 삭제",
            use_container_width=True
        ):
            if not confirm_delete:
                st.warning(
                    "삭제 확인을 먼저 체크해 주세요."
                )

            else:
                _, deleted_detail_files = unpack_detail(product.get("description", ""))
                delete_local_images({"images": [item["url"] for item in deleted_detail_files]})
                delete_local_images(
                    product
                )

                PRODUCTS[:] = [
                    p for p in PRODUCTS
                    if p.get("id") != selected_id
                ]

                save_products(
                    PRODUCTS
                )

                st.session_state["product_action_notice"] = (
                    f"상품 삭제 완료 · {product.get('name', '')}"
                )

                st.rerun()


# =========================================================
# ADMIN
# =========================================================

def read_keyword_report(raw):
    import csv
    import io
    import re

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp949")
    normalize = lambda value: re.sub(r"[\s_()（）]", "", str(value)).lower()
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines)
                   if "키워드" in line or "relKeyword" in line), None)
    if header is None:
        raise ValueError("키워드 열을 찾지 못했습니다. 첫 행에 키워드와 PC·모바일 검색수 열이 필요합니다.")
    content = "\n".join(lines[header:])
    delimiter = "\t" if "\t" in lines[header] else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    names = {normalize(name): name for name in (reader.fieldnames or [])}
    def field(aliases):
        return next((names[a] for a in aliases if a in names), None)
    keyword = field(["키워드", "연관키워드", "relkeyword"])
    pc = field(["월간검색수pc", "pc월간검색수", "pc검색수", "monthlypcqccnt"])
    mobile = field(["월간검색수모바일", "모바일월간검색수", "모바일검색수", "monthlymobileqccnt"])
    if not all([keyword, pc, mobile]):
        raise ValueError("필수 열: 키워드, 월간검색수(PC), 월간검색수(모바일)")
    def count(value):
        value = str(value or "").replace(",", "").replace(" ", "")
        if value.startswith("<") and value[1:].isdigit():
            return 0, max(0, int(value[1:]) - 1)
        if value.isdigit():
            return int(value), int(value)
        raise ValueError("검색수에 숫자 또는 <10 형식 이외의 값이 있습니다.")
    result = []
    for row in reader:
        name = str(row.get(keyword) or "").strip()
        if not name:
            continue
        lo1, hi1 = count(row.get(pc))
        lo2, hi2 = count(row.get(mobile))
        low, high = lo1 + lo2, hi1 + hi2
        result.append({"키워드": name, "PC 검색수": row[pc], "모바일 검색수": row[mobile],
                       "합계": str(low) if low == high else f"{low}~{high}",
                       "_low": low})
    result.sort(key=lambda row: row["_low"], reverse=True)
    return [{k: v for k, v in row.items() if k != "_low"} for row in result]


def render_site_status():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    st.subheader("사이트 현황")
    st.caption("상품 데이터 조회 시각: " + datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M"))
    actual = [p for p in PRODUCTS if not p.get("demo")]
    columns = st.columns(4)
    columns[0].metric("등록 상품", len(actual))
    for column, category in zip(columns[1:], ["중고 바이크", "바이크 의류", "바이크 용품"]):
        column.metric(category, sum(p.get("category") == category for p in actual))
    st.write("상품 저장 연결: " + str(globals().get("SUPABASE_STATUS", "로컬 파일 저장")))
    st.caption("이 수치는 등록 상품 수이며 방문자·조회수와는 다릅니다.")
    st.markdown("#### 검색 준비 상태")
    st.dataframe([
        {"항목": "상품 설명 없는 상품", "상태": str(sum(not any(unpack_detail(p.get("description", ""))) for p in actual)) + "개"},
        {"항목": "사진 없는 상품", "상태": str(sum(not product_images(p) for p in actual)) + "개"},
        {"항목": "페이지 제목", "상태": "카테고리별 제목 설정됨"},
        {"항목": "검색용 설명 메타 태그", "상태": "원본 HTML 적용 필요"},
        {"항목": "네이버 소유 확인·수집·색인", "상태": "서치어드바이저 확인 필요"},
        {"항목": "검색 노출·클릭·방문자", "상태": "통계 연결 전 · 미측정"},
    ], hide_index=True, use_container_width=True)
    st.link_button("네이버 서치어드바이저 열기", "https://searchadvisor.naver.com/")
    st.info("현재 상품 화면은 실행 후 표시되는 구조입니다. 검색 최적화는 검색 로봇이 받는 원본 HTML의 상품 정보·제목·설명까지 확인해야 합니다.")
    st.markdown("#### 실제 검색량으로 키워드 비교")
    st.caption("출처: 사용자가 제공한 네이버 연관키워드 20260911 2014.xlsx · 월간 PC+모바일 검색수 · 실시간 수치 아님")
    st.dataframe([{'키워드': '바이크자켓', 'PC': 370, '모바일': 1670, '월간 합계': 2040}, {'키워드': '오토바이자켓', 'PC': 250, '모바일': 960, '월간 합계': 1210}, {'키워드': '라이딩자켓', 'PC': 160, '모바일': 660, '월간 합계': 820}, {'키워드': '오토바이장갑', 'PC': 670, '모바일': 2490, '월간 합계': 3160}, {'키워드': '바이크장갑', 'PC': 550, '모바일': 2480, '월간 합계': 3030}, {'키워드': '바이크부츠', 'PC': 310, '모바일': 1410, '월간 합계': 1720}, {'키워드': '바이크바지', 'PC': 110, '모바일': 680, '월간 합계': 790}, {'키워드': '바이크의류', 'PC': 80, '모바일': 270, '월간 합계': 350}, {'키워드': '오토바이의류', 'PC': 60, '모바일': 160, '월간 합계': 220}, {'키워드': '오토바이헬멧', 'PC': 4280, '모바일': 19100, '월간 합계': 23380}], hide_index=True, use_container_width=True)

    st.write("조회 후보: 바이크의류, 오토바이의류, 라이딩자켓, 오토바이자켓, 오토바이장갑, 오토바이헬멧")
    st.caption("후보는 검색량 순위가 아닙니다. 취급 상품과 맞는 키워드만 선택하세요. 광고 경쟁도는 자연검색 경쟁도와 다릅니다.")
    st.link_button("네이버 검색광고 키워드 도구로 이동", "https://searchad.naver.com/")
    report = st.file_uploader("키워드 도구 검색량 CSV", type=["csv"], key="keyword_volume_csv",
                              help="필수 열: 키워드, 월간검색수(PC), 월간검색수(모바일). UTF-8 또는 CP949 CSV")
    st.caption("보고서의 조회 기간을 기준으로 비교합니다. 실시간 검색량이 아니며 파일은 이 화면에서만 분석합니다.")
    if report:
        try:
            rows = read_keyword_report(report.getvalue())
            st.dataframe(rows, hide_index=True, use_container_width=True)
            st.caption("PC+모바일 합계순. <10은 0~9 범위로 유지하며 범위의 최솟값으로 정렬합니다.")
        except (ValueError, UnicodeError) as error:
            st.error(str(error))



def render_marketing_center():
    import marketing_center as marketing

    st.subheader("광고 · 노출 자동화")
    st.caption(
        "상품·서비스 정보를 한 번 입력해 채널별 광고 작업본을 생성하고 게시 상태를 관리합니다. "
        "공식 API가 연결되지 않은 채널은 작업본까지만 만들며 자동 로그인·비공식 매크로 게시를 사용하지 않습니다."
    )

    channel_rows = []
    for channel, info in marketing.CHANNEL_INFO.items():
        channel_rows.append({
            "채널": info["label"],
            "현재 단계": info["mode"],
            "운영 기준": info["note"],
        })
    st.dataframe(channel_rows, hide_index=True, use_container_width=True)

    st.markdown("#### 새 광고 작업 만들기")
    business_label = st.selectbox(
        "사업",
        ["TWO J ROAD", "사랑을실은설비공"],
        key="marketing_business",
    )
    business = "twojroad" if business_label == "TWO J ROAD" else "wheng"

    source_product = None
    source_id = ""
    payload = {}
    if business == "twojroad":
        actual_products = [p for p in PRODUCTS if not p.get("demo")]
        option_map = {"직접 입력": None}
        for p in actual_products:
            label = f"{p.get('name', '상품')} · {p.get('id', '')}"
            option_map[label] = p
        selected_source = st.selectbox(
            "TWO J ROAD 상품 불러오기",
            list(option_map.keys()),
            key="marketing_product_source",
        )
        source_product = option_map[selected_source]
        if source_product:
            source_id = str(source_product.get("id") or "")
            source_type = "product"
            default_name = str(source_product.get("name") or "")
            try:
                default_description = unpack_detail(source_product.get("description", ""))[0]
            except Exception:
                default_description = str(source_product.get("description") or "")
            payload = {
                "brand": str(source_product.get("brand") or ""),
                "category": str(source_product.get("category") or ""),
                "price": source_product.get("price") or 0,
                "description": str(default_description or "")[:800],
                "site_url": SITE_URL + "/products/" + source_id,
            }
            default_region = "경기 포천"
            default_keyword = str(source_product.get("category") or "바이크 의류")
        else:
            source_type = "manual"
            default_name = ""
            default_region = "경기 포천"
            default_keyword = ""
    else:
        source_type = st.selectbox(
            "소재 종류",
            ["시공사례", "서비스", "일반홍보"],
            key="marketing_wheng_source_type",
        )
        default_name = ""
        default_region = "수원"
        default_keyword = ""
        payload = {}

    source_key = source_id or f"{business}_{source_type}"
    source_name = st.text_input(
        "상품 · 서비스 · 시공명",
        value=default_name,
        key=f"marketing_source_name_{source_key}",
        placeholder="예: 스트라이프 데님 와이드 팬츠 / 양변기 전체 교체",
    )
    c1, c2 = st.columns(2)
    with c1:
        region = st.text_input(
            "지역",
            value=default_region,
            key=f"marketing_region_{source_key}",
            placeholder="예: 경기 포천 / 수원",
        )
        primary_keyword = st.text_input(
            "핵심 검색어",
            value=default_keyword,
            key=f"marketing_primary_{source_key}",
            placeholder="예: 바이크 의류 / 수원 변기 교체",
        )
    with c2:
        secondary_raw = st.text_area(
            "보조 검색어",
            key=f"marketing_secondary_{source_key}",
            placeholder="쉼표 또는 줄바꿈으로 구분\n예: 바이크 바지, 남성 라이딩 팬츠",
            height=108,
        )
        objective = st.selectbox(
            "목표",
            ["검색 노출", "판매 문의", "방문 유도", "시공 문의"],
            key=f"marketing_objective_{source_key}",
        )

    channels = st.multiselect(
        "작업할 채널",
        list(marketing.CHANNEL_INFO.keys()),
        default=list(marketing.CHANNEL_INFO.keys()),
        format_func=marketing.channel_label,
        key=f"marketing_channels_{source_key}",
    )
    contact_text = st.text_input(
        "문의 문구",
        key=f"marketing_contact_{source_key}",
        placeholder="예: 구매 문의는 사이트 또는 매장으로 연락해 주세요.",
    )

    if st.button("채널별 광고 작업본 생성", type="primary", use_container_width=True):
        secondary_keywords = [
            item.strip()
            for item in secondary_raw.replace("\n", ",").split(",")
            if item.strip()
        ]
        try:
            campaign = marketing.create_campaign(
                business=business,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                region=region,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
                channels=channels,
                objective=objective,
                contact_text=contact_text,
                payload=payload,
            )
            st.session_state["marketing_notice"] = (
                f"광고 작업본 생성 완료 · {source_name} · {str(campaign.get('id', ''))[:8]}"
            )
            st.rerun()
        except Exception as exc:
            st.error(f"광고 작업 생성 실패: {exc}")

    notice = st.session_state.pop("marketing_notice", None)
    if notice:
        st.success(notice)

    st.markdown("#### 광고 작업 현황")
    try:
        campaigns = marketing.list_campaigns(80)
    except Exception as exc:
        st.error(f"광고관리 DB를 불러오지 못했습니다: {exc}")
        return

    if not campaigns:
        st.info("아직 생성된 광고 작업이 없습니다.")
        return

    rows = []
    for campaign in campaigns:
        rows.append({
            "생성": str(campaign.get("created_at") or "")[:16].replace("T", " "),
            "사업": marketing.BUSINESS_LABEL.get(campaign.get("business"), campaign.get("business")),
            "소재": campaign.get("source_name", ""),
            "핵심 검색어": campaign.get("primary_keyword", ""),
            "채널": ", ".join(marketing.channel_label(c) for c in (campaign.get("channels") or [])),
            "상태": campaign.get("status", ""),
            "ID": str(campaign.get("id", ""))[:8],
        })
    st.dataframe(rows, hide_index=True, use_container_width=True)

    campaign_map = {
        f"{c.get('source_name', '')} · {str(c.get('id', ''))[:8]}": c
        for c in campaigns
    }
    selected_label = st.selectbox(
        "작업 상세 보기",
        list(campaign_map.keys()),
        key="marketing_campaign_select",
    )
    selected_campaign = campaign_map[selected_label]
    campaign_id = selected_campaign["id"]

    status_col, action_col = st.columns([3, 1])
    with status_col:
        campaign_status = st.selectbox(
            "캠페인 상태",
            ["draft", "ready", "published", "archived"],
            index=["draft", "ready", "published", "archived"].index(
                selected_campaign.get("status")
                if selected_campaign.get("status") in {"draft", "ready", "published", "archived"}
                else "draft"
            ),
            format_func=lambda x: {
                "draft": "작성중",
                "ready": "게시 준비",
                "published": "게시 완료",
                "archived": "보관",
            }[x],
            key=f"marketing_campaign_status_{campaign_id}",
        )
    with action_col:
        st.write("")
        st.write("")
        if st.button("상태 저장", key=f"marketing_campaign_save_{campaign_id}", use_container_width=True):
            try:
                marketing.update_campaign_status(campaign_id, campaign_status)
                st.success("캠페인 상태를 저장했습니다.")
            except Exception as exc:
                st.error(str(exc))

    try:
        posts = marketing.list_posts(campaign_id)
    except Exception as exc:
        st.error(f"채널 작업본 조회 실패: {exc}")
        return

    for post in posts:
        channel = post.get("channel", "")
        label = marketing.channel_label(channel)
        with st.expander(f"{label} · {post.get('status', 'draft')}", expanded=True):
            st.caption(marketing.channel_note(channel))
            st.text_input(
                "제목",
                value=str(post.get("title") or ""),
                key=f"marketing_title_{post['id']}",
                disabled=True,
            )
            st.text_area(
                "본문",
                value=str(post.get("body") or ""),
                key=f"marketing_body_{post['id']}",
                height=220,
                disabled=True,
            )
            hashtags = " ".join("#" + str(tag) for tag in (post.get("hashtags") or []))
            if hashtags:
                st.text_area(
                    "해시태그",
                    value=hashtags,
                    key=f"marketing_tags_{post['id']}",
                    height=80,
                    disabled=True,
                )

            p1, p2 = st.columns([2, 3])
            with p1:
                post_status = st.selectbox(
                    "게시 상태",
                    ["draft", "ready", "published", "error"],
                    index=["draft", "ready", "published", "error"].index(
                        post.get("status")
                        if post.get("status") in {"draft", "ready", "published", "error"}
                        else "draft"
                    ),
                    format_func=lambda x: {
                        "draft": "작업본",
                        "ready": "게시 준비",
                        "published": "게시 완료",
                        "error": "오류",
                    }[x],
                    key=f"marketing_post_status_{post['id']}",
                )
            with p2:
                publish_url = st.text_input(
                    "실제 게시 링크",
                    value=str(post.get("publish_url") or ""),
                    key=f"marketing_post_url_{post['id']}",
                    placeholder="https://... 실제로 올라간 글 주소",
                    help="게시 완료 상태는 실제 게시 링크가 있어야 저장됩니다.",
                )

            verification_status = str(post.get("verification_status") or "unchecked")
            verification_label = {
                "unchecked": "미확인",
                "verified": "접속 확인",
                "blocked": "자동 확인 제한",
                "failed": "확인 실패",
            }.get(verification_status, verification_status)
            verify_meta = []
            if post.get("http_status"):
                verify_meta.append("HTTP " + str(post.get("http_status")))
            if post.get("last_checked_at"):
                verify_meta.append("확인 " + str(post.get("last_checked_at"))[:16].replace("T", " "))
            st.caption("게시 링크 상태: " + verification_label + ((" · " + " · ".join(verify_meta)) if verify_meta else ""))

            action1, action2, action3 = st.columns([2, 2, 2])
            with action1:
                if st.button(
                    f"{label} 상태 저장",
                    key=f"marketing_post_save_{post['id']}",
                    use_container_width=True,
                ):
                    try:
                        marketing.update_post(
                            post["id"],
                            status=post_status,
                            publish_url=publish_url,
                        )
                        st.session_state["marketing_notice"] = f"{label} 상태를 저장했습니다."
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with action2:
                if st.button(
                    "게시 링크 확인",
                    key=f"marketing_post_verify_{post['id']}",
                    use_container_width=True,
                    disabled=not bool(publish_url.strip()),
                ):
                    try:
                        result = marketing.verify_post_url(post["id"], publish_url)
                        st.session_state["marketing_notice"] = result["message"]
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with action3:
                if publish_url.strip():
                    st.link_button(
                        "실제 게시글 열기",
                        publish_url.strip(),
                        use_container_width=True,
                    )

            if channel == "naver_blog":
                naver_share = marketing.naver_share_url(selected_campaign, post)
                st.link_button(
                    "네이버 공식 블로그 공유창 열기",
                    naver_share,
                    use_container_width=True,
                )
                st.caption(
                    "네이버 공식 공유창에서 내용을 확인해 게시한 뒤, 최종 블로그 글 주소를 "
                    "위 '실제 게시 링크'에 붙여 넣으면 게시 여부를 추적할 수 있습니다."
                )

            if verification_status == "verified":
                st.success("실제 게시 링크에 접속 가능한 상태입니다.")
            elif verification_status == "blocked":
                st.warning("플랫폼이 자동 접속 확인을 막고 있습니다. '실제 게시글 열기'로 직접 확인해 주세요.")
            elif verification_status == "failed" and publish_url.strip():
                st.error("저장된 게시 링크가 현재 정상 응답하지 않습니다.")

    st.markdown("---")
    delete_confirm = st.checkbox(
        "이 광고 작업 삭제 확인",
        key=f"marketing_delete_confirm_{campaign_id}",
    )
    if st.button(
        "선택한 광고 작업 삭제",
        key=f"marketing_delete_{campaign_id}",
        disabled=not delete_confirm,
    ):
        try:
            marketing.delete_campaign(campaign_id)
            st.session_state["marketing_notice"] = "광고 작업을 삭제했습니다."
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def render_admin():
    if not admin_login():
        return

    st.caption("적용 버전: TWOJROAD-20260919-MKT3")
    top1, top2 = st.columns(
        [5, 1]
    )

    with top1:
        st.success(
            f"관리자 로그인 상태 · 저장 위치: {PRODUCT_FILE}"
        )

    with top2:
        if st.button(
            "로그아웃",
            use_container_width=True
        ):
            st.session_state[
                "admin_logged_in"
            ] = False

            st.rerun()

    naver_notice = st.session_state.get("naver_action_notice")
    if naver_notice:
        st.error(naver_notice)
        if st.button("네이버 안내 닫기", key="dismiss_naver_notice"):
            st.session_state.pop("naver_action_notice", None)
            st.rerun()

    notice = st.session_state.get("product_action_notice")
    if notice:
        notice_area, dismiss_area = st.columns([5, 1])
        with dismiss_area:
            dismiss_notice = st.button("확인", key="dismiss_product_notice")
        if dismiss_notice:
            st.session_state.pop("product_action_notice", None)
        else:
            with notice_area:
                st.success(notice)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "상품 등록",
            "상품 수정 · 삭제",
            "사이트 현황",
            "광고 · 노출 자동화",
        ]
    )

    with tab1:
        render_add_product()

    with tab2:
        render_manage_products()
    with tab3:
        render_site_status()
    with tab4:
        render_marketing_center()


def render_offline_store():
    from urllib.parse import quote

    st.subheader("오프라인매장")
    banner = banner_image_src()
    if banner:
        safe_markdown(
            f'<img src="{escape(banner, quote=True)}" alt="TWO J ROAD 매장 전경" '
            'style="display:block;width:100%;height:auto;margin-bottom:24px;">',
            unsafe_allow_html=True
        )
    st.write(STORE_NAME)
    st.write(STORE_ADDRESS)
    map_url = "https://map.naver.com/p/search/" + quote(STORE_ADDRESS, safe="")
    safe_markdown(
        f'<a class="contact-btn primary" href="{escape(map_url, quote=True)}" '
        'target="_blank" rel="noopener noreferrer">네이버 지도에서 위치 보기</a>',
        unsafe_allow_html=True
    )
    if MASPICK_PHONE:
        st.write("매장 문의: " + MASPICK_PHONE)


# =========================================================
# ROUTER
# =========================================================

page = get_param(
    "page",
    "home"
)

if page == "shop":
    render_shop()

elif page == "detail":
    render_home()

elif page == "admin":
    render_admin()

elif page == "store":
    render_offline_store()

else:
    render_home()

if page != "admin":
    render_popup_triggers()

_popup_product_id = get_param("detail", "") or (get_param("id", "") if page == "detail" else "")
if _popup_product_id and page != "admin":
    render_product_popup(_popup_product_id)


# =========================================================
# FOOTER
# =========================================================

BIZ_NAME = "투제이-로드(2J-ROAD)"
BIZ_OWNER = "전선옥"
BIZ_REG_NO = "505-48-00676"
BIZ_ADDRESS = "경기도 포천시 내촌면 금강로3224번길 11-7, 다동 1층"
BIZ_MAIL_ORDER_NO = os.getenv("MASPICK_MAIL_ORDER_NO", "").strip() or "2024-경기포천-0754"
_biz_check_url = "https://www.ftc.go.kr/bizCommPop.do?wrkr_no=" + BIZ_REG_NO.replace("-", "")
_biz_phone = f" · 전화 {escape(MASPICK_PHONE)}" if MASPICK_PHONE else ""
_biz_mail_order = f" · 통신판매업신고 {escape(BIZ_MAIL_ORDER_NO)}" if BIZ_MAIL_ORDER_NO else ""

safe_markdown(
    f"""
    <div
        class="footer-block"
        translate="no"
    >
        <b>{escape(BIZ_NAME)}</b><br>
        대표 {escape(BIZ_OWNER)} · 사업자등록번호 {escape(BIZ_REG_NO)}
        (<a href="{escape(_biz_check_url, quote=True)}" target="_blank" rel="noopener noreferrer">사업자정보확인</a>){_biz_mail_order}<br>
        {escape(BIZ_ADDRESS)}{_biz_phone}<br>
        <a href="/terms" target="_self">이용약관</a> ·
        <a href="/privacy" target="_self"><b>개인정보처리방침</b></a> ·
        <a href="/refund" target="_self">교환·환불 안내</a><br>

        중고 오토바이 · 바이크 의류 · 헬멧 · 라이딩 용품<br>

        경기 포천 · 바이크 매물 및 상품 문의
        <br><br>

        © TWO J ROAD. 모든 권리 보유.<br>

        <a href="/catalog/bike" target="_self">중고 바이크</a> ·
        <a href="/catalog/wear" target="_self">바이크 의류</a> ·
        <a href="/catalog/gear" target="_self">바이크 용품</a> ·
        <a href="/sitemap.xml" target="_self">사이트맵</a>
    </div>
    """,
    unsafe_allow_html=True
)
