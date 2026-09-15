"""TWO J ROAD 상품 팝업용 기능: 옵션, 사이즈표, 찜, 상품문의, 후기.

DB 접근은 결제 서버(seo_server)와 같은 서버 키 클라이언트를 사용합니다.
모든 테이블은 RLS가 켜져 있고 공개 정책이 없어 서버에서만 읽고 쓸 수 있습니다.
"""
import hashlib
import hmac
import re
import secrets
import time

import seo_server as _backend

_option_cache = {}
_OPTION_TTL = 10


def _db():
    return _backend.db_client()


# ---------------------------------------------------------------- 옵션

def get_options(product_id):
    product_id = str(product_id or "")
    hit = _option_cache.get(product_id)
    if hit and time.monotonic() - hit[0] < _OPTION_TTL:
        return hit[1]
    try:
        rows = _backend.product_options(product_id)
    except Exception:
        rows = hit[1] if hit else []
    _option_cache[product_id] = (time.monotonic(), rows)
    return rows


def options_to_text(rows):
    lines = []
    for row in rows:
        stock = "" if row.get("stock") is None else str(int(row["stock"]))
        extra = int(row.get("extra_price") or 0)
        lines.append(f"{row.get('name')}, {stock}, {extra}")
    return "\n".join(lines)


def parse_options_text(text):
    """한 줄에 하나: '옵션명, 재고, 추가금액'. 재고를 비우면 재고 제한 없음."""
    rows, seen = [], set()
    for number, raw in enumerate(str(text or "").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        name = parts[0]
        if not 1 <= len(name) <= 60:
            raise ValueError(f"{number}번째 줄: 옵션명은 1~60자로 입력해 주세요.")
        if name in seen:
            raise ValueError(f"{number}번째 줄: '{name}' 옵션이 중복됐습니다.")
        stock = None
        if len(parts) > 1 and parts[1] != "":
            if not re.fullmatch(r"\d{1,6}", parts[1]):
                raise ValueError(f"{number}번째 줄: 재고는 0 이상의 숫자로 입력해 주세요.")
            stock = int(parts[1])
        extra = 0
        if len(parts) > 2 and parts[2] != "":
            value = parts[2].replace("+", "").replace("원", "").replace(" ", "")
            if not re.fullmatch(r"\d{1,9}", value.replace(",", "")):
                raise ValueError(f"{number}번째 줄: 추가금액은 0 이상의 숫자로 입력해 주세요.")
            extra = int(value.replace(",", ""))
        seen.add(name)
        rows.append({"name": name, "stock": stock, "extra_price": extra, "sort": len(rows)})
    if len(rows) > 50:
        raise ValueError("옵션은 최대 50개까지 등록할 수 있습니다.")
    return rows


def save_options(product_id, rows):
    product_id = str(product_id)
    client = _db()
    names = {row["name"] for row in rows}
    existing = _backend.product_options(product_id)
    for row in existing:
        if row.get("name") not in names:
            client.table("product_options").delete().eq("product_id", product_id).eq(
                "name", row.get("name")
            ).execute()
    if rows:
        client.table("product_options").upsert(
            [dict(row, product_id=product_id) for row in rows],
            on_conflict="product_id,name",
        ).execute()
    _option_cache.pop(product_id, None)


# ---------------------------------------------------------------- 사이즈표

def parse_size_table(text):
    """첫 줄은 제목 줄. 칸은 쉼표 또는 탭으로 구분."""
    rows = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        cells = [c.strip() for c in re.split(r"\t|,", line)]
        rows.append(cells[:12])
    if not rows:
        return [], []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    return rows[0], rows[1:30]


# ---------------------------------------------------------------- 찜

def like_count(product_id):
    try:
        rows = (
            _db().table("product_likes").select("visitor_id", count="exact")
            .eq("product_id", str(product_id)).limit(1).execute()
        )
        return int(rows.count or 0)
    except Exception:
        return 0


def is_liked(product_id, visitor_id):
    if not visitor_id:
        return False
    try:
        rows = (
            _db().table("product_likes").select("product_id")
            .eq("product_id", str(product_id)).eq("visitor_id", visitor_id)
            .limit(1).execute().data
        )
        return bool(rows)
    except Exception:
        return False


def toggle_like(product_id, visitor_id):
    if not visitor_id or not 8 <= len(visitor_id) <= 64:
        raise ValueError("브라우저 정보를 확인할 수 없어 찜할 수 없습니다. 새로고침 후 다시 시도해 주세요.")
    client = _db()
    if is_liked(product_id, visitor_id):
        client.table("product_likes").delete().eq("product_id", str(product_id)).eq(
            "visitor_id", visitor_id
        ).execute()
        return False
    client.table("product_likes").upsert(
        {"product_id": str(product_id), "visitor_id": visitor_id},
        on_conflict="product_id,visitor_id",
    ).execute()
    return True


# ---------------------------------------------------------------- 상품문의

def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def _check_password(password, stored):
    try:
        salt, _ = str(stored).split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(_hash_password(password, salt), str(stored))


def list_qna(product_id, limit=30):
    rows = (
        _db().table("product_qna")
        .select("id,author,is_secret,question,answer,answered_at,created_at")
        .eq("product_id", str(product_id)).eq("hidden", False)
        .order("created_at", desc=True).limit(limit).execute().data
    ) or []
    return rows


def add_qna(product_id, author, password, question, is_secret):
    author = str(author or "").strip()
    question = str(question or "").strip()
    password = str(password or "")
    if not 1 <= len(author) <= 20:
        raise ValueError("작성자 이름을 1~20자로 입력해 주세요.")
    if not 4 <= len(password) <= 30:
        raise ValueError("비밀번호를 4~30자로 입력해 주세요.")
    if not 5 <= len(question) <= 1000:
        raise ValueError("문의 내용을 5~1000자로 입력해 주세요.")
    _db().table("product_qna").insert({
        "product_id": str(product_id),
        "author": author,
        "password_hash": _hash_password(password),
        "is_secret": bool(is_secret),
        "question": question,
    }).execute()


def read_secret_qna(qna_id, password):
    rows = (
        _db().table("product_qna").select("question,answer,password_hash")
        .eq("id", int(qna_id)).eq("hidden", False).limit(1).execute().data
    ) or []
    if not rows or not _check_password(str(password or ""), rows[0].get("password_hash")):
        raise ValueError("비밀번호가 맞지 않습니다.")
    return rows[0]


def admin_list_qna(limit=200):
    return (
        _db().table("product_qna")
        .select("id,product_id,author,is_secret,question,answer,answered_at,hidden,created_at")
        .order("created_at", desc=True).limit(limit).execute().data
    ) or []


def admin_answer_qna(qna_id, answer):
    answer = str(answer or "").strip()
    if not answer:
        raise ValueError("답변 내용을 입력해 주세요.")
    _db().table("product_qna").update({
        "answer": answer[:2000],
        "answered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }).eq("id", int(qna_id)).execute()


def admin_set_qna_hidden(qna_id, hidden):
    _db().table("product_qna").update({"hidden": bool(hidden)}).eq("id", int(qna_id)).execute()


# ---------------------------------------------------------------- 후기

def _mask_name(name):
    name = str(name or "").strip()
    if len(name) <= 1:
        return name + "*"
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def list_reviews(product_id, limit=30):
    return (
        _db().table("product_reviews")
        .select("id,author,rating,content,option_name,created_at")
        .eq("product_id", str(product_id)).eq("hidden", False)
        .order("created_at", desc=True).limit(limit).execute().data
    ) or []


def review_summary(reviews):
    if not reviews:
        return 0.0, 0
    return round(sum(int(r.get("rating") or 0) for r in reviews) / len(reviews), 1), len(reviews)


def add_review(product_id, order_id, phone, rating, content):
    order_id = str(order_id or "").strip()
    digits = re.sub(r"\D", "", str(phone or ""))
    content = str(content or "").strip()
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = 0
    if not 1 <= rating <= 5:
        raise ValueError("별점을 선택해 주세요.")
    if not 10 <= len(content) <= 1000:
        raise ValueError("후기는 10~1000자로 입력해 주세요.")
    order = _backend._order_row(order_id) if order_id.startswith("TJR_") else None
    if not order or not digits or order.get("buyer_phone") != digits:
        raise ValueError("주문번호와 휴대폰 번호가 일치하는 주문을 찾을 수 없습니다.")
    if order.get("status") != "paid":
        raise ValueError("결제가 완료된 주문만 후기를 남길 수 있습니다.")
    items = [i for i in _backend.order_items(order) if str(i.get("product_id")) == str(product_id)]
    if not items:
        raise ValueError("이 주문에는 해당 상품이 없습니다.")
    option = str(items[0].get("option_name") or "")
    existing = (
        _db().table("product_reviews").select("id")
        .eq("order_id", order_id).eq("product_id", str(product_id)).eq("option_name", option)
        .limit(1).execute().data
    )
    if existing:
        raise ValueError("이미 이 주문으로 후기를 작성하셨습니다.")
    _db().table("product_reviews").insert({
        "product_id": str(product_id),
        "order_id": order_id,
        "option_name": option,
        "author": _mask_name(order.get("buyer_name")),
        "rating": rating,
        "content": content,
    }).execute()


def admin_list_reviews(limit=200):
    return (
        _db().table("product_reviews")
        .select("id,product_id,order_id,author,rating,content,option_name,hidden,created_at")
        .order("created_at", desc=True).limit(limit).execute().data
    ) or []


def admin_set_review_hidden(review_id, hidden):
    _db().table("product_reviews").update({"hidden": bool(hidden)}).eq("id", int(review_id)).execute()
