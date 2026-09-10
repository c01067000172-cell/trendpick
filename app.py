import streamlit as st
import os
import json
import uuid
from pathlib import Path
from html import escape

st.set_page_config(
    page_title="MASPICK | Motorcycle Store",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 저장소
# Render: /var/data/trendpick/products.json
# 로컬: ./data/products.json
# =========================================================

DATA_DIR = Path(
    os.getenv(
        "TRENDPICK_DATA_DIR",
        str(Path(__file__).parent / "data")
    )
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_FILE = DATA_DIR / "products.json"

ADMIN_PASSWORD = os.getenv("MASPICK_ADMIN_PASSWORD", "")


# =========================================================
# 최초 샘플 데이터
# 실제 상품 등록 후 관리자 페이지에서 삭제 가능
# =========================================================

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
        "subcategory": "재킷",
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


# =========================================================
# 데이터 함수
# =========================================================

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
        save_products(DEMO_PRODUCTS)
        return DEMO_PRODUCTS.copy()

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


PRODUCTS = load_products()


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

.demo {
    position:absolute;
    right:11px;
    top:11px;
    padding:6px 9px;
    background:#333;
    color:#aaa;
    font-size:9px;
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

.page-title {
    margin-top:38px;
    font-size:29px;
    font-weight:1000;
}

.page-subtitle {
    color:#777;
    font-size:12px;
    margin-top:7px;
    margin-bottom:28px;
}

.detail-photo {
    width:100%;
    max-height:650px;
    object-fit:cover;
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

.admin-box {
    border:1px solid #292929;
    background:#0e0e0e;
    padding:22px;
    margin-bottom:18px;
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

    .grid {
        grid-template-columns:repeat(2,minmax(0,1fr));
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
        ♡ WISH &nbsp;&nbsp; ◎ MY &nbsp;&nbsp; ▣ CART
    </div>

</div>

<div class="navbar">
    <a href="?page=shop&cat=중고 바이크">중고 바이크</a>
    <a href="?page=shop&cat=바이크 의류">바이크 의류</a>
    <a href="?page=shop&cat=바이크 용품">바이크 용품</a>
    <a href="?page=shop&cat=전체상품">전체상품</a>
    <a class="sale" href="?page=admin">ADMIN</a>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 상품 카드
# =========================================================

def card_html(product):

    if product.get("type") == "bike":
        info = (
            f"{escape(str(product.get('year','')))} · "
            f"{escape(str(product.get('mileage','')))} · "
            f"{escape(str(product.get('cc','')))}"
        )
    else:
        info = escape(str(product.get("subcategory", "")))

    demo_badge = ""

    if product.get("demo"):
        demo_badge = '<div class="demo">DEMO</div>'

    return f"""
    <a href="?page=detail&id={escape(str(product.get('id','')))}">
        <div class="card">

            <div class="card-imgbox">

                <img
                    class="card-img"
                    src="{escape(str(product.get('image','')))}"
                >

                <div class="badge">
                    {escape(str(product.get('badge','')))}
                </div>

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
    """


def render_grid(products):

    if not products:
        st.info("등록된 상품이 없습니다.")
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

            <div class="hero-eyebrow">
                MASPICK MOTORCYCLE STORE
            </div>

            <div class="hero-title">
                RIDE YOUR<br>
                OWN WAY.
            </div>

            <div class="hero-copy">
                중고 바이크부터 라이딩 의류와 바이크 용품까지.<br>
                라이더를 위한 모든 것을 한 곳에서.
            </div>

            <a
                class="hero-btn"
                href="?page=shop&cat=중고 바이크"
            >
                중고 바이크 보기 →
            </a>

        </div>

    </div>

    <div class="home-section-title">
        USED MOTORCYCLE
    </div>
    """, unsafe_allow_html=True)

    render_grid(
        [
            p for p in PRODUCTS
            if p.get("category") == "중고 바이크"
        ][:8]
    )

    st.markdown("""
    <div class="home-section-title">
        RIDING WEAR & GEAR
    </div>
    """, unsafe_allow_html=True)

    render_grid(
        [
            p for p in PRODUCTS
            if p.get("category") != "중고 바이크"
        ][:8]
    )


# =========================================================
# SHOP
# =========================================================

def render_shop():

    category = get_param("cat", "전체상품")

    if category == "전체상품":
        items = PRODUCTS.copy()
    else:
        items = [
            p for p in PRODUCTS
            if p.get("category") == category
        ]

    st.markdown(
        f"""
        <div class="page-title">
            {escape(category)}
        </div>

        <div class="page-subtitle">
            HOME › SHOP › {escape(category)}
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([3,1])

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

    if keyword:

        k = keyword.lower().strip()

        items = [
            p for p in items
            if (
                k in str(p.get("name","")).lower()
                or
                k in str(p.get("brand","")).lower()
                or
                k in str(p.get("subcategory","")).lower()
            )
        ]

    if sort == "낮은 가격순":

        items.sort(
            key=lambda x: int(x.get("price",0))
        )

    elif sort == "높은 가격순":

        items.sort(
            key=lambda x: int(x.get("price",0)),
            reverse=True
        )

    else:
        items = list(reversed(items))

    st.caption(
        f"총 {len(items)}개의 상품"
    )

    render_grid(items)


# =========================================================
# DETAIL
# =========================================================

def render_detail():

    product_id = get_param("id", "")

    product = get_product(
        PRODUCTS,
        product_id
    )

    if not product:

        st.error("상품을 찾을 수 없습니다.")
        return

    st.markdown(
        '<div class="page-title">PRODUCT DETAIL</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(
        [1.15, .85],
        gap="large"
    )

    with left:

        st.markdown(
            f"""
            <img
                class="detail-photo"
                src="{escape(str(product.get('image','')))}"
            >
            """,
            unsafe_allow_html=True
        )

    with right:

        st.markdown(
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
                ("상태", product.get("condition","")),
                ("연식", product.get("year","")),
                ("주행거리", product.get("mileage","")),
                ("배기량", product.get("cc","")),
                ("지역", product.get("region","")),
                ("사고유무", product.get("accident","")),
            ]

        else:

            specs = [
                ("상품구분", product.get("category","")),
                ("종류", product.get("subcategory","")),
                ("브랜드", product.get("brand","")),
                ("상태", product.get("condition","")),
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

        st.markdown(
            html,
            unsafe_allow_html=True
        )

        st.write("")
        st.write(
            product.get(
                "description",
                ""
            )
        )

        if st.button(
            "구매 · 상담 문의",
            use_container_width=True
        ):
            st.info(
                "전화/카카오톡 문의 연결은 다음 단계에서 설정합니다."
            )


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login():

    st.markdown(
        """
        <div class="page-title">
            MASPICK ADMIN
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
# 상품 등록
# =========================================================

def render_add_product():

    st.subheader("상품 등록")

    product_type = st.selectbox(
        "상품 종류",
        [
            "중고 바이크",
            "바이크 의류",
            "바이크 용품"
        ],
        key="add_type"
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

        subcategory = st.text_input(
            "세부 카테고리",
            placeholder="예: 투어링 / 재킷 / 헬멧",
            key="add_subcategory"
        )

        badge = st.text_input(
            "상품 배지",
            value="NEW",
            key="add_badge"
        )

    with c2:

        condition = st.selectbox(
            "판매상태",
            [
                "판매중",
                "예약중",
                "판매완료"
            ],
            key="add_condition"
        )

        image = st.text_input(
            "대표 이미지 URL",
            key="add_image"
        )

        description = st.text_area(
            "상품 설명",
            height=150,
            key="add_description"
        )

    year = ""
    mileage = ""
    cc = ""
    region = ""
    accident = ""

    if product_type == "중고 바이크":

        st.markdown("#### 중고 바이크 정보")

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

        if not image.strip():

            st.error(
                "대표 이미지 URL을 입력해 주세요."
            )

            return

        type_code = {
            "중고 바이크": "bike",
            "바이크 의류": "wear",
            "바이크 용품": "gear",
        }[product_type]

        new_product = {
            "id": uuid.uuid4().hex[:12],
            "type": type_code,
            "category": product_type,
            "subcategory": subcategory.strip(),
            "brand": brand.strip(),
            "name": name.strip(),
            "price": int(price),
            "condition": condition,
            "badge": badge.strip() or "NEW",
            "image": image.strip(),
            "description": description.strip(),
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

        PRODUCTS.append(new_product)

        save_products(PRODUCTS)

        st.success(
            "상품이 등록되었습니다."
        )

        st.rerun()


# =========================================================
# 상품 수정 / 삭제
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
        f"{p.get('name','상품')} | {money(p.get('price',0))} | {p.get('id','')}":
        p.get("id","")
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

    st.markdown(
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
            product.get(
                "brand",
                ""
            )
        ),
        key="edit_brand"
    )

    edit_name = st.text_input(
        "상품명",
        value=str(
            product.get(
                "name",
                ""
            )
        ),
        key="edit_name"
    )

    edit_price = st.number_input(
        "가격",
        min_value=0,
        value=int(
            product.get(
                "price",
                0
            )
        ),
        step=10000,
        key="edit_price"
    )

    edit_subcategory = st.text_input(
        "세부 카테고리",
        value=str(
            product.get(
                "subcategory",
                ""
            )
        ),
        key="edit_subcategory"
    )

    edit_condition = st.selectbox(
        "판매상태",
        [
            "판매중",
            "예약중",
            "판매완료"
        ],
        index=(
            [
                "판매중",
                "예약중",
                "판매완료"
            ].index(
                product.get(
                    "condition",
                    "판매중"
                )
            )
            if product.get(
                "condition"
            ) in [
                "판매중",
                "예약중",
                "판매완료"
            ]
            else 0
        ),
        key="edit_condition"
    )

    edit_badge = st.text_input(
        "배지",
        value=str(
            product.get(
                "badge",
                ""
            )
        ),
        key="edit_badge"
    )

    edit_image = st.text_input(
        "대표 이미지 URL",
        value=str(
            product.get(
                "image",
                ""
            )
        ),
        key="edit_image"
    )

    edit_description = st.text_area(
        "설명",
        value=str(
            product.get(
                "description",
                ""
            )
        ),
        height=140,
        key="edit_description"
    )

    bike_values = {}

    if product.get("type") == "bike":

        st.markdown(
            "#### 차량 정보"
        )

        e1, e2, e3 = st.columns(3)

        with e1:

            bike_values["year"] = st.text_input(
                "연식",
                value=str(
                    product.get(
                        "year",
                        ""
                    )
                ),
                key="edit_year"
            )

            bike_values["region"] = st.text_input(
                "지역",
                value=str(
                    product.get(
                        "region",
                        ""
                    )
                ),
                key="edit_region"
            )

        with e2:

            bike_values["mileage"] = st.text_input(
                "주행거리",
                value=str(
                    product.get(
                        "mileage",
                        ""
                    )
                ),
                key="edit_mileage"
            )

            bike_values["accident"] = st.text_input(
                "사고유무",
                value=str(
                    product.get(
                        "accident",
                        ""
                    )
                ),
                key="edit_accident"
            )

        with e3:

            bike_values["cc"] = st.text_input(
                "배기량",
                value=str(
                    product.get(
                        "cc",
                        ""
                    )
                ),
                key="edit_cc"
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
            product["badge"] = edit_badge.strip()
            product["image"] = edit_image.strip()
            product["description"] = edit_description.strip()

            for key, value in bike_values.items():
                product[key] = value.strip()

            product["demo"] = False

            save_products(PRODUCTS)

            st.success(
                "수정되었습니다."
            )

            st.rerun()

    with b2:

        confirm_delete = st.checkbox(
            "삭제 확인",
            key="delete_confirm"
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

                PRODUCTS[:] = [
                    p for p in PRODUCTS
                    if p.get("id") != selected_id
                ]

                save_products(
                    PRODUCTS
                )

                st.success(
                    "삭제되었습니다."
                )

                st.rerun()


# =========================================================
# ADMIN
# =========================================================

def render_admin():

    if not admin_login():
        return

    top1, top2 = st.columns(
        [5,1]
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

    tab1, tab2 = st.tabs(
        [
            "상품 등록",
            "상품 수정 · 삭제"
        ]
    )

    with tab1:
        render_add_product()

    with tab2:
        render_manage_products()


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