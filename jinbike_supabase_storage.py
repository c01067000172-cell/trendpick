import base64
import json
import mimetypes
import os
import uuid
from pathlib import Path
from urllib.parse import unquote

from supabase import create_client


PRODUCT_COLUMNS = (
    "id",
    "type",
    "category",
    "subcategory",
    "brand",
    "name",
    "price",
    "condition",
    "badge",
    "image",
    "images",
    "description",
    "demo",
    "year",
    "mileage",
    "cc",
    "region",
    "accident",
)


_CLIENT_CACHE = {}
_PREFLIGHT = {
    "signature": None,
    "db_ok": False,
    "storage_ok": False,
    "error": "",
}


def _decode_legacy_role(key):
    try:
        parts = key.split(".")
        if len(parts) < 2:
            return ""
        payload = parts[1] + ("=" * (-len(parts[1]) % 4))
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        return str(data.get("role") or "")
    except Exception:
        return ""


def _validate_server_key(key):
    if key.startswith("sb_secret_"):
        return "secret"

    if key.startswith("sb_publishable_"):
        raise RuntimeError(
            "Render의 SUPABASE_SECRET_KEY에 Publishable key가 들어 있습니다. "
            "서버 저장에는 Supabase Project Settings > API Keys의 Secret key(sb_secret_...)가 필요합니다."
        )

    if key.startswith("eyJ"):
        role = _decode_legacy_role(key)
        if role == "service_role":
            return "legacy_service_role"
        if role == "anon":
            raise RuntimeError(
                "Render의 SUPABASE_SECRET_KEY에 legacy anon key가 들어 있습니다. "
                "Secret key(sb_secret_...) 또는 legacy service_role key가 필요합니다."
            )
        raise RuntimeError(
            "Render의 Supabase JWT 키가 service_role 키인지 확인할 수 없습니다. "
            "Secret key(sb_secret_...)를 사용해 주세요."
        )

    raise RuntimeError(
        "Render의 SUPABASE_SECRET_KEY 형식을 확인할 수 없습니다. "
        "Supabase Secret key(sb_secret_...)를 넣어 주세요."
    )


def _clean_product(product):
    row = {key: product.get(key) for key in PRODUCT_COLUMNS}

    row["id"] = str(row.get("id") or "").strip()
    row["type"] = str(row.get("type") or "").strip()
    row["category"] = str(row.get("category") or "").strip()
    row["name"] = str(row.get("name") or "").strip()

    try:
        row["price"] = int(row.get("price") or 0)
    except (TypeError, ValueError):
        row["price"] = 0

    if not isinstance(row.get("images"), list):
        row["images"] = []

    row["demo"] = bool(row.get("demo", False))

    for key in (
        "subcategory",
        "brand",
        "condition",
        "badge",
        "image",
        "description",
        "year",
        "mileage",
        "cc",
        "region",
        "accident",
    ):
        if row.get(key) is not None:
            row[key] = str(row[key])

    if not row["id"]:
        raise ValueError("상품 ID가 비어 있습니다.")
    if not row["type"]:
        raise ValueError("상품 종류가 비어 있습니다.")
    if not row["category"]:
        raise ValueError("상품 카테고리가 비어 있습니다.")
    if not row["name"]:
        raise ValueError("상품명이 비어 있습니다.")

    return row


def _get_client(supabase_url, server_key):
    signature = (supabase_url, server_key)
    client = _CLIENT_CACHE.get(signature)
    if client is None:
        client = create_client(supabase_url, server_key)
        _CLIENT_CACHE.clear()
        _CLIENT_CACHE[signature] = client
    return client


def _run_preflight(client, storage, supabase_url, server_key, bucket, key_type):
    signature = (supabase_url, server_key, bucket)
    if _PREFLIGHT["signature"] == signature:
        return (
            _PREFLIGHT["db_ok"],
            _PREFLIGHT["storage_ok"],
            _PREFLIGHT["error"],
        )

    _PREFLIGHT.update(
        signature=signature,
        db_ok=False,
        storage_ok=False,
        error="",
    )

    try:
        client.table("products").select("id").limit(1).execute()
        _PREFLIGHT["db_ok"] = True
    except Exception as exc:
        _PREFLIGHT["error"] = f"DB 연결 실패: {type(exc).__name__}: {exc}"
        print(
            f"[JINBIKE] Supabase DB preflight FAIL key_type={key_type}: "
            f"{type(exc).__name__}: {str(exc)[:500]}",
            flush=True,
        )
        return False, False, _PREFLIGHT["error"]

    probe_path = f"__healthcheck__/storage-{uuid.uuid4().hex[:12]}.txt"
    try:
        storage.upload(
            path=probe_path,
            file=b"jinbike-storage-preflight",
            file_options={
                "content-type": "text/plain",
                "cache-control": "0",
                "upsert": "false",
            },
        )
        storage.remove([probe_path])
        _PREFLIGHT["storage_ok"] = True
        print(
            f"[JINBIKE] Supabase SDK preflight OK key_type={key_type} bucket={bucket}",
            flush=True,
        )
        return True, True, ""
    except Exception as exc:
        _PREFLIGHT["error"] = (
            f"Storage 권한 확인 실패: {type(exc).__name__}: {exc}"
        )
        print(
            f"[JINBIKE] Supabase Storage preflight FAIL key_type={key_type}: "
            f"{type(exc).__name__}: {str(exc)[:700]}",
            flush=True,
        )
        return True, False, _PREFLIGHT["error"]


def install(namespace):
    """Replace app.py product/image persistence with Supabase server storage."""

    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    server_key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip()
    bucket = bucket or "product-images"

    if not supabase_url or not server_key:
        namespace["SUPABASE_ENABLED"] = False
        namespace["SUPABASE_STATUS"] = "Supabase 환경변수 미설정"
        return False

    st = namespace.get("st")
    product_images = namespace["product_images"]
    local_load_products = namespace["load_products"]

    try:
        key_type = _validate_server_key(server_key)
        client = _get_client(supabase_url, server_key)
        storage = client.storage.from_(bucket)
    except Exception as exc:
        message = str(exc)
        namespace["SUPABASE_ENABLED"] = False
        namespace["SUPABASE_STATUS"] = message

        def blocked_save_products(_products):
            raise RuntimeError(message)

        def blocked_save_uploaded_images(_files, _product_id):
            raise RuntimeError(message)

        def blocked_delete_images(_product):
            raise RuntimeError(message)

        namespace["save_products"] = blocked_save_products
        namespace["save_uploaded_images"] = blocked_save_uploaded_images
        namespace["delete_local_images"] = blocked_delete_images

        if st is not None:
            st.error(message)
        return False

    db_ok, storage_ok, preflight_error = _run_preflight(
        client,
        storage,
        supabase_url,
        server_key,
        bucket,
        key_type,
    )

    public_prefix = (
        f"{supabase_url}/storage/v1/object/public/{bucket}/"
    )
    pending_delete_paths = set()
    state = {
        "load_ok": False,
        "db_ok": db_ok,
        "storage_ok": storage_ok,
    }

    def storage_path_from_url(value):
        value = str(value or "").strip()
        if not value.startswith(public_prefix):
            return None
        return unquote(value[len(public_prefix):].split("?", 1)[0])

    def queue_product_images(product):
        for value in product_images(product):
            path = storage_path_from_url(value)
            if path:
                pending_delete_paths.add(path)

    def remove_storage_paths(paths):
        unique_paths = list(dict.fromkeys(str(p) for p in paths if p))
        if unique_paths:
            storage.remove(unique_paths)

    def load_products():
        try:
            response = (
                client.table("products")
                .select("*")
                .order("created_at")
                .execute()
            )
            data = response.data or []
            if not isinstance(data, list):
                raise ValueError("Supabase products 응답 형식이 올바르지 않습니다.")

            products = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                product = {
                    key: item.get(key)
                    for key in PRODUCT_COLUMNS
                    if key in item
                }
                if not isinstance(product.get("images"), list):
                    product["images"] = []
                products.append(product)

            state["load_ok"] = True
            state["db_ok"] = True
            return products

        except Exception as exc:
            state["load_ok"] = False
            state["db_ok"] = False
            if st is not None:
                st.warning(
                    "Supabase 상품 DB 연결에 실패했습니다. 데이터 보호를 위해 "
                    f"관리자 저장/삭제를 차단합니다. ({type(exc).__name__})"
                )
            try:
                return local_load_products()
            except Exception:
                return []

    def save_products(products):
        if not state["load_ok"] or not state["db_ok"]:
            raise RuntimeError(
                "Supabase DB 연결이 확인되지 않아 상품 저장을 차단했습니다."
            )

        rows = [_clean_product(product) for product in products]
        wanted_ids = {row["id"] for row in rows}

        current_response = (
            client.table("products")
            .select("id,image,images")
            .execute()
        )
        current_rows = current_response.data or []
        if not isinstance(current_rows, list):
            raise ValueError("Supabase products 응답 형식이 올바르지 않습니다.")

        stale_rows = [
            row for row in current_rows
            if str(row.get("id") or "") not in wanted_ids
        ]

        try:
            if rows:
                (
                    client.table("products")
                    .upsert(rows, on_conflict="id")
                    .execute()
                )

            for stale in stale_rows:
                stale_id = str(stale.get("id") or "")
                if not stale_id:
                    continue
                (
                    client.table("products")
                    .delete()
                    .eq("id", stale_id)
                    .execute()
                )
                queue_product_images(stale)

            if pending_delete_paths:
                remove_storage_paths(pending_delete_paths)
                pending_delete_paths.clear()

        except Exception:
            pending_delete_paths.clear()
            raise

    def save_uploaded_images(uploaded_files, product_id):
        if not state["load_ok"] or not state["db_ok"]:
            raise RuntimeError(
                "Supabase DB 연결이 확인되지 않아 이미지 업로드를 차단했습니다."
            )
        if not state["storage_ok"]:
            detail = preflight_error or "Storage 쓰기 권한을 확인하지 못했습니다."
            raise RuntimeError(
                "Supabase Storage 서버 권한 확인에 실패했습니다. " + detail
            )

        saved = []
        uploaded_paths = []
        if not uploaded_files:
            return saved

        mime_ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }

        try:
            for index, uploaded in enumerate(uploaded_files[:8], start=1):
                mime = getattr(uploaded, "type", "") or "image/jpeg"
                ext = mime_ext.get(mime, "")

                if not ext:
                    original_ext = Path(
                        getattr(uploaded, "name", "")
                    ).suffix.lower()
                    if original_ext in (".jpg", ".jpeg", ".png", ".webp"):
                        ext = ".jpg" if original_ext == ".jpeg" else original_ext
                    else:
                        ext = mimetypes.guess_extension(mime) or ".jpg"

                filename = f"{index}_{uuid.uuid4().hex[:12]}{ext}"
                object_path = f"products/{product_id}/{filename}"

                storage.upload(
                    path=object_path,
                    file=bytes(uploaded.getvalue()),
                    file_options={
                        "content-type": mime,
                        "cache-control": "3600",
                        "upsert": "false",
                    },
                )
                uploaded_paths.append(object_path)
                saved.append(f"{public_prefix}{object_path}")

            return saved

        except Exception:
            if uploaded_paths:
                try:
                    remove_storage_paths(uploaded_paths)
                except Exception:
                    pass
            raise

    def delete_local_images(product):
        queue_product_images(product)

    namespace["load_products"] = load_products
    namespace["save_products"] = save_products
    namespace["save_uploaded_images"] = save_uploaded_images
    namespace["delete_local_images"] = delete_local_images
    namespace["SUPABASE_ENABLED"] = bool(db_ok and storage_ok)
    namespace["SUPABASE_STATUS"] = (
        "Supabase DB + Storage"
        if db_ok and storage_ok
        else (preflight_error or "Supabase 연결 확인 실패")
    )
    namespace["SUPABASE_BUCKET"] = bucket
    namespace["SUPABASE_KEY_TYPE"] = key_type

    if st is not None and preflight_error:
        st.error(
            "Supabase 서버 저장소 사전검사 실패: " + preflight_error
        )

    return bool(db_ok and storage_ok)
