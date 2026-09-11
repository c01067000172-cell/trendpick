"""Public HTML routes alongside the existing Streamlit storefront."""
import asyncio
import json
import os
import time
from html import escape as esc
from urllib.parse import quote, urlencode
from xml.sax.saxutils import escape as xml_escape

SITE = 'https://www.maspick.co.kr'
CATEGORIES = {'bike': '중고 바이크', 'wear': '바이크 의류', 'gear': '바이크 용품'}
_cache = {'time': 0, 'rows': None}


def products():
    if _cache['rows'] is not None and time.monotonic() - _cache['time'] < 30:
        return _cache['rows']
    from supabase import create_client
    from jinbike_supabase_storage import _validate_server_key
    key = os.getenv('SUPABASE_SECRET_KEY', '').strip() or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    _validate_server_key(key)
    client = create_client(os.environ['SUPABASE_URL'].strip(), key)
    rows = []
    offset = 0
    while True:
        batch = client.table('products').select('id,type,category,subcategory,brand,name,price,condition,image,images,description,demo').order('id').range(offset, offset + 999).execute().data
        if not isinstance(batch, list):
            raise ValueError('Invalid products response')
        rows.extend(row for row in batch if not row.get('demo'))
        if len(batch) < 1000:
            break
        offset += 1000
    _cache.update(time=time.monotonic(), rows=rows)
    return rows


def description(product):
    value = str(product.get('description') or '')
    if value.startswith('DOOJAY_DETAIL_V1:'):
        try:
            data = json.loads(value.split(':', 1)[1])
            return str(data.get('text', '')), data.get('files', [])
        except (ValueError, AttributeError):
            return '', []
    return value, []


def image(url, alt):
    if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
        return ''
    return f'<img src="{esc(url, quote=True)}" alt="{esc(alt, quote=True)}" loading="lazy">'


def page(title, summary, path, body):
    url = esc(SITE + path, quote=True)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(summary, quote=True)}">
<link rel="canonical" href="{url}"><meta property="og:title" content="{esc(title, quote=True)}">
<meta property="og:description" content="{esc(summary, quote=True)}"><meta property="og:url" content="{url}">
<meta property="og:type" content="website"><style>
body{{background:#080808;color:#eee;font:16px/1.7 sans-serif;max-width:1100px;margin:auto;padding:24px}}
a{{color:#ff8a24}}nav{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:24px}}
img{{display:block;max-width:100%;max-height:700px;object-fit:contain;margin:12px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:20px}}
.card{{border:1px solid #333;padding:16px}}.card img{{width:100%;height:220px}}
.text{{white-space:pre-wrap}}h1{{font-size:28px}}</style></head><body>
<nav><a href="/">TWO J ROAD</a><a href="/catalog/bike">중고 바이크</a><a href="/catalog/wear">바이크 의류</a><a href="/catalog/gear">바이크 용품</a></nav>
{body}<footer><p>포천 TWO J ROAD · 경기 포천시 내촌면 금강로3224번길 11-7</p></footer></body></html>'''


def product_page(p):
    name = str(p.get('name') or '상품')
    text, files = description(p)
    summary = ' '.join((str(p.get('brand') or ''), name, str(p.get('condition') or ''), text)).strip()
    summary = ' '.join(summary.split())[:150] or name
    pics = p.get('images') or [p.get('image')]
    body = f'<h1>{esc(name)}</h1><p>{esc(str(p.get("brand") or ""))}</p>'
    body += f'<p>{int(p.get("price") or 0):,}원 · {esc(str(p.get("condition") or ""))}</p>'
    body += ''.join(image(url, name) for url in pics)
    body += f'<div class="text">{esc(text)}</div>'
    for item in files:
        url = item.get('url', '')
        if item.get('kind') == 'image':
            body += image(url, item.get('name', name))
        elif isinstance(url, str) and url.startswith(('http://', 'https://')):
            body += f'<p><a href="{esc(url, quote=True)}">{esc(item.get("name", "상세 자료"))}</a></p>'
    detail = '/?' + urlencode({'page': 'detail', 'id': p['id']})
    body += f'<p><a href="{esc(detail, quote=True)}">상품 상세·구매 문의</a></p>'
    return page(name + ' | TWO J ROAD', summary, '/products/' + quote(str(p['id']), safe=''), body)


def catalog_page(kind, rows):
    label = CATEGORIES[kind]
    filtered = [p for p in rows if p.get('type') == kind]
    body = f'<h1>{label}</h1><div class="grid">'
    for p in filtered:
        name = str(p.get('name') or '상품')
        url = '/products/' + quote(str(p['id']), safe='')
        body += f'<article class="card"><a href="{url}">{image(p.get("image"), name)}<h2>{esc(name)}</h2></a><p>{int(p.get("price") or 0):,}원</p></article>'
    body += '</div>' if filtered else '</div><p>등록된 상품이 없습니다.</p>'
    return page(label + ' | TWO J ROAD', 'TWO J ROAD의 ' + label + ' 상품과 가격을 확인하세요.', '/catalog/' + kind, body)


def sitemap(rows):
    urls = [SITE + '/'] + [SITE + '/catalog/' + kind for kind in CATEGORIES]
    urls += [SITE + '/products/' + quote(str(p['id']), safe='') for p in rows]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + xml_escape(url) + '</loc></url>' for url in urls) + '</urlset>'


def main():
    import tornado.web
    from streamlit.web.server.server import Server
    from streamlit.web import cli

    class Public(tornado.web.RequestHandler):
        async def get(self, kind=None, ident=None):
            path = self.request.path
            self.set_header('Cache-Control', 'no-cache')
            if path == '/robots.txt':
                self.set_header('Content-Type', 'text/plain; charset=utf-8')
                self.finish('User-agent: *\nAllow: /\nSitemap: ' + SITE + '/sitemap.xml\n')
                return
            try:
                rows = await asyncio.to_thread(products)
            except Exception:
                self.set_status(503)
                self.set_header('Retry-After', '60')
                self.finish('상품 정보를 일시적으로 불러올 수 없습니다.')
                return
            if path.endswith('sitemap.xml'):
                self.set_header('Content-Type', 'application/xml; charset=utf-8')
                self.finish(sitemap(rows))
            elif path.startswith('/catalog/'):
                if kind not in CATEGORIES:
                    raise tornado.web.HTTPError(404)
                self.set_header('Content-Type', 'text/html; charset=utf-8')
                self.finish(catalog_page(kind, rows))
            else:
                product = next((p for p in rows if str(p['id']) == str(kind)), None)
                if product is None:
                    raise tornado.web.HTTPError(404)
                self.set_header('Content-Type', 'text/html; charset=utf-8')
                self.finish(product_page(product))

    original = Server._create_app
    def create_app(server):
        application = original(server)
        application.add_handlers(r'.*', [
            (r'/robots\.txt', Public),
            (r'/(?:app/static/)?sitemap\.xml', Public),
            (r'/catalog/([^/]+)', Public),
            (r'/products/([^/]+)', Public),
        ])
        return application
    Server._create_app = create_app
    cli.main()


if __name__ == '__main__':
    main()
