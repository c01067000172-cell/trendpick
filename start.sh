#!/usr/bin/env bash
set -e

mkdir -p static

# Install Naver ownership verification and crawler-visible SEO metadata
# before Streamlit's browser code runs.
python - <<'NAVER_VERIFY'
from pathlib import Path
from html import escape
import json
import re
import streamlit

SITE = "https://www.maspick.co.kr"
BRAND_KO = "투제이로드"
BRAND_EN = "TWO J ROAD"
STORE_ADDRESS = "경기 포천시 내촌면 금강로3224번길 11-7"

index = Path(streamlit.__file__).resolve().parent / "static" / "index.html"
html = index.read_text(encoding="utf-8")
if "</head>" not in html:
    raise RuntimeError("Streamlit index.html head was not found")

# Remove old copies so every deploy has one clean canonical metadata set.
patterns = [
    r'<meta\b(?=[^>]*\bname=["\']naver-site-verification["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:title["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:description["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:type["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:site_name["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:url["\'])[^>]*>',
    r'<meta\b(?=[^>]*\bproperty=["\']og:locale["\'])[^>]*>',
    r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>',
    r'<script[^>]*id=["\']twojroad-schema["\'][^>]*>.*?</script>',
]
for pattern in patterns:
    html = re.sub(pattern, "", html, flags=re.I | re.S)
html = re.sub(r"<title\b[^>]*>.*?</title>", "", html, flags=re.I | re.S)

page_title = "투제이로드 (TWO J ROAD) | 포천 중고 바이크·바이크 의류·용품"
page_description = (
    "투제이로드(TWO J ROAD)는 포천 중고 바이크와 중고 오토바이, "
    "바이크 의류, 오토바이 자켓·장갑·헬멧 등 라이딩 용품을 판매하는 바이크 전문점입니다."
)

schema = {
    "@context": "https://schema.org",
    "@type": "Store",
    "@id": SITE + "/#store",
    "name": BRAND_EN,
    "alternateName": [BRAND_KO, "포천 투제이로드", "TWOJROAD", "TWO J ROAD 포천"],
    "url": SITE + "/",
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
        "투제이로드", "TWO J ROAD", "포천 투제이로드", "중고 바이크",
        "중고 오토바이", "바이크 의류", "오토바이 자켓", "바이크 장갑",
        "오토바이 헬멧", "라이딩 용품"
    ],
}

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
    + '<script id="twojroad-schema" type="application/ld+json">'
    + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    + '</script>\n'
)
html = html.replace("</head>", verification + metadata + "</head>", 1)
index.write_text(html, encoding="utf-8")
print("TWO J ROAD Korean brand SEO metadata installed")
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
PY

# Fallback crawler files. seo_server.py also exposes /robots.txt and /sitemap.xml.
printf '%s\n' \
  'User-agent: *' \
  'Allow: /' \
  'Sitemap: https://www.maspick.co.kr/sitemap.xml' \
  > static/robots.txt

printf '%s\n' \
  '<?xml version="1.0" encoding="UTF-8"?>' \
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \
  '  <url><loc>https://www.maspick.co.kr/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/bike</loc><changefreq>daily</changefreq><priority>0.9</priority></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/wear</loc><changefreq>daily</changefreq><priority>0.9</priority></url>' \
  '  <url><loc>https://www.maspick.co.kr/catalog/gear</loc><changefreq>daily</changefreq><priority>0.9</priority></url>' \
  '</urlset>' > static/sitemap.xml

exec python seo_server.py run supabase_runner.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true \
  --server.enableStaticServing=true \
  --server.fileWatcherType=none \
  --server.runOnSave=false \
  --browser.gatherUsageStats=false
