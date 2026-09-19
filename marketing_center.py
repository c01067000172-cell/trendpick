import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from supabase import create_client

from jinbike_supabase_storage import _validate_server_key


CHANNEL_INFO = {
    "site_seo": {
        "label": "사이트 SEO",
        "mode": "사이트 내부 적용",
        "note": "검색용 제목·설명 작업본을 생성합니다. 실제 페이지 반영은 사이트 코드/콘텐츠 연결 단계가 필요합니다.",
    },
    "naver_blog": {
        "label": "네이버 블로그",
        "mode": "작업본 생성",
        "note": "공식 게시 연동 전 단계입니다. 자동 로그인·비공식 매크로 게시를 사용하지 않습니다.",
    },
    "daangn": {
        "label": "당근",
        "mode": "작업본 생성",
        "note": "비즈프로필/광고 상품의 공식 기능과 정책 범위에서만 게시 연동합니다.",
    },
    "instagram": {
        "label": "인스타그램",
        "mode": "작업본 생성",
        "note": "Meta 공식 API 연결 전 단계입니다.",
    },
}

BUSINESS_LABEL = {
    "twojroad": "TWO J ROAD",
    "wheng": "사랑을실은설비공",
}

_client = None
_client_sig = None


def _db():
    global _client, _client_sig
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    if not url or not key:
        raise RuntimeError("광고관리 DB 연결용 Supabase 환경변수가 없습니다.")
    _validate_server_key(key)
    sig = (url, key)
    if _client is None or _client_sig != sig:
        _client = create_client(url, key)
        _client_sig = sig
    return _client


def _clean(value, limit=5000):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:limit]


def _keywords(primary, secondary):
    raw = [primary] + list(secondary or [])
    result = []
    seen = set()
    for item in raw:
        item = _clean(item, 80)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _hashtags(words, business):
    tags = []
    base = list(words)
    if business == "twojroad":
        base += ["투제이로드", "TWOJROAD", "바이크의류", "바이크용품"]
    else:
        base += ["사랑을실은설비공", "설비", "수도설비", "출장설비"]
    for word in base:
        tag = re.sub(r"[^0-9A-Za-z가-힣_]", "", str(word or ""))
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:15]


def _truncate(text, limit):
    text = _clean(text, limit * 2)
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def generate_posts(
    business,
    source_name,
    region,
    primary_keyword,
    secondary_keywords,
    channels,
    objective="검색 노출",
    contact_text="",
    payload=None,
):
    payload = dict(payload or {})
    business_name = BUSINESS_LABEL.get(business, business)
    source_name = _clean(source_name, 160)
    region = _clean(region, 80)
    primary_keyword = _clean(primary_keyword, 80)
    words = _keywords(primary_keyword, secondary_keywords)
    keyword_text = ", ".join(words)
    contact_text = _clean(contact_text, 180)
    category = _clean(payload.get("category"), 80)
    brand = _clean(payload.get("brand"), 80)
    price = payload.get("price")
    description = _clean(payload.get("description"), 500)
    site_url = _clean(payload.get("site_url"), 300)
    if not site_url and business == "twojroad":
        site_url = "https://www.maspick.co.kr/"

    facts = []
    if brand:
        facts.append(f"브랜드: {brand}")
    if category:
        facts.append(f"분류: {category}")
    if price not in (None, "", 0, "0"):
        try:
            facts.append(f"가격: {int(price):,}원")
        except (TypeError, ValueError):
            pass
    fact_text = "\n".join(f"- {x}" for x in facts)
    description_line = description or f"{source_name} 관련 정보를 확인해 주세요."

    posts = []
    for channel in channels:
        if channel not in CHANNEL_INFO:
            continue

        if channel == "site_seo":
            title_base = " · ".join(x for x in [region, primary_keyword, source_name] if x)
            title = _truncate(f"{title_base} | {business_name}", 60)
            body = _truncate(
                f"{business_name}의 {source_name} 안내입니다. "
                f"{region + ' ' if region else ''}{primary_keyword} 관련 정보와 "
                f"{keyword_text or primary_keyword} 내용을 확인하세요. {description_line}",
                155,
            )
            hashtags = []

        elif channel == "naver_blog":
            title = _truncate(
                " ".join(x for x in [region, primary_keyword, source_name, business_name] if x),
                80,
            )
            parts = [
                f"{business_name}에서 안내드립니다.",
                "",
                f"{source_name} 관련 내용입니다.",
                description_line,
            ]
            if fact_text:
                parts += ["", "■ 기본 정보", fact_text]
            if keyword_text:
                parts += ["", f"■ 관련 키워드: {keyword_text}"]
            if site_url:
                parts += ["", f"자세한 내용: {site_url}"]
            if contact_text:
                parts += ["", contact_text]
            parts += [
                "",
                "실제 상품 상태·시공 범위·비용 등은 현장 또는 상품별 조건에 따라 달라질 수 있습니다.",
            ]
            body = "\n".join(parts)
            hashtags = _hashtags(words, business)

        elif channel == "daangn":
            title = _truncate(" · ".join(x for x in [source_name, region] if x), 55)
            parts = [
                f"{business_name}입니다.",
                f"{source_name} 안내드립니다.",
                description_line,
            ]
            if fact_text:
                parts += ["", fact_text]
            if contact_text:
                parts += ["", contact_text]
            body = "\n".join(parts)
            hashtags = _hashtags(words, business)[:8]

        else:  # instagram
            title = _truncate(source_name, 80)
            parts = [
                f"{source_name}",
                "",
                description_line,
            ]
            if region:
                parts += ["", f"📍 {region}"]
            if contact_text:
                parts += ["", contact_text]
            body = "\n".join(parts)
            hashtags = _hashtags(words, business)

        posts.append(
            {
                "channel": channel,
                "title": title,
                "body": body,
                "hashtags": hashtags,
                "status": "draft",
            }
        )
    return posts


def create_campaign(
    *,
    business,
    source_type,
    source_id,
    source_name,
    region,
    primary_keyword,
    secondary_keywords,
    channels,
    objective,
    contact_text,
    payload=None,
):
    if business not in BUSINESS_LABEL:
        raise ValueError("지원하지 않는 사업 구분입니다.")
    if not _clean(source_name):
        raise ValueError("광고할 상품·서비스명을 입력해 주세요.")
    if not _clean(primary_keyword):
        raise ValueError("핵심 검색어를 입력해 주세요.")
    selected = [c for c in channels if c in CHANNEL_INFO]
    if not selected:
        raise ValueError("채널을 1개 이상 선택해 주세요.")

    payload = dict(payload or {})
    row = {
        "business": business,
        "source_type": _clean(source_type, 40) or "manual",
        "source_id": _clean(source_id, 200) or None,
        "source_name": _clean(source_name, 160),
        "region": _clean(region, 80),
        "primary_keyword": _clean(primary_keyword, 80),
        "secondary_keywords": _keywords("", secondary_keywords),
        "channels": selected,
        "objective": _clean(objective, 80) or "검색 노출",
        "contact_text": _clean(contact_text, 180),
        "status": "draft",
        "payload": payload,
    }
    created = (
        _db().table("marketing_campaigns")
        .insert(row)
        .execute()
        .data
    )
    if not created:
        raise RuntimeError("캠페인 저장 결과를 받지 못했습니다.")
    campaign = created[0]
    posts = generate_posts(
        business=business,
        source_name=row["source_name"],
        region=row["region"],
        primary_keyword=row["primary_keyword"],
        secondary_keywords=row["secondary_keywords"],
        channels=selected,
        objective=row["objective"],
        contact_text=row["contact_text"],
        payload=payload,
    )
    post_rows = [dict(post, campaign_id=campaign["id"]) for post in posts]
    if post_rows:
        _db().table("marketing_posts").insert(post_rows).execute()
    return campaign


def list_campaigns(limit=50):
    data = (
        _db().table("marketing_campaigns")
        .select(
            "id,business,source_type,source_id,source_name,region,primary_keyword,"
            "secondary_keywords,channels,objective,contact_text,status,payload,created_at,updated_at"
        )
        .order("created_at", desc=True)
        .limit(max(1, min(int(limit), 200)))
        .execute()
        .data
    )
    return data if isinstance(data, list) else []


def list_posts(campaign_id):
    data = (
        _db().table("marketing_posts")
        .select("id,campaign_id,channel,title,body,hashtags,status,publish_url,external_id,error,created_at,updated_at")
        .eq("campaign_id", str(campaign_id))
        .order("created_at")
        .execute()
        .data
    )
    return data if isinstance(data, list) else []


def update_post(post_id, *, status, publish_url=""):
    if status not in {"draft", "ready", "published", "error"}:
        raise ValueError("지원하지 않는 게시 상태입니다.")
    values = {
        "status": status,
        "publish_url": _clean(publish_url, 500) or None,
        "updated_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
    }
    _db().table("marketing_posts").update(values).eq("id", str(post_id)).execute()


def update_campaign_status(campaign_id, status):
    if status not in {"draft", "ready", "published", "archived"}:
        raise ValueError("지원하지 않는 캠페인 상태입니다.")
    values = {
        "status": status,
        "updated_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
    }
    _db().table("marketing_campaigns").update(values).eq("id", str(campaign_id)).execute()


def delete_campaign(campaign_id):
    _db().table("marketing_campaigns").delete().eq("id", str(campaign_id)).execute()


def channel_label(channel):
    return CHANNEL_INFO.get(channel, {}).get("label", channel)


def channel_note(channel):
    info = CHANNEL_INFO.get(channel, {})
    return " · ".join(x for x in [info.get("mode", ""), info.get("note", "")] if x)
