import mimetypes
import os
import uuid
from pathlib import Path
from urllib.parse import unquote

import requests


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


def _server_headers(server_key):
    headers = {"apikey": server_key}

    # Legacy service_role keys are JWTs and may be used as bearer tokens.
    # Modern sb_secret_* keys must be sent as apikey only.
    if server_key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {server_key}"

    return headers


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


def install(namespace):
    """Replace app.py storage functions when Supabase is configured."""

    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    server_key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip()
    bucket = bucket or "product-images"

    if not supabase_url or not server_key:
        namespace["SUPABASE_ENABLED"] = False
        return False

    st = namespace.get("st")
    product_images = namespace["product_images"]
    local_load_products = namespace["load_products"]

    api_headers = _server_headers(server_key)
    rest_base = f"{supabase_url}/rest/v1"
    storage_base = f"{supabase_url}/storage/v1/object"
    public_prefix = f"{storage_base}/public/{bucket}/"

    pending_delete_paths = set()
    state = {"load_ok": False}

    def request(method, url, **kwargs):
        headers = dict(api_headers)
        headers.update(kwargs.pop("headers", {}) or {})
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response

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
        for path in list(paths):
            try:
                request("DELETE", f"{storage_base}/{bucket}/{path}")
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code != 404:
                    raise

    def load_products():
        try:
            response = request(
                "GET",
                f"{rest_base}/products",
                params={"select": "*", "order": "created_at.asc"},
            )
            data = response.json()
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
            return products

        except Exception:
            state["load_ok"] = False
            if st is not None:
                st.warning(
                    "Supabase 상품 저장소에 연결하지 못했습니다. "
                    "기존 데이터를 임시 표시하며, 데이터 보호를 위해 "
                    "관리자 저장/삭제는 연결 복구 전 차단됩니다."
                )
            try:
                return local_load_products()
            except Exception:
                return []

    def save_products(products):
        if not state["load_ok"]:
            raise RuntimeError(
                "Supabase 연결이 확인되지 않아 상품 저장을 차단했습니다. "
                "페이지를 새로고침한 뒤 다시 시도해 주세요."
            )

        rows = [_clean_product(product) for product in products]
        wanted_ids = {row["id"] for row in rows}

        try:
            current_response = request(
                "GET",
                f"{rest_base}/products",
                params={"select": "id,image,images"},
            )
            current_rows = current_response.json()
            if not isinstance(current_rows, list):
                raise ValueError("Supabase products 응답 형식이 올바르지 않습니다.")

            stale_rows = [
                row for row in current_rows
                if str(row.get("id") or "") not in wanted_ids
            ]

            if rows:
                request(
                    "POST",
                    f"{rest_base}/products",
                    params={"on_conflict": "id"},
                    headers={
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates,return=minimal",
                    },
                    json=rows,
                )

            for stale in stale_rows:
                stale_id = str(stale.get("id") or "")
                if not stale_id:
                    continue
                request(
                    "DELETE",
                    f"{rest_base}/products",
                    params={"id": f"eq.{stale_id}"},
                    headers={"Prefer": "return=minimal"},
                )
                queue_product_images(stale)

            if pending_delete_paths:
                remove_storage_paths(pending_delete_paths)
                pending_delete_paths.clear()

        except Exception:
            pending_delete_paths.clear()
            raise

    def save_uploaded_images(uploaded_files, product_id):
        if not state["load_ok"]:
            raise RuntimeError(
                "Supabase 연결이 확인되지 않아 이미지 업로드를 차단했습니다."
            )

        saved = []
        if not uploaded_files:
            return saved

        mime_ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }

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

            request(
                "POST",
                f"{storage_base}/{bucket}/{object_path}",
                headers={"Content-Type": mime, "x-upsert": "false"},
                data=uploaded.getvalue(),
            )

            saved.append(f"{public_prefix}{object_path}")

        return saved

    def delete_local_images(product):
        queue_product_images(product)

    namespace["load_products"] = load_products
    namespace["save_products"] = save_products
    namespace["save_uploaded_images"] = save_uploaded_images
    namespace["delete_local_images"] = delete_local_images
    namespace["SUPABASE_ENABLED"] = True
    namespace["SUPABASE_BUCKET"] = bucket

    return True
