"""Policy-safe search discovery notifications for public TWO J ROAD pages.

IndexNow is only a discovery hint. It does not create fake traffic, rankings,
or clicks, and a failure here must never prevent an administrator from saving
a product.
"""

from __future__ import annotations

import os
import json
import threading
import time
from urllib.parse import quote
from urllib.request import Request, urlopen


SITE = "https://www.maspick.co.kr"
INDEXNOW_KEY = os.getenv(
    "INDEXNOW_KEY",
    "e954432e18b9dc1b9ba03e4835a0915ff000aaf4dc3f5f720fe73ccd88263941",
).strip()
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

_lock = threading.Lock()
_last_signature = ""
_last_sent_at = 0.0


def public_urls(products) -> list[str]:
    """Return canonical public URLs derived only from real product records."""
    urls = {
        SITE + "/",
        SITE + "/sitemap.xml",
        SITE + "/rss.xml",
        SITE + "/catalog/bike",
        SITE + "/catalog/wear",
        SITE + "/catalog/gear",
    }
    for product in products or []:
        if not isinstance(product, dict) or product.get("demo"):
            continue
        product_id = str(product.get("id") or "").strip()
        if product_id:
            urls.add(SITE + "/products/" + quote(product_id, safe=""))
    return sorted(urls)


def _submit(urls: list[str]) -> None:
    global _last_signature, _last_sent_at
    if os.getenv("INDEXNOW_ENABLED", "1").strip().lower() in {"0", "false", "no"}:
        return
    if not INDEXNOW_KEY or not urls:
        return

    signature = "\n".join(urls)
    now = time.monotonic()
    with _lock:
        if signature == _last_signature and now - _last_sent_at < 300:
            return
        _last_signature, _last_sent_at = signature, now

    try:
        payload = json.dumps({
                "host": "www.maspick.co.kr",
                "key": INDEXNOW_KEY,
                "keyLocation": SITE + "/" + INDEXNOW_KEY + ".txt",
                "urlList": urls[:10_000],
            }, separators=(",", ":")).encode("utf-8")
        request = Request(
            INDEXNOW_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=8) as response:
            status = response.status
        print(
            f"[SEO] IndexNow discovery hint status={status} urls={len(urls)}",
            flush=True,
        )
    except Exception as exc:
        print(f"[SEO] IndexNow hint skipped: {type(exc).__name__}: {exc}", flush=True)


def notify_product_change(products) -> None:
    """Submit in a daemon thread so product saves remain fast and reliable."""
    urls = public_urls(products)
    threading.Thread(target=_submit, args=(urls,), daemon=True, name="indexnow").start()
