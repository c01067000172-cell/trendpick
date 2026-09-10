import streamlit as st
from urllib.parse import quote

st.set_page_config(
    page_title="MASPICK | Motorcycle & Gear",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# SAMPLE PRODUCTS
# 추후 관리자 상품등록 / DB로 교체
# =========================================================

PRODUCTS = [
    {
        "category": "중고 바이크",
        "brand": "HARLEY-DAVIDSON",
        "name": "Street Glide Special",
        "price": 31500000,
        "info": "2021년식 · 18,200km · 1,868cc",
        "badge": "추천매물",
        "image": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "중고 바이크",
        "brand": "HARLEY-DAVIDSON",
        "name": "Fat Boy 114",
        "price": 26800000,
        "info": "2020년식 · 21,400km · 1,868cc",
        "badge": "인기",
        "image": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "중고 바이크",
        "brand": "BMW MOTORRAD",
        "name": "R 18",
        "price": 22900000,
        "info": "2022년식 · 9,800km · 1,802cc",
        "badge": "신규",
        "image": "https://images.unsplash.com/photo-1524591652733-73fa1ae7b5ee?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "중고 바이크",
        "brand": "INDIAN",
        "name": "Scout Bobber",
        "price": 17800000,
        "info": "2021년식 · 14,100km · 1,133cc",
        "badge": "인기",
        "image": "https://images.unsplash.com/photo-1599819811279-d5ad9cccf838?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "바이크 의류",
        "brand": "HARLEY-DAVIDSON",
        "name": "라이딩 레더 재킷",
        "price": 489000,
        "info": "Black · M / L / XL",
        "badge": "BEST",
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "바이크 의류",
        "brand": "MASPICK",
        "name": "라이더 워크 셔츠",
        "price": 89000,
        "info": "Black · M / L / XL / 2XL",
        "badge": "NEW",
        "image": "https://images.unsplash.com/photo-1603252109303-2751441dd157?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "바이크 용품",
        "brand": "BELL",
        "name": "Custom 500 Helmet",
        "price": 259000,
        "info": "Matte Black · DOT",
        "badge": "BEST",
        "image": "https://images.unsplash.com/photo-1558980394-0c7c9299fe96?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "바이크 용품",
        "brand": "MASPICK",
        "name": "프리미엄 라이딩 글러브",
        "price": 79000,
        "info": "Black · M / L / XL",
        "badge": "NEW",
        "image": "https://images.unsplash.com/photo-1609630875171-b1321377ee65?auto=format&fit=crop&w=900&q=80",
    },
]


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>
    /* Streamlit 기본 요소 제거 */
    #MainMenu, footer, header {visibility:hidden;}
    [data-testid="stSidebar"] {display:none;}

    .stApp {
        background:#080808;
        color:#f5f5f5;
    }

    .block-container {
        max-width:1500px;
        padding-top:0;
        padding-left:32px;
        padding-right:32px;
        padding-bottom:70px;
    }

    html, body, [class*="css"] {
        font-family: Arial, Pretendard, "Noto Sans KR", sans-serif;
    }

    /* 상단 유틸 */
    .top-util {
        width:100%;
        height:34px;
        display:flex;
        justify-content:flex-end;
        align-items:center;
        gap:20px;
        color:#888;
        font-size:12px;
        border-bottom:1px solid #1d1d1d;
    }

    /* 헤더 */
    .main-header {
        min-height:92px;
        display:grid;
        grid-template-columns:260px 1fr 260px;
        align-items:center;
        gap:30px;
        border-bottom:1px solid #222;
    }

    .logo {
        font-size:34px;
        font-weight:1000;
        letter-spacing:-2px;
        color:#fff;
        text-decoration:none;
    }

    .logo-m {
        color:#ff6a00;
    }

    .logo-sub {
        display:block;
        font-size:9px;
        letter-spacing:4px;
        color:#777;
        margin-top:-3px;
    }

    .search-wrap {
        width:100%;
        max-width:660px;
        margin:auto;
        background:#111;
        border:1px solid #333;
        border-radius:4px;
        display:flex;
        align-items:center;
        height:48px;
        padding:0 18px;
    }

    .search-placeholder {
        color:#777;
        font-size:14px;
        flex:1;
    }

    .search-icon {
        color:#fff;
        font-size:19px;
    }

    .header-icons {
        display:flex;
        justify-content:flex-end;
        gap:22px;
        font-size:13px;
        color:#bbb;
    }

    /* 메뉴 */
    .nav-wrap {
        display:flex;
        align-items:center;
        justify-content:center;
        min-height:62px;
        border-bottom:1px solid #222;
        gap:46px;
    }

    .nav-item {
        color:#e8e8e8;
        font-size:14px;
        font-weight:800;
        text-decoration:none;
    }

    .nav-item:hover {
        color:#ff6a00;
    }

    .nav-hot {
        color:#ff6a00;
    }

    /* 히어로 */
    .hero {
        margin-top:26px;
        min-height:400px;
        border:1px solid #202020;
        position:relative;
        border-radius:3px;
        overflow:hidden;
        background:
            linear-gradient(90deg, rgba(0,0,0,.96) 0%, rgba(0,0,0,.78) 42%, rgba(0,0,0,.15) 100%),
            url("https://images.unsplash.com/photo-1558980394-4c7c9299fe96?auto=format&fit=crop&w=1800&q=85");
        background-size:cover;
        background-position:center;
        display:flex;
        align-items:center;
        padding:56px;
    }

    .hero-small {
        color:#ff6a00;
        font-weight:900;
        letter-spacing:3px;
        font-size:12px;
    }

    .hero-title {
        margin-top:12px;
        color:#fff;
        font-size:54px;
        line-height:1.05;
        font-weight:1000;
        letter-spacing:-2px;
    }

    .hero-text {
        margin-top:18px;
        max-width:520px;
        font-size:16px;
        color:#aaa;
        line-height:1.7;
    }

    .hero-button {
        display:inline-block;
        margin-top:28px;
        padding:14px 25px;
        background:#ff6a00;
        color:#fff !important;
        text-decoration:none;
        font-weight:900;
        font-size:13px;
    }

    /* 카테고리 */
    .category-row {
        margin:40px 0 15px;
        display:grid;
        grid-template-columns:repeat(4, 1fr);
        gap:12px;
    }

    .category-box {
        height:110px;
        background:#101010;
        border:1px solid #242424;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        transition:.2s ease;
    }

    .category-box:hover {
        border-color:#ff6a00;
        transform:translateY(-2px);
    }

    .category-icon {
        font-size:26px;
    }

    .category-name {
        margin-top:9px;
        font-size:14px;
        color:#eee;
        font-weight:900;
    }

    /* 상품 영역 */
    .section-head {
        display:flex;
        align-items:end;
        justify-content:space-between;
        margin-top:50px;
        margin-bottom:20px;
        padding-bottom:14px;
        border-bottom:1px solid #292929;
    }

    .section-title {
        font-size:25px;
        font-weight:1000;
        color:#fff;
    }

    .section-sub {
        font-size:12px;
        color:#777;
        margin-top:6px;
    }

    .more {
        color:#777;
        font-size:12px;
    }

    /* 카드 */
    .product-card {
        width:100%;
        background:#0c0c0c;
        border:1px solid #1f1f1f;
        overflow:hidden;
        margin-bottom:18px;
        min-height:430px;
        transition:.2s ease;
    }

    .product-card:hover {
        border-color:#555;
        transform:translateY(-3px);
    }

    .product-image-wrap {
        width:100%;
        height:235px;
        background:#151515;
        overflow:hidden;
        position:relative;
    }

    .product-image {
        width:100%;
        height:100%;
        object-fit:cover;
        display:block;
        transition:.35s;
    }

    .product-card:hover .product-image {
        transform:scale(1.035);
    }

    .badge {
        position:absolute;
        left:12px;
        top:12px;
        background:#ff6a00;
        color:#fff;
        padding:6px 9px;
        font-size:10px;
        font-weight:900;
    }

    .product-body {
        padding:17px 16px 20px;
    }

    .brand {
        color:#777;
        font-size:10px;
        font-weight:900;
        letter-spacing:1px;
    }

    .product-name {
        color:#f5f5f5;
        font-size:16px;
        font-weight:900;
        margin-top:8px;
        white-space:nowrap;
        overflow:hidden;
        text-overflow:ellipsis;
    }

    .product-info {
        color:#777;
        font-size:12px;
        margin-top:8px;
        min-height:18px;
    }

    .product-price {
        color:#fff;
        font-size:20px;
        font-weight:1000;
        margin-top:17px;
    }

    .won {
        font-size:13px;
        font-weight:700;
    }

    /* 하단 띠 */
    .trust {
        margin-top:55px;
        padding:32px;
        border-top:1px solid #222;
        border-bottom:1px solid #222;
        display:grid;
        grid-template-columns:repeat(4,1fr);
        text-align:center;
        gap:10px;
    }

    .trust-title {
        font-size:13px;
        color:#ddd;
        font-weight:900;
    }

    .trust-sub {
        margin-top:6px;
        color:#666;
        font-size:11px;
    }

    .footer {
        text-align:center;
        padding:40px 0 15px;
        color:#555;
        font-size:11px;
        line-height:1.8;
    }

    @media(max-width:1000px) {
        .block-container {
            padding-left:15px;
            padding-right:15px;
        }

        .main-header {
            grid-template-columns:1fr;
            gap:12px;
            padding:18px 0;
        }

        .logo {
            text-align:center;
        }

        .header-icons {
            display:none;
        }

        .nav-wrap {
            gap:19px;
            overflow-x:auto;
            justify-content:flex-start;
            white-space:nowrap;
        }

        .hero {
            min-height:340px;
            padding:32px 25px;
        }

        .hero-title {
            font-size:38px;
        }

        .category-row {
            grid-template-columns:repeat(2,1fr);
        }

        .trust {
            grid-template-columns:repeat(2,1fr);
            row-gap:25px;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
<div class="top-util">
    <span>LOGIN</span>
    <span>JOIN</span>
    <span>ORDER</span>
    <span>MY PAGE</span>
    <span>CART 0</span>
</div>

<div class="main-header">
    <div>
        <div class="logo"><span class="logo-m">M</span>ASPICK</div>
        <span class="logo-sub">MOTORCYCLE CULTURE</span>
    </div>

    <div class="search-wrap">
        <span class="search-placeholder">바이크, 의류, 용품 검색</span>
        <span class="search-icon">⌕</span>
    </div>

    <div class="header-icons">
        <span>♡ WISH</span>
        <span>◎ MY</span>
        <span>▣ CART</span>
    </div>
</div>

<div class="nav-wrap">
    <a class="nav-item" href="#usedbike">중고 바이크</a>
    <a class="nav-item" href="#wear">바이크 의류</a>
    <a class="nav-item" href="#gear">바이크 용품</a>
    <a class="nav-item" href="#new">신상품</a>
    <a class="nav-item nav-hot" href="#sale">SALE</a>
    <a class="nav-item" href="#community">커뮤니티</a>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">
    <div>
        <div class="hero-small">MASPICK MOTORCYCLE STORE</div>
        <div class="hero-title">RIDE YOUR<br>OWN WAY.</div>
        <div class="hero-text">
            엄선된 중고 바이크부터 라이딩 의류와 커스텀 파츠까지.<br>
            바이크 라이프에 필요한 모든 것을 MASPICK에서 만나보세요.
        </div>
        <a class="hero-button" href="#usedbike">중고 바이크 보기 →</a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# CATEGORY
# =========================================================

st.markdown(
    """
<div class="category-row">
    <div class="category-box">
        <div class="category-icon">🏍</div>
        <div class="category-name">중고 바이크</div>
    </div>
    <div class="category-box">
        <div class="category-icon">◈</div>
        <div class="category-name">라이딩 의류</div>
    </div>
    <div class="category-box">
        <div class="category-icon">⛑</div>
        <div class="category-name">헬멧 · 보호장비</div>
    </div>
    <div class="category-box">
        <div class="category-icon">⚙</div>
        <div class="category-name">커스텀 · 용품</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# PRODUCT RENDER
# =========================================================

def won(value):
    return f"{int(value):,}"


def render_section(title, subtitle, products, anchor):
    st.markdown(
        f"""
        <div id="{anchor}" class="section-head">
            <div>
                <div class="section-title">{title}</div>
                <div class="section-sub">{subtitle}</div>
            </div>
            <div class="more">VIEW ALL +</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)

    for idx, p in enumerate(products):
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div class="product-card">
                    <div class="product-image-wrap">
                        <img class="product-image" src="{p['image']}">
                        <div class="badge">{p['badge']}</div>
                    </div>
                    <div class="product-body">
                        <div class="brand">{p['brand']}</div>
                        <div class="product-name">{p['name']}</div>
                        <div class="product-info">{p['info']}</div>
                        <div class="product-price">
                            {won(p['price'])}<span class="won"> 원</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


bikes = [p for p in PRODUCTS if p["category"] == "중고 바이크"]
wear = [p for p in PRODUCTS if p["category"] == "바이크 의류"]
gear = [p for p in PRODUCTS if p["category"] == "바이크 용품"]

render_section(
    "USED MOTORCYCLE",
    "MASPICK이 선별한 중고 바이크",
    bikes,
    "usedbike",
)

render_section(
    "RIDING WEAR",
    "라이더를 위한 의류 컬렉션",
    wear,
    "wear",
)

render_section(
    "PARTS & GEAR",
    "헬멧부터 커스텀 용품까지",
    gear,
    "gear",
)


# =========================================================
# SERVICE
# =========================================================

st.markdown(
    """
<div class="trust">
    <div>
        <div class="trust-title">중고 바이크 상담</div>
        <div class="trust-sub">차량 상태와 상세정보 상담</div>
    </div>
    <div>
        <div class="trust-title">전국 문의 가능</div>
        <div class="trust-sub">지역별 상담 및 출고 안내</div>
    </div>
    <div>
        <div class="trust-title">라이딩 전문 상품</div>
        <div class="trust-sub">바이크 의류 · 용품 · 파츠</div>
    </div>
    <div>
        <div class="trust-title">MASPICK PICK</div>
        <div class="trust-sub">직접 선별한 추천 상품</div>
    </div>
</div>

<div class="footer">
    MASPICK MOTORCYCLE STORE<br>
    USED MOTORCYCLE · RIDING WEAR · PARTS & GEAR<br><br>
    © MASPICK. ALL RIGHTS RESERVED.
</div>
""",
    unsafe_allow_html=True,
)