#!/usr/bin/env bash
set -e

mkdir -p static

# Install the Naver verification tag in the initial server HTML.
python - <<'NAVER_VERIFY'
from pathlib import Path
import re
import streamlit

index = Path(streamlit.__file__).resolve().parent / "static" / "index.html"
html = index.read_text(encoding="utf-8")
if "</head>" not in html:
    raise RuntimeError("Streamlit index.html head was not found")
html = re.sub(r'<meta\b(?=[^>]*\bname=[\"\']naver-site-verification[\"\'])[^>]*>', '', html, flags=re.I)
tag = '<meta name="naver-site-verification" content="9f3ca97a7b93c85fbea2d89bd64466f9e891c066" />'
html = html.replace("</head>", tag + "\n</head>", 1)
index.write_text(html, encoding="utf-8")
print("Naver ownership verification tag installed")
NAVER_VERIFY


# Build a smaller browser-friendly banner once at service start.
# The source PNG stays untouched; the site serves the generated WebP file.
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

printf '%s\n' \
  '<?xml version="1.0" encoding="UTF-8"?>' \
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \
  '  <url><loc>https://www.maspick.co.kr/</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EC%A0%84%EC%B2%B4%EC%83%81%ED%92%88</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EC%A4%91%EA%B3%A0%20%EB%B0%94%EC%9D%B4%ED%81%AC</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EB%B0%94%EC%9D%B4%ED%81%AC%20%EC%9D%98%EB%A5%98</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EB%B0%94%EC%9D%B4%ED%81%AC%20%EC%9A%A9%ED%92%88</loc></url>' \
  '</urlset>' > static/sitemap.xml

exec streamlit run supabase_runner.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true \
  --server.enableStaticServing=true \
  --server.fileWatcherType=none \
  --server.runOnSave=false \
  --browser.gatherUsageStats=false
