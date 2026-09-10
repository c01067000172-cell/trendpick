#!/usr/bin/env bash
set -e

mkdir -p static
printf '%s\n' \
  '<?xml version="1.0" encoding="UTF-8"?>' \
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \
  '  <url><loc>https://www.maspick.co.kr/</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EC%A0%84%EC%B2%B4%EC%83%81%ED%92%88</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EC%A4%91%EA%B3%A0%20%EB%B0%94%EC%9D%B4%ED%81%AC</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EB%B0%94%EC%9D%B4%ED%81%AC%20%EC%9D%98%EB%A5%98</loc></url>' \
  '  <url><loc>https://www.maspick.co.kr/?page=shop&amp;cat=%EB%B0%94%EC%9D%B4%ED%81%AC%20%EC%9A%A9%ED%92%88</loc></url>' \
  '</urlset>' > static/sitemap.xml

exec streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true \
  --server.enableStaticServing=true \
  --browser.gatherUsageStats=false
