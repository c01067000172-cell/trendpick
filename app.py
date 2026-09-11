import streamlit as st
import os
import json
import uuid
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
    <a href="?page=detail&id={escape(str(product.get('id','')))}">
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


def pack_detail(text, files):
    if not files:
        return text
    return DETAIL_PREFIX + json.dumps({"text": text, "files": files}, ensure_ascii=False)


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

        uploaded_images = st.file_uploader(
            "상품 사진 직접 업로드",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            accept_multiple_files=True,
            help="최대 8장까지 등록할 수 있습니다.",
            key="add_uploaded_images"
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

    if st.button(
        "상품 등록하기",
        use_container_width=True
    ):
        if not name.strip():
            st.error(
                "상품명을 입력해 주세요."
            )
            return

        if len(uploaded_images or []) > 8:
            st.error(
                "상품 사진은 최대 8장까지 등록할 수 있습니다."
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
            "description": pack_detail(description.strip(), saved_detail_files),
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

        st.session_state["product_action_notice"] = (
            f"상품 등록 완료 · {new_product['name']}"
        )

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

    if current_images:
        st.caption(
            f"현재 등록 사진: {len(current_images)}장"
        )

    replacement_images = st.file_uploader(
        "새 사진으로 전체 교체",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        accept_multiple_files=True,
        help="새 사진을 선택하면 기존 사진 전체가 교체됩니다.",
        key=f"edit_uploaded_images_{selected_id}"
    )

    edit_image = st.text_input(
        "또는 대표 이미지 URL",
        value=(
            str(current_images[0])
            if current_images
            else ""
        ),
        key=f"edit_image_{selected_id}"
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
            product["brand"] = edit_brand.strip()
            product["name"] = edit_name.strip()
            product["price"] = int(edit_price)
            product["subcategory"] = edit_subcategory.strip()
            product["condition"] = edit_condition
            product["badge"] = edit_badge

            if replacement_images:
                if len(replacement_images) > 8:
                    st.error(
                        "상품 사진은 최대 8장까지 등록할 수 있습니다."
                    )
                    return

                delete_local_images(
                    product
                )

                updated_images = save_uploaded_images(
                    replacement_images,
                    product.get(
                        "id",
                        uuid.uuid4().hex[:12]
                    )
                )

                product["images"] = updated_images
                product["image"] = (
                    updated_images[0]
                    if updated_images
                    else ""
                )

            elif edit_image.strip():
                if (
                    not current_images
                    or
                    edit_image.strip()
                    != str(current_images[0])
                ):
                    product["images"] = [
                        edit_image.strip()
                    ]

                    product["image"] = (
                        edit_image.strip()
                    )

            detail_files = [] if remove_detail_files else current_detail_files
            if replacement_detail_files:
                try:
                    detail_files = upload_detail_files(replacement_detail_files, str(selected_id))
                except Exception:
                    st.error("상세 첨부파일 저장에 실패했습니다. 파일 수·크기와 저장소 연결을 확인해 주세요.")
                    return
            if replacement_detail_files or remove_detail_files:
                delete_local_images({"images": [item["url"] for item in current_detail_files]})
            product["description"] = pack_detail(edit_description.strip(), detail_files)

            for key, value in bike_values.items():
                product[key] = value.strip()

            product["demo"] = False

            save_products(
                PRODUCTS
            )

            st.session_state["product_action_notice"] = (
                f"상품 수정 완료 · {product.get('name', '')}"
            )

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
    render_detail()

elif page == "admin":
    render_admin()

elif page == "store":
    render_offline_store()

else:
    render_home()


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

        <a href="/catalog/wear" target="_self">상품 안내</a> ·
        <a href="/app/static/sitemap.xml">
            사이트맵
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
