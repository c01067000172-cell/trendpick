from pathlib import Path


APP_FILE = Path(__file__).with_name("app.py")
SOURCE = APP_FILE.read_text(encoding="utf-8")

LOAD_TARGET = "PRODUCTS = load_products()"
LOAD_INJECTION = """import jinbike_supabase_storage as _jinbike_supabase_storage\n_jinbike_supabase_storage.install(globals())\n\nPRODUCTS = load_products()"""

STATUS_TARGET = 'f"관리자 로그인 상태 · 저장 위치: {PRODUCT_FILE}"'
STATUS_REPLACEMENT = 'f"관리자 로그인 상태 · 저장 위치: {globals().get(\'SUPABASE_STATUS\', PRODUCT_FILE)}"'

if LOAD_TARGET not in SOURCE:
    raise RuntimeError("Supabase storage injection point was not found in app.py")

PATCHED_SOURCE = SOURCE.replace(LOAD_TARGET, LOAD_INJECTION, 1)
PATCHED_SOURCE = PATCHED_SOURCE.replace(
    STATUS_TARGET,
    STATUS_REPLACEMENT,
    1,
)

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
