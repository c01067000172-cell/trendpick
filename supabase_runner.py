from pathlib import Path


APP_FILE = Path(__file__).with_name("app.py")
SOURCE = APP_FILE.read_text(encoding="utf-8")

LOAD_TARGET = "PRODUCTS = load_products()"
LOAD_INJECTION = """import jinbike_supabase_storage as _jinbike_supabase_storage
import seo_server as _payment_backend
from datetime import datetime as _analytics_datetime, timedelta as _analytics_timedelta, timezone as _analytics_timezone
from zoneinfo import ZoneInfo as _analytics_ZoneInfo

PAYMENT_TEST_MODE = bool(_payment_backend.TOSS_TEST_MODE)

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


def render_order_admin():
    st.subheader(\"주문 · 결제 관리\")
    if PAYMENT_TEST_MODE:
        st.warning(\"현재 토스페이먼츠 TEST 모드입니다. 테스트 결제는 실제 금액이 청구되지 않습니다.\")

    try:
        rows = _payment_backend.admin_orders(200)
    except Exception as exc:
        st.error(\"주문 DB를 불러오지 못했습니다: \" + str(exc))
        return

    paid = [row for row in rows if row.get(\"status\") == \"paid\"]
    pending = [row for row in rows if row.get(\"status\") in (\"pending\", \"awaiting_deposit\")]
    canceled = [row for row in rows if row.get(\"status\") in (\"canceled\", \"partial_canceled\")]
    metrics = st.columns(4)
    metrics[0].metric(\"전체 주문\", len(rows))
    metrics[1].metric(\"결제 완료\", len(paid))
    metrics[2].metric(\"결제 완료 금액\", f\"{sum(int(row.get('amount') or 0) for row in paid):,}원\")
    metrics[3].metric(\"결제 대기\", len(pending))
    st.caption(\"Supabase 실제 주문·결제 데이터 기준 · 테스트 주문과 실결제 주문은 구분 표시\")

    if not rows:
        st.info(\"아직 주문이 없습니다.\")
        return

    status_labels = {
        \"pending\": \"결제대기\",
        \"paid\": \"결제완료\",
        \"awaiting_deposit\": \"입금대기\",
        \"failed\": \"결제실패\",
        \"canceled\": \"취소완료\",
        \"partial_canceled\": \"부분취소\",
    }
    table_rows = []
    for row in rows:
        table_rows.append({
            \"구분\": \"TEST\" if row.get(\"is_test\") else \"LIVE\",
            \"주문번호\": row.get(\"order_id\", \"\"),
            \"상품\": row.get(\"product_name\", \"\"),
            \"금액\": int(row.get(\"amount\") or 0),
            \"상태\": status_labels.get(row.get(\"status\"), row.get(\"status\", \"\")),
            \"결제수단\": \" / \".join(x for x in [str(row.get(\"payment_method\") or \"\"), str(row.get(\"easy_pay_provider\") or \"\")] if x),
            \"주문자\": row.get(\"buyer_name\", \"\"),
            \"주문시각\": row.get(\"created_at\", \"\"),
        })
    st.dataframe(table_rows, hide_index=True, use_container_width=True)

    selected_id = st.selectbox(
        \"주문 상세 선택\",
        [row.get(\"order_id\", \"\") for row in rows],
        format_func=lambda value: next(
            (
                (\"[TEST] \" if row.get(\"is_test\") else \"[LIVE] \")
                + str(row.get(\"product_name\") or \"상품\")
                + \" · \"
                + f\"{int(row.get('amount') or 0):,}원\"
                + \" · \"
                + status_labels.get(row.get(\"status\"), str(row.get(\"status\") or \"\"))
                for row in rows
                if row.get(\"order_id\") == value
            ),
            value,
        ),
        key=\"admin_order_select\",
    )
    order = next((row for row in rows if row.get(\"order_id\") == selected_id), None)
    if not order:
        return

    st.write(\"주문번호: \" + str(order.get(\"order_id\") or \"\"))
    st.write(\"상품: \" + str(order.get(\"product_name\") or \"\"))
    st.write(\"금액: \" + f\"{int(order.get('amount') or 0):,}원\")
    st.write(\"주문자: \" + str(order.get(\"buyer_name\") or \"\") + \" / \" + str(order.get(\"buyer_phone\") or \"\"))
    if order.get(\"buyer_email\"):
        st.write(\"이메일: \" + str(order.get(\"buyer_email\")))
    address = \" \".join(
        str(x or \"\").strip()
        for x in [order.get(\"postal_code\"), order.get(\"address1\"), order.get(\"address2\")]
        if str(x or \"\").strip()
    )
    st.write(\"배송지: \" + address)
    if order.get(\"failure_message\"):
        st.error(str(order.get(\"failure_code\") or \"결제 오류\") + \" · \" + str(order.get(\"failure_message\")))

    if order.get(\"status\") == \"paid\" and order.get(\"payment_key\"):
        st.markdown(\"#### 결제 취소\")
        cancel_reason = st.text_input(
            \"취소 사유\",
            value=\"고객 요청\",
            key=\"cancel_reason_\" + str(selected_id),
        )
        confirm_cancel = st.checkbox(
            \"결제 취소를 확인했습니다\",
            key=\"confirm_cancel_\" + str(selected_id),
        )
        if st.button(\"결제 전액 취소\", key=\"cancel_payment_\" + str(selected_id), use_container_width=True):
            if not confirm_cancel:
                st.warning(\"취소 확인을 체크해 주세요.\")
            else:
                try:
                    _payment_backend.cancel_order(selected_id, cancel_reason)
                    st.success(\"토스페이먼츠 결제 취소와 주문 상태 변경이 완료되었습니다.\")
                    st.rerun()
                except Exception as exc:
                    st.error(\"결제 취소 실패: \" + str(exc))


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

DETAIL_PAYMENT_TARGET = """        st.write(detail_text)
        render_detail_files(detail_files)

        contact_buttons = \"\""""
DETAIL_PAYMENT_REPLACEMENT = """        st.write(detail_text)
        render_detail_files(detail_files)

        if (
            str(product.get(\"condition\", \"\")) == \"판매중\"
            and int(product.get(\"price\", 0) or 0) > 0
            and not product.get(\"demo\")
        ):
            payment_label = \"테스트 결제\" if globals().get(\"PAYMENT_TEST_MODE\", True) else \"구매하기\"
            safe_markdown(
                f'<div class=\"contact-actions\"><a class=\"contact-btn primary\" '
                f'href=\"/checkout/{escape(str(product.get(\"id\", \"\")), quote=True)}\" target=\"_self\">'
                f'{payment_label}</a></div>',
                unsafe_allow_html=True,
            )
            if globals().get(\"PAYMENT_TEST_MODE\", True):
                st.caption(\"현재 TEST 결제 모드 · 실제 금액은 청구되지 않습니다.\")

        contact_buttons = \"\""""

ADMIN_TABS_TARGET = """    tab1, tab2, tab3 = st.tabs(
        [
            \"상품 등록\",
            \"상품 수정 · 삭제\",
            \"사이트 현황\",
        ]
    )

    with tab1:
        render_add_product()

    with tab2:
        render_manage_products()
    with tab3:
        render_site_status()"""
ADMIN_TABS_REPLACEMENT = """    tab1, tab2, tab3, tab4 = st.tabs(
        [
            \"상품 등록\",
            \"상품 수정 · 삭제\",
            \"주문 · 결제\",
            \"사이트 현황\",
        ]
    )

    with tab1:
        render_add_product()

    with tab2:
        render_manage_products()
    with tab3:
        render_order_admin()
    with tab4:
        render_site_status()"""

BANNER_TARGET = """def banner_image_src():
    if not BANNER_FILE.exists():"""
BANNER_REPLACEMENT = """def banner_image_src():
    static_banner = Path(__file__).parent / \"static\" / \"jinbike_banner.webp\"
    if static_banner.exists():
        return \"/app/static/jinbike_banner.webp\"

    if not BANNER_FILE.exists():"""

if LOAD_TARGET not in SOURCE:
    raise RuntimeError("Supabase storage injection point was not found in app.py")
if SITE_STATUS_TARGET not in SOURCE:
    raise RuntimeError("Site status injection point was not found in app.py")
if DETAIL_PAYMENT_TARGET not in SOURCE:
    raise RuntimeError("Product payment button injection point was not found in app.py")
if ADMIN_TABS_TARGET not in SOURCE:
    raise RuntimeError("Admin payment tab injection point was not found in app.py")

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
    DETAIL_PAYMENT_TARGET,
    DETAIL_PAYMENT_REPLACEMENT,
    1,
)
PATCHED_SOURCE = PATCHED_SOURCE.replace(
    ADMIN_TABS_TARGET,
    ADMIN_TABS_REPLACEMENT,
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
