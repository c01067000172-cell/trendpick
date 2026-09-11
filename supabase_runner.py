from pathlib import Path


APP_FILE = Path(__file__).with_name("app.py")
SOURCE = APP_FILE.read_text(encoding="utf-8")

LOAD_TARGET = "PRODUCTS = load_products()"
LOAD_INJECTION = """import jinbike_supabase_storage as _jinbike_supabase_storage
from datetime import datetime as _analytics_datetime, timedelta as _analytics_timedelta, timezone as _analytics_timezone
from zoneinfo import ZoneInfo as _analytics_ZoneInfo

_jinbike_local_load_products = load_products
_jinbike_old_error = getattr(st, \"error\", None)
if _jinbike_old_error is not None:
    st.error = lambda *args, **kwargs: None
try:
    _jinbike_supabase_ready = _jinbike_supabase_storage.install(globals())
finally:
    if _jinbike_old_error is not None:
        st.error = _jinbike_old_error

if not _jinbike_supabase_ready:
    def _jinbike_safe_load_products():
        try:
            return _jinbike_local_load_products()
        except Exception:
            return []
    load_products = _jinbike_safe_load_products
else:
    # Avoid a Supabase round-trip on every Streamlit rerun.
    # Admin saves clear this cache immediately so changes still appear at once.
    _jinbike_uncached_load_products = load_products
    _jinbike_uncached_save_products = save_products

    @st.cache_data(ttl=30, show_spinner=False)
    def _jinbike_cached_load_products():
        return _jinbike_uncached_load_products()

    def _jinbike_cached_save_products(products):
        result = _jinbike_uncached_save_products(products)
        _jinbike_cached_load_products.clear()
        return result

    load_products = _jinbike_cached_load_products
    save_products = _jinbike_cached_save_products

PRODUCTS = load_products()

_site_analytics_client = None
if _jinbike_supabase_ready:
    try:
        _analytics_url = os.getenv(\"SUPABASE_URL\", \"\").strip().rstrip(\"/\")
        _analytics_key = (
            os.getenv(\"SUPABASE_SECRET_KEY\", \"\").strip()
            or os.getenv(\"SUPABASE_SERVICE_ROLE_KEY\", \"\").strip()
        )
        _jinbike_supabase_storage._validate_server_key(_analytics_key)
        _site_analytics_client = _jinbike_supabase_storage._get_client(
            _analytics_url,
            _analytics_key,
        )
    except Exception as _analytics_exc:
        print(
            \"[ANALYTICS] client init failed: \"
            + type(_analytics_exc).__name__
            + \": \"
            + str(_analytics_exc)[:300],
            flush=True,
        )


def _record_real_pageview():
    if _site_analytics_client is None:
        return

    page = str(get_param(\"page\", \"home\") or \"home\")
    if page == \"admin\":
        return

    category = str(get_param(\"cat\", \"\") or \"\")
    subcategory = str(get_param(\"sub\", \"\") or \"\")
    product_id = str(get_param(\"id\", \"\") or \"\")
    route_key = (page, category, subcategory, product_id)

    if \"_analytics_session_id\" not in st.session_state:
        st.session_state[\"_analytics_session_id\"] = uuid.uuid4().hex

    if st.session_state.get(\"_analytics_last_route\") == route_key:
        return

    event_page = page + ((\":\" + product_id) if product_id else \"\")
    try:
        (
            _site_analytics_client.table(\"site_visit_events\")
            .insert({
                \"session_id\": st.session_state[\"_analytics_session_id\"],
                \"page\": event_page,
                \"category\": category,
                \"subcategory\": subcategory,
                \"event_type\": \"pageview\",
            })
            .execute()
        )
        st.session_state[\"_analytics_last_route\"] = route_key
    except Exception as _analytics_exc:
        print(
            \"[ANALYTICS] pageview insert failed: \"
            + type(_analytics_exc).__name__
            + \": \"
            + str(_analytics_exc)[:300],
            flush=True,
        )


def load_real_site_metrics():
    if _site_analytics_client is None:
        return None

    kst = _analytics_ZoneInfo(\"Asia/Seoul\")
    now_kst = _analytics_datetime.now(kst)
    first_day = now_kst.date() - _analytics_timedelta(days=6)
    start_kst = _analytics_datetime(
        first_day.year,
        first_day.month,
        first_day.day,
        tzinfo=kst,
    )
    start_utc = start_kst.astimezone(_analytics_timezone.utc).isoformat()

    rows = []
    offset = 0
    try:
        while True:
            batch = (
                _site_analytics_client.table(\"site_visit_events\")
                .select(\"created_at,session_id,page,category,subcategory\")
                .gte(\"created_at\", start_utc)
                .order(\"created_at\")
                .range(offset, offset + 999)
                .execute()
                .data
            ) or []
            if not isinstance(batch, list):
                raise ValueError(\"site_visit_events 응답 형식이 올바르지 않습니다.\")
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
    except Exception as _analytics_exc:
        print(
            \"[ANALYTICS] metrics load failed: \"
            + type(_analytics_exc).__name__
            + \": \"
            + str(_analytics_exc)[:300],
            flush=True,
        )
        return None

    daily = {}
    for day_offset in range(7):
        day = first_day + _analytics_timedelta(days=day_offset)
        daily[day] = {\"sessions\": set(), \"pageviews\": 0}

    for row in rows:
        try:
            raw_stamp = str(row.get(\"created_at\") or \"\").replace(\"Z\", \"+00:00\")
            local_day = _analytics_datetime.fromisoformat(raw_stamp).astimezone(kst).date()
        except Exception:
            continue

        if local_day not in daily:
            continue
        daily[local_day][\"pageviews\"] += 1
        session_id = str(row.get(\"session_id\") or \"\")
        if session_id:
            daily[local_day][\"sessions\"].add(session_id)

    today = now_kst.date()
    seven_day_sessions = {
        str(row.get(\"session_id\") or \"\")
        for row in rows
        if str(row.get(\"session_id\") or \"\")
    }

    daily_rows = [
        {
            \"날짜\": day.strftime(\"%m-%d\"),
            \"방문 세션\": len(values[\"sessions\"]),
            \"페이지뷰\": values[\"pageviews\"],
        }
        for day, values in daily.items()
    ]

    return {
        \"today_sessions\": len(daily[today][\"sessions\"]),
        \"today_pageviews\": daily[today][\"pageviews\"],
        \"seven_day_sessions\": len(seven_day_sessions),
        \"seven_day_pageviews\": len(rows),
        \"daily\": daily_rows,
    }


_record_real_pageview()"""

STATUS_TARGET = 'f"관리자 로그인 상태 · 저장 위치: {PRODUCT_FILE}"'
STATUS_REPLACEMENT = 'f"관리자 로그인 상태 · 저장 위치: {globals().get(\'SUPABASE_STATUS\', PRODUCT_FILE)}"'

SITE_STATUS_TARGET = 'st.write("상품 저장 연결: " + str(globals().get("SUPABASE_STATUS", "로컬 파일 저장")))'
SITE_STATUS_REPLACEMENT = """st.write("상품 저장 연결: " + str(globals().get("SUPABASE_STATUS", "로컬 파일 저장")))

    st.divider()
    st.markdown("#### 실제 접속 통계")
    real_metrics = load_real_site_metrics()
    if real_metrics is None:
        st.warning("실제 접속 통계를 불러오지 못했습니다. 임의 수치는 표시하지 않습니다.")
    else:
        metric_columns = st.columns(4)
        metric_columns[0].metric("오늘 방문 세션", real_metrics["today_sessions"])
        metric_columns[1].metric("오늘 페이지뷰", real_metrics["today_pageviews"])
        metric_columns[2].metric("최근 7일 방문 세션", real_metrics["seven_day_sessions"])
        metric_columns[3].metric("최근 7일 페이지뷰", real_metrics["seven_day_pageviews"])
        st.caption("실제 사이트 접속 이벤트 기준 · 관리자 페이지 제외 · 통계 기능 적용 이후 데이터만 집계")
        st.dataframe(real_metrics["daily"], use_container_width=True, hide_index=True)"""

BANNER_TARGET = """def banner_image_src():
    if not BANNER_FILE.exists():"""
BANNER_REPLACEMENT = """def banner_image_src():
    static_banner = Path(__file__).parent / "static" / "jinbike_banner.webp"
    if static_banner.exists():
        return "/app/static/jinbike_banner.webp"

    if not BANNER_FILE.exists():"""

if LOAD_TARGET not in SOURCE:
    raise RuntimeError("Supabase storage injection point was not found in app.py")
if SITE_STATUS_TARGET not in SOURCE:
    raise RuntimeError("Site status injection point was not found in app.py")

PATCHED_SOURCE = SOURCE.replace(LOAD_TARGET, LOAD_INJECTION, 1)
PATCHED_SOURCE = PATCHED_SOURCE.replace(
    STATUS_TARGET,
    STATUS_REPLACEMENT,
    1,
)
PATCHED_SOURCE = PATCHED_SOURCE.replace(
    SITE_STATUS_TARGET,
    SITE_STATUS_REPLACEMENT,
    1,
)
PATCHED_SOURCE = PATCHED_SOURCE.replace(
    BANNER_TARGET,
    BANNER_REPLACEMENT,
    1,
)

# Store brand normalization for the deployed storefront.
# Keep all customer-facing labels, SEO text, admin title, footer and logo consistent.
PATCHED_SOURCE = PATCHED_SOURCE.replace("2J ROAD", "TWO J ROAD")
PATCHED_SOURCE = PATCHED_SOURCE.replace('content:"2J";', 'content:"TWO J";')
PATCHED_SOURCE = PATCHED_SOURCE.replace("2JROAD", "TWOJROAD")

namespace = {
    "__name__": "__main__",
    "__file__": str(APP_FILE),
    "__package__": None,
}

exec(
    compile(PATCHED_SOURCE, str(APP_FILE), "exec"),
    namespace,
    namespace,
)
