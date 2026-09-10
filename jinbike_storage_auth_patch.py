import os
import uuid

import requests


_ORIGINAL_REQUEST = requests.request
_PATCHED = False
_PROBED = False


def _is_storage_url(url):
    return "/storage/v1/" in str(url or "")


def _patched_request(method, url, **kwargs):
    headers = dict(kwargs.pop("headers", {}) or {})

    if _is_storage_url(url):
        api_key = headers.get("apikey") or headers.get("apiKey")
        if api_key and "Authorization" not in headers:
            # Supabase Storage clients forward the project key as both the
            # API key and the Storage authorization credential. Keeping this
            # server-side allows a Secret/service-role key to bypass RLS
            # without opening public storage policies.
            headers["Authorization"] = f"Bearer {api_key}"

    return _ORIGINAL_REQUEST(method, url, headers=headers, **kwargs)


def install():
    global _PATCHED
    if not _PATCHED:
        requests.request = _patched_request
        _PATCHED = True
    return True


def probe_storage():
    """One-time server-side write/delete probe. Never logs the secret value."""
    global _PROBED
    if _PROBED:
        return True
    _PROBED = True

    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip() or "product-images"

    if not url or not key:
        print("[JINBIKE] Storage probe skipped: Supabase URL/key missing")
        return False

    if key.startswith("sb_secret_"):
        key_type = "sb_secret"
    elif key.startswith("sb_publishable_"):
        key_type = "sb_publishable"
    elif key.startswith("eyJ"):
        key_type = "legacy_jwt"
    else:
        key_type = "unknown"

    path = f"__healthcheck__/render-{uuid.uuid4().hex[:12]}.txt"
    object_url = f"{url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "text/plain",
        "Cache-Control": "no-store",
    }

    try:
        upload = _ORIGINAL_REQUEST(
            "POST",
            object_url,
            headers=headers,
            data=b"jinbike-storage-ok",
            timeout=20,
        )
        if not upload.ok:
            print(
                f"[JINBIKE] Storage probe UPLOAD FAIL key_type={key_type} "
                f"HTTP={upload.status_code} body={upload.text[:500]}"
            )
            return False

        delete = _ORIGINAL_REQUEST(
            "DELETE",
            object_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
            timeout=20,
        )
        if not delete.ok and delete.status_code != 404:
            print(
                f"[JINBIKE] Storage probe DELETE FAIL key_type={key_type} "
                f"HTTP={delete.status_code} body={delete.text[:500]}"
            )
            return False

        print(f"[JINBIKE] Supabase Storage auth probe OK key_type={key_type}")
        return True

    except Exception as exc:
        print(f"[JINBIKE] Storage probe exception key_type={key_type}: {type(exc).__name__}: {exc}")
        return False
