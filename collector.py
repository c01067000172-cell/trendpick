from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
SECRETS_PATH = BASE_DIR / ".streamlit" / "secrets.toml"
SALES_DIR = Path(os.getenv("TRENDPICK_DATA_DIR", str(BASE_DIR / "sales_sources")))
SNAPSHOT_PATH = SALES_DIR / "candidate_snapshots.csv"
STATUS_PATH = SALES_DIR / "collector_status.json"

API_BASE = "https://naverapihub.apigw.ntruss.com"
SHOPPING_KEYWORD_PATH = "/shopping/v1/category/keywords"

CATEGORY_IDS = ("50000000", "50000001")
KEYWORDS = (
    "여성 가디건", "여성 원피스", "와이드 데님", "남성 바람막이",
    "러닝 벨트", "크로스백", "스니커즈", "기능성 티셔츠", "카고 팬츠"
)

PRODUCT_COLUMNS = [
    "검색어", "상품ID", "브랜드", "상품명", "플랫폼",
    "현재순위", "현재리뷰수", "현재가격", "할인율",
    "이미지URL", "상품URL"
]


def read_secrets():
    data = {}
    if SECRETS_PATH.exists():
        try:
            import tomllib
            with open(SECRETS_PATH, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            data = {}
    return data


def get_secret(name: str) -> str:
    env = os.getenv(name)
    if env:
        return env.strip()
    return str(read_secrets().get(name, "")).strip()


def api_headers():
    return {
        "X-NCP-APIGW-API-KEY-ID": get_secret("NAVER_CLIENT_ID"),
        "X-NCP-APIGW-API-KEY": get_secret("NAVER_CLIENT_SECRET"),
        "Content-Type": "application/json",
    }


def fetch_keyword_trends():
    headers = api_headers()
    if not headers["X-NCP-APIGW-API-KEY-ID"] or not headers["X-NCP-APIGW-API-KEY"]:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 없습니다.")

    end_candidates = [
        date.today() - timedelta(days=1),
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=3),
        date.today() - timedelta(days=5),
        date.today() - timedelta(days=7),
    ]

    last_error = None
    for end_date in end_candidates:
        rows = []
        failed = False
        start_date = end_date - timedelta(days=27)

        for category_id in CATEGORY_IDS:
            for pos in range(0, len(KEYWORDS), 5):
                batch = KEYWORDS[pos:pos+5]
                body = {
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "timeUnit": "date",
                    "category": category_id,
                    "keyword": [{"name": k, "param": [k]} for k in batch],
                }
                r = requests.post(
                    API_BASE + SHOPPING_KEYWORD_PATH,
                    headers=headers,
                    json=body,
                    timeout=25
                )
                if r.status_code != 200:
                    last_error = f"{r.status_code}: {r.text[:200]}"
                    failed = True
                    break

                for result in r.json().get("results", []):
                    pts = result.get("data", [])
                    vals = [float(x.get("ratio", 0) or 0) for x in pts]
                    if not vals:
                        continue
                    half = max(1, len(vals)//2)
                    old = sum(vals[:half]) / len(vals[:half])
                    new_vals = vals[half:] or vals[-1:]
                    new = sum(new_vals) / len(new_vals)
                    growth = ((new-old)/old*100) if old > 0 else (100.0 if new > 0 else 0.0)
                    rows.append({
                        "상품명": result.get("title") or (result.get("keyword") or ["키워드"])[0],
                        "검색증감률": round(growth, 1),
                        "최근지수": round(new, 1),
                    })
            if failed:
                break

        if not failed and rows:
            return (
                pd.DataFrame(rows)
                .sort_values(["검색증감률", "최근지수"], ascending=False)
                .drop_duplicates("상품명")
                .head(5)
            )

    raise RuntimeError(f"네이버 쇼핑인사이트 오류: {last_error}")


def parse_compact_count(value: str) -> int:
    s = str(value or "").replace(",", "").replace("+", "").strip()
    try:
        if "만" in s:
            return int(float(s.replace("만", "")) * 10000)
        if "천" in s:
            return int(float(s.replace("천", "")) * 1000)
        digits = re.sub(r"[^0-9.]", "", s)
        return int(float(digits)) if digits else 0
    except Exception:
        return 0


def fetch_musinsa_candidates(keyword: str, max_items: int = 8) -> pd.DataFrame:
    url = f"https://www.musinsa.com/search/goods?gf=A&keyword={quote(keyword)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.select(
        'a[href*="/products/"], a[href*="goodsNo="], a[href*="/app/goods/"]'
    )
    rows, seen = [], set()

    def clean(v):
        return re.sub(r"\s+", " ", str(v or "")).strip()

    def product_id_from_url(href: str) -> str:
        for pat in [
            r"/products/(\d+)",
            r"/app/goods/(\d+)",
            r"[?&]goodsNo=(\d+)",
        ]:
            m = re.search(pat, href)
            if m:
                return m.group(1)
        return ""

    def parse_price(text: str) -> int:
        vals = re.findall(r"(\d{1,3}(?:,\d{3})+)\s*원", text)
        nums = []
        for v in vals:
            try:
                nums.append(int(v.replace(",", "")))
            except Exception:
                pass
        return min(nums) if nums else 0

    def parse_discount(text: str) -> int:
        vals = re.findall(r"(?<!\d)(\d{1,2})\s*%", text)
        nums = [int(v) for v in vals if 0 <= int(v) <= 95]
        return max(nums) if nums else 0

    for a in links:
        href = clean(a.get("href"))
        if not href:
            continue
        href = urljoin(url, href)
        pid = product_id_from_url(href)

        dedupe_key = pid or href
        if dedupe_key in seen:
            continue

        card = a
        for _ in range(6):
            if getattr(card, "parent", None) is not None:
                card = card.parent

        card_text = clean(" ".join(card.stripped_strings)) if card is not None else ""
        link_text = clean(" ".join(a.stripped_strings))

        img = card.find("img") if card is not None else None
        alt = clean(img.get("alt")) if img else ""
        image_url = ""
        if img is not None:
            for key in ("src", "data-src", "data-original", "data-lazy-src"):
                candidate = clean(img.get(key))
                if candidate and not candidate.startswith("data:"):
                    if candidate.startswith("//"):
                        image_url = "https:" + candidate
                    elif candidate.startswith("/"):
                        image_url = urljoin(url, candidate)
                    else:
                        image_url = candidate
                    break

        name = alt if 3 <= len(alt) <= 100 else link_text
        if not name or len(name) < 3:
            name = card_text[:100]
        name = clean(name)[:100]
        if len(name) < 3:
            continue

        review_count = 0
        m = re.search(r"\d(?:\.\d)?\s*\(([\d,.]+(?:천|만)?\+?)\)", card_text)
        if m:
            review_count = parse_compact_count(m.group(1))

        price = parse_price(card_text)
        discount = parse_discount(card_text)

        # 브랜드는 상품명 앞의 짧은 텍스트를 후보로 사용
        brand = ""
        if name and name in card_text:
            before = clean(card_text.split(name, 1)[0])
            parts = [clean(x) for x in re.split(r"[|·/]", before)]
            for part in reversed(parts):
                if 1 < len(part) <= 30 and not re.search(r"\d", part):
                    if part.lower() not in ("무신사", "musinsa"):
                        brand = part
                        break

        seen.add(dedupe_key)
        rows.append({
            "검색어": keyword,
            "상품ID": pid,
            "브랜드": brand,
            "상품명": name,
            "플랫폼": "무신사",
            "현재순위": len(rows) + 1,
            "현재리뷰수": review_count,
            "현재가격": price,
            "할인율": discount,
            "이미지URL": image_url,
            "상품URL": href,
        })

        if len(rows) >= max_items:
            break

    return pd.DataFrame(rows, columns=PRODUCT_COLUMNS)


def save_snapshot(df: pd.DataFrame):
    SALES_DIR.mkdir(parents=True, exist_ok=True)
    if df.empty:
        return

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    snap = df.copy()
    snap["수집시각"] = now.strftime("%Y-%m-%d %H:%M:%S")
    snap["수집버킷"] = now.strftime("%Y%m%d%H")

    if SNAPSHOT_PATH.exists():
        try:
            old = pd.read_csv(SNAPSHOT_PATH, encoding="utf-8-sig")
        except Exception:
            old = pd.DataFrame()
    else:
        old = pd.DataFrame()

    if not old.empty:
        keys = set(zip(
            old["상품URL"].astype(str),
            old["플랫폼"].astype(str),
            old["수집버킷"].astype(str),
        ))
        snap = snap[
            ~snap.apply(
                lambda row: (
                    str(row["상품URL"]),
                    str(row["플랫폼"]),
                    str(row["수집버킷"])
                ) in keys,
                axis=1
            )
        ]

    if snap.empty:
        return

    merged = pd.concat([old, snap], ignore_index=True, sort=False)
    merged.to_csv(SNAPSHOT_PATH, index=False, encoding="utf-8-sig")


def write_status(ok: bool, keywords: int, products: int, message: str):
    SALES_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps({
            "ok": ok,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "keywords": keywords,
            "products": products,
            "message": message,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main():
    try:
        trends = fetch_keyword_trends()
        frames = []
        for keyword in trends["상품명"].astype(str).tolist():
            frames.append(fetch_musinsa_candidates(keyword, 8))

        products = (
            pd.concat(frames, ignore_index=True, sort=False)
            if frames else pd.DataFrame(columns=PRODUCT_COLUMNS)
        )
        save_snapshot(products)
        write_status(
            True,
            len(trends),
            len(products),
            f"정상 수집 완료 · {len(trends)}개 급상승 검색어 / {len(products)}개 상품"
        )
        print(f"[OK] {datetime.now():%Y-%m-%d %H:%M:%S} / 키워드 {len(trends)} / 상품 {len(products)}")
    except Exception as exc:
        write_status(False, 0, 0, f"오류: {exc}")
        print(f"[ERROR] {exc}")
        raise


if __name__ == "__main__":
    main()
