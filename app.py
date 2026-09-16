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
            "바이크 용품 | 헬멧·장갑·라이딩 기어 | 포천 TWO J ROAD",
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
        photos.append(
            f'<div class="pg-slide s-{index}"><img src="{esc_src}" '
            f'alt="{escape(name, quote=True)} 사진 {index + 1}">'
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
        ".pp-size th{background:#1b1b1b;padding:7px 4px;font-weight:700}"
        ".pp-size td{border-bottom:1px solid #262626;padding:7px 4px}</style>"
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
        "<style>.pp-fabric{width:100%;border-collapse:collapse;font-size:14px;border-top:1px solid #555}"
        ".pp-fabric th{text-align:left;padding:14px 8px;width:28%;font-weight:700}"
        ".pp-fabric td{padding:14px 8px;color:#6b6f7a}"
        ".pp-fabric td.on{color:#fff;font-weight:700}"
        ".pp-fabric tr{border-bottom:1px solid #2a2a2a}</style>"
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

        if features:
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


def render_image_order_editor(key, entries, allow_remove=False):
    """사진 미리보기 + 순서 변경(◀ ▶ ★) + 삭제(✕). 정렬된 항목 목록을 돌려줍니다."""
    by_id = {e["id"]: e for e in entries}
    state = st.session_state.get(key) or {"order": [], "removed": []}
    removed = [i for i in state["removed"] if i in by_id]
    order = [i for i in state["order"] if i in by_id and i not in removed]
    order += [e["id"] for e in entries if e["id"] not in order and e["id"] not in removed]
    st.session_state[key] = {"order": order, "removed": removed}
    if not order:
        return []

    st.caption("첫 번째 사진이 대표 사진입니다. ◀ ▶ 로 순서를 바꾸고, ★ 를 누르면 맨 앞으로 옮깁니다.")
    per_row = 5
    action = None
    for row_start in range(0, len(order), per_row):
        cols = st.columns(per_row)
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
                buttons = st.columns(4 if allow_remove else 3, gap="small")
                if buttons[0].button("◀", key=f"{key}_l_{item_id}", disabled=idx == 0, help="앞으로"):
                    action = ("move", idx, idx - 1)
                if buttons[1].button("▶", key=f"{key}_r_{item_id}", disabled=idx == len(order) - 1, help="뒤로"):
                    action = ("move", idx, idx + 1)
                if buttons[2].button("★", key=f"{key}_f_{item_id}", disabled=idx == 0, help="대표 사진으로"):
                    action = ("first", idx, 0)
                if allow_remove and buttons[3].button("✕", key=f"{key}_x_{item_id}", help="이 사진 빼기"):
                    action = ("remove", idx, None)
    if action:
        kind, a, b = action
        if kind == "move":
            order[a], order[b] = order[b], order[a]
        elif kind == "first":
            order.insert(0, order.pop(a))
        elif kind == "remove":
            removed.append(order.pop(a))
        st.session_state[key] = {"order": order, "removed": removed}
        st.rerun()
    return [by_id[i] for i in order]


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

    st.markdown("#### 사진 순서 · 미리보기")
    add_image_entries = render_image_order_editor(
        f"add_img_order_{add_ver}",
        uploaded_image_entries(uploaded_images),
        allow_remove=True,
    )
    if not add_image_entries:
        st.caption("위에서 상품 사진을 선택하면 여기에 미리보기가 나오고 순서를 바꿀 수 있습니다.")
    uploaded_images = [e["file"] for e in add_image_entries]

    add_options_text, add_extras = "", {}
    if product_type != "중고 바이크":
        add_options_text, add_extras = render_product_extras_inputs("add_extras")

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


def render_admin():
    if not admin_login():
        return

    st.caption("적용 버전: TWOJROAD-20260911-R8")
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

    tab1, tab2, tab3 = st.tabs(
        [
            "상품 등록",
            "상품 수정 · 삭제",
            "사이트 현황",
        ]
    )

    with tab1:
        render_add_product()

    with tab2:
        render_manage_products()
    with tab3:
        render_site_status()


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

safe_markdown(
    f"""
    <div
        class="footer-block"
        translate="no"
    >
        {STORE_NAME}<br>
        {STORE_ADDRESS}<br>

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
