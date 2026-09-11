"""JIN BIKE Render boot-time Supabase verification, checkout patch, and SEO metadata."""

import base64
import json
import os
import re
import sys
import uuid
from html import escape
from pathlib import Path
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


def _install_twoj_seo_metadata():
    """Strengthen homepage brand signals for Naver/Google without changing storefront UI."""
    if not _is_streamlit_process():
        return
    try:
        import streamlit

        index = Path(streamlit.__file__).resolve().parent / "static" / "index.html"
        html = index.read_text(encoding="utf-8")
        if "</head>" not in html:
            return

        title = "투제이로드 (TWO J ROAD) | 포천 중고 바이크·바이크 의류·용품"
        description = (
            "포천 투제이로드(TWO J ROAD). 중고 바이크와 중고 오토바이, "
            "바이크 의류, 라이딩 자켓·장갑·헬멧 등 바이크 용품을 확인하세요."
        )
        canonical = "https://www.maspick.co.kr/"

        html = re.sub(r"<title\b[^>]*>.*?</title>", "", html, flags=re.I | re.S)
        for attr, name in [
            ("name", "description"),
            ("name", "robots"),
            ("property", "og:title"),
            ("property", "og:description"),
            ("property", "og:type"),
            ("property", "og:site_name"),
            ("property", "og:url"),
            ("property", "og:locale"),
        ]:
            pattern = r"<meta\b(?=[^>]*\b" + attr + r"=[\"']" + re.escape(name) + r"[\"'])[^>]*>"
            html = re.sub(pattern, "", html, flags=re.I)
        html = re.sub(r'<link\b(?=[^>]*\brel=[\"\']canonical[\"\'])[^>]*>', '', html, flags=re.I)
        html = re.sub(
            r'<script\b(?=[^>]*\bid=[\"\']twoj-jsonld[\"\'])[^>]*>.*?</script>',
            '',
            html,
            flags=re.I | re.S,
        )

        structured_data = {
            "@context": "https://schema.org",
            "@type": "Store",
            "name": "TWO J ROAD",
            "alternateName": ["투제이로드", "포천 투제이로드"],
            "url": canonical,
            "description": description,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "금강로3224번길 11-7",
                "addressLocality": "포천시 내촌면",
                "addressRegion": "경기도",
                "addressCountry": "KR",
            },
        }

        metadata = (
            "<title>" + escape(title) + "</title>\n"
            + '<meta name="description" content="' + escape(description, quote=True) + '" />\n'
            + '<meta name="robots" content="index,follow,max-image-preview:large" />\n'
            + '<link rel="canonical" href="' + canonical + '" />\n'
            + '<meta property="og:title" content="' + escape(title, quote=True) + '" />\n'
            + '<meta property="og:description" content="' + escape(description, quote=True) + '" />\n'
            + '<meta property="og:type" content="website" />\n'
            + '<meta property="og:site_name" content="TWO J ROAD (투제이로드)" />\n'
            + '<meta property="og:url" content="' + canonical + '" />\n'
            + '<meta property="og:locale" content="ko_KR" />\n'
            + '<script id="twoj-jsonld" type="application/ld+json">'
            + json.dumps(structured_data, ensure_ascii=False, separators=(",", ":"))
            + '</script>\n'
        )
        html = html.replace("</head>", metadata + "</head>", 1)
        index.write_text(html, encoding="utf-8")
        print("[TWOJ-SEO] Korean brand metadata installed", flush=True)
    except Exception as exc:
        print(
            f"[TWOJ-SEO] patch failed {type(exc).__name__}: {str(exc)[:300]}",
            flush=True,
        )


try:
    _install_checkout_xsrf_patch()
except Exception as _exc:
    print(
        f"[PAYMENT-XSRF] FATAL {type(_exc).__name__}: {str(_exc)[:500]}",
        flush=True,
    )

try:
    _install_twoj_seo_metadata()
except Exception as _exc:
    print(
        f"[TWOJ-SEO] FATAL {type(_exc).__name__}: {str(_exc)[:500]}",
        flush=True,
    )

try:
    _verify()
except Exception as _exc:
    print(
        f"[JINBIKE-BOOT] FATAL {type(_exc).__name__}: {str(_exc)[:500]}",
        flush=True,
    )
