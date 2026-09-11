"""JIN BIKE Render boot-time Supabase verification and narrow checkout patch.

Loaded only when PYTHONPATH includes the repository. Supabase verification runs
only for the Streamlit server process. The checkout patch exempts only the
server-owned /api/orders/create endpoint from Streamlit's built-in XSRF token
check; the endpoint itself still enforces same-origin and rate limiting.
"""

import base64
import json
import os
import sys
import uuid
from urllib.parse import urlparse


def _is_streamlit_process():
    args = [str(x).lower() for x in getattr(sys, "orig_argv", sys.argv)]
    return any("streamlit" in arg for arg in args)


def _key_kind(key):
    if key.startswith("sb_secret_"):
        return "secret"
    if key.startswith("sb_publishable_"):
        return "publishable"
    if key.startswith("eyJ"):
        try:
            part = key.split(".")[1]
            part += "=" * (-len(part) % 4)
            role = json.loads(base64.urlsafe_b64decode(part).decode()).get("role")
            return f"legacy:{role or 'unknown'}"
        except Exception:
            return "legacy:unknown"
    return "unknown"


def _verify():
    if not _is_streamlit_process():
        return

    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip() or "product-images"

    if not url or not key:
        print("[JINBIKE-BOOT] FAIL missing SUPABASE_URL or server key", flush=True)
        return

    kind = _key_kind(key)
    print(f"[JINBIKE-BOOT] key_type={kind} bucket={bucket}", flush=True)

    if kind in ("publishable", "legacy:anon", "legacy:unknown", "unknown"):
        print(
            "[JINBIKE-BOOT] FAIL server key is not a Secret/service_role credential",
            flush=True,
        )
        return

    try:
        from supabase import create_client
    except Exception as exc:
        print(
            f"[JINBIKE-BOOT] FAIL SDK import {type(exc).__name__}: {str(exc)[:300]}",
            flush=True,
        )
        return

    try:
        client = create_client(url, key)
        client.table("products").select("id").limit(1).execute()
        print("[JINBIKE-BOOT] DB OK", flush=True)
    except Exception as exc:
        print(
            f"[JINBIKE-BOOT] DB FAIL {type(exc).__name__}: {str(exc)[:600]}",
            flush=True,
        )
        return

    storage = client.storage.from_(bucket)
    path = f"__healthcheck__/boot-{uuid.uuid4().hex[:12]}.txt"
    try:
        storage.upload(
            path=path,
            file=b"jinbike-storage-boot-check",
            file_options={
                "content-type": "text/plain",
                "cache-control": "0",
                "upsert": "false",
            },
        )
        print("[JINBIKE-BOOT] STORAGE WRITE OK", flush=True)
        storage.remove([path])
        print("[JINBIKE-BOOT] STORAGE DELETE OK", flush=True)
        print("[JINBIKE-BOOT] ALL OK", flush=True)
    except Exception as exc:
        print(
            f"[JINBIKE-BOOT] STORAGE FAIL {type(exc).__name__}: {str(exc)[:800]}",
            flush=True,
        )


def _install_checkout_xsrf_patch():
    """Keep Streamlit XSRF protection except for our same-origin order API."""
    try:
        import tornado.web
    except Exception as exc:
        print(
            f"[PAYMENT-XSRF] patch import failed {type(exc).__name__}: {str(exc)[:300]}",
            flush=True,
        )
        return

    handler_cls = tornado.web.RequestHandler
    if getattr(handler_cls, "_twoj_checkout_xsrf_patched", False):
        return

    original = handler_cls.check_xsrf_cookie

    def patched_check_xsrf_cookie(self):
        request = getattr(self, "request", None)
        path = getattr(request, "path", "") if request is not None else ""
        if path == "/api/orders/create":
            origin = request.headers.get("Origin", "").strip()
            if origin:
                try:
                    if urlparse(origin).netloc.lower() != request.host.lower():
                        raise tornado.web.HTTPError(403, "Cross-origin checkout request blocked")
                except tornado.web.HTTPError:
                    raise
                except Exception:
                    raise tornado.web.HTTPError(403, "Invalid checkout origin")
            return None
        return original(self)

    handler_cls.check_xsrf_cookie = patched_check_xsrf_cookie
    handler_cls._twoj_checkout_xsrf_patched = True
    print("[PAYMENT-XSRF] checkout endpoint patch installed", flush=True)


try:
    _install_checkout_xsrf_patch()
except Exception as _exc:
    print(
        f"[PAYMENT-XSRF] FATAL {type(_exc).__name__}: {str(_exc)[:500]}",
        flush=True,
    )

try:
    _verify()
except Exception as _exc:
    print(
        f"[JINBIKE-BOOT] FATAL {type(_exc).__name__}: {str(_exc)[:500]}",
        flush=True,
    )
