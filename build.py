"""CBA Cards & Prints website + Pinterest RSS feeds.
- index.html: all products; p/<slug>.html: one page per product with a Buy on Etsy button
- feeds/<board>.xml: one RSS feed per Pinterest board, releasing `per_day` more pins daily from pins.json
Runs daily via .github/workflows/daily.yml."""
import json, re, html, os, datetime as dt
from email.utils import format_datetime
from urllib.parse import urlparse
cfg = json.load(open('config.json')); pins = json.load(open('pins.json'))
SITE = cfg.get('site_url', 'https://cbacardsadmin-cyber.github.io')
today = dt.date.today(); start = dt.date.fromisoformat(cfg['start_date']); days = (today - start).days
fd, per = cfg.get('first_day', cfg['per_day']), cfg['per_day']
released = [] if days < 0 else pins[: fd + per * days]
def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')).strip('-')
def pslug(link):
    parts = urlparse(link).path.strip('/').split('/')
    return '-'.join(parts[1:3]) if len(parts) >= 3 else slug(link)
E = html.escape
# ---- products (one per Etsy listing) ----
prods = {}
for p in pins:
    s = pslug(p['link'])
    d = prods.setdefault(s, {'slug': s, 'link': p['link'], 'images': [], 'title': p['title'], 'desc': p['description'], 'board': p['board']})
    if p['image'] not in d['images']: d['images'].append(p['image'])
    if len(p['title']) > len(d['title']): d['title'] = p['title']
CSS = """:root{--cream:#F7F0E7;--red:#B22834;--pink:#EEAAB4;--ink:#3C2828;--card:#FFFFFF}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--ink);font:16px/1.55 'Work Sans',system-ui,sans-serif}
.stripes{height:22px;background:repeating-linear-gradient(90deg,var(--red) 0 36px,var(--pink) 36px 72px)}
header{text-align:center;padding:28px 16px 8px}header a{text-decoration:none}
.logo{font-family:'Fraunces',serif;font-weight:800;color:var(--red);font-size:44px;line-height:1;margin:0}
.tag{letter-spacing:.18em;text-transform:uppercase;font-size:12px;font-weight:600;margin-top:8px}
main{max-width:1080px;margin:0 auto;padding:16px}
h2{font-family:'Fraunces',serif;font-weight:800;color:var(--red);font-size:26px;margin:28px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.card{background:var(--card);border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;box-shadow:0 2px 10px rgba(60,40,40,.08)}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#eee}.card div{padding:10px 12px;font-size:14px}
.btn{display:inline-block;background:var(--red);color:#fff;text-decoration:none;font-weight:700;padding:14px 26px;border-radius:999px;font-size:17px}
.prod{display:grid;grid-template-columns:1.2fr 1fr;gap:28px;align-items:start}@media(max-width:760px){.prod{grid-template-columns:1fr}}
.prod img{width:100%;border-radius:12px;display:block;margin-bottom:12px}
.prod h1{font-family:'Fraunces',serif;font-weight:800;font-size:30px;line-height:1.15;margin:0 0 12px}
a{color:var(--red)}.note{font-size:13px;opacity:.75;margin-top:10px}footer{text-align:center;font-size:13px;padding:30px 16px;opacity:.75}"""
def page(title, body, desc='', image='', canon=''):
    meta = (f'<meta name="description" content="{E(desc[:300])}"><meta property="og:title" content="{E(title)}">'
            f'<meta property="og:description" content="{E(desc[:300])}">' + (f'<meta property="og:image" content="{E(image)}">' if image else '')
            + (f'<link rel="canonical" href="{E(canon)}">' if canon else '') + cfg.get('head_extra', ''))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title>{meta}<link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,800&family=Work+Sans:wght@400;600;700&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style></head><body><div class="stripes"></div><header><a href="/"><p class="logo">CBA Cards &amp; Prints</p></a>'
            f'<div class="tag">Cheeky cards, minimal effort &middot; Printed in the UK</div></header><main>{body}</main>'
            f'<footer>Orders are made and sent through our Etsy shop &middot; <a href="{cfg["shop_url"]}">CBA Cards on Etsy</a></footer><div class="stripes"></div></body></html>')
os.makedirs('p', exist_ok=True)
for d in prods.values():
    buy = d['link'] + '?utm_source=cba-site'
    imgs = ''.join(f'<img src="{E(i)}" alt="{E(d["title"])}" loading="lazy">' for i in d['images'])
    body = (f'<div class="prod"><div>{imgs}</div><div><h1>{E(d["title"])}</h1><p>{E(d["desc"])}</p>'
            f'<p><a class="btn" href="{E(buy)}">Buy on Etsy</a></p><p class="note">Secure checkout, delivery and personalisation are all handled on Etsy.</p>'
            f'<p><a href="/">&larr; More from CBA</a></p></div></div>')
    open(f'p/{d["slug"]}.html', 'w', encoding='utf-8').write(page(d['title'] + ' | CBA Cards & Prints', body, d['desc'], d['images'][0], f'{SITE}/p/{d["slug"]}.html'))
sections = {}
for d in prods.values(): sections.setdefault(d['board'], []).append(d)
body = ''.join(f'<h2>{E(b)}</h2><div class="grid">' + ''.join(
    f'<a class="card" href="/p/{d["slug"]}.html"><img src="{E(d["images"][0])}" alt="{E(d["title"])}" loading="lazy"><div>{E(d["title"].split(",")[0])}</div></a>' for d in ds) + '</div>'
    for b, ds in sorted(sections.items()))
body = f'<p style="text-align:center"><a class="btn" href="{cfg["shop_url"]}">Visit our Etsy shop</a></p>' + body
open('index.html', 'w', encoding='utf-8').write(page('CBA Cards & Prints - funny Christmas cards and prints', body, 'Funny and personalised Christmas cards, posters and prints, designed and printed in the UK.'))
# ---- feeds ----
os.makedirs('feeds', exist_ok=True)
boards = {p['board']: [] for p in pins}
count = {}
for i, p in enumerate(released):
    day = start + dt.timedelta(days=0 if i < fd else 1 + (i - fd) // per)
    s = pslug(p['link']); count[s] = count.get(s, 0) + 1
    boards[p['board']].append(dict(p, idx=i, url=f'{SITE}/p/{s}.html' + ('' if count[s] == 1 else f'?v={count[s]}'),
                                   date=dt.datetime(day.year, day.month, day.day, 6, 0, i % 60, tzinfo=dt.timezone.utc)))
listing = []
for board, items in boards.items():
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">', '<channel>',
           f'<title>{E("CBA Cards & Prints - " + board)}</title>', f'<link>{SITE}/</link>', f'<description>{E(board)}</description>']
    for p in items:
        out += ['<item>', f'<title>{E(p["title"])}</title>', f'<link>{E(p["url"])}</link>', f'<guid isPermaLink="false">cba-pin-{p["idx"]}</guid>',
                f'<pubDate>{format_datetime(p["date"])}</pubDate>',
                f'<description><![CDATA[<p><img src="{p["image"]}" alt="{E(p["title"])}"/></p><p>{E(p["description"])}</p>]]></description>',
                f'<enclosure url="{E(p["image"])}" type="image/jpeg" length="0"/>', f'<media:content url="{E(p["image"])}" medium="image" type="image/jpeg"/>', '</item>']
    out += ['</channel>', '</rss>']
    open(f'feeds/{slug(board)}.xml', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    listing.append((board, slug(board), len(items)))
open('feeds/index.html', 'w', encoding='utf-8').write(page('Pinterest feeds', f'<h2>Pinterest feeds</h2><p>{len(released)} of {len(pins)} pins released ({today}).</p><ul>' +
    ''.join(f'<li>{E(b)}: <a href="/feeds/{s}.xml">{SITE}/feeds/{s}.xml</a> ({n})</li>' for b, s, n in sorted(listing)) + '</ul>'))
print(f'{len(prods)} product pages, {len(released)}/{len(pins)} pins released')
