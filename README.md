# TrendPick - Render 배포본

이 패키지는 기존 Windows/PowerShell/Cloudflare Quick Tunnel 없이
Render에서 24시간 실행하도록 정리한 배포본입니다.

## 구조
- `app.py` : TrendPick Streamlit 웹사이트
- `collector.py` : 1회 상품/랭킹 수집
- `collector_loop.py` : 1시간마다 collector.py 자동 실행
- `start.sh` : 웹사이트 + 자동수집기 동시 시작
- `render.yaml` : Render Blueprint 설정
- `requirements.txt` : Python 패키지

## 비밀키
NAVER API 키는 파일에 넣지 않습니다.
Render 생성 과정에서 아래 환경변수를 입력합니다.
- NAVER_CLIENT_ID
- NAVER_CLIENT_SECRET

## 데이터 보존
`TRENDPICK_DATA_DIR=/var/data/trendpick`를 사용합니다.
Render Persistent Disk를 이 경로에 연결하여
`candidate_snapshots.csv`, `collector_status.json`, 판매근거 CSV를 보존합니다.

## 중요
현재 로컬 PC에 있던 기존 `sales_sources/candidate_snapshots.csv` 이력은
이 패키지에 포함하지 않았습니다. 클라우드 배포 후 새 이력이 쌓이기 시작합니다.
기존 이력을 이어가려면 해당 CSV를 별도로 업로드해야 합니다.
