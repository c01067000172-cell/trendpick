from pathlib import Path


APP_FILE = Path(__file__).with_name("app.py")
SOURCE = APP_FILE.read_text(encoding="utf-8")

TARGET = "PRODUCTS = load_products()"
INJECTION = """import jinbike_supabase_storage as _jinbike_supabase_storage\n_jinbike_supabase_storage.install(globals())\n\nPRODUCTS = load_products()"""

if TARGET not in SOURCE:
    raise RuntimeError("Supabase storage injection point was not found in app.py")

PATCHED_SOURCE = SOURCE.replace(TARGET, INJECTION, 1)

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
