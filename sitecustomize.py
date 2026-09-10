"""Render startup preflight for JIN BIKE Supabase Storage.

Python imports sitecustomize automatically at interpreter startup when this
repository is on sys.path. This lets us verify the server credential without
waiting for a Streamlit browser session. No secret value is ever logged.
"""

import base64
import json
import os
import uuid


def _key_kind(key: str) -> str:
    if key.startswith("sb_secret_"):
        return "sb_secret"
    if key.startswith("sb_publishable_"):
        return "sb_publishable"
    if key.startswith("eyJ"):
        try:
            payload = key.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            role = json.loads(base64.urlsafe_b64decode(payload).decode()).get("role")
            return f"legacy_jwt:{role or 'unknown'}"
        except Exception:
            return "legacy_jwt:unknown"
    return "unknown"


def _run_storage_preflight() -> None:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip() or "product-images"

    if not url or not key:
        return

    try:
        import requests
    except Exception as exc:
        print(f"[JINBIKE-PREFLIGHT] requests import failed: {type(exc).__name__}", flush=True)
        return

    kind = _key_kind(key)
    path = f"__healthcheck__/startup-{uuid.uuid4().hex[:12]}.txt"
    object_url = f"{url}/storage/v1/object/{bucket}/{path}"

    variants = []
    if key.startswith("eyJ"):
        variants.append(("legacy-bearer", {"apikey": key, "Authorization": f"Bearer {key}"}))
    else:
        variants.append(("apikey-only", {"apikey": key}))
        variants.append(("apikey-plus-bearer", {"apikey": key, "Authorization": f"Bearer {key}"}))

    print(f"[JINBIKE-PREFLIGHT] key_kind={kind} bucket={bucket}", flush=True)

    for label, auth_headers in variants:
        headers = dict(auth_headers)
        headers.update({"Content-Type": "text/plain", "Cache-Control": "no-store"})
        try:
            response = requests.post(
                object_url,
                headers=headers,
                data=b"jinbike-storage-preflight",
                timeout=20,
            )
        except Exception as exc:
            print(
                f"[JINBIKE-PREFLIGHT] {label} exception={type(exc).__name__}: {str(exc)[:200]}",
                flush=True,
            )
            continue

        safe_body = (response.text or "").replace("\n", " ")[:500]
        print(
            f"[JINBIKE-PREFLIGHT] {label} upload_http={response.status_code} body={safe_body}",
            flush=True,
        )

        if 200 <= response.status_code < 300:
            try:
                delete_response = requests.delete(
                    object_url,
                    headers=auth_headers,
                    timeout=20,
                )
                print(
                    f"[JINBIKE-PREFLIGHT] {label} delete_http={delete_response.status_code} "
                    f"body={(delete_response.text or '')[:300]}",
                    flush=True,
                )
            except Exception as exc:
                print(
                    f"[JINBIKE-PREFLIGHT] {label} delete_exception={type(exc).__name__}: {str(exc)[:200]}",
                    flush=True,
                )
            break


try:
    _run_storage_preflight()
except Exception as _exc:
    print(
        f"[JINBIKE-PREFLIGHT] fatal={type(_exc).__name__}: {str(_exc)[:200]}",
        flush=True,
    )
