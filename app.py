import streamlit as st
from html import escape

st.set_page_config(
    page_title="MASPICK | Motorcycle Store",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 상품 데이터
# 현재는 화면 제작용 샘플 데이터
# 이후 관리자 상품등록/DB로 교체
# =========================================================

PRODUCTS = [
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
        "description": "장거리 투어링과 일상 주행을 모두 만족시키는 프리미엄 투어링 모델입니다.",
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
        "description": "강한 존재감과 클래식한 실루엣이 특징인 크루저 모델입니다.",
    },
    {
        "id": "bike-003",
        "type": "bike",
        "category": "중고 바이크",
        "subcategory": "크루저",
        "brand": "BMW MOTORRAD",
        "name": "R 18",
        "price": 22900000,
        "year": "2022",
        "mileage": "9,800km",
        "cc": "1,802cc",
        "condition": "판매중",
        "region": "경기 포천",
        "accident": "상담문의",
        "badge": "신규",
        "image": "https://images.unsplash.com/photo-1524591652733-73fa1ae7b5ee?auto=format&fit=crop&w=1200&q=85",
        "description": "BMW의 대배기량 박서 엔진을 탑재한 클래식 크루저입니다.",
    },
    {
        "id": "bike-004",
        "type": "bike",
        "category": "중고 바이크",
        "subcategory": "크루저",
        "brand": "INDIAN",
        "name": "Scout Bobber",
        "price": 17800000,
        "year": "2021",
        "mileage": "14,100km",
        "cc": "1,133cc",
        "condition": "판매중",
        "region": "경기 포천",
        "accident": "상담문의",
        "badge": "인기",
        "image": "https://images.unsplash.com/photo-1599819811279-d5ad9cccf838?auto=format&fit=crop&w=1200&q=85",
        "description": "낮은 차체와 강한 스타일을 갖춘 아메리칸 크루저입니다.",
    },
    {
        "id": "wear-001",
        "type": "wear",
        "category": "바이크 의류",
        "subcategory": "재킷",
        "brand": "HARLEY-DAVIDSON",
        "name": "라이딩 레더 재킷",
        "price": 489000,
        "condition": "판매중",
        "badge": "BEST",
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=1200&q=85",
        "description": "바이크 라이딩에 어울리는 클래식 레더 재킷입니다.",
    },
    {
        "id": "wear-002",
        "type": "wear",
        "category": "바이크 의류",
        "subcategory": "셔츠",
        "brand": "MASPICK",
        "name": "라이더 워크 셔츠",
        "price": 89000,
        "condition": "판매중",
        "badge": "NEW",
        "image": "https://images.unsplash.com/photo-1603252109303-2751441dd157?auto=format&fit=crop&w=1200&q=85",
        "description": "라이딩과 일상에서 모두 활용하기 좋은 워크 셔츠입니다.",
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
        "description": "클래식 바이크 스타일과 잘 어울리는 오픈페이스 헬멧입니다.",
    },
    {
        "id": "gear-002",
        "type": "gear",
        "category": "바이크 용품",
        "subcategory": "장갑",
        "brand": "MASPICK",
        "name": "프리미엄 라이딩 글러브",
        "price": 79000,
        "condition": "판매중",
        "badge": "NEW",
        "image": "https://images.unsplash.com/photo-1609630875171-b1321377ee65?auto=format&fit=crop&w=1200&q=85",
        "description": "그립감과 착용감을 고려한 라이딩 글러브입니다.",
    },
]

CATEGORY_MAP = {
    "전체상품": None,
    "중고 바이크": "중고 바이크",
    "바이크 의류": "바이크 의류",
    "바이크 용품": "바이크 용품",
}


# =========================================================
# 공통 함수
# =========================================================

def money(value):
    return f"{int(value):,}원"


def get_param(name, default=""):
    try:
        return st.query_params.get(name, default)
    except Exception:
        return default


def product_by_id(product_id):
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    return None


# =========================================================
# CSS
# =========================================================

st.markdown("""
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
        radial-gradient(circle at top, #171717 0, #080808 520px);
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

.topline {
    min-height:34px;
    border-bottom:1px solid #222;
    display:flex;
    align-items:center;
    justify-content:flex-end;
    gap:20px;
    font-size:11px;
    color:#777;
}

.header {
    display:grid;
    grid-template-columns:260px 1fr 260px;
    align-items:center;
    min-height:100px;
    border-bottom:1px solid #242424;
    gap:28px;
}

.logo {
    color:white;
    font-size:38px;
    font-weight:1000;
    letter-spacing:-2.5px;
}

.logo span {
    color:#ff6900;
}

.logo-small {
    color:#696969;
    letter-spacing:4px;
    font-size:8px;
    margin-top:-4px;
}

.fake-search {
    height:48px;
    border:1px solid #383838;
    background:#101010;
    max-width:650px;
    margin:auto;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 17px;
    width:100%;
    color:#737373;
    font-size:13px;
}

.header-right {
    text-align:right;
    color:#aaa;
    font-size:12px;
    word-spacing:15px;
}

.navbar {
    min-height:62px;
    display:flex;
    justify-content:center;
    align-items:center;
    gap:46px;
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

.navbar .sale {
    color:#ff6900;
}

.hero {
    height:410px;
    margin-top:26px;
    border:1px solid #222;
    background:
        linear-gradient(
            90deg,
            rgba(0,0,0,.97) 0%,
            rgba(0,0,0,.82) 38%,
            rgba(0,0,0,.22) 100%
        ),
        url("https://images.unsplash.com/photo-1558980394-4c7c9299fe96?auto=format&fit=crop&w=1800&q=85");
    background-size:cover;
    background-position:center;
    display:flex;
    align-items:center;
    padding:55px;
}

.hero-eyebrow {
    color:#ff6900;
    font-size:11px;
    font-weight:900;
    letter-spacing:4px;
}

.hero-title {
    color:#fff;
    font-size:56px;
    font-weight:1000;
    line-height:1.02;
    letter-spacing:-3px;
    margin-top:12px;
}

.hero-copy {
    color:#999;
    font-size:15px;
    margin-top:18px;
    line-height:1.8;
}

.hero-btn {
    display:inline-block;
    margin-top:25px;
    background:#ff6900;
    color:white !important;
    padding:14px 24px;
    font-size:12px;
    font-weight:900;
}

.home-section-title {
    margin-top:48px;
    margin-bottom:18px;
    font-size:24px;
    font-weight:1000;
    border-bottom:1px solid #292929;
    padding-bottom:13px;
}

.shop-layout {
    display:grid;
    grid-template-columns:220px minmax(0,1fr);
    gap:34px;
    margin-top:35px;
}

.side-menu {
    border-top:2px solid #f1f1f1;
}

.side-title {
    font-size:18px;
    font-weight:1000;
    padding:20px 5px 15px;
    border-bottom:1px solid #333;
}

.side-menu a {
    display:block;
    padding:14px 8px;
    border-bottom:1px solid #232323;
    color:#9b9b9b;
    font-size:13px;
}

.side-menu a:hover {
    color:#fff;
    padding-left:13px;
}

.shop-title {
    font-size:27px;
    font-weight:1000;
    margin-bottom:7px;
}

.breadcrumb {
    font-size:11px;
    color:#666;
    margin-bottom:28px;
}

.result-top {
    display:flex;
    justify-content:space-between;
    align-items:center;
    border-top:1px solid #333;
    border-bottom:1px solid #333;
    min-height:54px;
    margin-bottom:22px;
}

.result-count {
    font-size:12px;
    color:#888;
}

.result-count b {
    color:#ff6900;
}

.grid {
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:16px;
}

.card {
    border:1px solid #202020;
    background:#0d0d0d;
    transition:.2s;
    min-width:0;
}

.card:hover {
    border-color:#555;
    transform:translateY(-3px);
}

.card-imgbox {
    position:relative;
    width:100%;
    aspect-ratio:1 / 1;
    overflow:hidden;
    background:#151515;
}

.card-img {
    width:100%;
    height:100%;
    object-fit:cover;
}

.badge {
    position:absolute;
    left:11px;
    top:11px;
    padding:6px 9px;
    background:#ff6900;
    color:#fff;
    font-size:9px;
    font-weight:900;
}

.card-body {
    padding:14px 14px 18px;
}

.card-brand {
    font-size:9px;
    color:#777;
    font-weight:900;
    letter-spacing:1px;
}

.card-name {
    color:#eee;
    font-weight:900;
    font-size:14px;
    margin-top:7px;
    overflow:hidden;
    text-overflow:ellipsis;
    white-space:nowrap;
}

.card-info {
    font-size:11px;
    color:#777;
    margin-top:7px;
    min-height:17px;
}

.card-price {
    margin-top:15px;
    color:#fff;
    font-size:18px;
    font-weight:1000;
}

.detail-wrap {
    margin-top:38px;
}

.detail-grid {
    display:grid;
    grid-template-columns:minmax(0,1.15fr) minmax(340px,.85fr);
    gap:42px;
}

.detail-photo {
    width:100%;
    max-height:650px;
    object-fit:cover;
    background:#111;
    border:1px solid #252525;
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

.detail-desc {
    margin-top:25px;
    line-height:1.8;
    font-size:13px;
    color:#999;
}

.contact-box {
    margin-top:22px;
    border:1px solid #333;
    background:#111;
    padding:18px;
}

.contact-title {
    color:#fff;
    font-weight:900;
}

.contact-text {
    color:#888;
    font-size:12px;
    margin-top:6px;
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

div[data-testid="stTextInput"] input {
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
    width:100%;
    border-radius:0 !important;
    background:#ff6900 !important;
    color:#fff !important;
    border:0 !important;
    font-weight:900 !important;
}

@media(max-width:1100px) {

    .header {
        grid-template-columns:1fr;
        padding:18px 0;
        gap:12px;
        text-align:center;
    }

    .header-right {
        display:none;
    }

    .logo-small {
        text-align:center;
    }

    .shop-layout {
        grid-template-columns:1fr;
    }

    .side-menu {
        display:none;
    }

    .grid {
        grid-template-columns:repeat(2,minmax(0,1fr));
    }

    .detail-grid {
        grid-template-columns:1fr;
    }
}

@media(max-width:600px) {

    .block-container {
        padding-left:12px !important;
        padding-right:12px !important;
    }

    .topline {
        display:none;
    }

    .logo {
        font-size:31px;
    }

    .navbar {
        justify-content:flex-start;
        gap:25px;
        min-height:53px;
    }

    .hero {
        height:330px;
        padding:28px 22px;
    }

    .hero-title {
        font-size:39px;
    }

    .hero-copy {
        font-size:12px;
    }

    .grid {
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:8px;
    }

    .card-body {
        padding:10px;
    }

    .card-name {
        font-size:12px;
    }

    .card-price {
        font-size:15px;
    }

    .detail-name {
        font-size:28px;
    }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 헤더
# =========================================================

st.markdown("""
<div class="topline">
    <span>LOGIN</span>
    <span>JOIN</span>
    <span>ORDER</span>
    <span>MY PAGE</span>
    <span>CART 0</span>
</div>

<div class="header">

    <div>
        <a href="?page=home">
            <div class="logo"><span>M</span>ASPICK</div>
            <div class="logo-small">MOTORCYCLE CULTURE</div>
        </a>
    </div>

    <div class="fake-search">
        <span>바이크, 의류, 용품 검색</span>
        <span>⌕</span>
    </div>

    <div class="header-right">
        ♡ WISH &nbsp; ◎ MY &nbsp; ▣ CART
    </div>

</div>

<div class="navbar">
    <a href="?page=shop&cat=중고 바이크">중고 바이크</a>
    <a href="?page=shop&cat=바이크 의류">바이크 의류</a>
    <a href="?page=shop&cat=바이크 용품">바이크 용품</a>
    <a href="?page=shop&cat=전체상품">전체상품</a>
    <a href="?page=shop&cat=신상품">신상품</a>
    <a class="sale" href="?page=shop&cat=SALE">SALE</a>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 상품 카드
# =========================================================

def card_html(product):
    info = ""

    if product["type"] == "bike":
        info = (
            f"{escape(product.get('year',''))} · "
            f"{escape(product.get('mileage',''))} · "
            f"{escape(product.get('cc',''))}"
        )
    else:
        info = escape(product.get("subcategory", ""))

    return f"""
    <a href="?page=detail&id={escape(product['id'])}">
        <div class="card">
            <div class="card-imgbox">
                <img class="card-img" src="{escape(product['image'])}">
                <div class="badge">{escape(product['badge'])}</div>
            </div>

            <div class="card-body">
                <div class="card-brand">{escape(product['brand'])}</div>
                <div class="card-name">{escape(product['name'])}</div>
                <div class="card-info">{info}</div>
                <div class="card-price">{money(product['price'])}</div>
            </div>
        </div>
    </a>
    """


def render_grid(products):
    if not products:
        st.info("현재 조건에 맞는 상품이 없습니다.")
        return

    html = '<div class="grid">'
    for product in products:
        html += card_html(product)
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# HOME
# =========================================================

def render_home():

    st.markdown("""
    <div class="hero">
        <div>
            <div class="hero-eyebrow">MASPICK MOTORCYCLE STORE</div>

            <div class="hero-title">
                RIDE YOUR<br>
                OWN WAY.
            </div>

            <div class="hero-copy">
                중고 바이크부터 라이딩 의류와 바이크 용품까지.<br>
                라이더를 위한 모든 것을 한 곳에서.
            </div>

            <a class="hero-btn" href="?page=shop&cat=중고 바이크">
                중고 바이크 보기 →
            </a>
        </div>
    </div>

    <div class="home-section-title">
        USED MOTORCYCLE
    </div>
    """, unsafe_allow_html=True)

    render_grid([p for p in PRODUCTS if p["type"] == "bike"])

    st.markdown("""
    <div class="home-section-title">
        RIDING WEAR & GEAR
    </div>
    """, unsafe_allow_html=True)

    render_grid([p for p in PRODUCTS if p["type"] != "bike"])


# =========================================================
# SHOP
# =========================================================

def render_shop():

    requested = get_param("cat", "전체상품")

    if requested in ("신상품", "SALE"):
        requested = "전체상품"

    selected_category = CATEGORY_MAP.get(requested)

    if selected_category:
        products = [
            p for p in PRODUCTS
            if p["category"] == selected_category
        ]
    else:
        products = PRODUCTS.copy()

    st.markdown('<div class="shop-layout">', unsafe_allow_html=True)

    left, right = st.columns([1, 4], gap="large")

    with left:

        st.markdown("""
        <div class="side-menu">

            <div class="side-title">
                CATEGORY
            </div>

            <a href="?page=shop&cat=전체상품">
                전체상품
            </a>

            <a href="?page=shop&cat=중고 바이크">
                중고 바이크
            </a>

            <a href="?page=shop&cat=바이크 의류">
                바이크 의류
            </a>

            <a href="?page=shop&cat=바이크 용품">
                바이크 용품
            </a>

            <a href="?page=shop&cat=중고 바이크">
                └ 투어링
            </a>

            <a href="?page=shop&cat=중고 바이크">
                └ 크루저
            </a>

            <a href="?page=shop&cat=바이크 의류">
                └ 재킷
            </a>

            <a href="?page=shop&cat=바이크 의류">
                └ 셔츠
            </a>

            <a href="?page=shop&cat=바이크 용품">
                └ 헬멧
            </a>

            <a href="?page=shop&cat=바이크 용품">
                └ 장갑
            </a>

        </div>
        """, unsafe_allow_html=True)

    with right:

        st.markdown(
            f"""
            <div class="shop-title">
                {escape(requested)}
            </div>

            <div class="breadcrumb">
                HOME &nbsp;›&nbsp; SHOP &nbsp;›&nbsp;
                {escape(requested)}
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2 = st.columns([3,1])

        with c1:
            keyword = st.text_input(
                "상품 검색",
                placeholder="상품명 또는 브랜드 검색",
                label_visibility="collapsed",
            )

        with c2:
            sort = st.selectbox(
                "정렬",
                ["최신순", "낮은 가격순", "높은 가격순"],
                label_visibility="collapsed",
            )

        if keyword:
            k = keyword.lower().strip()
            products = [
                p for p in products
                if k in p["name"].lower()
                or k in p["brand"].lower()
                or k in p["subcategory"].lower()
            ]

        if sort == "낮은 가격순":
            products.sort(key=lambda x: x["price"])
        elif sort == "높은 가격순":
            products.sort(key=lambda x: x["price"], reverse=True)
        else:
            products = list(reversed(products))

        st.markdown(
            f"""
            <div class="result-top">
                <div class="result-count">
                    총 <b>{len(products)}</b>개의 상품이 있습니다.
                </div>
                <div class="result-count">
                    MASPICK STORE
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        render_grid(products)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# DETAIL
# =========================================================

def render_detail():

    product_id = get_param("id", "")
    product = product_by_id(product_id)

    if not product:
        st.error("상품을 찾을 수 없습니다.")
        st.markdown(
            '<a class="hero-btn" href="?page=home">메인으로 돌아가기</a>',
            unsafe_allow_html=True
        )
        return

    st.markdown('<div class="detail-wrap">', unsafe_allow_html=True)

    left, right = st.columns([1.15, .85], gap="large")

    with left:

        st.markdown(
            f"""
            <img
                class="detail-photo"
                src="{escape(product['image'])}"
            >
            """,
            unsafe_allow_html=True
        )

    with right:

        st.markdown(
            f"""
            <div class="detail-brand">
                {escape(product['brand'])}
            </div>

            <div class="detail-name">
                {escape(product['name'])}
            </div>

            <div class="detail-price">
                {money(product['price'])}
            </div>
            """,
            unsafe_allow_html=True
        )

        if product["type"] == "bike":

            specs = [
                ("차량상태", product.get("condition","")),
                ("연식", product.get("year","")),
                ("주행거리", product.get("mileage","")),
                ("배기량", product.get("cc","")),
                ("지역", product.get("region","")),
                ("사고유무", product.get("accident","")),
            ]

        else:

            specs = [
                ("상품구분", product.get("category","")),
                ("카테고리", product.get("subcategory","")),
                ("브랜드", product.get("brand","")),
                ("판매상태", product.get("condition","")),
            ]

        spec_html = ""

        for label, value in specs:
            spec_html += f"""
            <div class="spec-row">
                <div class="spec-label">
                    {escape(str(label))}
                </div>

                <div class="spec-value">
                    {escape(str(value))}
                </div>
            </div>
            """

        st.markdown(spec_html, unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="detail-desc">
                {escape(product.get('description',''))}
            </div>

            <div class="contact-box">
                <div class="contact-title">
                    구매 및 차량 문의
                </div>

                <div class="contact-text">
                    중고 바이크는 차량 상태와 옵션을 확인한 뒤
                    상담을 통해 판매를 진행합니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("구매 · 상담 문의", key=f"contact_{product['id']}"):
            st.success("문의 기능은 다음 단계에서 카카오톡 또는 전화 연결로 설정합니다.")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# ROUTER
# =========================================================

page = get_param("page", "home")

if page == "shop":
    render_shop()

elif page == "detail":
    render_detail()

else:
    render_home()


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer-block">

    MASPICK MOTORCYCLE STORE<br>

    USED MOTORCYCLE · RIDING WEAR · PARTS & GEAR<br>

    경기 포천 · 바이크 매물 및 상품 문의<br><br>

    © MASPICK. ALL RIGHTS RESERVED.

</div>
""", unsafe_allow_html=True)