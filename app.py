from pathlib import Path
import os
from datetime import date, timedelta, datetime

import pandas as pd
import requests
import streamlit as st
import altair as alt
from io import StringIO
import json

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


st.set_page_config(page_title="실시간 상품 트렌드", page_icon="🔥", layout="wide")

API_BASE = "https://naverapihub.apigw.ntruss.com"
SHOPPING_KEYWORD_PATH = "/shopping/v1/category/keywords"


def get_secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, ""))
    except Exception:
        return os.getenv(name, "")


def api_headers() -> dict:
    return {
        "X-NCP-APIGW-API-KEY-ID": get_secret("NAVER_CLIENT_ID"),
        "X-NCP-APIGW-API-KEY": get_secret("NAVER_CLIENT_SECRET"),
        "Content-Type": "application/json",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_keyword_trends(category_ids: tuple[str, ...], keywords: tuple[str, ...]) -> pd.DataFrame:
    headers = api_headers()
    if not all(headers.get(k) for k in ("X-NCP-APIGW-API-KEY-ID", "X-NCP-APIGW-API-KEY")):
        raise RuntimeError("Streamlit Secrets에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 먼저 저장해주세요.")

    # 쇼핑인사이트 최신 데이터가 당일/전일 바로 제공되지 않는 경우가 있어
    # 최근 날짜부터 최대 7일 전까지 자동으로 재시도합니다.
    end_candidates = [
        date.today() - timedelta(days=1),
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=3),
        date.today() - timedelta(days=5),
        date.today() - timedelta(days=7),
    ]

    last_error = None

    for end_date in end_candidates:
        start_date = end_date - timedelta(days=27)
        rows = []
        failed = False

        for category_id in category_ids:
            for pos in range(0, len(keywords), 5):
                batch = keywords[pos : pos + 5]
                body = {
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "timeUnit": "date",
                    "category": str(category_id),
                    "keyword": [{"name": str(k), "param": [str(k)]} for k in batch],
                }

                response = requests.post(
                    API_BASE + SHOPPING_KEYWORD_PATH,
                    headers=headers,
                    json=body,
                    timeout=20,
                )

                if response.status_code != 200:
                    last_error = (
                        f"HTTP {response.status_code} / 조회종료일 {end_date.isoformat()} / "
                        f"카테고리 {category_id} / 응답 {response.text[:300]}"
                    )
                    failed = True
                    break

                payload = response.json()
                for result in payload.get("results", []):
                    points = result.get("data", [])
                    values = [float(p.get("ratio", 0) or 0) for p in points]
                    if not values:
                        continue

                    half = max(1, len(values) // 2)
                    old_values = values[:half]
                    new_values = values[half:] or values[-1:]

                    old_avg = sum(old_values) / len(old_values)
                    new_avg = sum(new_values) / len(new_values)
                    growth = (
                        ((new_avg - old_avg) / old_avg * 100)
                        if old_avg > 0
                        else (100.0 if new_avg > 0 else 0.0)
                    )

                    rows.append({
                        "상품명": result.get("title") or (result.get("keyword") or ["키워드"])[0],
                        "이전지수": round(old_avg, 1),
                        "최근지수": round(new_avg, 1),
                        "검색증감률": round(growth, 1),
                        "추이": values,
                        "카테고리ID": str(category_id),
                        "데이터기준일": end_date.isoformat(),
                    })

            if failed:
                break

        if not failed:
            if not rows:
                return pd.DataFrame()
            return (
                pd.DataFrame(rows)
                .sort_values("최근지수", ascending=False)
                .drop_duplicates("상품명")
            )

    raise RuntimeError(
        "네이버 쇼핑인사이트 API가 최근 날짜 조회를 모두 거절했습니다. "
        + (last_error or "상세 응답 없음")
    )



def live_trend_panel(df: pd.DataFrame):
    if df is None or df.empty:
        st.warning("네이버 쇼핑인사이트에서 표시할 데이터가 없습니다.")
        return

    ranked = score_and_classify(df).copy()
    if ranked.empty:
        st.warning("분석 가능한 데이터가 없습니다.")
        return

    top = ranked.sort_values(["검색증감률", "최근지수"], ascending=False).head(10).reset_index(drop=True)

    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:8px 0 14px;">
      <span style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;
                   background:#ecfdf5;color:#047857;font-size:12px;font-weight:800;">
        <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;"></span>
        NAVER SHOPPING INSIGHT LIVE
      </span>
      <span style="font-size:12px;color:#64748b;">검색·클릭 상대지수 기반</span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    for i, row in top.head(5).iterrows():
        with cols[i]:
            growth = float(row.get("검색증감률", 0))
            recent = float(row.get("최근지수", 0))
            st.markdown(f"""
            <div style="border:1px solid #e5e7eb;border-radius:18px;padding:16px;background:#fff;min-height:142px;">
              <div style="font-size:12px;color:#64748b;font-weight:800;">#{i+1} 급상승</div>
              <div style="font-size:17px;font-weight:900;color:#0f172a;margin-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {row.get("상품명","-")}
              </div>
              <div style="font-size:24px;font-weight:900;color:#16a34a;margin-top:12px;">+{growth:.1f}%</div>
              <div style="font-size:12px;color:#94a3b8;margin-top:4px;">최근지수 {recent:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 1시간 급상승 TOP 10")
    display = top[["상품명","검색증감률","최근지수","순위변화","점수"]].copy()
    display.index = range(1, len(display)+1)
    display.index.name = "순위"
    st.dataframe(
        display,
        width="stretch",
        hide_index=False,
        column_config={
            "검색증감률": st.column_config.NumberColumn("검색증감률", format="%.1f%%"),
            "최근지수": st.column_config.NumberColumn("최근지수", format="%.1f"),
            "순위변화": st.column_config.NumberColumn("순위변화"),
            "점수": st.column_config.NumberColumn("점수"),
        },
    )


def score_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    ranked = df.copy().sort_values(["검색증감률", "최근지수"], ascending=False).reset_index(drop=True)
    ranked["이전순위"] = ranked["이전지수"].rank(method="min", ascending=False).astype(int)
    ranked["현재순위"] = ranked["최근지수"].rank(method="min", ascending=False).astype(int)
    ranked["순위변화"] = ranked["이전순위"] - ranked["현재순위"]

    # API로 검증 가능한 검색 상승분을 점수화하고, 확인되지 않은 판매량은 점수에 넣지 않습니다.
    ranked["점수"] = ranked.apply(
        lambda r: min(
            100,
            25
            + (25 if r["순위변화"] > 0 else 10)
            + (15 if r["검색증감률"] > 5 else 5)
            + (15 if r["이전지수"] == 0 and r["최근지수"] > 0 else 0)
            + (20 if r["최근지수"] >= ranked["최근지수"].median() else 10),
        ),
        axis=1,
    ).astype(int)
    ranked["카테고리"] = ranked.apply(
        lambda r: "신규 진입" if r["이전지수"] == 0 and r["최근지수"] > 0 else ("급상승" if r["검색증감률"] >= 10 else "스테디셀러"),
        axis=1,
    )
    ranked["등급"] = pd.qcut(ranked["점수"].rank(method="first", ascending=False), 3, labels=["S", "A", "B"]) if len(ranked) >= 3 else "S"
    ranked["플랫폼 순위"] = ranked.apply(lambda r: f"네이버 키워드: {r['이전순위']}위→{r['현재순위']}위", axis=1)
    ranked["네이버 검색 트렌드"] = ranked.apply(lambda r: f"{r['이전지수']}→{r['최근지수']} ({r['검색증감률']:+.1f}%)", axis=1)
    ranked["URL"] = ranked["상품명"].map(lambda x: f"https://search.shopping.naver.com/search/all?query={requests.utils.quote(str(x))}")
    return ranked


def demo_data() -> pd.DataFrame:
    names = ["경량 바람막이", "와이드 데님", "러닝 벨트", "미니 크로스백", "무선 보조배터리", "캠핑 랜턴", "기능성 티셔츠", "텀블러", "차량용 방향제"]
    growth = [82, 61, 45, 32, 24, 18, 9, 4, 2]
    return pd.DataFrame({"상품명": names, "이전지수": [22,25,31,35,42,45,58,71,76], "최근지수": [40,40.3,45,46.2,52.1,53.1,63.2,73.8,77.5], "검색증감률": growth, "추이": [[] for _ in names]})


PRODUCT_COLUMNS = [
    "검색어", "상품명", "플랫폼", "현재순위", "이전순위", "판매수량",
    "현재리뷰수", "이전리뷰수", "상품URL",
]


def product_csv_template() -> bytes:
    sample = pd.DataFrame(columns=PRODUCT_COLUMNS)
    return sample.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")



SALES_SOURCE_DIR = Path(os.getenv("TRENDPICK_DATA_DIR", str(Path(__file__).resolve().parent / "sales_sources")))


def load_product_evidence_path(csv_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp949")

    missing = [c for c in PRODUCT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path.name}: 필요한 열이 없습니다: " + ", ".join(missing))

    for col in ["현재순위", "이전순위", "판매수량", "현재리뷰수", "이전리뷰수"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["검색어", "상품명", "플랫폼", "상품URL"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df = df[
        df["상품명"].ne("")
        & df["상품URL"].str.startswith(("http://", "https://"))
    ].copy()

    df["데이터파일"] = csv_path.name
    df["파일수정시각"] = datetime.fromtimestamp(
        csv_path.stat().st_mtime
    ).strftime("%Y-%m-%d %H:%M:%S")
    return df


def collect_sales_source_folder() -> tuple[pd.DataFrame, pd.DataFrame]:
    SALES_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    status_rows = []

    for csv_path in sorted(SALES_SOURCE_DIR.glob("*.csv")):
        try:
            part = load_product_evidence_path(csv_path)
            frames.append(part)
            status_rows.append({
                "파일": csv_path.name,
                "상태": "정상",
                "행수": len(part),
                "수정시각": datetime.fromtimestamp(
                    csv_path.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })
        except Exception as exc:
            status_rows.append({
                "파일": csv_path.name,
                "상태": f"오류: {exc}",
                "행수": 0,
                "수정시각": datetime.fromtimestamp(
                    csv_path.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })

    if frames:
        merged = pd.concat(frames, ignore_index=True)
        merged = merged.drop_duplicates(
            subset=["검색어", "상품명", "플랫폼", "상품URL"],
            keep="last"
        )
    else:
        merged = pd.DataFrame(columns=PRODUCT_COLUMNS + ["데이터파일", "파일수정시각"])

    status_df = pd.DataFrame(
        status_rows,
        columns=["파일", "상태", "행수", "수정시각"]
    )
    return merged, status_df


def merge_sales_evidence(existing: pd.DataFrame | None, incoming: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if isinstance(existing, pd.DataFrame) and not existing.empty:
        frames.append(existing.copy())
    if isinstance(incoming, pd.DataFrame) and not incoming.empty:
        frames.append(incoming.copy())

    if not frames:
        return pd.DataFrame(columns=PRODUCT_COLUMNS)

    merged = pd.concat(frames, ignore_index=True, sort=False)
    for c in PRODUCT_COLUMNS:
        if c not in merged.columns:
            merged[c] = 0 if c in ["현재순위", "이전순위", "판매수량", "현재리뷰수", "이전리뷰수"] else ""

    return merged.drop_duplicates(
        subset=["검색어", "상품명", "플랫폼", "상품URL"],
        keep="last"
    ).reset_index(drop=True)



PARTNER_CONNECTOR_COLUMNS = [
    "이름", "플랫폼", "유형", "상태", "설명"
]


def get_optional_secret(name: str, default: str = "") -> str:
    """환경변수 또는 Streamlit Secrets에서 선택적으로 값을 읽습니다."""
    value = os.getenv(name)
    if value:
        return value.strip()
    try:
        value = st.secrets.get(name, default)
        return str(value).strip() if value is not None else default
    except Exception:
        return default


def normalize_partner_records(payload, platform_name: str) -> pd.DataFrame:
    """
    제휴 API/공식 피드 응답을 판매근거 표준 형식으로 정규화합니다.
    지원 입력:
      1) JSON 배열
      2) {"items":[...]} / {"data":[...]} / {"results":[...]}
    각 항목은 표준 한글 필드 또는 아래 영문 alias를 사용할 수 있습니다.
    """
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "products"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break

    if not isinstance(payload, list):
        raise ValueError("제휴 API 응답은 JSON 배열 또는 items/data/results 배열이어야 합니다.")

    alias = {
        "검색어": ["검색어", "keyword", "query"],
        "상품명": ["상품명", "product_name", "name", "title"],
        "플랫폼": ["플랫폼", "platform", "mall"],
        "현재순위": ["현재순위", "current_rank", "rank"],
        "이전순위": ["이전순위", "previous_rank", "prev_rank"],
        "판매수량": ["판매수량", "sales_qty", "sales_count", "sold"],
        "현재리뷰수": ["현재리뷰수", "review_count", "current_reviews"],
        "이전리뷰수": ["이전리뷰수", "previous_reviews", "prev_reviews"],
        "상품URL": ["상품URL", "product_url", "url", "link"],
    }

    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        row = {}
        for target, keys in alias.items():
            value = ""
            for k in keys:
                if k in item and item[k] is not None:
                    value = item[k]
                    break
            row[target] = value

        if not row["플랫폼"]:
            row["플랫폼"] = platform_name
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=PRODUCT_COLUMNS)

    df = pd.DataFrame(rows)
    for col in ["현재순위", "이전순위", "판매수량", "현재리뷰수", "이전리뷰수"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["검색어", "상품명", "플랫폼", "상품URL"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df[
        df["상품명"].ne("")
        & df["상품URL"].str.startswith(("http://", "https://"))
    ].copy()


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_partner_json_feed(
    url: str,
    platform_name: str,
    bearer_token: str = "",
    api_key: str = "",
) -> pd.DataFrame:
    """
    사용 권한이 있는 공식/제휴 JSON 피드를 1시간 캐시로 수집합니다.
    """
    if not url:
        return pd.DataFrame(columns=PRODUCT_COLUMNS)

    headers = {"Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if api_key:
        headers["X-API-Key"] = api_key

    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    return normalize_partner_records(response.json(), platform_name)


def collect_configured_partner_feeds() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    secrets.toml / 환경변수에 설정된 공식 제휴 피드를 수집합니다.
    현재 지원 슬롯:
      PARTNER_FEED_1_URL / _PLATFORM / _TOKEN / _API_KEY
      ...
      PARTNER_FEED_5_URL / _PLATFORM / _TOKEN / _API_KEY
    """
    frames = []
    statuses = []

    for n in range(1, 6):
        url = get_optional_secret(f"PARTNER_FEED_{n}_URL")
        platform = get_optional_secret(f"PARTNER_FEED_{n}_PLATFORM", f"파트너{n}")
        token = get_optional_secret(f"PARTNER_FEED_{n}_TOKEN")
        api_key = get_optional_secret(f"PARTNER_FEED_{n}_API_KEY")

        if not url:
            continue

        try:
            df = fetch_partner_json_feed(url, platform, token, api_key)
            frames.append(df)
            statuses.append({
                "이름": f"PARTNER_FEED_{n}",
                "플랫폼": platform,
                "유형": "공식/제휴 JSON",
                "상태": "정상",
                "설명": f"{len(df):,}건 수집",
            })
        except Exception as exc:
            statuses.append({
                "이름": f"PARTNER_FEED_{n}",
                "플랫폼": platform,
                "유형": "공식/제휴 JSON",
                "상태": "오류",
                "설명": str(exc)[:160],
            })

    merged = (
        pd.concat(frames, ignore_index=True, sort=False)
        if frames else pd.DataFrame(columns=PRODUCT_COLUMNS)
    )
    if not merged.empty:
        merged = merged.drop_duplicates(
            subset=["검색어", "상품명", "플랫폼", "상품URL"],
            keep="last",
        )

    return merged, pd.DataFrame(statuses, columns=PARTNER_CONNECTOR_COLUMNS)


def connector_status_table() -> pd.DataFrame:
    """
    현재 프로젝트에서 사용할 수 있는 데이터 소스를 명확하게 표시합니다.
    """
    naver_ok = bool(
        get_optional_secret("NAVER_CLIENT_ID")
        and get_optional_secret("NAVER_CLIENT_SECRET")
    )

    rows = [
        {
            "이름": "NAVER Shopping Insight",
            "플랫폼": "네이버",
            "유형": "공식 API",
            "상태": "연결됨" if naver_ok else "설정 필요",
            "설명": "검색·클릭 상대지수. 실제 판매수량은 아님",
        },
        {
            "이름": "sales_sources",
            "플랫폼": "복수 플랫폼",
            "유형": "공식 내보내기/제휴 CSV",
            "상태": "사용 가능",
            "설명": "판매량·순위·리뷰 데이터 자동 병합",
        },
        {
            "이름": "PARTNER_FEED_1~5",
            "플랫폼": "제휴처",
            "유형": "공식/제휴 JSON",
            "상태": "설정 가능",
            "설명": "URL/토큰을 Secrets에 넣으면 1시간 캐시 수집",
        },
        {
            "이름": "PUBLIC_RANK_FEEDS_JSON",
            "플랫폼": "공개 페이지",
            "유형": "공개 랭킹 신호",
            "상태": "설정 가능",
            "설명": "순위·리뷰 신호만 사용. 실제 판매수량으로 취급하지 않음",
        },
        {
            "이름": "MUSINSA_SEARCH",
            "플랫폼": "무신사",
            "유형": "공개 검색 상품 후보",
            "상태": "자동 연결",
            "설명": "네이버 급상승 검색어를 무신사 추천순 공개 검색결과와 자동 매칭",
        },
    ]
    return pd.DataFrame(rows)



PUBLIC_RANKING_COLUMNS = [
    "검색어", "상품명", "플랫폼", "현재순위", "이전순위",
    "판매수량", "현재리뷰수", "이전리뷰수", "상품URL"
]


def parse_compact_count(value: str) -> int:
    """'5천+', '1.2만', '328' 형태 리뷰수를 정수로 변환합니다."""
    if value is None:
        return 0
    s = str(value).replace(",", "").replace("+", "").strip()
    try:
        if "만" in s:
            return int(float(s.replace("만", "")) * 10000)
        if "천" in s:
            return int(float(s.replace("천", "")) * 1000)
        digits = re.sub(r"[^0-9.]", "", s)
        return int(float(digits)) if digits else 0
    except Exception:
        return 0


def get_public_rank_feed_config() -> list[dict]:
    """
    secrets.toml 의 PUBLIC_RANK_FEEDS_JSON 값을 읽습니다.
    이 커넥터는 '실제 판매수량'이 아니라 공개 페이지의 노출/판매순 랭킹 신호를 수집합니다.
    """
    raw = get_optional_secret("PUBLIC_RANK_FEEDS_JSON")
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_public_ranking_page(
    url: str,
    keyword: str,
    platform_name: str,
    ranking_basis: str = "공개 랭킹",
    max_items: int = 30,
) -> tuple[pd.DataFrame, str]:
    """
    공개 HTML 페이지에서 상품명/URL/리뷰수/현재 노출순위를 읽습니다.
    주의: 이는 판매수량이 아니라 공개 랭킹/노출 신호입니다.
    """
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4가 설치되어 있지 않습니다.")

    headers = {
        "User-Agent": "Mozilla/5.0 TrendPick/1.0",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    seen = set()

    # 일반적인 상품 링크 후보
    selectors = [
        'a[href*="/products/"]',
        'a[href*="/goods/"]',
        'a[href*="/product/"]',
        'a[href*="goodsNo="]',
    ]

    for selector in selectors:
        for a in soup.select(selector):
            href = (a.get("href") or "").strip()
            label = " ".join(a.stripped_strings).strip()
            if not href or not label or len(label) < 3:
                continue

            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            key = (label, href)
            if key in seen:
                continue
            seen.add(key)

            # 너무 긴 카드 전체 텍스트는 앞부분만 사용
            product_name = re.sub(r"\s+", " ", label).strip()
            if len(product_name) > 180:
                product_name = product_name[:180].strip()

            # 링크 주변 카드에서 리뷰수 패턴 탐색
            review_count = 0
            parent_text = ""
            parent = a.parent
            if parent is not None:
                parent_text = " ".join(parent.stripped_strings)
            m = re.search(r"\(([\d,.]+(?:천|만)?\+?)\)", parent_text)
            if m:
                review_count = parse_compact_count(m.group(1))

            candidates.append({
                "검색어": keyword,
                "상품명": product_name,
                "플랫폼": platform_name,
                "현재순위": len(candidates) + 1,
                "이전순위": 0,
                "판매수량": 0,
                "현재리뷰수": review_count,
                "이전리뷰수": 0,
                "상품URL": href,
            })

            if len(candidates) >= max_items:
                break
        if len(candidates) >= max_items:
            break

    df = pd.DataFrame(candidates, columns=PUBLIC_RANKING_COLUMNS)
    return df, ranking_basis


def collect_public_ranking_feeds() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    설정된 공개 랭킹 URL을 1시간 간격으로 읽습니다.
    판매수량으로 오인하지 않도록 판매수량은 항상 0으로 둡니다.
    """
    configs = get_public_rank_feed_config()
    frames = []
    statuses = []

    for i, cfg in enumerate(configs, start=1):
        url = str(cfg.get("url", "")).strip()
        keyword = str(cfg.get("keyword", "")).strip()
        platform = str(cfg.get("platform", "공개랭킹")).strip()
        ranking_basis = str(cfg.get("ranking_basis", "공개 랭킹")).strip()
        max_items = int(cfg.get("max_items", 30) or 30)

        if not url or not keyword:
            continue

        try:
            df, basis = fetch_public_ranking_page(
                url=url,
                keyword=keyword,
                platform_name=platform,
                ranking_basis=ranking_basis,
                max_items=max_items,
            )
            frames.append(df)
            statuses.append({
                "이름": f"PUBLIC_RANK_{i}",
                "플랫폼": platform,
                "유형": basis,
                "상태": "정상",
                "설명": f"{len(df):,}개 상품 랭킹 신호",
            })
        except Exception as exc:
            statuses.append({
                "이름": f"PUBLIC_RANK_{i}",
                "플랫폼": platform,
                "유형": ranking_basis,
                "상태": "오류",
                "설명": str(exc)[:160],
            })

    merged = (
        pd.concat(frames, ignore_index=True, sort=False)
        if frames else pd.DataFrame(columns=PUBLIC_RANKING_COLUMNS)
    )

    return merged, pd.DataFrame(statuses, columns=PARTNER_CONNECTOR_COLUMNS)


def select_rank_signal_products(rank_df: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    """
    판매량이 없는 공개 랭킹 데이터는 '판매TOP'이 아니라 '랭킹 강도'로 별도 계산합니다.
    순위 60 + 리뷰 20 + 검색상승 20 = 100점.
    """
    if rank_df is None or rank_df.empty:
        return pd.DataFrame()

    out = rank_df.copy()

    trend_map = {}
    if isinstance(trends, pd.DataFrame) and not trends.empty and "상품명" in trends.columns:
        trend_map = trends.set_index("상품명")["검색증감률"].to_dict()

    out["검색증감률"] = out["검색어"].map(trend_map).fillna(0)

    out["랭킹점수"] = out["현재순위"].apply(
        lambda r: max(0, 61 - int(r)) if int(r) > 0 else 0
    ).clip(upper=60)

    top_reviews = float(out["현재리뷰수"].max()) if "현재리뷰수" in out.columns else 0
    if top_reviews > 0:
        out["리뷰점수"] = (out["현재리뷰수"] / top_reviews * 20).round(1)
    else:
        out["리뷰점수"] = 0.0

    out["검색점수"] = out["검색증감률"].apply(
        lambda x: 20 if x >= 50 else (15 if x >= 20 else (10 if x >= 10 else (5 if x > 0 else 0)))
    )

    out["랭킹강도"] = (
        out["랭킹점수"] + out["리뷰점수"] + out["검색점수"]
    ).round(1)

    return out.sort_values(
        ["랭킹강도", "현재리뷰수", "현재순위"],
        ascending=[False, False, True]
    ).reset_index(drop=True)



def match_trending_keywords_to_rank_products(
    trends: pd.DataFrame,
    rank_df: pd.DataFrame,
    top_keywords: int = 5,
    per_keyword: int = 5,
) -> pd.DataFrame:
    """
    급상승 검색어와 공개 랭킹 상품 후보를 자동 매칭합니다.

    매칭 방식:
    - rank_df의 '검색어'와 트렌드 '상품명'이 정확히 같으면 우선 매칭
    - 공백 제거 후 포함관계가 있으면 보조 매칭
    - 실제 판매수량은 사용하지 않으며, 랭킹강도 기반 후보만 반환
    """
    if (
        trends is None or getattr(trends, "empty", True)
        or rank_df is None or getattr(rank_df, "empty", True)
    ):
        return pd.DataFrame()

    trend_ranked = trends.copy().sort_values(
        ["검색증감률", "최근지수"],
        ascending=False
    ).head(top_keywords)

    rank_scored = select_rank_signal_products(rank_df, trends)
    if rank_scored.empty:
        return pd.DataFrame()

    rows = []

    for _, trow in trend_ranked.iterrows():
        trend_keyword = str(trow.get("상품명", "")).strip()
        compact_trend = re.sub(r"\s+", "", trend_keyword)

        candidates = rank_scored.copy()
        candidates["_compact_keyword"] = (
            candidates["검색어"].fillna("").astype(str)
            .map(lambda x: re.sub(r"\s+", "", x))
        )

        exact = candidates[
            candidates["_compact_keyword"] == compact_trend
        ].copy()

        if exact.empty:
            exact = candidates[
                candidates["_compact_keyword"].map(
                    lambda x: bool(
                        x and compact_trend
                        and (x in compact_trend or compact_trend in x)
                    )
                )
            ].copy()

        if exact.empty:
            continue

        exact = exact.sort_values(
            ["랭킹강도", "현재순위", "현재리뷰수"],
            ascending=[False, True, False]
        ).head(per_keyword)

        for pos, (_, prow) in enumerate(exact.iterrows(), start=1):
            rows.append({
                "급상승검색어": trend_keyword,
                "검색증감률": float(trow.get("검색증감률", 0)),
                "후보순위": pos,
                "상품명": prow.get("상품명", ""),
                "플랫폼": prow.get("플랫폼", ""),
                "공개현재순위": int(prow.get("현재순위", 0)),
                "리뷰수": int(prow.get("현재리뷰수", 0)),
                "랭킹강도": float(prow.get("랭킹강도", 0)),
                "상품URL": prow.get("상품URL", ""),
            })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values(
        ["검색증감률", "급상승검색어", "후보순위"],
        ascending=[False, True, True]
    ).reset_index(drop=True)


def render_auto_candidate_cards(matched: pd.DataFrame):
    """
    급상승 검색어별 자동 매칭된 구체 상품 후보를 카드로 표시합니다.
    """
    if matched is None or matched.empty:
        st.info(
            "현재 급상승 검색어와 연결된 공개 랭킹 상품 후보가 없습니다. "
            "PUBLIC_RANK_FEEDS_JSON에 해당 검색어의 공식/공개 랭킹 URL을 연결하면 자동 표시됩니다."
        )
        return

    for keyword in matched["급상승검색어"].drop_duplicates().tolist():
        subset = matched[matched["급상승검색어"] == keyword].copy()
        growth = float(subset["검색증감률"].iloc[0])

        st.markdown(f"#### {html.escape(keyword)} · 검색 {growth:+.1f}%")

        cols = st.columns(min(3, len(subset)))
        for i, (_, row) in enumerate(subset.head(3).iterrows()):
            with cols[i]:
                name = html.escape(str(row.get("상품명", "-")))
                platform = html.escape(str(row.get("플랫폼", "-")))
                url = html.escape(str(row.get("상품URL", "#")), quote=True)
                rank = int(row.get("공개현재순위", 0))
                reviews = int(row.get("리뷰수", 0))
                strength = float(row.get("랭킹강도", 0))

                review_text = f"리뷰 {reviews:,}" if reviews > 0 else "리뷰 데이터 없음"

                st.markdown(
                    f"""
                    <div style="border:1px solid #e5e7eb;border-radius:18px;padding:16px;
                                margin-bottom:14px;background:#fff;min-height:220px;">
                      <div style="display:flex;justify-content:space-between;gap:8px;">
                        <span style="font-size:12px;font-weight:900;color:#2563eb;">
                          후보 {i+1}
                        </span>
                        <span style="font-size:12px;font-weight:900;color:#16a34a;">
                          {strength:.0f}점
                        </span>
                      </div>
                      <div style="font-size:12px;color:#64748b;margin-top:10px;">
                        {platform} · 공개순위 {rank}위
                      </div>
                      <div style="font-size:16px;font-weight:900;color:#111827;
                                  margin-top:7px;line-height:1.45;">
                        {name}
                      </div>
                      <div style="font-size:12px;color:#64748b;margin-top:10px;">
                        {review_text}
                      </div>
                      <a href="{url}" target="_blank"
                         style="display:inline-block;margin-top:12px;font-size:12px;
                                font-weight:800;color:#2563eb;text-decoration:none;">
                        상품 보기 →
                      </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.caption(
            "※ 위 후보는 공개 랭킹·리뷰·검색상승을 조합한 상품 후보입니다. "
            "실제 판매수량 TOP으로 확정된 상품은 아닙니다."
        )



@st.cache_data(ttl=3600, show_spinner=False)
def fetch_musinsa_search_candidates(keyword: str, max_items: int = 12) -> tuple[pd.DataFrame, str]:
    """
    무신사 공개 검색결과에서 구체 상품 후보를 수집합니다.
    상품명/브랜드/가격/할인율/리뷰수/이미지 URL을 가능한 범위에서 정리합니다.
    실제 판매수량이나 공식 판매순위로 취급하지 않습니다.
    """
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4가 설치되어 있지 않습니다.")

    from urllib.parse import quote, urljoin

    search_url = (
        "https://www.musinsa.com/search/goods"
        f"?gf=A&keyword={quote(str(keyword))}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = requests.get(search_url, headers=headers, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    rows = []
    seen_urls = set()

    def clean_text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def nearest_card(node):
        card = node
        for _ in range(7):
            if card is None:
                break
            classes = " ".join(card.get("class", [])) if hasattr(card, "get") else ""
            if any(x in classes.lower() for x in ("card", "item", "goods", "product")):
                return card
            card = getattr(card, "parent", None)
        return getattr(node, "parent", None)

    def extract_image(card, link):
        img = None
        if card is not None:
            img = card.find("img")
        if img is None and link is not None:
            img = link.find("img")
        if img is None:
            return ""

        for key in ("src", "data-src", "data-original", "data-lazy-src"):
            val = clean_text(img.get(key))
            if val and not val.startswith("data:"):
                if val.startswith("//"):
                    return "https:" + val
                if val.startswith("/"):
                    return urljoin(search_url, val)
                return val
        return ""

    def extract_price(text_value):
        txt = clean_text(text_value)
        matches = re.findall(r"(\d{1,3}(?:,\d{3})+)\s*원", txt)
        if not matches:
            return 0
        nums = []
        for m in matches:
            try:
                nums.append(int(m.replace(",", "")))
            except Exception:
                pass
        return min(nums) if nums else 0

    def extract_discount(text_value):
        txt = clean_text(text_value)
        vals = re.findall(r"(?<!\d)(\d{1,2})\s*%", txt)
        if not vals:
            return 0
        nums = [int(x) for x in vals if 0 <= int(x) <= 95]
        return max(nums) if nums else 0

    def extract_review(text_value):
        txt = clean_text(text_value)
        patterns = [
            r"\d(?:\.\d)?\s*\(([\d,.]+(?:천|만)?\+?)\)",
            r"리뷰\s*([\d,.]+(?:천|만)?\+?)",
            r"후기\s*([\d,.]+(?:천|만)?\+?)",
        ]
        for pat in patterns:
            m = re.search(pat, txt)
            if m:
                return parse_compact_count(m.group(1))
        return 0

    def guess_brand_and_name(card_text, link_text, img_alt):
        raw = clean_text(card_text)
        link_label = clean_text(link_text)
        alt = clean_text(img_alt)

        # 상품명 후보는 링크 텍스트 → 이미지 alt → 카드 텍스트 순
        name = link_label if 3 <= len(link_label) <= 100 else ""
        if not name and 3 <= len(alt) <= 100:
            name = alt

        # 카드 텍스트에서 가격/할인/평점/혜택 문구 제거
        cleaned = re.sub(r"\d{1,3}(?:,\d{3})+\s*원", " ", raw)
        cleaned = re.sub(r"\b\d{1,2}\s*%", " ", cleaned)
        cleaned = re.sub(r"\d(?:\.\d)?\s*\([\d,.]+(?:천|만)?\+?\)", " ", cleaned)
        cleaned = re.sub(
            r"(무료배송|쿠폰|적립|회원가|오늘출발|무신사|추천|리뷰|후기|품절)",
            " ",
            cleaned,
            flags=re.I
        )
        cleaned = clean_text(cleaned)

        if not name:
            # 너무 긴 카드 텍스트를 그대로 쓰지 않고 앞쪽 의미 단위만 취함
            parts = [p.strip() for p in re.split(r"[\n|·]", cleaned) if p.strip()]
            parts = [p for p in parts if not re.fullmatch(r"[\d,\s원%]+", p)]
            if parts:
                name = parts[-1][:90]

        # 브랜드는 상품명보다 앞에 있는 짧은 텍스트 후보
        brand = ""
        if name and name in raw:
            before = raw.split(name, 1)[0].strip()
            candidates = [
                clean_text(x) for x in re.split(r"[|·/]", before)
                if 1 < len(clean_text(x)) <= 30
            ]
            for c in reversed(candidates):
                if not re.search(r"\d", c) and c.lower() not in ("무신사", "musinsa"):
                    brand = c
                    break

        return brand[:30], clean_text(name)[:100]

    product_links = soup.select(
        'a[href*="/products/"], a[href*="goodsNo="], a[href*="/app/goods/"]'
    )

    for a in product_links:
        href = clean_text(a.get("href"))
        if not href:
            continue
        href = urljoin(search_url, href)

        if href in seen_urls:
            continue

        card = nearest_card(a)
        card_text = clean_text(" ".join(card.stripped_strings)) if card is not None else ""
        link_text = clean_text(" ".join(a.stripped_strings))

        img = card.find("img") if card is not None else a.find("img")
        img_alt = clean_text(img.get("alt")) if img is not None else ""

        brand, product_name = guess_brand_and_name(card_text, link_text, img_alt)

        if len(product_name) < 3:
            continue

        image_url = extract_image(card, a)
        price = extract_price(card_text)
        discount = extract_discount(card_text)
        review_count = extract_review(card_text)

        seen_urls.add(href)
        rows.append({
            "검색어": keyword,
            "상품명": product_name,
            "브랜드": brand,
            "플랫폼": "무신사",
            "현재순위": len(rows) + 1,
            "이전순위": 0,
            "판매수량": 0,
            "현재리뷰수": review_count,
            "이전리뷰수": 0,
            "현재가격": price,
            "할인율": discount,
            "이미지URL": image_url,
            "상품URL": href,
            "근거유형": "무신사 공개 검색결과(추천순)",
            "검색URL": search_url,
        })

        if len(rows) >= max_items:
            break

    return pd.DataFrame(rows), search_url


def collect_musinsa_for_trends(
    trends: pd.DataFrame,
    top_keywords: int = 5,
    per_keyword: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    네이버 급상승 검색어 상위 N개를 무신사 공개 검색결과와 자동 연결합니다.
    """
    if trends is None or getattr(trends, "empty", True):
        return pd.DataFrame(), pd.DataFrame()

    top = trends.sort_values(
        ["검색증감률", "최근지수"],
        ascending=False
    ).head(top_keywords)

    frames = []
    statuses = []

    for _, row in top.iterrows():
        keyword = str(row.get("상품명", "")).strip()
        if not keyword:
            continue

        try:
            df, search_url = fetch_musinsa_search_candidates(
                keyword,
                max_items=per_keyword
            )
            frames.append(df)
            statuses.append({
                "검색어": keyword,
                "검색증감률": float(row.get("검색증감률", 0)),
                "후보수": len(df),
                "상태": "정상" if not df.empty else "상품 링크 미검출",
                "무신사검색": search_url,
            })
        except Exception as exc:
            statuses.append({
                "검색어": keyword,
                "검색증감률": float(row.get("검색증감률", 0)),
                "후보수": 0,
                "상태": f"오류: {str(exc)[:120]}",
                "무신사검색": (
                    "https://www.musinsa.com/search/goods"
                    f"?gf=A&keyword={requests.utils.quote(keyword)}"
                ),
            })

    merged = (
        pd.concat(frames, ignore_index=True, sort=False)
        if frames else pd.DataFrame()
    )

    return merged, pd.DataFrame(statuses)


def score_musinsa_candidates(
    musinsa_df: pd.DataFrame,
    trends: pd.DataFrame,
) -> pd.DataFrame:
    """
    무신사 추천순 노출 + 리뷰 + 네이버 검색상승을 합친 후보점수.
    실제 판매TOP 점수와는 별도입니다.
    """
    if musinsa_df is None or musinsa_df.empty:
        return pd.DataFrame()

    out = musinsa_df.copy()

    trend_map = {}
    if isinstance(trends, pd.DataFrame) and not trends.empty:
        trend_map = trends.set_index("상품명")["검색증감률"].to_dict()

    out["검색증감률"] = out["검색어"].map(trend_map).fillna(0)

    # 추천순 노출 위치 최대 60점
    out["노출점수"] = out["현재순위"].apply(
        lambda r: max(0, 61 - int(r)) if int(r) > 0 else 0
    ).clip(upper=60)

    # 리뷰 최대 20점
    max_reviews = float(out["현재리뷰수"].max()) if not out.empty else 0
    out["리뷰점수"] = (
        (out["현재리뷰수"] / max_reviews * 20).round(1)
        if max_reviews > 0 else 0.0
    )

    # 검색상승 최대 20점
    out["검색점수"] = out["검색증감률"].apply(
        lambda x: 20 if x >= 50 else (
            15 if x >= 20 else (
                10 if x >= 10 else (
                    5 if x > 0 else 0
                )
            )
        )
    )

    out["후보점수"] = (
        out["노출점수"] + out["리뷰점수"] + out["검색점수"]
    ).round(1)

    return out.sort_values(
        ["검색증감률", "검색어", "후보점수", "현재순위"],
        ascending=[False, True, False, True]
    ).reset_index(drop=True)



def build_verified_product_map(sales_df: pd.DataFrame | None) -> dict:
    """
    업로드/제휴 판매근거에서 상품 URL 기준으로 검증 상태를 만듭니다.
    URL이 같으면 가장 강한 판매근거 1건을 사용합니다.
    """
    if sales_df is None or getattr(sales_df, "empty", True):
        return {}

    df = sales_df.copy()

    for col in ["판매수량", "현재순위", "현재리뷰수", "이전리뷰수"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "상품URL" not in df.columns:
        return {}

    df["상품URL"] = df["상품URL"].fillna("").astype(str).str.strip()
    df = df[df["상품URL"].str.startswith(("http://", "https://"))].copy()
    if df.empty:
        return {}

    df["리뷰증가"] = (df["현재리뷰수"] - df["이전리뷰수"]).clip(lower=0)
    df["근거강도"] = (
        (df["판매수량"] > 0).astype(int) * 3
        + (df["현재순위"] > 0).astype(int) * 2
        + (df["리뷰증가"] > 0).astype(int)
    )

    df = df.sort_values(
        ["근거강도", "판매수량", "현재리뷰수"],
        ascending=False
    ).drop_duplicates("상품URL")

    out = {}
    for _, row in df.iterrows():
        evidence = []
        if row["판매수량"] > 0:
            evidence.append(f"판매 {int(row['판매수량']):,}개")
        if row["현재순위"] > 0:
            evidence.append(f"베스트 {int(row['현재순위'])}위")
        if row["리뷰증가"] > 0:
            evidence.append(f"리뷰 +{int(row['리뷰증가']):,}")

        out[row["상품URL"]] = {
            "verified": bool(evidence),
            "evidence": " · ".join(evidence),
            "sales_qty": int(row["판매수량"]),
            "best_rank": int(row["현재순위"]),
            "review_growth": int(row["리뷰증가"]),
            "platform": str(row.get("플랫폼", "")),
        }

    return out


def attach_verification_to_candidates(
    candidates: pd.DataFrame,
    sales_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    후보 상품에 실제 판매근거가 있으면 판매 검증 배지를 붙일 수 있도록 필드를 추가합니다.
    """
    if candidates is None or candidates.empty:
        return candidates

    verified_map = build_verified_product_map(sales_df)
    out = candidates.copy()

    def lookup(url):
        return verified_map.get(str(url).strip(), {})

    out["판매검증"] = out["상품URL"].map(
        lambda u: bool(lookup(u).get("verified", False))
    )
    out["검증근거"] = out["상품URL"].map(
        lambda u: lookup(u).get("evidence", "")
    )
    out["검증판매수량"] = out["상품URL"].map(
        lambda u: lookup(u).get("sales_qty", 0)
    )
    out["검증베스트순위"] = out["상품URL"].map(
        lambda u: lookup(u).get("best_rank", 0)
    )
    out["검증리뷰증가"] = out["상품URL"].map(
        lambda u: lookup(u).get("review_growth", 0)
    )

    # 판매근거가 있으면 후보점수에 가산하되 100점 이내
    if "후보점수" in out.columns:
        out["최종후보점수"] = (
            out["후보점수"]
            + out["판매검증"].astype(int) * 20
        ).clip(upper=100).round(1)
    else:
        out["최종후보점수"] = out["판매검증"].astype(int) * 20

    return out



SNAPSHOT_DIR = Path(os.getenv("TRENDPICK_DATA_DIR", str(Path(__file__).resolve().parent / "sales_sources")))
SNAPSHOT_PATH = SNAPSHOT_DIR / "candidate_snapshots.csv"


def save_candidate_snapshot(candidates: pd.DataFrame) -> None:
    """
    현재 상품 후보의 공개 순위/리뷰를 로컬 이력으로 저장합니다.
    같은 1시간 구간에는 중복 저장하지 않습니다.
    """
    if candidates is None or candidates.empty:
        return

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    bucket = now.replace(
        minute=(now.minute // 10) * 10,
        second=0,
        microsecond=0
    )
    # 같은 시간대에 페이지를 여러 번 새로고침해도 중복 저장되지 않도록
    # 1시간 단위 버킷 사용
    bucket = now.replace(minute=0, second=0, microsecond=0)

    snap = candidates.copy()

    needed = {
        "검색어": "",
        "상품명": "",
        "플랫폼": "",
        "현재순위": 0,
        "현재리뷰수": 0,
        "상품URL": "",
    }
    for col, default in needed.items():
        if col not in snap.columns:
            snap[col] = default

    snap = snap[list(needed.keys())].copy()
    snap["수집시각"] = bucket.strftime("%Y-%m-%d %H:%M:%S")
    snap["수집버킷"] = bucket.strftime("%Y%m%d%H")
    snap["현재순위"] = pd.to_numeric(
        snap["현재순위"], errors="coerce"
    ).fillna(0).astype(int)
    snap["현재리뷰수"] = pd.to_numeric(
        snap["현재리뷰수"], errors="coerce"
    ).fillna(0).astype(int)

    if SNAPSHOT_PATH.exists():
        try:
            old = pd.read_csv(SNAPSHOT_PATH, encoding="utf-8-sig")
        except Exception:
            old = pd.DataFrame()
    else:
        old = pd.DataFrame()

    if not old.empty:
        # 동일 상품/플랫폼/버킷 중복 제거
        existing_keys = set(
            zip(
                old.get("상품URL", pd.Series(dtype=str)).astype(str),
                old.get("플랫폼", pd.Series(dtype=str)).astype(str),
                old.get("수집버킷", pd.Series(dtype=str)).astype(str),
            )
        )
        snap = snap[
            ~snap.apply(
                lambda r: (
                    str(r["상품URL"]),
                    str(r["플랫폼"]),
                    str(r["수집버킷"])
                ) in existing_keys,
                axis=1
            )
        ].copy()

    if snap.empty:
        return

    merged = pd.concat([old, snap], ignore_index=True, sort=False)
    merged.to_csv(SNAPSHOT_PATH, index=False, encoding="utf-8-sig")


def load_candidate_history() -> pd.DataFrame:
    if not SNAPSHOT_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(SNAPSHOT_PATH, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    for col in ["현재순위", "현재리뷰수"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "수집시각" in df.columns:
        df["수집시각_dt"] = pd.to_datetime(
            df["수집시각"], errors="coerce"
        )
    return df


def build_signal_verification(
    current_candidates: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    자동 수집 가능한 공개 신호로 상품별 변화량을 계산합니다.

    검증 신호:
    - 리뷰 증가
    - 공개 노출순위 상승
    - 반복 상위 노출
    - 여러 플랫폼 동시 등장(향후 플랫폼 확장 시 자동 적용)

    이것은 '실제 판매수량 검증'과 구분되는 '판매 신호 검증'입니다.
    """
    if current_candidates is None or current_candidates.empty:
        return pd.DataFrame()

    cur = current_candidates.copy()

    for col in ["현재순위", "현재리뷰수"]:
        if col not in cur.columns:
            cur[col] = 0
        cur[col] = pd.to_numeric(cur[col], errors="coerce").fillna(0)

    rows = []

    # 현재 데이터에서 같은 상품명이 여러 플랫폼에 있는지 확인
    normalized_name = (
        cur["상품명"].fillna("").astype(str)
        .str.lower()
        .str.replace(r"[^0-9a-z가-힣]+", "", regex=True)
    )
    cur["_norm_name"] = normalized_name
    platform_counts = (
        cur.groupby("_norm_name")["플랫폼"].nunique().to_dict()
        if "_norm_name" in cur.columns else {}
    )

    for _, row in cur.iterrows():
        url = str(row.get("상품URL", "")).strip()
        platform = str(row.get("플랫폼", "")).strip()

        prev_rank = 0
        prev_reviews = 0
        appearances = 0

        if (
            history is not None
            and not history.empty
            and "상품URL" in history.columns
        ):
            h = history[
                (history["상품URL"].astype(str) == url)
                & (history["플랫폼"].astype(str) == platform)
            ].copy()

            if not h.empty:
                h = h.sort_values("수집시각_dt")
                appearances = len(h)

                # 현재 스냅샷 직전 데이터
                previous_rows = h.iloc[:-1] if len(h) > 1 else h.iloc[:0]
                if not previous_rows.empty:
                    prev = previous_rows.iloc[-1]
                    prev_rank = int(prev.get("현재순위", 0) or 0)
                    prev_reviews = int(prev.get("현재리뷰수", 0) or 0)

        current_rank = int(row.get("현재순위", 0) or 0)
        current_reviews = int(row.get("현재리뷰수", 0) or 0)

        review_growth = max(0, current_reviews - prev_reviews) if prev_reviews > 0 else 0
        rank_rise = max(0, prev_rank - current_rank) if prev_rank > 0 and current_rank > 0 else 0

        norm = str(row.get("_norm_name", ""))
        platform_count = int(platform_counts.get(norm, 1))

        signals = []
        score = 0

        if review_growth > 0:
            signals.append(f"리뷰 +{review_growth:,}")
            score += min(35, 10 + review_growth)

        if rank_rise > 0:
            signals.append(f"노출순위 +{rank_rise}")
            score += min(25, 10 + rank_rise * 3)

        if appearances >= 2 and current_rank > 0:
            signals.append(f"반복 상위노출 {appearances}회")
            score += min(20, appearances * 5)

        if platform_count >= 2:
            signals.append(f"{platform_count}개 플랫폼 동시등장")
            score += 20

        signal_count = len(signals)

        if signal_count >= 2:
            signal_level = "판매 신호 검증"
        elif signal_count == 1:
            signal_level = "관찰 신호"
        else:
            signal_level = "랭킹 후보"

        rows.append({
            "상품URL": url,
            "이전리뷰수_자동": prev_reviews,
            "리뷰증가_자동": review_growth,
            "이전순위_자동": prev_rank,
            "순위상승_자동": rank_rise,
            "반복노출횟수": appearances,
            "플랫폼수_자동": platform_count,
            "판매신호": signal_level,
            "판매신호근거": " · ".join(signals),
            "판매신호점수": min(100, score),
        })

    sig = pd.DataFrame(rows)
    out = cur.merge(sig, on="상품URL", how="left")
    return out.drop(columns=["_norm_name"], errors="ignore")


def attach_official_and_signal_badges(
    candidates: pd.DataFrame,
    sales_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    '실제 판매 검증'과 '판매 신호 검증'을 분리해 카드에 사용합니다.
    """
    official = attach_verification_to_candidates(candidates, sales_df)

    save_candidate_snapshot(official)
    history = load_candidate_history()
    signal = build_signal_verification(official, history)

    if signal.empty:
        return official

    # 실제 판매 근거가 있으면 최우선
    signal["표시배지"] = signal.apply(
        lambda r: (
            "판매 검증"
            if bool(r.get("판매검증", False))
            else str(r.get("판매신호", "랭킹 후보"))
        ),
        axis=1,
    )

    signal["표시근거"] = signal.apply(
        lambda r: (
            str(r.get("검증근거", ""))
            if bool(r.get("판매검증", False))
            else str(r.get("판매신호근거", ""))
        ),
        axis=1,
    )

    signal["종합후보점수"] = signal.apply(
        lambda r: min(
            100,
            float(r.get("후보점수", 0))
            + (
                20
                if bool(r.get("판매검증", False))
                else float(r.get("판매신호점수", 0)) * 0.25
            ),
        ),
        axis=1,
    ).round(1)

    return signal



def build_one_hour_change_dashboard(signal_df: pd.DataFrame) -> pd.DataFrame:
    """
    현재 후보 데이터에서 1시간 변화 대시보드용 표를 만듭니다.
    """
    if signal_df is None or signal_df.empty:
        return pd.DataFrame()

    out = signal_df.copy()

    defaults = {
        "리뷰증가_자동": 0,
        "순위상승_자동": 0,
        "반복노출횟수": 0,
        "플랫폼수_자동": 1,
        "판매신호점수": 0,
        "판매신호": "랭킹 후보",
        "판매신호근거": "",
        "종합후보점수": 0,
        "검색증감률": 0,
        "현재순위": 0,
        "현재리뷰수": 0,
        "브랜드": "",
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default

    out["1시간변화점수"] = (
        pd.to_numeric(out["리뷰증가_자동"], errors="coerce").fillna(0).clip(upper=50)
        + pd.to_numeric(out["순위상승_자동"], errors="coerce").fillna(0).clip(upper=30) * 2
        + (pd.to_numeric(out["반복노출횟수"], errors="coerce").fillna(0) >= 2).astype(int) * 15
        + (pd.to_numeric(out["플랫폼수_자동"], errors="coerce").fillna(1) >= 2).astype(int) * 20
    ).clip(upper=100).round(1)

    out["변화상태"] = out.apply(
        lambda r: (
            "급상승 신호"
            if r["1시간변화점수"] >= 40
            else ("상승 신호" if r["1시간변화점수"] >= 15 else "관찰")
        ),
        axis=1,
    )

    return out.sort_values(
        ["1시간변화점수", "판매신호점수", "종합후보점수", "검색증감률"],
        ascending=False
    ).reset_index(drop=True)


def render_one_hour_signal_dashboard(signal_df: pd.DataFrame):
    """
    고객용 1시간 변화 판매신호 대시보드.
    """
    st.markdown("## ⏱ 1시간 변화 판매신호 대시보드")
    st.caption(
        "1시간 전과 비교한 리뷰 증가·공개 노출순위 상승·반복 상위노출을 기준으로 "
        "상품별 판매 신호 변화를 보여줍니다."
    )

    dash = build_one_hour_change_dashboard(signal_df)

    if dash.empty:
        st.info("아직 표시할 판매신호 데이터가 없습니다.")
        return

    history_df = load_candidate_history()
    if history_df is None or history_df.empty:
        history_buckets = 0
    else:
        history_buckets = (
            history_df["수집버킷"].astype(str).nunique()
            if "수집버킷" in history_df.columns else 0
        )

    changed = dash[
        (pd.to_numeric(dash["리뷰증가_자동"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(dash["순위상승_자동"], errors="coerce").fillna(0) > 0)
    ].copy()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("추적 상품", f"{len(dash):,}개")
    m2.metric("1시간 상승 신호", f"{len(changed):,}개")
    m3.metric(
        "리뷰 증가",
        f"+{int(pd.to_numeric(dash['리뷰증가_자동'], errors='coerce').fillna(0).sum()):,}"
    )
    m4.metric("누적 시간대", f"{history_buckets}개")

    if history_buckets < 2:
        st.warning(
            "첫 번째 시간대 데이터가 저장된 상태입니다. "
            "다음 1시간 데이터가 쌓이면 리뷰 증가·순위 상승이 본격적으로 계산됩니다."
        )

    top = dash.head(10).copy()

    st.markdown("### 1시간 변화 TOP 10")
    view_cols = [
        "검색어", "브랜드", "상품명", "플랫폼",
        "현재순위", "현재리뷰수",
        "리뷰증가_자동", "순위상승_자동",
        "판매신호", "판매신호근거",
        "1시간변화점수", "변화상태", "상품URL"
    ]
    available = [c for c in view_cols if c in top.columns]

    st.dataframe(
        top[available],
        width="stretch",
        hide_index=True,
        column_config={
            "상품URL": st.column_config.LinkColumn("상품", display_text="보기"),
            "1시간변화점수": st.column_config.NumberColumn("1시간 변화점수", format="%.1f"),
            "리뷰증가_자동": st.column_config.NumberColumn("리뷰 증가", format="%d"),
            "순위상승_자동": st.column_config.NumberColumn("순위 상승", format="%d"),
        },
    )

    # 리뷰 증가 차트
    review_chart = top[
        ["상품명", "리뷰증가_자동"]
    ].copy()
    review_chart["리뷰증가_자동"] = pd.to_numeric(
        review_chart["리뷰증가_자동"], errors="coerce"
    ).fillna(0)

    if review_chart["리뷰증가_자동"].sum() > 0:
        st.markdown("### 리뷰 증가")
        chart = (
            alt.Chart(review_chart)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("리뷰증가_자동:Q", title="1시간 리뷰 증가"),
                y=alt.Y("상품명:N", sort="-x", title=None),
                tooltip=[
                    "상품명",
                    alt.Tooltip("리뷰증가_자동:Q", title="리뷰 증가")
                ],
            )
            .properties(height=max(260, len(review_chart) * 30))
        )
        st.altair_chart(chart, width="stretch")

    # 순위 상승 차트
    rank_chart = top[
        ["상품명", "순위상승_자동"]
    ].copy()
    rank_chart["순위상승_자동"] = pd.to_numeric(
        rank_chart["순위상승_자동"], errors="coerce"
    ).fillna(0)

    if rank_chart["순위상승_자동"].sum() > 0:
        st.markdown("### 공개 노출순위 상승")
        chart2 = (
            alt.Chart(rank_chart)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("순위상승_자동:Q", title="1시간 순위 상승폭"),
                y=alt.Y("상품명:N", sort="-x", title=None),
                tooltip=[
                    "상품명",
                    alt.Tooltip("순위상승_자동:Q", title="순위 상승")
                ],
            )
            .properties(height=max(260, len(rank_chart) * 30))
        )
        st.altair_chart(chart2, width="stretch")


@st.fragment(run_every="1h")
def render_hourly_auto_tracker(
    trends: pd.DataFrame,
):
    """
    판매TOP 페이지가 열려 있는 동안 1시간마다 자동으로 다시 수집하고
    스냅샷을 저장한 뒤 1시간 변화 대시보드를 갱신합니다.
    """
    st.markdown("### 🔄 자동 갱신 상태")

    now = datetime.now()
    next_run = (now + timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("갱신 주기", "1시간")
    c2.metric("마지막 갱신", now.strftime("%H:%M"))
    c3.metric("다음 예정", next_run.strftime("%H:%M"))

    if trends is None or getattr(trends, "empty", True):
        st.warning("트렌드 데이터가 없어 자동 추적을 실행하지 못했습니다.")
        return

    try:
        with st.spinner("1시간 판매신호 데이터를 갱신하는 중..."):
            fresh_candidates, _ = collect_musinsa_for_trends(
                trends,
                top_keywords=5,
                per_keyword=8,
            )

            fresh_scored = score_musinsa_candidates(
                fresh_candidates,
                trends,
            )

            sales_evidence = st.session_state.get("sales_data")
            tracked = attach_official_and_signal_badges(
                fresh_scored,
                sales_evidence
                if isinstance(sales_evidence, pd.DataFrame)
                else pd.DataFrame(),
            )

        if tracked is None or tracked.empty:
            st.info("이번 갱신에서 추적할 상품 후보를 찾지 못했습니다.")
            return

        # 가장 최근 자동 추적 결과도 세션에 보관
        st.session_state["hourly_signal_data"] = tracked
        st.session_state["hourly_signal_updated_at"] = now.isoformat()

        render_one_hour_signal_dashboard(tracked)

    except Exception as exc:
        st.error(f"1시간 자동 갱신 오류: {exc}")



def build_exact_hourly_change_from_history(history: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    저장된 스냅샷의 가장 최근 시간대와 바로 이전 시간대를 정확히 비교합니다.

    핵심:
    - 현재/이전 양쪽 상품을 OUTER JOIN 하여 신규진입과 랭킹이탈을 모두 감지
    - 랭킹이탈은 '판매 상승'으로 보지 않고 별도 품질/이탈 신호로 기록
    - 이전 대비 현재 수집 커버리지가 급격히 낮아지면 수집불안정으로 표시

    반환:
      - 상품별 1시간 변화 DataFrame
      - 비교 메타정보
    """
    meta = {
        "current_bucket": "-",
        "previous_bucket": "-",
        "current_count": 0,
        "previous_count": 0,
        "matched_count": 0,
        "new_count": 0,
        "rise_count": 0,
        "fall_count": 0,
        "review_up_count": 0,
        "dropout_count": 0,
        "coverage_ratio": 1.0,
        "collection_unstable": False,
    }

    if history is None or history.empty or "수집버킷" not in history.columns:
        return pd.DataFrame(), meta

    df = history.copy()

    for col in ["현재순위", "현재리뷰수", "현재가격", "할인율"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["수집버킷"] = df["수집버킷"].astype(str)
    buckets = sorted([b for b in df["수집버킷"].dropna().unique().tolist() if b])

    if not buckets:
        return pd.DataFrame(), meta

    current_bucket = buckets[-1]
    previous_bucket = buckets[-2] if len(buckets) >= 2 else None

    cur = df[df["수집버킷"] == current_bucket].copy()
    prev = (
        df[df["수집버킷"] == previous_bucket].copy()
        if previous_bucket else pd.DataFrame(columns=df.columns)
    )

    meta["current_bucket"] = current_bucket
    meta["previous_bucket"] = previous_bucket or "-"

    key_cols = ["상품URL", "플랫폼"]

    info_cols = [
        "검색어", "상품ID", "브랜드", "상품명", "플랫폼",
        "현재순위", "현재리뷰수", "현재가격", "할인율",
        "이미지URL", "상품URL", "수집시각", "수집버킷"
    ]
    for c in info_cols:
        if c not in cur.columns:
            cur[c] = 0 if c in ["현재순위", "현재리뷰수", "현재가격", "할인율"] else ""
        if c not in prev.columns:
            prev[c] = 0 if c in ["현재순위", "현재리뷰수", "현재가격", "할인율"] else ""

    cur = cur[info_cols].drop_duplicates(key_cols, keep="last")
    prev = prev[info_cols].drop_duplicates(key_cols, keep="last")

    meta["current_count"] = len(cur)
    meta["previous_count"] = len(prev)

    # 이전 스냅샷의 상품정보를 명확히 구분
    prev = prev.rename(columns={
        "검색어": "이전검색어",
        "상품ID": "이전상품ID",
        "브랜드": "이전브랜드",
        "상품명": "이전상품명",
        "현재순위": "이전순위",
        "현재리뷰수": "이전리뷰수",
        "현재가격": "이전가격",
        "할인율": "이전할인율",
        "이미지URL": "이전이미지URL",
        "수집시각": "이전수집시각",
        "수집버킷": "이전수집버킷",
    })

    # OUTER JOIN: 신규진입 + 현재에서 사라진 상품까지 모두 보존
    merged = cur.merge(
        prev,
        on=key_cols,
        how="outer",
        indicator=True,
    )

    # 이탈 행은 현재 상품정보가 비어 있으므로 이전 상품정보로 화면용 필드를 보완
    fallback_pairs = [
        ("검색어", "이전검색어"),
        ("상품ID", "이전상품ID"),
        ("브랜드", "이전브랜드"),
        ("상품명", "이전상품명"),
        ("이미지URL", "이전이미지URL"),
    ]
    for cur_col, prev_col in fallback_pairs:
        if cur_col not in merged.columns:
            merged[cur_col] = ""
        if prev_col in merged.columns:
            cur_series = merged[cur_col].fillna("").astype(str)
            prev_series = merged[prev_col].fillna("").astype(str)
            merged[cur_col] = cur_series.where(cur_series.str.strip().ne(""), prev_series)

    for col in ["현재순위", "현재리뷰수", "현재가격", "할인율", "이전순위", "이전리뷰수"]:
        if col not in merged.columns:
            merged[col] = 0
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    merged["신규진입"] = merged["_merge"].eq("left_only")
    merged["이탈감지"] = merged["_merge"].eq("right_only")
    merged["동일상품비교"] = merged["_merge"].eq("both")

    meta["matched_count"] = int(merged["동일상품비교"].sum())
    meta["new_count"] = int(merged["신규진입"].sum())
    meta["dropout_count"] = int(merged["이탈감지"].sum())

    # 수집 커버리지: 이전 상품 중 현재에도 잡힌 비율
    if meta["previous_count"] > 0:
        meta["coverage_ratio"] = round(
            meta["matched_count"] / meta["previous_count"], 4
        )
    else:
        meta["coverage_ratio"] = 1.0

    # 이전 대비 20% 이상이 한꺼번에 사라지면 수집불안정 가능성 경고
    meta["collection_unstable"] = bool(
        meta["previous_count"] >= 10
        and meta["coverage_ratio"] < 0.80
    )

    # 리뷰 증가: 동일 상품끼리만 계산
    merged["리뷰증가"] = 0
    matched_mask = merged["동일상품비교"]
    merged.loc[matched_mask, "리뷰증가"] = (
        merged.loc[matched_mask, "현재리뷰수"]
        - merged.loc[matched_mask, "이전리뷰수"]
    )

    # 순위 변화: +면 상승, -면 하락. 신규/이탈은 별도 상태로 관리
    merged["순위변화"] = 0
    rank_mask = (
        matched_mask
        & (merged["이전순위"] > 0)
        & (merged["현재순위"] > 0)
    )
    merged.loc[rank_mask, "순위변화"] = (
        merged.loc[rank_mask, "이전순위"]
        - merged.loc[rank_mask, "현재순위"]
    )

    def status_row(r):
        if bool(r["이탈감지"]):
            return "랭킹 이탈/미수집"
        if bool(r["신규진입"]):
            return "신규 진입"
        if int(r["리뷰증가"]) > 0 and int(r["순위변화"]) > 0:
            return "강한 상승"
        if int(r["리뷰증가"]) > 0:
            return "리뷰 상승"
        if int(r["순위변화"]) > 0:
            return "순위 상승"
        if int(r["순위변화"]) < 0:
            return "순위 하락"
        return "변화 없음"

    merged["1시간상태"] = merged.apply(status_row, axis=1)

    # 긍정 변화 점수:
    # 이탈은 판매상승 신호가 아니므로 점수를 주지 않음
    merged["1시간변화점수"] = (
        merged["리뷰증가"].clip(lower=0, upper=40)
        + merged["순위변화"].clip(lower=0, upper=20) * 2
        + merged["신규진입"].astype(int) * 15
    ).clip(upper=100).astype(float)

    merged.loc[merged["이탈감지"], "1시간변화점수"] = 0.0

    # 이탈은 별도 위험신호로 기록
    merged["이탈위험점수"] = 0.0
    merged.loc[merged["이탈감지"], "이탈위험점수"] = 100.0

    meta["rise_count"] = int((merged["순위변화"] > 0).sum())
    meta["fall_count"] = int((merged["순위변화"] < 0).sum())
    meta["review_up_count"] = int((merged["리뷰증가"] > 0).sum())

    # 긍정 변화 우선, 이탈은 뒤쪽 별도 관찰
    merged = merged.sort_values(
        ["이탈감지", "1시간변화점수", "리뷰증가", "순위변화", "현재순위"],
        ascending=[True, False, False, False, True]
    ).reset_index(drop=True)

    return merged, meta


def render_exact_hourly_change_dashboard():
    """
    백그라운드 수집 스냅샷을 기준으로 '정확히 이전 시간대 대비' 변화를 표시합니다.
    """
    st.markdown("## ⏱ 1시간 전 대비 실변화 대시보드")
    st.caption(
        "백그라운드 수집기가 저장한 가장 최근 시간대와 바로 이전 시간대를 직접 비교합니다."
    )

    history = load_candidate_history()
    changes, meta = build_exact_hourly_change_from_history(history)

    if history is None or history.empty:
        st.info("아직 백그라운드 수집 이력이 없습니다.")
        return

    if meta["previous_bucket"] == "-":
        st.warning(
            "현재 시간대 데이터는 저장됐지만 이전 시간대 데이터가 아직 없습니다. "
            "다음 자동수집 이후부터 1시간 전 대비 변화가 계산됩니다."
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("신규 진입", f"{meta['new_count']}개")
    m2.metric("순위 상승", f"{meta['rise_count']}개")
    m3.metric("리뷰 증가", f"{meta['review_up_count']}개")
    m4.metric("순위 하락", f"{meta['fall_count']}개")
    m5.metric("랭킹 이탈", f"{meta['dropout_count']}개")

    st.caption(
        f"비교 시간대: {meta['previous_bucket']} → {meta['current_bucket']} · "
        f"현재 {meta['current_count']}개 / 이전 {meta['previous_count']}개 · "
        f"이탈 {meta['dropout_count']}개 · "
        f"수집 커버리지 {meta['coverage_ratio']*100:.0f}%"
    )

    if meta.get("collection_unstable", False):
        st.warning(
            "이전 시간대 대비 수집 커버리지가 80% 미만입니다. "
            "랭킹 이탈과 수집 누락을 구분하기 위해 이탈 상품은 상승/하락 점수에 반영하지 않습니다."
        )

    if changes.empty:
        st.info("비교 가능한 상품 데이터가 없습니다.")
        return

    st.markdown("### 1시간 변화 TOP 10")

    top10 = changes[
        ~changes.get("이탈감지", pd.Series(False, index=changes.index)).fillna(False).astype(bool)
    ].head(10).copy()
    display_cols = [
        "검색어", "상품명", "플랫폼",
        "이전순위", "현재순위", "순위변화",
        "이전리뷰수", "현재리뷰수", "리뷰증가",
        "1시간상태", "1시간변화점수", "상품URL"
    ]
    available = [c for c in display_cols if c in top10.columns]

    st.dataframe(
        top10[available],
        width="stretch",
        hide_index=True,
        column_config={
            "상품URL": st.column_config.LinkColumn("상품", display_text="보기"),
            "순위변화": st.column_config.NumberColumn("순위 변화", format="%+d"),
            "리뷰증가": st.column_config.NumberColumn("리뷰 증가", format="%+d"),
            "1시간변화점수": st.column_config.NumberColumn(
                "1시간 변화점수", format="%.0f"
            ),
        },
    )

    # 실제 변화가 있는 상품만 그래프
    changed = changes[
        (
            (changes["리뷰증가"] != 0)
            | (changes["순위변화"] != 0)
            | (changes["신규진입"])
        )
        & (~changes.get("이탈감지", pd.Series(False, index=changes.index)).fillna(False).astype(bool))
    ].head(15).copy()

    if not changed.empty:
        chart_df = changed[
            ["상품명", "1시간변화점수", "1시간상태"]
        ].copy()

        chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("1시간변화점수:Q", title="1시간 변화점수"),
                y=alt.Y("상품명:N", sort="-x", title=None),
                tooltip=[
                    "상품명",
                    "1시간상태",
                    alt.Tooltip("1시간변화점수:Q", format=".0f"),
                ],
            )
            .properties(height=max(280, len(chart_df) * 32))
        )
        st.altair_chart(chart, width="stretch")

    dropouts = changes[
        changes.get("이탈감지", pd.Series(False, index=changes.index)).fillna(False).astype(bool)
    ].copy()

    if not dropouts.empty:
        with st.expander(f"랭킹 이탈/미수집 {len(dropouts)}개 보기", expanded=False):
            dropout_cols = [
                "검색어", "상품명", "플랫폼", "이전순위",
                "이전리뷰수", "1시간상태", "상품URL"
            ]
            available_drop = [c for c in dropout_cols if c in dropouts.columns]
            st.dataframe(
                dropouts[available_drop],
                width="stretch",
                hide_index=True,
                column_config={
                    "상품URL": st.column_config.LinkColumn("상품", display_text="보기")
                },
            )
            st.caption(
                "※ 이탈은 실제 판매 하락을 의미하지 않을 수 있습니다. "
                "공개 랭킹에서 빠졌거나 해당 시간 수집에서 누락된 경우를 함께 포함합니다."
            )

    st.caption(
        "※ 이 대시보드는 실제 판매수량이 아니라 공개 순위·리뷰 변화 데이터를 비교한 판매 신호입니다. "
        "공식/제휴 판매수량이 연결된 경우에는 별도의 `판매 검증` 근거로 표시됩니다."
    )



def render_sales_top_integrated_dashboard(
    trends: pd.DataFrame,
    current_candidates: pd.DataFrame,
):
    """
    고객용 판매TOP 통합 대시보드.
    기존 '자동갱신 대시보드'와 '1시간 실변화 대시보드'를 하나로 합칩니다.
    """
    st.markdown("## ⏱ 1시간 판매신호")
    st.caption(
        "백그라운드 자동수집 데이터를 기준으로 1시간 전 대비 실제 변화가 감지된 상품만 보여줍니다."
    )

    # 백그라운드 수집 상태
    status_path = Path(__file__).resolve().parent / "sales_sources" / "collector_status.json"
    last_run = "-"
    products_count = 0
    keywords_count = 0
    status_message = ""

    if status_path.exists():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            last_run = status.get("last_run", "-")
            products_count = int(status.get("products", 0) or 0)
            keywords_count = int(status.get("keywords", 0) or 0)
            status_message = str(status.get("message", "") or "")
        except Exception:
            pass

    history = load_candidate_history()
    changes, meta = build_exact_hourly_change_from_history(history)

    # 상단 지표
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("추적 상품", f"{products_count:,}개")
    m2.metric("신규 진입", f"{meta.get('new_count', 0)}개")
    m3.metric("순위 상승", f"{meta.get('rise_count', 0)}개")
    m4.metric("리뷰 증가", f"{meta.get('review_up_count', 0)}개")

    if last_run != "-":
        st.caption(
            f"마지막 자동수집 {last_run} · 급상승 검색어 {keywords_count}개 · "
            f"비교 시간대 {meta.get('previous_bucket','-')} → {meta.get('current_bucket','-')}"
        )

    if status_message:
        st.caption(status_message)

    if history is None or history.empty:
        st.info("아직 백그라운드 수집 이력이 없습니다.")
        return

    if meta.get("previous_bucket", "-") == "-":
        st.warning(
            "첫 시간대 데이터가 저장된 상태입니다. 다음 자동수집 이후부터 실제 1시간 전 대비 변화가 계산됩니다."
        )

    # TOP 10
    st.markdown("### 1시간 변화 TOP 10")

    if changes is None or changes.empty:
        st.info("아직 비교 가능한 상품 변화가 없습니다.")
    else:
        top10 = changes.head(10).copy()

        # v2 수집기 스냅샷에 저장된 상품정보를 우선 사용하고,
        # 구형 스냅샷은 현재 후보 데이터로 보완
        enriched = enrich_changes_from_snapshot(top10)
        needs_fallback = (
            enriched.get("이미지URL", pd.Series(index=enriched.index, dtype=object))
            .fillna("").astype(str).eq("").any()
        )
        if needs_fallback:
            enriched = enrich_changes_with_current_candidates(
                enriched,
                current_candidates
            )

        moving = enriched[
            (pd.to_numeric(enriched["리뷰증가"], errors="coerce").fillna(0) > 0)
            | (pd.to_numeric(enriched["순위변화"], errors="coerce").fillna(0) != 0)
            | (enriched["신규진입"].astype(bool))
        ].copy()

        # 변화점수까지 0인 행은 최종 카드에서 제외
        if "1시간변화점수" in moving.columns:
            moving = moving[
                pd.to_numeric(
                    moving["1시간변화점수"], errors="coerce"
                ).fillna(0) > 0
            ].copy()

        if moving.empty:
            st.info(
                "현재 1시간 구간에서 실제 변화가 감지된 상품이 없습니다. "
                "다음 자동수집 때 변화가 생기면 이 영역에 자동으로 표시됩니다."
            )
        else:
            card_cols = st.columns(3)
            for i, (_, row) in enumerate(moving.head(6).iterrows()):
                with card_cols[i % 3]:
                    name = html.escape(str(row.get("상품명", "-")))
                    brand = html.escape(str(row.get("브랜드", "") or ""))
                    image_url = html.escape(str(row.get("이미지URL", "") or ""), quote=True)
                    url = html.escape(str(row.get("상품URL", "#")), quote=True)
                    price = int(row.get("현재가격", 0) or 0) if pd.notna(row.get("현재가격", 0)) else 0
                    discount = int(row.get("할인율", 0) or 0) if pd.notna(row.get("할인율", 0)) else 0
                    rank_change = int(row.get("순위변화", 0) or 0)
                    review_growth = int(row.get("리뷰증가", 0) or 0)
                    state = html.escape(str(row.get("1시간상태", "변화 없음")))
                    score = float(row.get("1시간변화점수", 0) or 0)

                    image_html = (
                        f'<img src="{image_url}" alt="{name}" '
                        'style="width:100%;height:160px;object-fit:cover;border-radius:14px;background:#f8fafc;" />'
                        if image_url else
                        '<div style="width:100%;height:160px;border-radius:14px;background:#f8fafc;'
                        'display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:12px;">이미지 없음</div>'
                    )

                    price_html = (
                        '<div style="margin-top:8px;display:flex;align-items:center;gap:6px;">'
                        + (f'<span style="font-size:12px;font-weight:900;color:#ef4444;">{discount}%</span>' if discount > 0 else '')
                        + f'<span style="font-size:17px;font-weight:900;color:#111827;">{price:,}원</span>'
                        + '</div>'
                        if price > 0 else ''
                    )

                    st.markdown(
                        f"""
                        <div style="border:1px solid #e5e7eb;border-radius:18px;padding:12px;
                                    margin-bottom:14px;background:#fff;min-height:360px;">
                          {image_html}
                          <div style="display:flex;justify-content:space-between;margin-top:11px;">
                            <span style="font-size:11px;font-weight:900;color:#2563eb;">TOP {i+1}</span>
                            <span style="font-size:11px;font-weight:900;color:#16a34a;">{score:.0f}점</span>
                          </div>
                          <div style="font-size:11px;color:#64748b;margin-top:7px;">
                            {brand if brand else '브랜드 미확인'}
                          </div>
                          <div style="font-size:15px;font-weight:900;color:#111827;margin-top:5px;
                                      line-height:1.45;min-height:44px;">{name}</div>
                          {price_html}
                          <div style="font-size:12px;font-weight:800;color:#7c3aed;margin-top:9px;">{state}</div>
                          <div style="font-size:11px;color:#64748b;margin-top:6px;">
                            순위 {rank_change:+d} · 리뷰 {review_growth:+d}
                          </div>
                          <a href="{url}" target="_blank"
                             style="display:inline-block;margin-top:11px;font-size:12px;font-weight:800;
                                    color:#2563eb;text-decoration:none;">상품 보기 →</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # 상세 표
        with st.expander("1시간 변화 TOP 10 상세 보기", expanded=False):
            display_cols = [
                "검색어", "상품명", "플랫폼",
                "이전순위", "현재순위", "순위변화",
                "이전리뷰수", "현재리뷰수", "리뷰증가",
                "1시간상태", "1시간변화점수", "이미지매칭", "상품URL"
            ]
            available = [c for c in display_cols if c in changes.columns]
            detail_source = (
                moving.head(10)
                if 'moving' in locals() and isinstance(moving, pd.DataFrame) and not moving.empty
                else changes.head(10)
            )
            detail_available = [c for c in display_cols if c in detail_source.columns]
            st.dataframe(
                detail_source[detail_available],
                width="stretch",
                hide_index=True,
                column_config={
                    "상품URL": st.column_config.LinkColumn("상품", display_text="보기"),
                    "순위변화": st.column_config.NumberColumn("순위 변화", format="%+d"),
                    "리뷰증가": st.column_config.NumberColumn("리뷰 증가", format="%+d"),
                    "1시간변화점수": st.column_config.NumberColumn("변화점수", format="%.0f"),
                },
            )

        # 변화 그래프
        changed = (
            moving.head(15).copy()
            if 'moving' in locals() and isinstance(moving, pd.DataFrame)
            else pd.DataFrame()
        )

        if not changed.empty:
            st.markdown("### 변화 강도")
            chart_df = changed[
                ["상품명", "1시간변화점수", "1시간상태", "순위변화", "리뷰증가"]
            ].copy()

            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusEnd=5)
                .encode(
                    x=alt.X(
                        "1시간변화점수:Q",
                        title="1시간 변화점수",
                        scale=alt.Scale(domain=[0, max(10, float(chart_df["1시간변화점수"].max()) * 1.15)])
                    ),
                    y=alt.Y(
                        "상품명:N",
                        sort="-x",
                        title=None,
                        axis=alt.Axis(labelLimit=240)
                    ),
                    tooltip=[
                        "상품명",
                        "1시간상태",
                        alt.Tooltip("순위변화:Q", title="순위 변화", format="+.0f"),
                        alt.Tooltip("리뷰증가:Q", title="리뷰 증가", format="+.0f"),
                        alt.Tooltip("1시간변화점수:Q", title="변화점수", format=".0f"),
                    ],
                )
                .properties(height=max(220, len(chart_df) * 34))
            )
            st.altair_chart(chart, width="stretch")

    st.caption(
        "※ 이 대시보드는 공개 검색 노출순위·리뷰 변화 기반 판매신호입니다. "
        "공식/제휴 판매수량이 연결된 상품은 별도의 `판매 검증` 근거가 우선 적용됩니다."
    )



def normalize_product_url(url: str) -> str:
    """
    상품 URL을 비교 가능한 형태로 정규화합니다.
    추적 파라미터/프래그먼트를 제거하고 무신사 상품 ID 중심으로 맞춥니다.
    """
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

    s = str(url or "").strip()
    if not s:
        return ""

    try:
        p = urlparse(s)
        path = p.path.rstrip("/")

        # 무신사 /products/{id}, /app/goods/{id} 형태를 상품 ID 기준으로 통일
        m = re.search(r"/products/(\d+)", path)
        if not m:
            m = re.search(r"/app/goods/(\d+)", path)
        if m:
            return f"musinsa:{m.group(1)}"

        qs = dict(parse_qsl(p.query, keep_blank_values=False))
        for key in ("goodsNo", "goods_no", "productId", "product_id"):
            if key in qs and str(qs[key]).strip():
                return f"{p.netloc.lower()}:{key}:{str(qs[key]).strip()}"

        # 일반 URL은 추적성 파라미터 제거
        drop = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "source", "ref", "tracking"
        }
        kept = [(k, v) for k, v in parse_qsl(p.query) if k not in drop]
        clean = p._replace(
            scheme=p.scheme.lower(),
            netloc=p.netloc.lower(),
            path=path,
            query=urlencode(kept),
            fragment=""
        )
        return urlunparse(clean)
    except Exception:
        return s


def build_candidate_enrichment_map(current_candidates: pd.DataFrame) -> pd.DataFrame:
    """
    현재 후보 카드의 이미지/브랜드/가격 정보를 정규화 URL 기준으로 준비합니다.
    """
    if current_candidates is None or current_candidates.empty:
        return pd.DataFrame()

    cur = current_candidates.copy()
    if "상품URL" not in cur.columns:
        return pd.DataFrame()

    cur["_norm_url"] = cur["상품URL"].map(normalize_product_url)

    cols = ["_norm_url", "상품URL"]
    for c in ["브랜드", "이미지URL", "현재가격", "할인율", "상품명"]:
        if c in cur.columns:
            cols.append(c)

    return (
        cur[cols]
        .dropna(subset=["_norm_url"])
        .drop_duplicates("_norm_url", keep="first")
    )



def extract_product_id(url: str) -> str:
    """무신사 등 상품 URL에서 안정적인 상품 ID를 추출합니다."""
    s = str(url or "").strip()
    if not s:
        return ""
    patterns = [
        r"/products/(\d+)",
        r"/app/goods/(\d+)",
        r"[?&]goodsNo=(\d+)",
        r"[?&]goods_no=(\d+)",
        r"[?&]productId=(\d+)",
        r"[?&]product_id=(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    return ""


def normalize_product_name(name: str) -> str:
    """
    상품명 비교용 정규화.
    괄호/특수문자/공백을 제거하고 소문자화합니다.
    """
    s = str(name or "").lower()
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", s)
    s = re.sub(r"[^0-9a-z가-힣]+", "", s)
    return s.strip()


def enrich_changes_with_current_candidates(
    changes: pd.DataFrame,
    current_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """
    1시간 변화 데이터에 현재 후보의 이미지/브랜드/가격을
    1) 상품ID
    2) 정규화 URL
    3) 정규화 상품명
    순으로 매칭합니다.
    """
    if changes is None or changes.empty:
        return changes
    out = changes.copy()

    if current_candidates is None or current_candidates.empty:
        return out

    cur = current_candidates.copy()

    for frame in (out, cur):
        if "상품URL" not in frame.columns:
            frame["상품URL"] = ""
        if "상품명" not in frame.columns:
            frame["상품명"] = ""
        frame["_product_id"] = frame["상품URL"].map(extract_product_id)
        frame["_norm_url"] = frame["상품URL"].map(normalize_product_url)
        frame["_norm_name"] = frame["상품명"].map(normalize_product_name)

    enrich_cols = [
        c for c in [
            "_product_id", "_norm_url", "_norm_name",
            "브랜드", "이미지URL", "현재가격", "할인율", "상품명"
        ]
        if c in cur.columns
    ]
    enrich = cur[enrich_cols].copy()

    # 1) 상품 ID 우선 매칭
    if "_product_id" in enrich.columns:
        by_id = enrich[
            enrich["_product_id"].astype(str).ne("")
        ].drop_duplicates("_product_id", keep="first")

        out = out.merge(
            by_id,
            on="_product_id",
            how="left",
            suffixes=("", "_idmatch"),
        )

    # 2) URL 정규화 보완
    need_url = (
        out.get("이미지URL", pd.Series(index=out.index, dtype=object))
        .fillna("").astype(str).eq("")
        if "이미지URL" in out.columns
        else pd.Series(True, index=out.index)
    )

    by_url = enrich[
        enrich["_norm_url"].astype(str).ne("")
    ].drop_duplicates("_norm_url", keep="first")

    url_fields = [
        c for c in ["_norm_url", "브랜드", "이미지URL", "현재가격", "할인율", "상품명"]
        if c in by_url.columns
    ]
    url_map = by_url[url_fields].rename(columns={
        "브랜드": "브랜드_urlmatch",
        "이미지URL": "이미지URL_urlmatch",
        "현재가격": "현재가격_urlmatch",
        "할인율": "할인율_urlmatch",
        "상품명": "상품명_urlmatch",
    })
    out = out.merge(url_map, on="_norm_url", how="left")

    # 3) 상품명 정규화 보완
    by_name = enrich[
        enrich["_norm_name"].astype(str).str.len().ge(5)
    ].drop_duplicates("_norm_name", keep="first")

    name_fields = [
        c for c in ["_norm_name", "브랜드", "이미지URL", "현재가격", "할인율", "상품명"]
        if c in by_name.columns
    ]
    name_map = by_name[name_fields].rename(columns={
        "브랜드": "브랜드_namematch",
        "이미지URL": "이미지URL_namematch",
        "현재가격": "현재가격_namematch",
        "할인율": "할인율_namematch",
        "상품명": "상품명_namematch",
    })
    out = out.merge(name_map, on="_norm_name", how="left")

    # 매칭 우선순위 정리
    def choose(row, base, id_suffix="_idmatch", url_suffix="_urlmatch", name_suffix="_namematch"):
        candidates = [
            row.get(base),
            row.get(base + id_suffix),
            row.get(base + url_suffix),
            row.get(base + name_suffix),
        ]
        for v in candidates:
            if pd.notna(v) and str(v).strip() not in ("", "0", "nan", "None"):
                return v
        return ""

    for field in ["브랜드", "이미지URL", "현재가격", "할인율", "상품명"]:
        out[field] = out.apply(lambda r, f=field: choose(r, f), axis=1)

    # 매칭 경로 표시
    def match_type(row):
        if str(row.get("_product_id", "")).strip() and str(row.get("이미지URL_idmatch", "") or "").strip():
            return "상품ID"
        if str(row.get("이미지URL_urlmatch", "") or "").strip():
            return "URL"
        if str(row.get("이미지URL_namematch", "") or "").strip():
            return "상품명"
        return "미매칭"

    out["이미지매칭"] = out.apply(match_type, axis=1)
    return out



def enrich_changes_from_snapshot(changes: pd.DataFrame) -> pd.DataFrame:
    """
    v2 백그라운드 수집기가 스냅샷에 직접 저장한
    상품ID/브랜드/이미지/가격/할인율 정보를 그대로 사용합니다.
    현재 후보 재매칭보다 스냅샷 자체 정보를 우선합니다.
    """
    if changes is None or changes.empty:
        return changes

    out = changes.copy()

    defaults = {
        "상품ID": "",
        "브랜드": "",
        "이미지URL": "",
        "현재가격": 0,
        "할인율": 0,
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default

    return out



def build_hourly_keyword_ranking() -> tuple[pd.DataFrame, dict]:
    """
    백그라운드 스냅샷의 최근 1시간 변화를 검색어 단위로 집계합니다.
    네이버 검색량이 아니라 마스픽 자체 '1시간 상품 변화 신호'입니다.
    """
    history = load_candidate_history()
    changes, meta = build_exact_hourly_change_from_history(history)

    if changes is None or changes.empty:
        return pd.DataFrame(), meta

    work = changes.copy()
    for col in ["리뷰증가", "순위변화", "1시간변화점수"]:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    work["양의순위변화"] = work["순위변화"].clip(lower=0)
    work["변화상품"] = (
        (work["리뷰증가"] > 0)
        | (work["순위변화"] != 0)
        | (work["신규진입"].astype(bool))
    ).astype(int)

    grouped = (
        work.groupby("검색어", as_index=False)
        .agg(
            변화상품수=("변화상품", "sum"),
            리뷰증가=("리뷰증가", "sum"),
            순위상승합=("양의순위변화", "sum"),
            신규진입=("신규진입", "sum"),
            최고변화점수=("1시간변화점수", "max"),
        )
    )

    grouped["1시간급상승점수"] = (
        grouped["리뷰증가"].clip(upper=50)
        + grouped["순위상승합"].clip(upper=20) * 2
        + grouped["신규진입"].clip(upper=3) * 10
        + grouped["변화상품수"].clip(upper=5) * 5
    ).clip(upper=100).round(1)

    # 실제 변화가 전혀 없는 검색어는 급상승 순위에서 제외
    grouped = grouped[
        (grouped["1시간급상승점수"] > 0)
        | (grouped["변화상품수"] > 0)
        | (grouped["리뷰증가"] > 0)
        | (grouped["순위상승합"] > 0)
        | (grouped["신규진입"] > 0)
    ].copy()

    grouped = grouped.sort_values(
        ["1시간급상승점수", "변화상품수", "리뷰증가", "순위상승합"],
        ascending=False
    ).reset_index(drop=True)

    return grouped, meta


def render_hourly_keyword_ranking():
    st.markdown(
        '<div class="page-title">🔥 1시간 급상승</div>'
        '<div class="page-desc">마스픽이 1시간마다 수집한 상품 순위·리뷰 변화를 검색어 단위로 집계한 급상승 신호입니다.</div>',
        unsafe_allow_html=True
    )

    hourly, meta = build_hourly_keyword_ranking()

    if meta.get("previous_bucket", "-") == "-":
        st.warning(
            "이전 시간대 데이터가 아직 부족합니다. "
            "다음 자동수집 이후부터 1시간 급상승 순위가 실제 변화값으로 계산됩니다."
        )

    if hourly is None or hourly.empty:
        st.info(
            "현재 감지된 1시간 급상승 상품이 없습니다. "
            "순위 상승·리뷰 증가·신규 진입 같은 실제 변화가 발생하면 자동으로 순위가 표시됩니다."
        )
        st.caption("※ 변화가 0인 상품은 급상승 순위에 표시하지 않습니다.")
        return

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("변화 검색어", f"{len(hourly)}개")
    h2.metric("변화 상품", f"{int(hourly['변화상품수'].sum())}개")
    h3.metric("리뷰 증가", f"+{int(hourly['리뷰증가'].sum())}")
    h4.metric("최고 점수", f"{hourly['1시간급상승점수'].max():.0f}점")

    st.caption(
        f"비교 시간대: {meta.get('previous_bucket','-')} → {meta.get('current_bucket','-')}"
    )

    st.markdown("### 1시간 급상승 순위")
    view = hourly.head(10).copy()
    view.index = range(1, len(view) + 1)
    view.index.name = "순위"

    st.dataframe(
        view[
            ["검색어", "1시간급상승점수", "변화상품수", "리뷰증가", "순위상승합", "신규진입"]
        ],
        width="stretch",
        hide_index=False,
        column_config={
            "1시간급상승점수": st.column_config.NumberColumn("급상승 점수", format="%.0f"),
            "리뷰증가": st.column_config.NumberColumn("리뷰 증가", format="%+d"),
            "순위상승합": st.column_config.NumberColumn("순위 상승 합", format="%+d"),
        },
    )

    # 카드
    cols = st.columns(5)
    for i, row in hourly.head(5).iterrows():
        with cols[i]:
            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb;border-radius:18px;padding:16px;background:#fff;min-height:145px;">
                  <div style="font-size:12px;color:#64748b;font-weight:800;">상위 {i+1}위</div>
                  <div style="font-size:17px;font-weight:900;color:#111827;margin-top:8px;">
                    {html.escape(str(row.get("검색어","-")))}
                  </div>
                  <div style="font-size:24px;font-weight:900;color:#16a34a;margin-top:12px;">
                    {float(row.get("1시간급상승점수",0)):.0f}점
                  </div>
                  <div style="font-size:11px;color:#64748b;margin-top:5px;">
                    변화상품 {int(row.get("변화상품수",0))} · 리뷰 +{int(row.get("리뷰증가",0))}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def load_product_evidence(uploaded_file) -> pd.DataFrame:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="cp949")
    missing = [c for c in PRODUCT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("판매근거 CSV에 필요한 열이 없습니다: " + ", ".join(missing))
    for col in ["현재순위", "이전순위", "판매수량", "현재리뷰수", "이전리뷰수"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["검색어", "상품명", "플랫폼", "상품URL"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df = df[df["상품명"].ne("") & df["상품URL"].str.startswith(("http://", "https://"))].copy()
    return df


def select_real_products(products: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    if products.empty:
        return products
    trend_map = trends.set_index("상품명")["검색증감률"].to_dict() if not trends.empty else {}
    products = products.copy()
    products["검색증감률"] = products["검색어"].map(trend_map).fillna(0)
    products["리뷰증가"] = (products["현재리뷰수"] - products["이전리뷰수"]).clip(lower=0)
    products["순위상승"] = (products["이전순위"] - products["현재순위"]).clip(lower=0)
    products["플랫폼수"] = products.groupby("상품명")["플랫폼"].transform("nunique")

    # 확인 가능한 실제 근거가 하나도 없는 상품은 최종 추천에서 제외합니다.
    evidence = (products["판매수량"] > 0) | (products["현재순위"] > 0) | (products["현재리뷰수"] > 0)
    products = products[evidence].copy()
    if products.empty:
        return products

    def relative_score(series: pd.Series, maximum: int) -> pd.Series:
        top = float(series.max())
        return (series / top * maximum).round(1) if top > 0 else pd.Series(0.0, index=series.index)

    # 총 100점: 판매량 35 + 베스트순위 20 + 리뷰증가 15 + 다중플랫폼 15 + 검색상승 15
    products["판매점수"] = relative_score(products["판매수량"], 35)
    products["순위점수"] = products["현재순위"].apply(lambda x: max(0, 21 - x) if x > 0 else 0).clip(upper=20)
    products["리뷰점수"] = relative_score(products["리뷰증가"], 15)
    products["교차검증점수"] = products["플랫폼수"].apply(lambda x: 15 if x >= 2 else 5)
    products["검색점수"] = products["검색증감률"].apply(lambda x: 15 if x >= 30 else (10 if x >= 10 else (5 if x > 0 else 0)))
    products["총점"] = products[["판매점수", "순위점수", "리뷰점수", "교차검증점수", "검색점수"]].sum(axis=1).round(1)

    products["판매근거"] = products.apply(
        lambda r: " · ".join(filter(None, [
            f"판매 {int(r['판매수량']):,}개" if r["판매수량"] > 0 else "",
            f"베스트 {int(r['현재순위'])}위" if r["현재순위"] > 0 else "",
            f"리뷰 +{int(r['리뷰증가']):,}" if r["리뷰증가"] > 0 else "",
        ])), axis=1,
    )
    products["분류"] = products.apply(
        lambda r: "신규 진입" if r["이전순위"] == 0 and r["현재순위"] > 0 else ("급상승" if r["순위상승"] > 0 or r["검색증감률"] >= 10 else "스테디셀러"),
        axis=1,
    )
    products = products.sort_values(["총점", "판매수량", "현재리뷰수"], ascending=False)
    # 같은 검색어에서 가장 근거가 강한 실제 상품 1개만 선택합니다.
    products = products.drop_duplicates("검색어").head(9).reset_index(drop=True)
    products["등급"] = ["S" if i < 3 else ("A" if i < 6 else "B") for i in range(len(products))]
    return products







# =========================
# 9차: 실제 검색창 + 네이버 상품 검색 + 상품 이미지 카드
# =========================
import html
import re
from urllib.parse import quote

# -------------------------
# 추가 API: 네이버 쇼핑 검색
# -------------------------
def build_naver_search_url(query: str) -> str:
    """2026-07-31 종료된 종료된 네이버 쇼핑 검색 API 대신 사용자가 네이버 쇼핑 검색으로 이동할 수 있는 링크를 만듭니다."""
    return f"https://search.shopping.naver.com/search/all?query={quote(query)}"



# -------------------------
# 최근 6시간 지속상승 분석
# -------------------------
def build_six_hour_persistence(history: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    meta = {
        "hours_available": 0,
        "intervals": 0,
        "persistent_count": 0,
        "start_bucket": "-",
        "end_bucket": "-",
    }

    if history is None or history.empty or "수집버킷" not in history.columns:
        return pd.DataFrame(), meta

    df = history.copy()
    df["수집버킷"] = df["수집버킷"].astype(str)
    buckets = sorted([b for b in df["수집버킷"].dropna().unique().tolist() if b])
    if len(buckets) < 2:
        return pd.DataFrame(), meta

    selected = buckets[-7:]
    meta["hours_available"] = len(selected)
    meta["intervals"] = len(selected) - 1
    meta["start_bucket"] = selected[0]
    meta["end_bucket"] = selected[-1]

    key_cols = ["상품URL", "플랫폼"]
    records = []

    for i in range(1, len(selected)):
        prev_bucket = selected[i - 1]
        cur_bucket = selected[i]

        prev = df[df["수집버킷"] == prev_bucket].copy()
        cur = df[df["수집버킷"] == cur_bucket].copy()

        for frame in (prev, cur):
            for c in ["현재순위", "현재리뷰수"]:
                if c not in frame.columns:
                    frame[c] = 0
                frame[c] = pd.to_numeric(frame[c], errors="coerce").fillna(0)

        p = prev[key_cols + ["현재순위", "현재리뷰수"]].drop_duplicates(
            key_cols, keep="last"
        ).rename(columns={
            "현재순위": "이전순위",
            "현재리뷰수": "이전리뷰수",
        })

        cur_cols = key_cols + [
            "검색어", "상품ID", "브랜드", "상품명",
            "현재순위", "현재리뷰수", "현재가격",
            "할인율", "이미지URL"
        ]
        c = cur[[x for x in cur_cols if x in cur.columns]].drop_duplicates(
            key_cols, keep="last"
        )

        merged = c.merge(p, on=key_cols, how="left", indicator=True)
        merged["신규"] = merged["_merge"].eq("left_only")
        merged["순위변화"] = (
            pd.to_numeric(merged.get("이전순위", 0), errors="coerce").fillna(0)
            - pd.to_numeric(merged.get("현재순위", 0), errors="coerce").fillna(0)
        )
        merged["리뷰증가"] = (
            pd.to_numeric(merged.get("현재리뷰수", 0), errors="coerce").fillna(0)
            - pd.to_numeric(merged.get("이전리뷰수", 0), errors="coerce").fillna(0)
        )
        merged["긍정구간"] = (
            (merged["순위변화"] > 0)
            | (merged["리뷰증가"] > 0)
            | merged["신규"]
        )
        merged["비교버킷"] = cur_bucket
        records.append(merged)

    if not records:
        return pd.DataFrame(), meta

    all_changes = pd.concat(records, ignore_index=True)

    grouped = all_changes.groupby(key_cols)
    agg = grouped.agg({
        "긍정구간": "sum",
        "비교버킷": "nunique",
        "신규": "sum",
    }).reset_index().rename(columns={
        "긍정구간": "상승구간수",
        "비교버킷": "관측구간수",
        "신규": "신규진입횟수",
    })

    rank_sum = grouped["순위변화"].apply(
        lambda s: int(s.clip(lower=0).sum())
    ).reset_index(name="6시간순위상승합")
    review_sum = grouped["리뷰증가"].apply(
        lambda s: int(s.clip(lower=0).sum())
    ).reset_index(name="6시간리뷰증가합")

    agg = agg.merge(rank_sum, on=key_cols, how="left").merge(
        review_sum, on=key_cols, how="left"
    )

    latest = df[df["수집버킷"] == selected[-1]].drop_duplicates(
        key_cols, keep="last"
    ).copy()
    keep = [
        "상품URL", "플랫폼", "검색어", "상품ID", "브랜드",
        "상품명", "현재순위", "현재리뷰수", "현재가격",
        "할인율", "이미지URL"
    ]
    latest = latest[[c for c in keep if c in latest.columns]]

    out = latest.merge(agg, on=key_cols, how="left")
    numeric_cols = [
        "상승구간수", "관측구간수", "6시간순위상승합",
        "6시간리뷰증가합", "신규진입횟수"
    ]
    for c in numeric_cols:
        if c not in out.columns:
            out[c] = 0
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)

    out["6시간지속상승"] = out["상승구간수"] >= 2
    out["6시간지속점수"] = (
        out["상승구간수"].clip(upper=4) * 4
        + (out["6시간리뷰증가합"] > 0).astype(int) * 2
        + (out["6시간순위상승합"] >= 3).astype(int) * 2
    ).clip(upper=20).astype(float)

    meta["persistent_count"] = int(out["6시간지속상승"].sum())
    return out, meta


# -------------------------
# AI 판매가능성 추천 엔진
# -------------------------
def build_ai_sales_recommendations(
    trends: pd.DataFrame,
    candidates: pd.DataFrame,
    sales_evidence: pd.DataFrame | None,
) -> tuple[pd.DataFrame, dict]:
    """
    실제 수집 신호를 결합한 규칙형 'AI 판매가능성' 점수입니다.
    학습된 ML 모델이나 실제 판매 보장값이 아닙니다.

    배점:
      - 네이버 검색 상승: 30
      - 최근 1시간 상품 변화: 25
      - 실제 판매근거: 25
      - 다중 플랫폼 신호: 10
      - 신규진입/모멘텀: 10
    """
    meta = {
        "candidate_count": 0,
        "strong_count": 0,
        "rising_count": 0,
        "verified_count": 0,
        "current_bucket": "-",
        "previous_bucket": "-",
        "six_hour_intervals": 0,
        "six_hour_persistent_count": 0,
        "six_hour_start": "-",
        "six_hour_end": "-",
    }

    if candidates is None or getattr(candidates, "empty", True):
        return pd.DataFrame(), meta

    out = candidates.copy()

    defaults = {
        "검색어": "",
        "브랜드": "",
        "상품명": "",
        "플랫폼": "",
        "현재순위": 0,
        "현재리뷰수": 0,
        "현재가격": 0,
        "할인율": 0,
        "이미지URL": "",
        "상품URL": "",
        "검색증감률": 0.0,
        "플랫폼수_자동": 1,
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default

    # 네이버 검색상승률 연결
    if isinstance(trends, pd.DataFrame) and not trends.empty:
        trend_map = (
            trends.drop_duplicates("상품명")
            .set_index("상품명")["검색증감률"]
            .to_dict()
        )
        base_growth = pd.to_numeric(out["검색증감률"], errors="coerce").fillna(0)
        mapped_growth = out["검색어"].map(trend_map)
        out["검색증감률"] = mapped_growth.where(mapped_growth.notna(), base_growth)
    else:
        out["검색증감률"] = pd.to_numeric(
            out["검색증감률"], errors="coerce"
        ).fillna(0)

    # 실제 판매근거 연결
    out = attach_verification_to_candidates(out, sales_evidence)

    # 정확한 최근 1시간 변화 연결
    history = load_candidate_history()
    changes, change_meta = build_exact_hourly_change_from_history(history)
    meta["current_bucket"] = change_meta.get("current_bucket", "-")
    meta["previous_bucket"] = change_meta.get("previous_bucket", "-")
    meta["dropout_count"] = change_meta.get("dropout_count", 0)
    meta["coverage_ratio"] = change_meta.get("coverage_ratio", 1.0)
    meta["collection_unstable"] = change_meta.get("collection_unstable", False)

    if isinstance(changes, pd.DataFrame) and not changes.empty:
        change_cols = [
            "상품URL", "플랫폼", "리뷰증가", "순위변화",
            "신규진입", "이탈감지", "1시간변화점수", "1시간상태"
        ]
        change_df = changes[
            [c for c in change_cols if c in changes.columns]
        ].drop_duplicates(["상품URL", "플랫폼"], keep="last")

        out = out.merge(
            change_df,
            on=["상품URL", "플랫폼"],
            how="left",
        )
    else:
        out["리뷰증가"] = 0
        out["순위변화"] = 0
        out["신규진입"] = False
        out["1시간변화점수"] = 0.0
        out["1시간상태"] = "비교 데이터 부족"

    for col in ["리뷰증가", "순위변화", "1시간변화점수"]:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    if "신규진입" not in out.columns:
        out["신규진입"] = False
    out["신규진입"] = out["신규진입"].fillna(False).astype(bool)

    if "이탈감지" not in out.columns:
        out["이탈감지"] = False
    out["이탈감지"] = out["이탈감지"].fillna(False).astype(bool)

    if "1시간상태" not in out.columns:
        out["1시간상태"] = "비교 데이터 부족"
    out["1시간상태"] = out["1시간상태"].fillna("비교 데이터 부족").astype(str)

    six_hour, six_meta = build_six_hour_persistence(history)
    meta["six_hour_intervals"] = six_meta.get("intervals", 0)
    meta["six_hour_persistent_count"] = six_meta.get("persistent_count", 0)
    meta["six_hour_start"] = six_meta.get("start_bucket", "-")
    meta["six_hour_end"] = six_meta.get("end_bucket", "-")

    if isinstance(six_hour, pd.DataFrame) and not six_hour.empty:
        six_cols = [
            "상품URL", "플랫폼", "상승구간수", "관측구간수",
            "6시간순위상승합", "6시간리뷰증가합",
            "6시간지속상승", "6시간지속점수"
        ]
        out = out.merge(
            six_hour[[c for c in six_cols if c in six_hour.columns]].drop_duplicates(
                ["상품URL", "플랫폼"], keep="last"
            ),
            on=["상품URL", "플랫폼"],
            how="left",
        )
    else:
        out["상승구간수"] = 0
        out["관측구간수"] = 0
        out["6시간순위상승합"] = 0
        out["6시간리뷰증가합"] = 0
        out["6시간지속상승"] = False
        out["6시간지속점수"] = 0.0

    for col in ["상승구간수", "관측구간수", "6시간순위상승합", "6시간리뷰증가합", "6시간지속점수"]:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    if "6시간지속상승" not in out.columns:
        out["6시간지속상승"] = False
    out["6시간지속상승"] = out["6시간지속상승"].fillna(False).astype(bool)

    out["플랫폼수_자동"] = pd.to_numeric(
        out.get("플랫폼수_자동", 1), errors="coerce"
    ).fillna(1)

    # 판매근거 파일에서 동일 검색어/상품명의 다중 플랫폼 여부 보조 계산
    if isinstance(sales_evidence, pd.DataFrame) and not sales_evidence.empty:
        sales_tmp = sales_evidence.copy()
        if "플랫폼" in sales_tmp.columns:
            sales_tmp["플랫폼"] = sales_tmp["플랫폼"].fillna("").astype(str)
            for key_col in ["상품명", "검색어"]:
                if key_col in sales_tmp.columns and key_col in out.columns:
                    platform_map = (
                        sales_tmp[
                            sales_tmp[key_col].fillna("").astype(str).ne("")
                        ]
                        .groupby(key_col)["플랫폼"]
                        .nunique()
                        .to_dict()
                    )
                    mapped = pd.to_numeric(
                        out[key_col].map(platform_map), errors="coerce"
                    ).fillna(0)
                    out["플랫폼수_자동"] = pd.concat(
                        [out["플랫폼수_자동"], mapped], axis=1
                    ).max(axis=1)

    # AI 점수 총 100점:
    # 검색25 + 1시간20 + 6시간20 + 실제판매20 + 다중플랫폼10 + 모멘텀5
    def search_score(growth):
        g = float(growth or 0)
        if g >= 100: return 25
        if g >= 50: return 22
        if g >= 25: return 18
        if g >= 10: return 13
        if g > 0: return 6
        return 0

    out["검색상승점수"] = out["검색증감률"].apply(search_score)
    out["1시간신호점수"] = (
        out["1시간변화점수"].clip(lower=0, upper=100) * 0.20
    ).round(1)
    out["6시간신호점수"] = out["6시간지속점수"].clip(
        lower=0, upper=20
    ).round(1)

    def evidence_score(r):
        if not bool(r.get("판매검증", False)):
            return 0
        score = 8
        if float(r.get("검증판매수량", 0) or 0) > 0: score += 6
        if float(r.get("검증베스트순위", 0) or 0) > 0: score += 3
        if float(r.get("검증리뷰증가", 0) or 0) > 0: score += 3
        return min(20, score)

    out["판매근거점수"] = out.apply(evidence_score, axis=1)
    out["다중플랫폼점수"] = out["플랫폼수_자동"].apply(
        lambda x: 10 if float(x or 0) >= 2 else 0
    )

    def momentum_score(r):
        score = 0
        if bool(r.get("신규진입", False)): score += 3
        if float(r.get("순위변화", 0) or 0) > 0: score += 1
        if float(r.get("리뷰증가", 0) or 0) > 0: score += 1
        return min(5, score)

    out["모멘텀점수"] = out.apply(momentum_score, axis=1)

    out["AI판매가능성"] = (
        out["검색상승점수"]
        + out["1시간신호점수"]
        + out["6시간신호점수"]
        + out["판매근거점수"]
        + out["다중플랫폼점수"]
        + out["모멘텀점수"]
    ).clip(upper=100).round(1)

    def verdict(score):
        s = float(score or 0)
        if s >= 80:
            return "🔥 강력추천"
        if s >= 60:
            return "↗ 상승예상"
        return "관찰"

    out["AI판정"] = out["AI판매가능성"].apply(verdict)

    # 실제 추천 대상:
    # 검색상승만 있는 상품은 '관찰'로 두고,
    # 1시간 변화 / 실제 판매근거 / 다중플랫폼 중 하나라도 있을 때만 추천 카드에 노출
    out["실제신호강도"] = (
        out["1시간신호점수"]
        + out["6시간신호점수"]
        + out["판매근거점수"]
        + out["다중플랫폼점수"]
        + out["모멘텀점수"]
    ).round(1)

    out["실제추천대상"] = (
        (
            (out["1시간변화점수"] > 0)
            | (out["리뷰증가"] > 0)
            | (out["순위변화"] > 0)
            | (out["신규진입"] == True)
            | (out["6시간지속상승"] == True)
            | (out["판매검증"] == True)
            | (out["플랫폼수_자동"] >= 2)
        )
        & (out["이탈감지"] == False)
    )

    def reason_text(r):
        reasons = []
        growth = float(r.get("검색증감률", 0) or 0)
        if growth > 0:
            reasons.append(f"검색 +{growth:.1f}%")

        rank_move = int(float(r.get("순위변화", 0) or 0))
        if rank_move > 0:
            reasons.append(f"1시간 순위 +{rank_move}")

        review_move = int(float(r.get("리뷰증가", 0) or 0))
        if review_move > 0:
            reasons.append(f"리뷰 +{review_move}")

        if bool(r.get("신규진입", False)):
            reasons.append("1시간 신규진입")

        if bool(r.get("6시간지속상승", False)):
            intervals = int(float(r.get("상승구간수", 0) or 0))
            reasons.append(f"6시간 지속상승 {intervals}구간")

        platforms = int(float(r.get("플랫폼수_자동", 1) or 1))
        if platforms >= 2:
            reasons.append(f"{platforms}개 플랫폼 확인")

        evidence = str(r.get("검증근거", "") or "").strip()
        if bool(r.get("판매검증", False)) and evidence:
            reasons.append(evidence)

        if not reasons:
            reasons.append("현재 공개신호 관찰 중")

        return " · ".join(reasons[:5])

    out["추천근거"] = out.apply(reason_text, axis=1)

    out = out.sort_values(
        ["실제추천대상", "실제신호강도", "AI판매가능성", "판매검증", "검색증감률", "현재순위"],
        ascending=[False, False, False, False, False, True],
    ).drop_duplicates(
        subset=["상품URL", "플랫폼"],
        keep="first",
    ).reset_index(drop=True)

    meta["candidate_count"] = len(out)
    meta["strong_count"] = int((out["AI판매가능성"] >= 80).sum())
    meta["rising_count"] = int(
        ((out["AI판매가능성"] >= 60) & (out["AI판매가능성"] < 80)).sum()
    )
    meta["verified_count"] = int(
        out["판매검증"].fillna(False).astype(bool).sum()
    )
    meta["real_signal_count"] = int(
        out["실제추천대상"].fillna(False).astype(bool).sum()
    )

    return out, meta


def render_ai_recommendation_cards(df: pd.DataFrame, max_items: int = 9):
    if df is None or df.empty:
        st.info("현재 추천할 상품 후보가 없습니다.")
        return

    rows = df.head(max_items).reset_index(drop=True)
    cols = st.columns(3)

    for i, row in rows.iterrows():
        with cols[i % 3]:
            image = html.escape(str(row.get("이미지URL", "") or ""), quote=True)
            brand = html.escape(str(row.get("브랜드", "") or "-"))
            name = html.escape(str(row.get("상품명", "") or "-"))
            platform = html.escape(str(row.get("플랫폼", "") or "-"))
            url = html.escape(str(row.get("상품URL", "") or "#"), quote=True)
            reason = html.escape(str(row.get("추천근거", "") or ""))
            verdict = html.escape(str(row.get("AI판정", "관찰")))
            score = float(row.get("AI판매가능성", 0) or 0)
            price = int(float(row.get("현재가격", 0) or 0))
            growth = float(row.get("검색증감률", 0) or 0)
            verified = bool(row.get("판매검증", False))

            price_text = f"{price:,}원" if price > 0 else "가격 정보 없음"
            badge = "판매 검증" if verified else "신호 기반"

            if image:
                img_html = (
                    f'<img src="{image}" alt="{name}" '
                    'style="width:100%;aspect-ratio:4/5;object-fit:cover;'
                    'border-radius:14px;background:#f8fafc;">'
                )
            else:
                img_html = (
                    '<div style="width:100%;aspect-ratio:4/5;border-radius:14px;'
                    'background:#f1f5f9;display:flex;align-items:center;'
                    'justify-content:center;color:#94a3b8;font-size:12px;">'
                    '이미지 없음</div>'
                )

            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb;border-radius:20px;padding:14px;
                            margin-bottom:16px;background:#fff;min-height:490px;">
                  {img_html}
                  <div style="display:flex;justify-content:space-between;gap:8px;
                              align-items:center;margin-top:12px;">
                    <span style="font-size:11px;font-weight:900;color:#7c3aed;">AI #{i+1}</span>
                    <span style="font-size:11px;font-weight:900;color:#16a34a;">{verdict}</span>
                  </div>
                  <div style="font-size:11px;color:#64748b;margin-top:8px;">
                    {platform} · {brand}
                  </div>
                  <div style="font-size:15px;font-weight:900;color:#111827;line-height:1.45;
                              margin-top:5px;min-height:44px;">
                    {name}
                  </div>
                  <div style="display:flex;align-items:flex-end;justify-content:space-between;
                              margin-top:12px;">
                    <div style="font-size:27px;font-weight:950;color:#111827;">
                      {score:.0f}<span style="font-size:14px;">점</span>
                    </div>
                    <div style="font-size:12px;font-weight:800;color:#475569;">
                      {price_text}
                    </div>
                  </div>
                  <div style="margin-top:8px;font-size:11px;color:#64748b;">
                    검색 {growth:+.1f}% · {badge}
                  </div>
                  <div style="margin-top:8px;font-size:11px;color:#475569;line-height:1.55;
                              min-height:52px;">
                    {reason}
                  </div>
                  <a href="{url}" target="_blank"
                     style="display:block;text-align:center;margin-top:12px;padding:10px 12px;
                            border-radius:12px;background:#111827;color:#fff;text-decoration:none;
                            font-size:12px;font-weight:900;">
                    상품 보기
                  </a>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -------------------------
# 상태
# -------------------------
page = st.query_params.get("page", "home")

# 내부 네비게이션은 일반 링크(href + target=_self)를 사용하므로
# 브라우저의 뒤로가기/앞으로가기 기록이 자연스럽게 유지됩니다.
if isinstance(page, list):
    page = page[0]

if "live_result" not in st.session_state:
    st.session_state["live_result"] = None
if "sales_data" not in st.session_state:
    st.session_state["sales_data"] = None
if "product_search_query" not in st.session_state:
    st.session_state["product_search_query"] = ""
if "product_search_result" not in st.session_state:
    st.session_state["product_search_result"] = pd.DataFrame()

demo_result = score_and_classify(demo_data())
result = st.session_state["live_result"] if st.session_state["live_result"] is not None else demo_result
data_label = "실시간 데이터" if st.session_state["live_result"] is not None else "데모 데이터"

# -------------------------
# CSS
# -------------------------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root{--g:#ff6b00;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--soft:#f7f8fa}
html,body,[class*="css"]{font-family:"Noto Sans KR",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.stApp{background:#fff;color:var(--ink)}
.block-container{max-width:1280px;padding:18px 24px 90px!important}
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],#MainMenu,header[data-testid="stHeader"],footer{display:none!important}
a{text-decoration:none!important}

.topbar{display:flex;align-items:center;justify-content:space-between;max-width:900px;margin:0 auto 14px}
.logo{display:flex;align-items:center;gap:10px;font-size:23px;font-weight:900;color:#111827}
.logo-box{width:36px;height:36px;border-radius:10px;background:var(--g);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900}
.top-actions{display:flex;gap:8px}
.nav-btn{border:1px solid var(--line);border-radius:999px;padding:8px 13px;font-size:12px;font-weight:700;color:#374151;background:#fff}
.nav-btn.dark{background:#111827;color:#fff;border-color:#111827}


/* 네이버형 통합 검색바 */
div[data-testid="stForm"]{
  max-width:900px;
  margin:8px auto 14px;
  padding:0!important;
  border:0!important;
  background:transparent!important;
  position:relative;
}
div[data-testid="stForm"]::before{
  content:"M";
  position:absolute;
  left:22px;
  top:31px;
  transform:translateY(-50%);
  z-index:5;
  color:var(--g);
  font-size:25px;
  font-weight:900;
  line-height:1;
  display:flex;
  align-items:center;
}
div[data-testid="stForm"]::after{
  content:"✦ AI";
  position:absolute;
  right:20px;
  top:31px;
  transform:translateY(-50%);
  z-index:5;
  color:#334155;
  font-size:13px;
  font-weight:900;
  line-height:1;
  display:flex;
  align-items:center;
  padding-left:16px;
  border-left:1px solid #e5e7eb;
  pointer-events:none;
}
div[data-testid="stForm"] [data-testid="stTextInput"]{
  margin:0!important;
}
div[data-testid="stForm"] [data-testid="stTextInput"] > div > div{
  border:2px solid var(--g)!important;
  border-radius:999px!important;
  min-height:62px!important;
  background:#fff!important;
  box-shadow:none!important;
}
div[data-testid="stForm"] [data-testid="stTextInput"] input{
  border:0!important;
  box-shadow:none!important;
  background:transparent!important;
  min-height:58px!important;
  padding:0 110px 0 52px!important;
  font-size:14px!important;
  color:#111827!important;
}
div[data-testid="stForm"] [data-testid="stTextInput"] input::placeholder{
  color:#9ca3af!important;
}
div[data-testid="stForm"] [data-testid="stFormSubmitButton"]{
  display:none!important;
}

.quick-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;max-width:900px;margin:14px auto 24px}
.quick-link{border:1px solid var(--line);border-radius:15px;padding:13px 8px;text-align:center;color:#111827;font-size:12px;font-weight:700;background:#fff;display:block}
.quick-icon{display:block;font-size:21px;margin-bottom:5px}

.hero-ad{border:1px solid var(--line);border-radius:18px;padding:18px 20px;display:flex;justify-content:space-between;align-items:center;background:#fafafa;margin-bottom:20px}
.ad-title{font-size:17px;font-weight:800}.ad-copy{font-size:12px;color:var(--muted);margin-top:3px}

.section-head{display:flex;justify-content:space-between;align-items:end;margin:24px 0 12px}
.section-title{font-size:21px;font-weight:900;letter-spacing:-.5px}.section-desc{font-size:12px;color:var(--muted);margin-top:4px}
.page-title{font-size:30px;font-weight:900;letter-spacing:-1px;margin:8px 0 6px}
.page-desc{font-size:13px;color:var(--muted);margin-bottom:22px}

.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
.metric{border:1px solid var(--line);border-radius:16px;padding:16px;background:#fff}
.metric-k{font-size:11px;color:#8b95a1}.metric-v{font-size:23px;font-weight:900;margin-top:4px}.metric-s{font-size:11px;color:var(--g);font-weight:700;margin-top:3px}

.hot-card{border:1px solid var(--line);border-radius:16px;padding:16px;background:#fff}
.hot-top{display:flex;justify-content:space-between}.hot-rank{font-size:11px;color:#9ca3af;font-weight:800}.hot-growth{font-size:13px;color:#ef4444;font-weight:900}
.hot-name{font-size:16px;font-weight:900;margin:10px 0 7px}.hot-meta{font-size:11px;color:#6b7280}.score-pill{display:inline-block;margin-top:10px;background:#ecfdf3;color:#057a44;border-radius:999px;padding:5px 8px;font-size:10px;font-weight:800}

.product-card{
  border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#fff;height:100%;
}
.product-image{
  width:100%;aspect-ratio:1/1;object-fit:cover;background:#f8fafc;display:block;
}
.product-body{padding:14px}
.product-mall{font-size:10px;color:#8b95a1;margin-bottom:5px}
.product-title{
  font-size:14px;font-weight:800;line-height:1.45;min-height:40px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.product-price{font-size:18px;font-weight:900;margin-top:10px}
.product-sub{font-size:10px;color:#94a3b8;margin-top:4px}
.product-link{display:inline-block;margin-top:11px;color:var(--g)!important;font-size:11px;font-weight:800}

.state-box{border-radius:14px;background:#f8fafc;padding:16px}
.state-title{font-weight:900;font-size:14px}.state-copy{font-size:11px;color:#6b7280;line-height:1.6;margin-top:5px}
.price-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.price-card{border:1px solid var(--line);border-radius:18px;padding:22px;background:#fff}.price-card.reco{border:2px solid var(--g)}
.price-name{font-weight:900;font-size:18px}.price{font-size:30px;font-weight:900;margin:10px 0}.price small{font-size:12px;color:#6b7280}
.feature{font-size:12px;padding:7px 0;border-bottom:1px solid #f1f3f5}
.fitting-box{border:1px dashed #cbd5e1;border-radius:20px;padding:34px;text-align:center;background:#fbfcfd}

div[data-baseweb="select"]>div,div[data-testid="stTextArea"] textarea,div[data-testid="stFileUploader"] section,div[data-testid="stTextInput"] input{background:#fff!important;color:#111827!important;border-color:#e5e7eb!important;border-radius:13px!important}
.stButton>button,.stDownloadButton>button{border-radius:12px!important;font-weight:800!important;min-height:42px}
.stButton>button[kind="primary"]{background:var(--g)!important;border-color:var(--g)!important}

.mobile-nav{display:none}
@media(max-width:900px){
 .topbar{max-width:none;width:100%}

 .block-container{padding:12px 14px 82px!important}
 .top-actions .nav-btn:not(.dark){display:none}
 div[data-testid="stForm"] [data-testid="stTextInput"] > div > div{min-height:54px!important}
 div[data-testid="stForm"] [data-testid="stTextInput"] input{min-height:50px!important;padding-left:48px!important;padding-right:92px!important}
 div[data-testid="stForm"]::before{left:18px;font-size:22px}
 div[data-testid="stForm"]::after{right:16px;font-size:12px}
 .quick-grid{grid-template-columns:repeat(3,1fr)}
 .metric-grid{grid-template-columns:repeat(2,1fr)}
 .price-grid{grid-template-columns:1fr}
 .mobile-nav{display:grid;grid-template-columns:repeat(5,1fr);position:fixed;left:0;right:0;bottom:0;z-index:9999;background:rgba(255,255,255,.98);border-top:1px solid var(--line);padding:8px 4px max(8px,env(safe-area-inset-bottom))}
 .mobile-nav a{text-align:center;font-size:10px;color:#6b7280}.mobile-nav b{display:block;font-size:18px;color:#111827}
}
</style>
""", unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div class="topbar">
      <a class="logo" href="?page=home" target="_self"><div class="logo-box">M</div>마스픽</a>
      <div class="top-actions">
        <a class="nav-btn" href="?page=pro" target="_self">광고문의</a>
        <a class="nav-btn" href="?page=login">로그인</a>
        <a class="nav-btn dark" href="?page=pro" target="_self">PRO 시작하기</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("top_search_form", clear_on_submit=False, border=False):
        query = st.text_input(
            "상품 검색",
            value=st.session_state["product_search_query"],
            placeholder="상품명이나 카테고리를 검색하세요",
            label_visibility="collapsed",
            key="header_search_input",
        )
        search_click = st.form_submit_button("검색")

    if search_click and query.strip():
        st.session_state["product_search_query"] = query.strip()
        st.query_params["page"] = "search"
        st.rerun()

    st.markdown("""
    <div class="quick-grid">
      <a class="quick-link" href="?page=trend" target="_self"><span class="quick-icon">🔥</span>급상승</a>
      <a class="quick-link" href="?page=sales" target="_self"><span class="quick-icon">🏆</span>판매TOP</a>
      <a class="quick-link" href="?page=ai" target="_self"><span class="quick-icon">✨</span>AI 추천</a>
      <a class="quick-link" href="?page=fitting" target="_self"><span class="quick-icon">👕</span>가상피팅</a>
      <a class="quick-link" href="?page=alerts" target="_self"><span class="quick-icon">🔔</span>알림</a>
      <a class="quick-link" href="?page=pro" target="_self"><span class="quick-icon">💎</span>PRO</a>
    </div>
    """, unsafe_allow_html=True)

def render_mobile_nav():
    st.markdown("""
    <div class="mobile-nav">
      <a href="?page=home" target="_self"><b>⌂</b>홈</a>
      <a href="?page=trend" target="_self"><b>↗</b>트렌드</a>
      <a href="?page=sales" target="_self"><b>★</b>베스트</a>
      <a href="?page=ai" target="_self"><b>AI</b>추천</a>
      <a href="?page=login"><b>☺</b>MY</a>
    </div>
    """, unsafe_allow_html=True)

def top_rows(n=6):
    return result.sort_values(["검색증감률","최근지수"], ascending=False).head(n).reset_index(drop=True)

def render_hot_cards(rows):
    cols = st.columns(3)
    for i, row in rows.iterrows():
        with cols[i % 3]:
            st.markdown(f"""
            <div class="hot-card">
              <div class="hot-top"><span class="hot-rank">TOP {i+1}</span><span class="hot-growth">▲ {row["검색증감률"]:+.1f}%</span></div>
              <div class="hot-name">{html.escape(str(row["상품명"]))}</div>
              <div class="hot-meta">{html.escape(str(row["카테고리"]))} · 현재지수 {row["최근지수"]:.1f}</div>
              <span class="score-pill">AI 점수 {int(row["점수"])}점</span>
            </div>
            """, unsafe_allow_html=True)

def render_product_cards(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("검색된 상품이 없습니다.")
        return
    cols = st.columns(4)
    for i, row in df.iterrows():
        with cols[i % 4]:
            image_url = html.escape(str(row.get("이미지","")), quote=True)
            name = html.escape(str(row.get("상품명","")))
            mall = html.escape(str(row.get("쇼핑몰","")))
            brand = html.escape(str(row.get("브랜드","")))
            link = html.escape(str(row.get("링크","")), quote=True)
            price = int(row.get("최저가",0) or 0)
            price_text = f"{price:,}원~" if price > 0 else "가격 정보 없음"
            img_html = f'<img class="product-image" src="{image_url}" alt="{name}">' if image_url else '<div class="product-image"></div>'
            st.markdown(f"""
            <div class="product-card">
              {img_html}
              <div class="product-body">
                <div class="product-mall">{mall}</div>
                <div class="product-title">{name}</div>
                <div class="product-price">{price_text}</div>
                <div class="product-sub">{brand}</div>
                <a class="product-link" href="{link}" target="_blank">상품 보기 →</a>
              </div>
            </div>
            """, unsafe_allow_html=True)


def render_trend_detail_chart(row: pd.Series, title_prefix: str = ""):
    values = row.get("추이", [])
    if not isinstance(values, (list, tuple)) or len(values) == 0:
        st.info("기간별 추이 데이터가 없습니다.")
        return

    chart_df = pd.DataFrame({
        "기간": list(range(1, len(values) + 1)),
        "상대지수": [float(v) for v in values],
    })

    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("기간:Q", title="조회 기간"),
            y=alt.Y("상대지수:Q", title="검색·클릭 상대지수"),
            tooltip=[
                alt.Tooltip("기간:Q", title="기간"),
                alt.Tooltip("상대지수:Q", title="상대지수", format=".1f"),
            ],
        )
        .properties(height=320)
    )

    st.markdown(
        f"### {html.escape(title_prefix + str(row.get('상품명', '')))} 추이"
    )
    st.altair_chart(chart, width="stretch")
    st.caption("※ 쇼핑인사이트 지수는 실제 판매수량이 아니라 검색·클릭 상대지수입니다.")


def get_default_live_keywords():
    return (
        "여성 가디건", "여성 원피스", "와이드 데님", "남성 바람막이", "러닝 벨트",
        "크로스백", "스니커즈", "기능성 티셔츠", "카고 팬츠"
    )


render_header()

# -------------------------
# SEARCH
# -------------------------
if page == "search":
    q = st.session_state["product_search_query"].strip()
    safe_q = html.escape(q)

    st.markdown(
        f'<div class="page-title">“{safe_q}” 검색 분석</div>'
        '<div class="page-desc">네이버 쇼핑인사이트 검색·클릭 추이를 분석합니다.</div>',
        unsafe_allow_html=True
    )

    if not q:
        st.info("상단 검색창에 상품명이나 카테고리를 입력해주세요.")
    else:
        cat_options = {"패션의류": "50000000", "패션잡화": "50000001"}
        c1, c2 = st.columns([3, 1])
        with c1:
            cat_name = st.selectbox(
                "분석 카테고리",
                list(cat_options.keys()),
                key="search_page_category"
            )
        with c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            st.link_button(
                "네이버쇼핑 보기",
                build_naver_search_url(q),
                width="stretch"
            )

        try:
            with st.spinner(f"'{q}' 쇼핑인사이트 분석 중..."):
                raw_q = fetch_keyword_trends((cat_options[cat_name],), (q,))

            if raw_q.empty:
                st.warning("조회된 검색·클릭 데이터가 없습니다. 다른 카테고리로 바꿔보세요.")
            else:
                q_result = score_and_classify(raw_q)
                row = q_result.iloc[0]
                base_date = (
                    str(raw_q["데이터기준일"].iloc[0])
                    if "데이터기준일" in raw_q.columns else "-"
                )

                st.success(f"실데이터 조회 완료 · 기준일 {base_date}")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("최근지수", f"{row['최근지수']:.1f}")
                m2.metric("검색 증감률", f"{row['검색증감률']:+.1f}%")
                m3.metric("순위 변화", f"{int(row['순위변화']):+d}")
                m4.metric("트렌드 점수", f"{int(row['점수'])}점")

                render_trend_detail_chart(row)

                st.markdown("### 분석 결과")
                st.dataframe(
                    q_result[
                        ["상품명", "카테고리", "이전지수", "최근지수", "검색증감률",
                         "순위변화", "점수", "URL"]
                    ],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "URL": st.column_config.LinkColumn(
                            "네이버쇼핑",
                            display_text="상품 보기"
                        )
                    },
                )

                st.info(
                    "현재 단계에서는 검색·클릭 상승 여부를 확인합니다. "
                    "실제 판매TOP은 판매량·베스트순위·리뷰 증가 같은 판매근거가 연결된 뒤 별도로 판정합니다."
                )
        except Exception as exc:
            st.error(f"검색 분석 오류: {exc}")

elif page == "home":
    history = load_candidate_history()
    if isinstance(history, pd.DataFrame) and not history.empty and "수집버킷" in history.columns:
        latest_bucket = sorted(history["수집버킷"].dropna().astype(str).unique())[-1]
        latest = history[history["수집버킷"].astype(str) == latest_bucket].copy().sort_values(["검색어","현재순위"])
        st.markdown("## 🔥 최신 자동수집 상품")
        st.caption(f"자동수집 기준 {latest["수집시각"].max()} · {len(latest)}개 상품")
        cols=[c for c in ["검색어","브랜드","상품명","플랫폼","현재순위","현재리뷰수","현재가격","할인율","상품URL"] if c in latest.columns]
        st.dataframe(latest[cols],width="stretch",hide_index=True,column_config={"상품URL":st.column_config.LinkColumn("상품",display_text="보기")})
    try:
        live_df = fetch_keyword_trends(
            ("50000000", "50000001"),
            ("여성 가디건", "여성 원피스", "와이드 데님", "남성 바람막이", "러닝 벨트",
             "크로스백", "스니커즈", "기능성 티셔츠", "카고 팬츠")
        )
    except Exception as e:
        live_df = pd.DataFrame()
        st.error(f"쇼핑인사이트 연결 오류: {e}")

    if not live_df.empty:
        result = score_and_classify(live_df)
        st.session_state["live_result"] = result
        top = result.sort_values(["검색증감률", "최근지수"], ascending=False).reset_index(drop=True)

        # LIVE 상태 및 기준일
        base_date = str(live_df["데이터기준일"].iloc[0]) if "데이터기준일" in live_df.columns else "-"
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;justify-content:space-between;margin:8px 0 12px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;
                             background:#ecfdf5;color:#047857;font-size:12px;font-weight:800;">
                  <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;"></span>
                  NAVER 쇼핑인사이트 · 일간
                </span>
                <span style="font-size:12px;color:#64748b;">검색·클릭 상대지수 기반</span>
              </div>
              <div style="font-size:12px;color:#64748b;">데이터 기준일 {base_date}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 상위 5개 카드
        cols = st.columns(5)
        for i, row in top.head(5).iterrows():
            with cols[i]:
                growth = float(row.get("검색증감률", 0))
                recent = float(row.get("최근지수", 0))
                growth_text = f"{growth:+.1f}%"
                st.markdown(
                    f"""
                    <div style="border:1px solid #e5e7eb;border-radius:18px;padding:16px;background:#fff;min-height:142px;">
                      <div style="font-size:12px;color:#64748b;font-weight:800;">상위 {i+1}위</div>
                      <div style="font-size:17px;font-weight:900;color:#0f172a;margin-top:8px;
                                  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {row.get("상품명","-")}
                      </div>
                      <div style="font-size:24px;font-weight:900;color:#16a34a;margin-top:12px;">{growth_text}</div>
                      <div style="font-size:12px;color:#94a3b8;margin-top:4px;">최근지수 {recent:.1f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 스폰서 영역
        st.markdown("""
        <div style="border:1px solid #e5e7eb;border-radius:18px;padding:18px 20px;margin:16px 0 24px;
                    display:flex;align-items:center;justify-content:space-between;background:#fff;">
          <div>
            <div style="font-size:16px;font-weight:900;color:#111827;">브랜드 · 쇼핑몰 스폰서 영역</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">콘텐츠 흐름을 방해하지 않는 네이티브 광고 위치입니다.</div>
          </div>
          <div style="background:#111827;color:#fff;border-radius:999px;padding:10px 16px;font-size:12px;font-weight:800;">
            광고 상품 보기
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 홈 메트릭 - 모두 실데이터 기준
        st.markdown("## 오늘의 쇼핑 트렌드")
        st.caption("네이버 쇼핑인사이트 실데이터 기준")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("분석 후보", f"{len(result)}개")
        m2.metric("급상승", f"{(result['카테고리'] == '급상승').sum()}개")
        m3.metric("검색 상승", f"{(result['검색증감률'] > 0).sum()}개")
        m4.metric("최고 상승률", f"{result['검색증감률'].max():.1f}%")

        # 실제 TOP 6 카드
        card_cols = st.columns(3)
        for i, row in top.head(6).iterrows():
            with card_cols[i % 3]:
                url = row.get("URL", "#")
                st.markdown(
                    f"""
                    <div style="border:1px solid #e5e7eb;border-radius:18px;padding:16px;margin-bottom:12px;background:#fff;">
                      <div style="display:flex;justify-content:space-between;gap:10px;">
                        <span style="font-size:12px;color:#64748b;font-weight:800;">#{i+1}</span>
                        <span style="font-size:12px;color:#ef4444;font-weight:900;">{float(row.get("검색증감률",0)):+.1f}%</span>
                      </div>
                      <div style="font-size:17px;font-weight:900;color:#111827;margin-top:8px;">{row.get("상품명","-")}</div>
                      <div style="font-size:12px;color:#64748b;margin-top:6px;">
                        최근지수 {float(row.get("최근지수",0)):.1f} · {row.get("카테고리","-")}
                      </div>
                      <a href="{url}" target="_blank" style="display:inline-block;margin-top:10px;
                         font-size:12px;font-weight:800;color:#2563eb;text-decoration:none;">네이버쇼핑에서 보기 →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 실제 판매근거 섹션
        st.markdown("### 실제 판매근거")
        st.info(
            "현재 네이버 쇼핑인사이트는 검색·클릭 상대지수입니다. "
            "실제 판매TOP은 판매수량·베스트순위·리뷰 증가 등 검증 가능한 판매근거가 연결된 뒤에만 표시합니다."
        )

        with st.expander("판매근거 CSV 연결", expanded=False):
            st.caption("쇼핑몰 또는 제휴처에서 확보한 판매근거 CSV를 업로드하면 실제 상품 TOP을 선별합니다.")
            sales_csv = st.file_uploader(
                "판매근거 CSV",
                type=["csv"],
                key="home_sales_csv"
            )
            st.download_button(
                "판매근거 CSV 양식 받기",
                product_csv_template(),
                "상품_판매근거_입력양식.csv",
                "text/csv",
                key="home_sales_template"
            )

            if sales_csv is not None:
                try:
                    sales = load_product_evidence(sales_csv)
                    selected = select_real_products(sales, result)
                    if selected.empty:
                        st.warning("검증 가능한 판매근거가 있는 상품을 찾지 못했습니다.")
                    else:
                        st.success("판매근거가 확인된 상품을 선별했습니다.")
                        final_view = selected[
                            ["검색어", "상품명", "플랫폼", "분류", "등급", "판매근거", "검색증감률", "총점", "상품URL"]
                        ]
                        st.dataframe(
                            final_view,
                            width="stretch",
                            hide_index=True,
                            column_config={
                                "상품URL": st.column_config.LinkColumn("상품", display_text="상품 보기")
                            },
                        )
                except Exception as csv_exc:
                    st.warning(f"판매자료 CSV를 읽지 못했습니다: {csv_exc}")

    else:
        st.warning("쇼핑인사이트에서 표시할 실데이터가 없습니다.")

elif page == "trend":
    # 1) 실제 1시간 변화 기반 급상승
    render_hourly_keyword_ranking()

    st.markdown("---")

    # 2) 네이버 공식 일간 트렌드
    st.markdown(
        '<div class="page-title">📊 네이버 일간 트렌드</div>'
        '<div class="page-desc">네이버 쇼핑인사이트 공식 일간 검색·클릭 상대지수입니다. 실시간/시간 단위 데이터가 아닙니다.</div>',
        unsafe_allow_html=True
    )

    try:
        with st.spinner("네이버 일간 트렌드를 불러오는 중..."):
            live_df = fetch_keyword_trends(
                ("50000000", "50000001"),
                get_default_live_keywords()
            )

        if live_df.empty:
            st.warning("표시할 네이버 쇼핑인사이트 데이터가 없습니다.")
        else:
            trend_result = score_and_classify(live_df)
            st.session_state["live_result"] = trend_result
            ranked = trend_result.sort_values(
                ["검색증감률", "최근지수"],
                ascending=False
            ).reset_index(drop=True)

            base_date = (
                str(live_df["데이터기준일"].iloc[0])
                if "데이터기준일" in live_df.columns else "-"
            )

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                            gap:12px;margin:2px 0 18px;">
                  <span style="display:inline-flex;align-items:center;gap:6px;padding:7px 11px;
                               border-radius:999px;background:#ecfdf5;color:#047857;
                               font-size:12px;font-weight:800;">
                    <span style="width:8px;height:8px;border-radius:50%;
                                 background:#10b981;display:inline-block;"></span>
                    NAVER 쇼핑인사이트 · 일간
                  </span>
                  <span style="font-size:12px;color:#64748b;">데이터 기준일 {base_date}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("분석 검색어", f"{len(ranked)}개")
            m2.metric("일간 상승", f"{(ranked['검색증감률'] > 0).sum()}개")
            m3.metric("최고 상대지수", f"{ranked['최근지수'].max():.1f}")
            m4.metric("최고 증감률", f"{ranked['검색증감률'].max():.1f}%")

            st.markdown("### 네이버 일간 순위")
            table = ranked[
                ["상품명", "카테고리", "이전지수", "최근지수",
                 "검색증감률", "순위변화", "점수", "URL"]
            ].copy()
            table.index = range(1, len(table) + 1)
            table.index.name = "순위"

            st.dataframe(
                table,
                width="stretch",
                hide_index=False,
                column_config={
                    "검색증감률": st.column_config.NumberColumn(
                        "일간 증감률", format="%.1f%%"
                    ),
                    "URL": st.column_config.LinkColumn(
                        "네이버쇼핑", display_text="보기"
                    ),
                },
            )

            st.markdown("### 검색어 상세 보기")
            names = ranked["상품명"].astype(str).tolist()
            selected_name = st.selectbox(
                "분석할 검색어",
                names,
                key="trend_detail_keyword"
            )
            selected_row = ranked[
                ranked["상품명"].astype(str) == selected_name
            ].iloc[0]

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("이전지수", f"{selected_row['이전지수']:.1f}")
            d2.metric("최근지수", f"{selected_row['최근지수']:.1f}")
            d3.metric("일간 증감률", f"{selected_row['검색증감률']:+.1f}%")
            d4.metric("트렌드 점수", f"{int(selected_row['점수'])}점")

            render_trend_detail_chart(selected_row)

            st.link_button(
                f"네이버쇼핑에서 '{selected_name}' 보기",
                selected_row["URL"],
                width="stretch"
            )

            st.caption(
                "※ 네이버 쇼핑인사이트는 일간 검색·클릭 상대지수이며, 실제 검색 건수나 시간 단위 실시간 수치가 아닙니다."
            )

    except Exception as e:
        st.error(f"쇼핑인사이트 연결 오류: {e}")

# -------------------------
# SALES TOP
# -------------------------
elif page == "sales":
    st.markdown(
        '<div class="page-title">🏆 판매TOP</div>'
        '<div class="page-desc">급상승 검색과 1시간 판매신호를 결합해 지금 강한 상품을 보여줍니다. 판매 검증 근거가 있는 상품은 별도 표시합니다.</div>',
        unsafe_allow_html=True
    )

    # 판매TOP 페이지에서도 트렌드 데이터가 항상 준비되도록 보장
    trend_for_sales = st.session_state.get("live_result")
    if trend_for_sales is None or getattr(trend_for_sales, "empty", True):
        try:
            with st.spinner("검색 트렌드 데이터를 불러오는 중..."):
                live_sales_raw = fetch_keyword_trends(
                    ("50000000", "50000001"),
                    get_default_live_keywords()
                )
            if not live_sales_raw.empty:
                trend_for_sales = score_and_classify(live_sales_raw)
                st.session_state["live_result"] = trend_for_sales
            else:
                trend_for_sales = pd.DataFrame()
        except Exception:
            trend_for_sales = pd.DataFrame()


    # 네이버 급상승 검색어 → 무신사 공개 검색결과 자동 연결
    musinsa_candidates, musinsa_status = collect_musinsa_for_trends(
        trend_for_sales if isinstance(trend_for_sales, pd.DataFrame) else pd.DataFrame(),
        top_keywords=5,
        per_keyword=8,
    )
    musinsa_scored = score_musinsa_candidates(
        musinsa_candidates,
        trend_for_sales if isinstance(trend_for_sales, pd.DataFrame) else pd.DataFrame(),
    )

    current_sales_evidence = st.session_state.get("sales_data")
    musinsa_scored = attach_official_and_signal_badges(
        musinsa_scored,
        current_sales_evidence if isinstance(current_sales_evidence, pd.DataFrame) else pd.DataFrame()
    )

    st.markdown("""
    <div style="border:1px solid #e5e7eb;border-radius:18px;padding:18px 20px;margin:8px 0 18px;background:#fff;">
      <div style="font-weight:900;font-size:16px;color:#111827;">판매TOP 판정 기준</div>
      <div style="margin-top:8px;font-size:13px;color:#64748b;line-height:1.8;">
        판매량 35점 · 베스트순위 20점 · 리뷰증가 15점 · 다중플랫폼 15점 · 검색상승 15점
      </div>
      <div style="margin-top:6px;font-size:12px;color:#94a3b8;">
        검색 상승만으로는 판매TOP에 올라가지 않습니다. 실제 판매근거가 있는 상품만 계산합니다.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 자동 판매근거 수집 허브
    auto_sales, source_status = collect_sales_source_folder()
    partner_sales, partner_status = collect_configured_partner_feeds()
    public_rank_sales, public_rank_status = collect_public_ranking_feeds()

    # CSV 폴더 + 공식/제휴 JSON 피드는 실제 판매근거 데이터로 병합합니다.
    auto_sales = merge_sales_evidence(auto_sales, partner_sales)

    st.markdown("### 🔥 지금 잘 나가는 상품")
    st.caption(
        "네이버 급상승 검색어와 무신사 공개 상품 후보를 연결해 보여줍니다. "
        "공식 판매근거가 있으면 `판매 검증`, 리뷰증가·순위상승 등 자동 추적 근거가 쌓이면 `판매 신호 검증` 배지를 표시합니다."
    )

    if not musinsa_status.empty:
        st.dataframe(
            musinsa_status,
            width="stretch",
            hide_index=True,
            column_config={
                "검색증감률": st.column_config.NumberColumn(
                    "검색증감률", format="%.1f%%"
                ),
                "무신사검색": st.column_config.LinkColumn(
                    "무신사 검색", display_text="열기"
                ),
            },
        )

    if musinsa_scored.empty:
        st.info(
            "무신사 상품 링크를 자동으로 읽지 못했습니다. "
            "위 표의 '무신사 검색' 링크는 정상 작동하므로 해당 공개 검색페이지는 바로 확인할 수 있습니다."
        )
    else:
        for keyword in musinsa_scored["검색어"].drop_duplicates().tolist():
            sub = musinsa_scored[
                musinsa_scored["검색어"] == keyword
            ].head(3)

            growth = float(sub["검색증감률"].iloc[0])
            st.markdown(
                f"#### {html.escape(keyword)} · 네이버 검색 {growth:+.1f}%"
            )

            cols = st.columns(min(3, len(sub)))
            for i, (_, row) in enumerate(sub.iterrows()):
                with cols[i]:
                    name = html.escape(str(row.get("상품명", "-")))
                    url = html.escape(str(row.get("상품URL", "#")), quote=True)
                    reviews = int(row.get("현재리뷰수", 0))
                    score = float(row.get("종합후보점수", row.get("후보점수", 0)))
                    exposure_rank = int(row.get("현재순위", 0))
                    badge_text = html.escape(str(row.get("표시배지", "랭킹 후보")))
                    badge_evidence = html.escape(str(row.get("표시근거", "") or ""))
                    is_verified = badge_text == "판매 검증"
                    is_signal_verified = badge_text == "판매 신호 검증"

                    brand = html.escape(str(row.get("브랜드", "") or ""))
                    price = int(row.get("현재가격", 0) or 0)
                    discount = int(row.get("할인율", 0) or 0)
                    image_url = html.escape(str(row.get("이미지URL", "") or ""), quote=True)

                    image_html = (
                        f'<img src="{image_url}" alt="{name}" '
                        'style="width:100%;height:180px;object-fit:cover;'
                        'border-radius:14px;background:#f8fafc;" />'
                        if image_url else
                        '<div style="width:100%;height:180px;border-radius:14px;'
                        'background:#f8fafc;display:flex;align-items:center;'
                        'justify-content:center;color:#94a3b8;font-size:12px;">'
                        '이미지 없음</div>'
                    )

                    price_html = (
                        f'<div style="margin-top:10px;display:flex;align-items:center;gap:7px;">'
                        + (f'<span style="font-size:13px;font-weight:900;color:#ef4444;">{discount}%</span>' if discount > 0 else '')
                        + f'<span style="font-size:18px;font-weight:900;color:#111827;">{price:,}원</span>'
                        + '</div>'
                        if price > 0 else
                        '<div style="font-size:12px;color:#94a3b8;margin-top:10px;">가격 미확인</div>'
                    )

                    st.markdown(
                        f"""
                        <div style="border:1px solid #e5e7eb;border-radius:18px;
                                    padding:12px;margin-bottom:14px;background:#fff;
                                    min-height:390px;">
                          {image_html}
                          <div style="display:flex;justify-content:space-between;
                                      align-items:center;margin-top:12px;">
                            <span style="font-size:11px;font-weight:900;
                                         color:{'#16a34a' if is_verified else ('#7c3aed' if is_signal_verified else '#2563eb')};">
                              {badge_text} {i+1}
                            </span>
                            <span style="font-size:11px;font-weight:900;color:#64748b;">
                              종합점수 {score:.0f}
                            </span>
                          </div>
                          <div style="font-size:12px;color:#64748b;margin-top:8px;">
                            {brand if brand else '브랜드 미확인'}
                          </div>
                          <div style="font-size:15px;font-weight:900;color:#111827;
                                      margin-top:5px;line-height:1.45;min-height:44px;">
                            {name}
                          </div>
                          {price_html}
                          <div style="font-size:11px;color:#64748b;margin-top:8px;">
                            추천순 노출 {exposure_rank}위 ·
                            {' 리뷰 ' + format(reviews, ',') if reviews > 0 else ' 리뷰 미확인'}
                          </div>
                          {
                              f'<div style="font-size:11px;'
                              f'color:{("#16a34a" if is_verified else "#7c3aed")};'
                              f'font-weight:800;margin-top:7px;">✓ {badge_evidence}</div>'
                              if badge_evidence else ''
                          }
                          <a href="{url}" target="_blank"
                             style="display:inline-block;margin-top:11px;font-size:12px;
                                    font-weight:800;color:#2563eb;text-decoration:none;">
                            무신사 상품 보기 →
                          </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        with st.expander("무신사 자동 후보 전체 보기", expanded=False):
            cols = [
                "검색어", "브랜드", "상품명", "현재가격", "할인율",
                "현재순위", "현재리뷰수", "검색증감률",
                "후보점수", "판매검증", "검증근거",
                "리뷰증가_자동", "순위상승_자동", "반복노출횟수",
                "플랫폼수_자동", "판매신호", "판매신호근거",
                "판매신호점수", "표시배지", "종합후보점수",
                "이미지URL", "상품URL"
            ]
            available = [c for c in cols if c in musinsa_scored.columns]
            st.dataframe(
                musinsa_scored[available],
                width="stretch",
                hide_index=True,
                column_config={
                    "상품URL": st.column_config.LinkColumn(
                        "상품", display_text="보기"
                    ),
                    "검색증감률": st.column_config.NumberColumn(
                        "검색증감률", format="%.1f%%"
                    ),
                    "후보점수": st.column_config.NumberColumn(
                        "후보점수", format="%.1f"
                    ),
                    "현재가격": st.column_config.NumberColumn(
                        "현재가격", format="%d원"
                    ),
                    "할인율": st.column_config.NumberColumn(
                        "할인율", format="%d%%"
                    ),
                    "이미지URL": st.column_config.ImageColumn("이미지"),
                },
            )

    st.caption(
        "※ `판매 검증`은 공식/제휴 판매수량·베스트순위 등 직접 근거가 있는 상품입니다. "
        "`판매 신호 검증`은 리뷰 증가·공개순위 상승·반복 상위노출 등 자동 추적 신호가 2개 이상 확인된 상품입니다. "
        "두 배지는 서로 다른 수준의 근거입니다."
    )


    # 고객용 통합 1시간 판매신호 대시보드
    render_sales_top_integrated_dashboard(
        trend_for_sales
        if isinstance(trend_for_sales, pd.DataFrame)
        else pd.DataFrame(),
        musinsa_scored
        if isinstance(musinsa_scored, pd.DataFrame)
        else pd.DataFrame(),
    )


    with st.expander("운영자용 데이터 연결", expanded=False):
        st.markdown("### 자동 수집 허브")
        st.caption(
            "프로젝트 폴더의 `sales_sources` 안에 표준 CSV를 넣으면 앱이 자동으로 읽어 병합합니다. "
            "제휴처·쇼핑몰에서 내려받은 파일을 같은 형식으로 저장하면 됩니다."
        )

        st.markdown("#### 데이터 연결 상태")
        st.dataframe(
            connector_status_table(),
            width="stretch",
            hide_index=True,
        )

        if not partner_status.empty:
            st.markdown("#### 제휴 API 수집 상태")
            st.dataframe(
                partner_status,
                width="stretch",
                hide_index=True,
            )

        if not public_rank_status.empty:
            st.markdown("#### 공개 랭킹 수집 상태")
            st.dataframe(
                public_rank_status,
                width="stretch",
                hide_index=True,
            )

        h1, h2, h3 = st.columns(3)
        h1.metric("자동 감지 파일", f"{len(source_status)}개")
        h2.metric("자동 수집 행", f"{len(auto_sales):,}건")
        h3.metric(
            "자동 수집 플랫폼",
            f"{auto_sales['플랫폼'].replace('', pd.NA).dropna().nunique() if not auto_sales.empty else 0}개"
        )

        if not source_status.empty:
            st.dataframe(source_status, width="stretch", hide_index=True)
        else:
            st.info(
                f"아직 자동 수집 파일이 없습니다. 아래 폴더에 CSV를 넣으면 됩니다:\n\n"
                f"{SALES_SOURCE_DIR}"
            )

        if not auto_sales.empty:
            st.session_state["sales_data"] = merge_sales_evidence(
                st.session_state.get("sales_data"),
                auto_sales
            )
            st.success(
                "sales_sources 폴더의 판매근거를 자동으로 병합했습니다. "
                "같은 상품·플랫폼·URL은 최신 항목 하나만 유지합니다."
            )

        with st.expander("자동 수집 폴더 사용 방법", expanded=False):
            folder_guide = (
                "프로젝트 폴더\n"
                "└─ sales_sources\n"
                "   ├─ musinsa.csv\n"
                "   ├─ zigzag.csv\n"
                "   ├─ ably.csv\n"
                "   └─ partner_export.csv\n\n"
                "필수 열:\n"
                "검색어, 상품명, 플랫폼, 현재순위, 이전순위, 판매수량,\n"
                "현재리뷰수, 이전리뷰수, 상품URL\n\n"
                f"현재 자동수집 폴더:\n{SALES_SOURCE_DIR}"
            )
            st.code(folder_guide, language="text")
            st.markdown("**공개 랭킹 URL을 연결할 때 `.streamlit/secrets.toml` 예시**")
            st.code(
                """PUBLIC_RANK_FEEDS_JSON = """
                + """'[{"url":"https://www.musinsa.com/...","keyword":"여성 가디건","platform":"무신사","ranking_basis":"공개 판매순 랭킹","max_items":30}]'""",
                language="toml",
            )
            st.caption(
                "공개 랭킹 커넥터는 판매수량을 만들지 않습니다. 순위·리뷰·검색상승을 별도 보조지표로 사용합니다."
            )

            st.caption(
                "중요: JSON의 keyword 값이 네이버 급상승 검색어와 같아야 "
                "‘급상승 → 구체 상품 자동 후보’에 자동 매칭됩니다."
            )

            st.markdown("**제휴 JSON API를 연결할 때 `.streamlit/secrets.toml` 예시**")
            st.code(
                """PARTNER_FEED_1_URL = "https://partner.example.com/api/products"
    PARTNER_FEED_1_PLATFORM = "무신사"
    PARTNER_FEED_1_TOKEN = "발급받은 토큰"

    PARTNER_FEED_2_URL = "https://partner.example.com/api/products"
    PARTNER_FEED_2_PLATFORM = "제휴몰"
    PARTNER_FEED_2_API_KEY = "발급받은 키"
    """,
                language="toml",
            )
            st.caption(
                "피드에서 상품명·판매수량·순위·리뷰수·상품URL 중 제공되는 항목을 자동으로 표준화합니다."
            )

            st.warning(
                "웹사이트를 무단 크롤링하는 방식은 넣지 않았습니다. "
                "제휴 API·공식 내보내기·판매자 데이터처럼 사용 권한이 있는 자료를 이 폴더로 연결하는 구조입니다."
            )

        if not public_rank_sales.empty:
            st.markdown("### 공개 랭킹 강도")
            st.caption(
                "이 영역은 공개 페이지의 순위·리뷰·검색상승을 합친 보조 신호입니다. "
                "실제 판매수량 TOP으로 표시하지 않습니다."
            )
            rank_signal = select_rank_signal_products(
                public_rank_sales,
                trend_for_sales if isinstance(trend_for_sales, pd.DataFrame) else pd.DataFrame()
            )
            if not rank_signal.empty:
                rank_view = rank_signal[
                    ["검색어", "상품명", "플랫폼", "현재순위", "현재리뷰수",
                     "검색증감률", "랭킹강도", "상품URL"]
                ].head(30)
                st.dataframe(
                    rank_view,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "상품URL": st.column_config.LinkColumn("상품", display_text="보기"),
                        "검색증감률": st.column_config.NumberColumn("검색증감률", format="%.1f%%"),
                        "랭킹강도": st.column_config.NumberColumn("랭킹강도", format="%.1f"),
                    },
                )


        st.markdown("### 급상승 → 구체 상품 자동 후보")
        st.caption(
            "네이버에서 급상승한 검색어와 연결된 공개 랭킹 상품을 자동으로 매칭합니다."
        )

        matched_candidates = match_trending_keywords_to_rank_products(
            trend_for_sales if isinstance(trend_for_sales, pd.DataFrame) else pd.DataFrame(),
            public_rank_sales,
            top_keywords=5,
            per_keyword=5,
        )
        render_auto_candidate_cards(matched_candidates)

        if not matched_candidates.empty:
            with st.expander("자동 후보 전체 보기", expanded=False):
                st.dataframe(
                    matched_candidates,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "검색증감률": st.column_config.NumberColumn(
                            "검색증감률", format="%.1f%%"
                        ),
                        "랭킹강도": st.column_config.NumberColumn(
                            "랭킹강도", format="%.1f"
                        ),
                        "상품URL": st.column_config.LinkColumn(
                            "상품", display_text="보기"
                        ),
                    },
                )

    with st.expander("백그라운드 수집 상태", expanded=False):
        bg_log = Path(__file__).resolve().parent / "sales_sources" / "collector_status.json"
        if bg_log.exists():
            try:
                status = json.loads(bg_log.read_text(encoding="utf-8"))
                c1, c2, c3 = st.columns(3)
                c1.metric("마지막 백그라운드 수집", status.get("last_run", "-"))
                c2.metric("수집 검색어", f"{status.get('keywords', 0)}개")
                c3.metric("수집 상품", f"{status.get('products', 0)}개")
                st.caption(status.get("message", ""))
            except Exception as exc:
                st.warning(f"백그라운드 수집 상태를 읽지 못했습니다: {exc}")
        else:
            st.info(
                "아직 백그라운드 수집 기록이 없습니다. "
                "trendpick_hourly_collector.py를 Windows 작업 스케줄러에 등록하면 브라우저를 닫아도 매시간 수집됩니다."
            )

    with st.expander("판매 신호 추적 상태", expanded=False):
        st.caption(
            "판매TOP 페이지가 브라우저에 열려 있는 동안 1시간마다 자동 재수집·스냅샷 저장·변화 계산을 수행합니다."
        )
        history_df = load_candidate_history()
        if history_df.empty:
            st.info("아직 누적된 상품 이력이 없습니다.")
        else:
            st.metric("누적 스냅샷", f"{len(history_df):,}건")
            st.metric(
                "추적 상품",
                f"{history_df['상품URL'].nunique() if '상품URL' in history_df.columns else 0:,}개"
            )
            st.caption(
                f"이력 파일: {SNAPSHOT_PATH}"
            )
            recent_history = history_df.sort_values(
                "수집시각_dt", ascending=False
            ).head(100)
            st.dataframe(
                recent_history.drop(columns=["수집시각_dt"], errors="ignore"),
                width="stretch",
                hide_index=True,
            )

    upload_col, template_col = st.columns([3, 1])

    with upload_col:
        sales_csv_page = st.file_uploader(
            "판매근거 CSV 업로드",
            type=["csv"],
            key="sales_page_upload",
            help="검색어, 상품명, 플랫폼, 현재순위, 이전순위, 판매수량, 현재리뷰수, 이전리뷰수, 상품URL 열이 필요합니다."
        )

    with template_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.download_button(
            "CSV 양식 받기",
            product_csv_template(),
            "상품_판매근거_입력양식.csv",
            "text/csv",
            key="sales_page_template",
            width="stretch"
        )

    if sales_csv_page is not None:
        try:
            loaded_sales = load_product_evidence(sales_csv_page)
            st.session_state["sales_data"] = merge_sales_evidence(
                st.session_state.get("sales_data"),
                loaded_sales
            )
            st.success(
                f"업로드 판매근거 {len(loaded_sales):,}건을 병합했습니다. "
                f"현재 총 {len(st.session_state['sales_data']):,}건입니다."
            )
        except Exception as exc:
            st.error(f"판매근거 CSV 오류: {exc}")

    sales = st.session_state.get("sales_data")

    if sales is None or getattr(sales, "empty", True):
        st.markdown("""
        <div class="state-box">
          <div class="state-title">아직 검증된 판매 데이터가 없습니다.</div>
          <div class="state-copy">
            판매근거 CSV를 연결하면 상품별 판매수량·순위·리뷰 증가를 분석해서 실제 판매TOP을 자동으로 선별합니다.
            검색량이나 클릭량만 높은 상품은 이 순위에 포함하지 않습니다.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 필요한 판매근거")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("판매수량", "필수 근거")
        e2.metric("베스트 순위", "검증 가능")
        e3.metric("리뷰 증가", "보조 근거")
        e4.metric("플랫폼 교차", "신뢰도 강화")

    else:
        selected = select_real_products(
            sales,
            trend_for_sales if isinstance(trend_for_sales, pd.DataFrame) else pd.DataFrame()
        )

        if selected.empty:
            st.warning("판매수량·순위·리뷰 중 검증 가능한 근거가 있는 상품이 없습니다.")
        else:
            selected = selected.copy()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("검증 상품", f"{len(selected)}개")
            m2.metric(
                "연결 플랫폼",
                f"{sales['플랫폼'].replace('', pd.NA).dropna().nunique()}개"
            )
            m3.metric(
                "총 판매수량",
                f"{int(pd.to_numeric(sales['판매수량'], errors='coerce').fillna(0).sum()):,}개"
            )
            m4.metric(
                "최고 신뢰점수",
                f"{float(selected['총점'].max()):.0f}점"
            )

            platform_list = ["전체"] + sorted(
                [x for x in sales["플랫폼"].dropna().astype(str).unique().tolist() if x]
            )
            chosen_platform = st.selectbox(
                "플랫폼 필터",
                platform_list,
                key="sales_platform_filter"
            )

            view_selected = selected
            if chosen_platform != "전체":
                view_selected = selected[selected["플랫폼"] == chosen_platform].copy()

            st.markdown("### 실제 판매TOP")

            if view_selected.empty:
                st.info("선택한 플랫폼에 표시할 검증 상품이 없습니다.")
            else:
                card_cols = st.columns(3)
                for i, (_, row) in enumerate(view_selected.iterrows()):
                    with card_cols[i % 3]:
                        rank_no = i + 1
                        platform = html.escape(str(row.get("플랫폼", "-")))
                        product_name = html.escape(str(row.get("상품명", "-")))
                        evidence = html.escape(str(row.get("판매근거", "-")))
                        category = html.escape(str(row.get("분류", "-")))
                        grade = html.escape(str(row.get("등급", "-")))
                        url = html.escape(str(row.get("상품URL", "#")), quote=True)

                        st.markdown(
                            f"""
                            <div style="border:1px solid #e5e7eb;border-radius:18px;padding:17px;
                                        margin-bottom:12px;background:#fff;min-height:210px;">
                              <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-size:12px;font-weight:900;color:#2563eb;">TOP {rank_no}</span>
                                <span style="font-size:12px;font-weight:900;color:#64748b;">{grade} 등급</span>
                              </div>
                              <div style="font-size:12px;color:#64748b;margin-top:12px;">{platform} · {category}</div>
                              <div style="font-size:17px;font-weight:900;color:#111827;margin-top:6px;
                                          line-height:1.4;">{product_name}</div>
                              <div style="font-size:25px;font-weight:900;color:#16a34a;margin-top:14px;">
                                {float(row.get("총점", 0)):.0f}점
                              </div>
                              <div style="font-size:12px;color:#64748b;margin-top:6px;line-height:1.6;">
                                {evidence}
                              </div>
                              <a href="{url}" target="_blank"
                                 style="display:inline-block;margin-top:12px;font-size:12px;
                                        font-weight:800;color:#2563eb;text-decoration:none;">
                                상품 보기 →
                              </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.markdown("### 점수 상세")
                score_cols = [
                    "검색어", "상품명", "플랫폼", "판매수량", "현재순위",
                    "리뷰증가", "플랫폼수", "검색증감률",
                    "판매점수", "순위점수", "리뷰점수",
                    "교차검증점수", "검색점수", "총점", "상품URL"
                ]
                available_cols = [c for c in score_cols if c in view_selected.columns]

                st.dataframe(
                    view_selected[available_cols],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "상품URL": st.column_config.LinkColumn(
                            "상품", display_text="보기"
                        ),
                        "검색증감률": st.column_config.NumberColumn(
                            "검색증감률", format="%.1f%%"
                        ),
                        "총점": st.column_config.NumberColumn(
                            "총점", format="%.1f"
                        ),
                    },
                )

                st.caption(
                    "※ 실제 판매TOP은 업로드된 판매근거 데이터 안에서 계산된 상대 순위입니다. "
                    "플랫폼 전체 시장의 공식 판매량 순위라는 의미는 아닙니다."
                )

# -------------------------
# AI
# -------------------------
elif page == "ai":
    st.markdown(
        '<div class="page-title">✨ AI 추천</div>'
        '<div class="page-desc">네이버 검색 상승·1시간 상품 변화·실제 판매근거를 합쳐 판매 가능성이 높은 상품을 우선 추천합니다.</div>',
        unsafe_allow_html=True
    )

    ai_trends = st.session_state.get("live_result")
    if ai_trends is None or getattr(ai_trends, "empty", True):
        try:
            with st.spinner("네이버 트렌드를 불러오는 중..."):
                ai_raw = fetch_keyword_trends(
                    ("50000000", "50000001"),
                    get_default_live_keywords()
                )
            ai_trends = (
                score_and_classify(ai_raw)
                if isinstance(ai_raw, pd.DataFrame) and not ai_raw.empty
                else pd.DataFrame()
            )
            st.session_state["live_result"] = ai_trends
        except Exception as exc:
            ai_trends = pd.DataFrame()
            st.error(f"트렌드 데이터 연결 오류: {exc}")

    auto_sales_ai, _ = collect_sales_source_folder()
    partner_sales_ai, _ = collect_configured_partner_feeds()
    merged_sales_ai = merge_sales_evidence(auto_sales_ai, partner_sales_ai)

    if not merged_sales_ai.empty:
        st.session_state["sales_data"] = merge_sales_evidence(
            st.session_state.get("sales_data"),
            merged_sales_ai
        )

    ai_sales = st.session_state.get("sales_data")
    if not isinstance(ai_sales, pd.DataFrame):
        ai_sales = pd.DataFrame()

    ai_candidates = pd.DataFrame()
    if isinstance(ai_trends, pd.DataFrame) and not ai_trends.empty:
        try:
            with st.spinner("현재 상품 후보와 1시간 판매신호를 분석하는 중..."):
                ai_candidates, _ = collect_musinsa_for_trends(
                    ai_trends,
                    top_keywords=5,
                    per_keyword=8,
                )
                ai_candidates = score_musinsa_candidates(
                    ai_candidates,
                    ai_trends,
                )
        except Exception as exc:
            st.warning(f"현재 상품 후보 수집 일부 실패: {exc}")
            ai_candidates = pd.DataFrame()

    # 공개 후보 수집이 잠시 실패하면 최신 백그라운드 스냅샷 사용
    if ai_candidates.empty:
        history_ai = load_candidate_history()
        if (
            isinstance(history_ai, pd.DataFrame)
            and not history_ai.empty
            and "수집버킷" in history_ai.columns
        ):
            buckets = sorted(
                history_ai["수집버킷"].astype(str).dropna().unique().tolist()
            )
            if buckets:
                ai_candidates = history_ai[
                    history_ai["수집버킷"].astype(str) == buckets[-1]
                ].copy()

    recommendations, ai_meta = build_ai_sales_recommendations(
        ai_trends if isinstance(ai_trends, pd.DataFrame) else pd.DataFrame(),
        ai_candidates,
        ai_sales,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("관찰 후보", f"{ai_meta.get('candidate_count', 0)}개")
    m2.metric("실제 변화신호", f"{ai_meta.get('real_signal_count', 0)}개")
    m3.metric("강력추천", f"{ai_meta.get('strong_count', 0)}개")
    m4.metric("실제판매검증", f"{ai_meta.get('verified_count', 0)}개")

    st.markdown(
        """
        <div style="border:1px solid #e5e7eb;border-radius:18px;padding:15px 17px;
                    margin:14px 0 18px;background:#fff;">
          <div style="font-size:13px;font-weight:900;color:#111827;">
            AI 판매가능성 점수
          </div>
          <div style="font-size:12px;color:#64748b;line-height:1.7;margin-top:6px;">
            네이버 검색상승 25점 · 최근 1시간 상품변화 20점 · 최근 6시간 지속상승 20점 ·
            실제 판매근거 20점 · 다중플랫폼 10점 · 신규진입/모멘텀 5점
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ai_meta.get("previous_bucket", "-") == "-":
        st.info(
            "1시간 비교 데이터가 아직 충분하지 않으면 해당 25점 영역은 0점으로 계산됩니다. "
            "자동수집 데이터가 쌓이면 같은 상품의 점수가 자동으로 갱신됩니다."
        )
    else:
        st.caption(
            f"1시간 비교: {ai_meta.get('previous_bucket','-')} → "
            f"{ai_meta.get('current_bucket','-')} · "
            f"랭킹 이탈/미수집 {ai_meta.get('dropout_count',0)}개 · "
            f"수집 커버리지 {ai_meta.get('coverage_ratio',1.0)*100:.0f}%"
        )
        if ai_meta.get("collection_unstable", False):
            st.warning(
                "이전 시간대 상품의 20% 이상이 한꺼번에 사라졌습니다. "
                "사이트 랭킹 변화일 수도 있지만 수집 누락 가능성도 있으므로 "
                "이탈 상품을 판매 하락으로 단정하지 않고 AI 추천 점수에서 제외합니다."
            )

    if ai_meta.get("six_hour_intervals", 0) > 0:
        st.caption(
            f"6시간 추세 분석: {ai_meta.get('six_hour_start','-')} → "
            f"{ai_meta.get('six_hour_end','-')} · "
            f"{ai_meta.get('six_hour_intervals',0)}개 시간구간 비교 · "
            f"지속상승 {ai_meta.get('six_hour_persistent_count',0)}개"
        )

    if recommendations.empty:
        st.warning("현재 계산 가능한 AI 추천 상품이 없습니다.")
    else:
        real_recommendations = recommendations[
            recommendations["실제추천대상"].fillna(False).astype(bool)
        ].copy()

        if real_recommendations.empty:
            st.markdown(
                """
                <div style="border:1px solid #e5e7eb;border-radius:18px;padding:22px;
                            margin:18px 0;background:#fff;">
                  <div style="font-size:18px;font-weight:950;color:#111827;">
                    현재 강한 판매 상승 신호 없음
                  </div>
                  <div style="font-size:13px;color:#64748b;line-height:1.7;margin-top:8px;">
                    검색 상승은 감지됐지만 최근 1시간 순위·리뷰 변화,
                    실제 판매근거 또는 다중플랫폼 신호가 아직 확인되지 않았습니다.
                    억지로 상품을 추천하지 않고 관찰 상태로 유지합니다.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 지금 주목할 상품")
            st.caption(
                "최근 1시간 변화·실제 판매근거·다중플랫폼 신호 중 하나 이상 확인된 상품만 표시합니다."
            )
            render_ai_recommendation_cards(real_recommendations, max_items=9)

        st.markdown("### 전체 관찰 후보")
        st.caption(
            "검색 상승만 있는 상품은 추천 카드에서 제외하고 아래 표에서 관찰 후보로만 표시합니다."
        )

        detail_cols = [
            "검색어", "브랜드", "상품명", "플랫폼",
            "AI판매가능성", "AI판정", "실제신호강도",
            "검색증감률", "1시간상태",
            "리뷰증가", "순위변화", "신규진입",
            "6시간지속상승", "상승구간수", "6시간순위상승합", "6시간리뷰증가합",
            "이탈감지",
            "판매검증", "추천근거", "상품URL"
        ]
        available = [c for c in detail_cols if c in recommendations.columns]

        st.dataframe(
            recommendations[available].head(20),
            width="stretch",
            hide_index=True,
            column_config={
                "AI판매가능성": st.column_config.ProgressColumn(
                    "AI 판매가능성",
                    min_value=0,
                    max_value=100,
                    format="%.0f점",
                ),
                "실제신호강도": st.column_config.ProgressColumn(
                    "실제 신호",
                    min_value=0,
                    max_value=70,
                    format="%.0f점",
                ),
                "검색증감률": st.column_config.NumberColumn(
                    "검색 증감률",
                    format="%.1f%%",
                ),
                "상품URL": st.column_config.LinkColumn(
                    "상품",
                    display_text="보기",
                ),
            },
        )

    st.caption(
        "※ AI 판매가능성은 실제 수집 데이터를 조합한 규칙형 신호 점수입니다. "
        "검색 상승만으로는 추천 상품으로 노출하지 않으며, 6시간 반복 상승에는 추가 가중치를 부여합니다. "
        "판매를 보장하는 수치가 아니며, 네이버 쇼핑인사이트는 일간 검색·클릭 상대지수입니다. "
        "실제 판매 검증은 판매수량·베스트순위·리뷰증가 등 직접 근거가 있는 경우에만 표시합니다."
    )

# -------------------------
# FITTING
# -------------------------
elif page == "fitting":
    st.markdown('<div class="page-title">👕 AI 가상피팅</div><div class="page-desc">신체정보와 상품 이미지를 연결하는 다음 단계 기능입니다.</div>',unsafe_allow_html=True)
    st.markdown('<div class="fitting-box"><div style="font-size:52px">🧍‍♂️👕</div><h3>3D 가상피팅 준비</h3><p>신체 사이즈 저장 → 상품 선택 → 아바타 착용 순서로 구현합니다.</p></div>',unsafe_allow_html=True)

# -------------------------
# ALERTS
# -------------------------
elif page == "alerts":
    st.markdown('<div class="page-title">🔔 급상승 알림</div><div class="page-desc">관심 상품의 상승 조건을 등록하는 화면입니다.</div>',unsafe_allow_html=True)
    st.text_input("알림 받을 검색어",placeholder="예: 여성 가디건")
    st.slider("알림 기준 상승률",5,100,20)
    st.button("알림 등록",type="primary",width="stretch")
    st.caption("실제 알림 전송은 회원 시스템과 알림 채널 연결 후 활성화합니다.")

# -------------------------
# PRO
# -------------------------
elif page == "pro":
    st.markdown('<div class="page-title">💎 마스픽 PRO</div><div class="page-desc">구독 화면 구조입니다. 실제 결제 연결 전 가격은 예시입니다.</div>',unsafe_allow_html=True)
    st.markdown("""
    <div class="price-grid">
      <div class="price-card"><div class="price-name">FREE</div><div class="price">₩0 <small>/월</small></div><div class="feature">급상승 일부</div><div class="feature">기본 상품 검색</div></div>
      <div class="price-card reco"><div class="price-name">PRO</div><div class="price">₩9,900 <small>/월 예시</small></div><div class="feature">TOP 100</div><div class="feature">판매근거 상세</div><div class="feature">AI 예측</div><div class="feature">알림</div></div>
      <div class="price-card"><div class="price-name">BUSINESS</div><div class="price">별도문의</div><div class="feature">브랜드 리포트</div><div class="feature">대량 데이터</div><div class="feature">광고·제휴</div></div>
    </div>
    """,unsafe_allow_html=True)

# -------------------------
# LOGIN
# -------------------------
elif page == "login":
    st.markdown('<div class="page-title">로그인</div><div class="page-desc">다음 단계에서 실제 회원 DB를 연결합니다.</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.text_input("이메일")
        st.text_input("비밀번호",type="password")
        st.button("로그인",type="primary",width="stretch")
    with c2:
        st.markdown('<div class="state-box"><div class="state-title">회원 시스템 연결 예정</div><div class="state-copy">구독 권한, 관심상품, 알림 설정을 계정에 저장하도록 연결합니다.</div></div>',unsafe_allow_html=True)

# -------------------------
# 운영자 도구
# -------------------------
with st.expander("운영자 도구"):
    presets={
        "남성·여성 전체":"여성 반팔티\n여성 블라우스\n여성 원피스\n여성 가디건\n여성 청바지\n여성 크로스백\n여성 운동화\n남성 반팔티\n남성 셔츠\n남성 바람막이\n남성 청바지\n남성 백팩\n남성 스니커즈",
        "여성 인기상품":"여성 반팔티\n여성 블라우스\n여성 원피스\n여성 가디건\n여성 청바지\n여성 크로스백\n여성 운동화",
        "남성 인기상품":"남성 반팔티\n남성 셔츠\n남성 바람막이\n남성 청바지\n남성 백팩\n남성 스니커즈",
        "직접 입력":""
    }
    category_map={"패션의류":"50000000","패션잡화":"50000001"}
    c1,c2=st.columns(2)
    with c1:
        preset=st.selectbox("상품군",list(presets))
    with c2:
        selected_categories=st.multiselect("조회 카테고리",list(category_map),default=list(category_map))
    keywords_text=st.text_area("비교할 검색어",presets[preset],height=130)
    keywords=tuple(dict.fromkeys(k.strip() for k in keywords_text.splitlines() if k.strip()))[:25]
    category_ids=tuple(category_map[x] for x in selected_categories)

    if st.button("실시간 네이버 분석 실행",type="primary",width="stretch"):
        try:
            with st.spinner("쇼핑인사이트 분석 중..."):
                live_raw=fetch_keyword_trends(category_ids,keywords)
            if live_raw.empty:
                st.warning("조회된 데이터가 없습니다.")
            else:
                st.session_state["live_result"]=score_and_classify(live_raw)
                st.success("실시간 트렌드 데이터를 저장했습니다.")
                st.rerun()
        except Exception as exc:
            st.error(str(exc))

    sales_csv=st.file_uploader("실제 판매근거 CSV",type=["csv"])
    if sales_csv is not None:
        try:
            st.session_state["sales_data"]=load_product_evidence(sales_csv)
            st.success("판매근거 데이터를 연결했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.download_button("판매근거 CSV 양식 받기",product_csv_template(),"상품_판매근거_입력양식.csv","text/csv",width="stretch")

render_mobile_nav()


