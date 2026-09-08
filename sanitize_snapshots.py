from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SALES_DIR = Path(os.getenv("TRENDPICK_DATA_DIR", str(BASE_DIR / "sales_sources")))
SNAPSHOT_PATH = SALES_DIR / "candidate_snapshots.csv"

# MASPICK에서 다루는 상품군: 패션의류 / 패션잡화 / 화장품·미용
PRODUCT_TERMS = (
    "의류", "옷", "티셔츠", "셔츠", "블라우스", "니트", "가디건", "맨투맨", "후드",
    "자켓", "재킷", "점퍼", "코트", "패딩", "바람막이", "원피스", "스커트", "치마",
    "바지", "팬츠", "슬랙스", "데님", "청바지", "조끼", "하객룩",
    "신발", "운동화", "스니커즈", "구두", "부츠", "장화", "샌들", "슬리퍼",
    "가방", "백팩", "크로스백", "숄더백", "토트백", "지갑", "벨트", "모자", "캡",
    "스카프", "양말", "귀걸이", "목걸이", "팔찌", "반지", "악세사리", "액세서리",
    "화장품", "토너", "스킨", "로션", "크림", "세럼", "에센스", "앰플", "쿠션",
    "파운데이션", "팩트", "틴트", "립", "마스카라", "아이섀도", "선크림", "레티놀",
    "샴푸", "트리트먼트", "헤어", "가발", "네일", "속눈썹", "메이크업",
)

# 상품 구매 의도와 무관한 명확한 비상품 검색어. PRODUCT_TERMS보다 우선 차단.
NON_PRODUCT_TERMS = (
    "kbo", "프로야구", "야구일정", "야구 경기", "야구중계", "로또", "복권",
    "k리그", "라리가", "프리미어리그", "축구일정", "축구중계",
    "날씨", "환율", "주가", "증시", "채용", "면접", "학원", "강의", "수업",
    "자격증", "시험", "학과", "병원", "산부인과", "키즈카페", "헬스장",
    "전시회", "박람회", "행사", "축제", "여행", "가볼만한곳",
)


def is_product_keyword(value: object) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    if any(term in text for term in NON_PRODUCT_TERMS):
        return False
    return any(term in text for term in PRODUCT_TERMS)


def sanitize_snapshot() -> tuple[int, int]:
    if not SNAPSHOT_PATH.exists():
        return 0, 0

    try:
        df = pd.read_csv(SNAPSHOT_PATH, encoding="utf-8-sig")
    except Exception:
        return 0, 0

    if df.empty or "검색어" not in df.columns:
        return len(df), 0

    before = len(df)
    clean = df[df["검색어"].map(is_product_keyword)].copy()

    # 같은 시간대에 같은 상품이 여러 번 쌓인 경우 최신 1건만 유지
    dedupe_cols = [c for c in ["수집버킷", "검색어", "상품URL", "플랫폼"] if c in clean.columns]
    if dedupe_cols:
        clean = clean.drop_duplicates(dedupe_cols, keep="last")

    clean.to_csv(SNAPSHOT_PATH, index=False, encoding="utf-8-sig")
    removed = before - len(clean)
    return len(clean), removed


if __name__ == "__main__":
    remaining, removed = sanitize_snapshot()
    print(f"[sanitize] removed={removed} remaining={remaining}", flush=True)
