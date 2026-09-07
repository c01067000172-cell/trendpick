#!/usr/bin/env bash
set -e

mkdir -p "${TRENDPICK_DATA_DIR:-/var/data/trendpick}"

# 1시간 자동 수집기를 같은 서버에서 백그라운드 실행
python collector_loop.py &

# Render가 제공하는 PORT를 사용해 Streamlit 공개
exec streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true \
  --browser.gatherUsageStats=false
