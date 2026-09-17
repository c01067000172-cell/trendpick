#!/usr/bin/env bash
set -e

mkdir -p static

# Install Naver ownership verification, crawler-visible SEO metadata,
# and crawler-visible homepage text before Streamlit's browser code runs.
# (홈 SEO는 이 파일 한 곳에서만 관리합니다. sitecustomize.py에는 SEO 코드가 없습니다.)
python - <<'NAVER_VERIFY'
import json
import os
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit

SITE = "https://www.maspick.co.kr"
BRAND_KO = "투제이로드"
BRAND_EN = "TWO J ROAD"
STORE_ADDRESS = "경기 포천시 내촌면 금강로3224번길 11-7"
PHONE = os.getenv("MASPICK_PHONE", "").strip()

index = Path(streamlit.__file__).resolve().parent / "static" / "index.html"
html = index.read_text(encoding="utf-8")
if "</head>" not in html:
    raise RuntimeError("Streamlit index.html head was not found")

# Remove old copies so every deploy has one clean canonical metadata set.
patterns = [
    r'<meta\b(?=[^>]*\bname=["\']naver-site-verification["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:[a-z_]+["\'])[^>]*>',
    r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>',
    r'<script[^>]*id=["\']twojroad-schema["\'][^>]*>.*?</script>',
    r'<script[^>]*id=["\']twoj-jsonld["\'][^>]*>.*?</script>',
    r'<!--TWOJ-SEO-BODY-START-->.*?<!--TWOJ-SEO-BODY-END-->',
]
for pattern in patterns:
    html = re.sub(pattern, "", html, flags=re.I | re.S)
html = re.sub(r"<title\b[^>]*>.*?</title>", "", html, flags=re.I | re.S)

page_title = "투제이로드 (TWO J ROAD) | 포천 중고 바이크·오토바이 의류·헬멧"
page_description = (
    "투제이로드(TWO J ROAD)는 경기 포천의 바이크 매장입니다. 중고 바이크와 중고 오토바이, "
    "바이크 자켓·오토바이 장갑·오토바이 헬멧 등 바이크 의류와 라이딩 용품을 판매합니다."
)

schema = {
    "@context": "https://schema.org",
    "@type": "Store",
    "@id": SITE + "/#store",
    "name": BRAND_EN,
    "alternateName": [BRAND_KO, "포천 투제이로드", "TWOJROAD", "TWO J ROAD 포천"],
    "url": SITE + "/",
    "image": SITE + "/app/static/og_naver.jpg",
    "description": page_description,
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "내촌면 금강로3224번길 11-7",
        "addressLocality": "포천시",
        "addressRegion": "경기도",
        "addressCountry": "KR",
    },
    "areaServed": "대한민국",
    "keywords": [
        "투제이로드", "TWO J ROAD", "포천 투제이로드", "포천 중고 바이크",
        "중고 오토바이", "바이크 의류", "오토바이 자켓", "바이크 장갑",
        "오토바이 헬멧", "라이딩 용품"
    ],
}
if PHONE:
    schema["telephone"] = PHONE

verification = '<meta name="naver-site-verification" content="9f3ca97a7b93c85fbea2d89bd64466f9e891c066" />\n'
metadata = (
    "<title>" + escape(page_title) + "</title>\n"
    + '<meta name="description" content="' + escape(page_description, quote=True) + '" />\n'
    + '<meta name="robots" content="index,follow,max-image-preview:large" />\n'
    + '<link rel="canonical" href="' + SITE + '/" />\n'
    + '<meta property="og:title" content="' + escape(page_title, quote=True) + '" />\n'
    + '<meta property="og:description" content="' + escape(page_description, quote=True) + '" />\n'
    + '<meta property="og:type" content="website" />\n'
    + '<meta property="og:site_name" content="TWO J ROAD (투제이로드)" />\n'
    + '<meta property="og:url" content="' + SITE + '/" />\n'
    + '<meta property="og:locale" content="ko_KR" />\n'
    + '<meta property="og:image" content="' + SITE + '/app/static/og_naver.jpg" />\n'
    + '<meta property="og:image:width" content="1200" />\n'
    + '<meta property="og:image:height" content="630" />\n'
    + '<meta name="twitter:card" content="summary_large_image" />\n'
    + '<script id="twojroad-schema" type="application/ld+json">'
    + json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    + '</script>\n'
)
html = html.replace("</head>", verification + metadata + "</head>", 1)

# Homepage text inside #root. Search robots read it from the original HTML.
# In the browser, Streamlit replaces #root content when the app starts,
# so the storefront screen stays the same.
map_url = "https://map.naver.com/p/search/" + quote(STORE_ADDRESS, safe="")
phone_line = ("<br>매장 문의: " + escape(PHONE)) if PHONE else ""
body_text = (
    "<!--TWOJ-SEO-BODY-START-->"
    '<main style="max-width:1100px;margin:0 auto;padding:24px;color:#eee;'
    'background:#080808;font:16px/1.7 sans-serif">'
    "<h1>투제이로드 (TWO J ROAD) · 포천 중고 바이크 · 바이크 의류 · 오토바이 헬멧</h1>"
    "<p>투제이로드(TWO J ROAD)는 경기 포천에 있는 바이크 매장입니다. "
    "중고 바이크와 중고 오토바이 매물, 바이크 자켓·오토바이 장갑·바이크 바지·바이크 신발 같은 "
    "바이크 의류, 오토바이 헬멧과 라이딩 용품을 판매합니다.</p>"
    '<nav aria-label="상품 분류"><ul>'
    '<li><a href="/catalog/bike">포천 중고 바이크 · 중고 오토바이</a></li>'
    '<li><a href="/catalog/wear">바이크 의류</a> : '
    '<a href="/catalog/wear/jacket">바이크 자켓</a>, '
    '<a href="/catalog/wear/gloves">오토바이 장갑</a>, '
    '<a href="/catalog/wear/pants">바이크 바지</a>, '
    '<a href="/catalog/wear/shoes">바이크 신발</a>, '
    '<a href="/catalog/wear/tops">바이크 상의</a></li>'
    '<li><a href="/catalog/gear">바이크 용품</a> : '
    '<a href="/catalog/gear/helmet">오토바이 헬멧</a></li>'
    "</ul></nav>"
    "<h2>매장 안내</h2>"
    "<p>포천 투제이로드 (TWO J ROAD)<br>" + escape(STORE_ADDRESS) + phone_line + "<br>"
    '<a href="' + escape(map_url, quote=True) + '">네이버 지도에서 위치 보기</a> · '
    '<a href="/?page=store">오프라인매장 안내</a> · '
    '<a href="/sitemap.xml">사이트맵</a></p>'
    "</main>"
    "<!--TWOJ-SEO-BODY-END-->"
)
html, count = re.subn(
    r'(<div\b[^>]*\bid=["\']root["\'][^>]*>)',
    lambda m: m.group(1) + body_text,
    html,
    count=1,
    flags=re.I,
)
if count != 1:
    print("WARNING: Streamlit #root not found - homepage body text was not installed")

index.write_text(html, encoding="utf-8")
print("TWO J ROAD Korean brand SEO metadata installed (body text: %s)" % ("ok" if count == 1 else "skipped"))
NAVER_VERIFY

# Build a smaller browser-friendly banner once at service start.
python - <<'PY'
from pathlib import Path
from PIL import Image

src = Path("assets/jinbike_banner.png")
dst = Path("static/jinbike_banner.webp")

if src.exists():
    with Image.open(src) as image:
        if image.width > 1920:
            new_height = max(1, round(image.height * 1920 / image.width))
            image = image.resize((1920, new_height), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.save(dst, "WEBP", quality=82, method=6)

jpg = Path("static/og_naver.jpg")
if src.exists():
    with Image.open(src) as image:
        image = image.convert("RGB")
        w, h = image.size
        target = 1200 / 630
        if w / h > target:
            nw = int(h * target); x = (w - nw) // 2; image = image.crop((x, 0, x + nw, h))
        else:
            nh = int(w / target); y = (h - nh) // 2; image = image.crop((0, y, w, y + nh))
        image = image.resize((1200, 630), Image.Resampling.LANCZOS)
        image.save(jpg, "JPEG", quality=86, optimize=True)
PY

# Fallback crawler files. seo_server.py serves the live /robots.txt and /sitemap.xml.
printf '%s\n' \
  'User-agent: *' \
  'Allow: /' \
  'Sitemap: https://www.maspick.co.kr/sitemap.xml' \
  > static/robots.txt

printf '%s\n' \
  '<?xml version="1.0" encoding="UTF-8"?>' \
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \
  '  <url><loc>https://www.maspick.co.kr/</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/bike</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/wear</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/gear</loc></url>' \
  '</urlset>' > static/sitemap.xml

exec python seo_server.py run supabase_runner.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true \
  --server.enableStaticServing=true \
  --server.fileWatcherType=none \
  --server.runOnSave=false \
  --browser.gatherUsageStats=false
