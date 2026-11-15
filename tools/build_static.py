#!/usr/bin/env python3
"""Genera las páginas estáticas de trechodemenos.es a partir de index.html.

Uso:  python3 tools/build_static.py            (desde la raíz del repositorio)

Lee DATA, PROGRAMAS, PROG_INFO y VOTOS de index.html y escribe:
  promesa/<ID>/index.html    una página por compromiso de campaña
  medida/<ID>/index.html     una página por medida de programa
  partido/<p>/index.html     una página por partido
  tema/<slug>/index.html     una página por tema
  promesas/index.html        índice de todo
  sitemap.xml, robots.txt
Las páginas son legibles sin JavaScript (para buscadores y vistas previas)
y enlazan a la ficha de la web interactiva.
"""
import html, json, os, re, shutil, unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://trechodemenos.es"
SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def grab(name):
    m = re.search(r"const " + name + r"\s*=\s*(.*?);\n", SRC, re.S)
    return json.loads(m.group(1))

DATA = [r for r in grab("DATA") if r.get("leg") == "XVI"]
PI = grab("PROG_INFO")
m = re.search(r"const PROGRAMAS=(\{.*?\});\n", SRC, re.S)
PROGRAMAS = json.loads(re.sub(r"([{,])([A-Z]+):\[", r'\1"\2":[', m.group(1)))
VOTOS = grab("VOTOS")
UPD = re.search(r'id="upd">Actualizado el ([^<]+)<', SRC).group(1)

PARTIES = ["SUMAR", "PP", "PSOE", "VOX"]
P = {
    "SUMAR": dict(n="Frente Amplio", corto="Frente Amplio", ini="FA", slug="frente-amplio", hash="sumar", cand="Candidata: Ada Colau", de="del Frente Amplio"),
    "PP": dict(n="Partido Popular", corto="PP", ini="PP", slug="pp", hash="pp", cand="Candidato: Alberto Núñez Feijóo", de="del PP"),
    "PSOE": dict(n="Partido Socialista", corto="PSOE", ini="PSOE", slug="psoe", hash="psoe", cand="Candidato: Pedro Sánchez", de="del PSOE"),
    "VOX": dict(n="VOX", corto="VOX", ini="VOX", slug="vox", hash="vox", cand="Candidato: Santiago Abascal", de="de VOX"),
}
TEMAS = ["Vivienda", "Empleo y pensiones", "Impuestos", "Sanidad", "Educación", "Familia", "Inmigración", "Seguridad", "Energía", "Campo", "Infraestructuras", "Instituciones y justicia", "Otros"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

e = lambda s: html.escape(str(s or ""), quote=True)

def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def fecha(d):
    try:
        y, mth, dd = d.split("-"); return f"{int(dd)} de {MESES[int(mth)-1]} de {y}"
    except Exception:
        return d or ""

def nota_parts(n):
    n = n or ""
    out = {}
    c = re.search(r"Cita: «(.+?)»\.", n)
    if c: out["cita"] = c.group(1)
    m1 = re.search(r"¿Concreto y medible\? ([^.]+)\.", n)
    if m1: out["medible"] = m1.group(1)
    m2 = re.search(r"Respecto a 2023: ([^.]+)\.", n)
    if m2: out["r2023"] = m2.group(1)
    resto = re.sub(r"Cita: «.+?»\.\s*|¿Concreto y medible\? [^.]+\.\s*|Respecto a 2023: [^.]+\.\s*", "", n).strip()
    if resto: out["resto"] = resto
    return out

# Medidas de programa con su ID (igual que en la web)
PROWS = []
for p, L in PROGRAMAS.items():
    seen = {}
    for mm in L:
        tot = sum(1 for x in L if x["n"] == mm["n"])
        k = seen[mm["n"]] = seen.get(mm["n"], 0) + 1
        rid = f"PRG-{p}-{mm['n']:03d}" + ("abcdefgh"[k-1] if tot > 1 else "")
        PROWS.append(dict(mm, p=p, id=rid))

def prog_url(mm):
    I = PI.get(mm["p"])
    if not I: return ""
    return I["url"] + ("#page=" + str(mm["pag"]) if I.get("pdf") else "")

CSS = """:root{--paper:#f3f4f1;--sheet:#fff;--ink:#14181f;--muted:#4f5763;--rule:#d9dcd6;--hl:#FFD60A}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 'Schibsted Grotesk',system-ui,-apple-system,'Segoe UI',Arial,sans-serif}
a{color:var(--ink)}.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{border-bottom:2px solid var(--ink);background:var(--paper)}header .wrap{display:flex;align-items:center;gap:12px;padding-top:14px;padding-bottom:14px}
.brand{font-weight:900;font-size:26px;letter-spacing:-.03em;text-decoration:none}.brand span{background:var(--hl);padding:0 4px}
.logo{width:40px;height:34px}nav.crumbs{font-size:14px;color:var(--muted);margin:22px 0 6px}nav.crumbs a{color:var(--muted)}
h1{font-size:30px;line-height:1.2;letter-spacing:-.02em;margin:6px 0 14px}h2{font-size:21px;margin:30px 0 10px}
.meta{display:flex;flex-wrap:wrap;gap:4px 14px;color:var(--muted);font-size:15px;margin-bottom:12px}
.tag{display:inline-block;font:600 12px/1.6 'JetBrains Mono',ui-monospace,monospace;border:1.5px solid var(--rule);border-radius:4px;padding:1px 7px;margin:0 6px 6px 0;background:var(--sheet)}
.card{background:var(--sheet);border:1.5px solid var(--rule);border-radius:10px;padding:16px 18px;margin:12px 0}
.cita{font-family:Newsreader,Georgia,serif;font-size:20px;font-style:italic;border-left:4px solid var(--hl);padding-left:12px;margin:14px 0}
.btn{display:inline-block;background:var(--ink);color:var(--paper);text-decoration:none;font-weight:700;border-radius:999px;padding:10px 18px;margin:8px 8px 0 0}
.btn.alt{background:var(--sheet);color:var(--ink);border:1.5px solid var(--ink)}
ul.list{list-style:none;padding:0;margin:0}ul.list li{border-bottom:1px solid var(--rule);padding:10px 0}ul.list li small{display:block;color:var(--muted);font-size:13.5px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
footer{margin:40px 0 0;border-top:2px solid var(--ink);padding:18px 0 40px;font-size:14px;color:var(--muted)}footer a{color:var(--muted)}
.muted{color:var(--muted)}"""

LOGO = '<svg class="logo" viewBox="200 250 680 580" aria-hidden="true"><rect x="200" y="250" width="170" height="580" fill="#14181f"/><rect x="710" y="250" width="170" height="580" fill="#14181f"/><rect x="370" y="490" width="230" height="100" fill="#FFD60A"/><rect x="622" y="522" width="22" height="36" fill="#14181f"/><rect x="662" y="522" width="22" height="36" fill="#14181f"/></svg>'
FAVICON = re.search(r'<link rel="icon" href="([^"]+)"', SRC).group(1)

def page(path, title, desc, body, crumbs, jsonld=None):
    url = BASE + "/" + path
    full_title = title if "TrechoDeMenos" in title else f"{title} · TrechoDeMenos"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    cr = " › ".join(f'<a href="{h}">{e(t)}</a>' if h else e(t) for t, h in crumbs)
    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="TrechoDeMenos">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="article">
<meta property="og:image" content="{BASE}/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TrechoDeMenos">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;700;900&family=Newsreader:ital@1&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
<style>{CSS}</style>{ld}
</head>
<body>
<header><div class="wrap"><a href="/" aria-label="TrechoDeMenos, inicio">{LOGO}</a><a class="brand" href="/">Trecho<span>DeMenos</span></a></div></header>
<main class="wrap">
<nav class="crumbs" aria-label="Estás en">{cr}</nav>
{body}
</main>
<footer><div class="wrap">TrechoDeMenos es un proyecto independiente que recoge las promesas electorales del 29-N y comprobará si se cumplen. Mismo método para todos los partidos. Actualizado el {e(UPD)}.<br>
<a href="/">Web interactiva</a> · <a href="/promesas/">Índice de promesas</a> · <a href="/balance-2023/">Balance 2023</a> · <a href="/#quienes">Quiénes somos</a> · <a href="/#metodo">Método</a> · <a href="/#erratas">Fe de erratas</a> · <a href="mailto:info@trechodemenos.es">info@trechodemenos.es</a> · <a href="https://instagram.com/trechodemenos" target="_blank" rel="noopener">Instagram</a> · <a href="https://x.com/TrechoDeMenos" target="_blank" rel="noopener">X</a></div></footer>
</body>
</html>
"""
    out = os.path.join(ROOT, path, "index.html") if not path.endswith(".html") else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)
    return url

URLS = []

def li_prom(r):
    return f'<li><a href="/promesa/{e(r["id"])}/">{e(r["txt"])}</a><small>{e(fecha(r["fecha"]))} · {e(r.get("acto"))} · {e(r.get("lugar"))}{" · lo dijo " + e(r["quien"]) if r.get("quien") else ""}</small></li>'

def li_med(mm):
    return f'<li><a href="/medida/{e(mm["id"])}/">{e(mm["txt"])}</a><small>Programa · medida {mm["n"]}, pág. {mm["pag"]}{" · " + e(mm["cifra"]) if mm.get("cifra") else ""}</small></li>'

# Limpieza de lo generado antes (por si se borra o renombra algo)
for d in ("promesa", "medida", "partido", "tema", "promesas", "balance-2023"):
    shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)

# 1) Compromisos de campaña
for r in DATA:
    pp = P[r["p"]]; o = nota_parts(r.get("nota"))
    tags = []
    if o.get("medible"): tags.append("¿Concreto y medible? " + o["medible"])
    if o.get("r2023"): tags.append("Respecto a 2023: " + o["r2023"])
    rel = [x for x in DATA if x["p"] == r["p"] and x["t"] == r["t"] and x["id"] != r["id"]]
    relm = [x for x in PROWS if x["p"] == r["p"] and x["t"] == r["t"]]
    body = f"""<p class="meta"><span><b>{e(pp['n'])}</b>{" · lo dijo " + e(r['quien']) if r.get('quien') else ""}</span><span>{e(fecha(r['fecha']))}</span><span>{e(r.get('acto'))} · {e(r.get('lugar'))}</span><span>{e(r['t'])}</span></p>
<h1>{e(r['txt'])}</h1>
<div class="card"><p style="margin:0 0 8px"><b>Estado:</b> {e(r['st'])}{" · verificado el " + e(fecha(r['fv'])) if r.get('fv') else ""}</p>
{''.join(f'<span class="tag">{e(t)}</span>' for t in tags)}
{f'<p class="cita">«{e(o["cita"])}»</p>' if o.get('cita') else ''}
{f'<p>{e(o["resto"])}</p>' if o.get('resto') else ''}
{f'<p><b>{e(r["fin"])}.</b> {e(r.get("freno"))}</p>' if r.get('fin') else ''}
<p style="margin:12px 0 0">{f'<a class="btn alt" href="{e(r["src"])}" target="_blank" rel="noopener">Fuente</a>' if r.get('src') else ''}{f'<a class="btn alt" href="{e(r["prueba"])}" target="_blank" rel="noopener">Prueba</a>' if r.get('prueba') else ''}<a class="btn" href="/#{e(r['id'])}">Ver en la web interactiva</a></p>
<p class="muted" style="font-size:13px;margin:10px 0 0">Referencia: {e(r['id'])}</p></div>
{f'<h2>Más de {e(pp["n"])} sobre {e(r["t"].lower())}</h2><ul class="list">' + ''.join(li_prom(x) for x in sorted(rel, key=lambda x: x["fecha"], reverse=True)) + ''.join(li_med(x) for x in relm) + '</ul>' if rel or relm else ''}
<p><a href="/tema/{slug(r['t'])}/">Qué prometen los cuatro partidos sobre {e(r['t'].lower())} →</a></p>"""
    desc = f"{pp['n']}: {r['txt']} Dicho el {fecha(r['fecha'])} ({r.get('acto')}, {r.get('lugar')}). Estado: {r['st']}. Con fuente."
    jl = {"@context": "https://schema.org", "@type": "Claim", "text": r["txt"], "datePublished": r["fecha"],
          "author": {"@type": "Organization", "name": pp["n"]}, "url": f"{BASE}/promesa/{r['id']}/"}
    URLS.append(page(f"promesa/{r['id']}/", f"{pp['corto']}: {r['txt'].rstrip('.')}", desc[:300], body,
                     [("Inicio", "/"), (pp["n"], f"/partido/{pp['slug']}/"), (r["id"], None)], jl))

# 2) Medidas de programa
for mm in PROWS:
    pp = P[mm["p"]]; I = PI[mm["p"]]
    rel = mm.get("rel") or ""
    rel_html = re.sub(r"C29-[A-Z]+-\d+", lambda x: f'<a href="/promesa/{x.group(0)}/">{x.group(0)}</a>', e(rel))
    body = f"""<p class="meta"><span><b>{e(pp['n'])}</b></span><span>Programa electoral «{e(I['titulo'])}»</span><span>Medida {mm['n']} · pág. {mm['pag']}</span><span>{e(mm['t'])}</span></p>
<h1>{e(mm['txt'])}</h1>
<div class="card">{f'<span class="tag">{e(mm["cifra"])}</span>' if mm.get('cifra') else ''}
{f'<p>Relación con lo dicho en campaña: {rel_html}</p>' if rel else ''}
<p class="muted" style="font-size:15px">Resumen fiel de la medida tal como aparece en el programa oficial, presentado el {e(I['presentado'])}. Solo recogemos las medidas concretas y medibles.</p>
<p style="margin:12px 0 0"><a class="btn alt" href="{e(prog_url(mm))}" target="_blank" rel="noopener">Ver en el programa oficial</a><a class="btn" href="/#{e(mm['id'])}">Ver en la web interactiva</a></p>
<p class="muted" style="font-size:13px;margin:10px 0 0">Referencia: {e(mm['id'])}</p></div>
<p><a href="/partido/{pp['slug']}/">Todo lo de {e(pp['n'])} →</a> · <a href="/tema/{slug(mm['t'])}/">{e(mm['t'])}: los cuatro partidos →</a></p>"""
    desc = f"Programa electoral {pp['de']} para el 29-N, medida {mm['n']}: {mm['txt']}"
    URLS.append(page(f"medida/{mm['id']}/", f"{pp['corto']}, medida {mm['n']}: {mm['txt'].rstrip('.')}", desc[:300], body,
                     [("Inicio", "/"), (pp["n"], f"/partido/{pp['slug']}/"), (f"Medida {mm['n']}", None)]))

# 3) Partidos
for p in PARTIES:
    pp = P[p]; rs = sorted([r for r in DATA if r["p"] == p], key=lambda x: x["fecha"], reverse=True)
    ms = [x for x in PROWS if x["p"] == p]; I = PI.get(p)
    vot = []
    for v in sorted(VOTOS, key=lambda x: x["d"], reverse=True):
        gname = "Sumar" if p == "SUMAR" else ("VOX" if p == "VOX" else p)
        s = "sí" if gname in v["psi"] else "no" if gname in v["pno"] else "abstención" if gname in (v.get("pab") or []) else None
        if s: vot.append(f'<li>{e(v["titulo"])}<small>{e(v["fecha"])} · {e(v["res"])} · su grupo votó {s}</small></li>')
    body = f"""<h1>{e(pp['n'])}: sus promesas para el 29-N</h1>
<p class="meta"><span>{e(pp['cand'])}</span><span>{len(rs)} compromisos de campaña</span><span>{str(len({x['n'] for x in ms})) + ' medidas concretas de su programa' if I else 'Programa: pendiente de revisar'}</span></p>
<p><a class="btn" href="/#{pp['hash']}">Ver con filtros en la web interactiva</a></p>
<h2>Dicho en campaña</h2><ul class="list">{''.join(li_prom(r) for r in rs) or '<li>Aún no hay compromisos apuntados.</li>'}</ul>
<h2>En su programa electoral</h2>{('<p class="muted">«' + e(I['titulo']) + '», presentado el ' + e(I['presentado']) + '. <a href="' + e(I['url']) + '" target="_blank" rel="noopener">Programa oficial</a>.</p><ul class="list">' + ''.join(li_med(x) for x in ms) + '</ul>') if I else '<p>Pendiente de revisar el programa electoral.</p>'}
{('<h2>Cómo ha votado su grupo en el Congreso</h2><ul class="list">' + ''.join(vot) + '</ul><p><a href="/#votaciones">Todas las votaciones →</a></p>') if vot else ''}"""
    desc = f"Las promesas {pp['de']} para las elecciones generales del 29 de noviembre de 2026: {len(rs)} compromisos de campaña" + (f" y {len({x['n'] for x in ms})} medidas de su programa" if I else "") + ", con fecha, lugar y fuente."
    URLS.append(page(f"partido/{pp['slug']}/", f"Promesas {pp['de']} para el 29-N", desc, body, [("Inicio", "/"), (pp["n"], None)]))

# 4) Temas
usados = [t for t in TEMAS if any(r["t"] == t for r in DATA) or any(x["t"] == t for x in PROWS)]
for t in usados:
    cols = []
    for p in PARTIES:
        pp = P[p]; rs = sorted([r for r in DATA if r["p"] == p and r["t"] == t], key=lambda x: x["fecha"], reverse=True)
        ms = [x for x in PROWS if x["p"] == p and x["t"] == t]
        cols.append(f'<div><h2><a href="/partido/{pp["slug"]}/">{e(pp["n"])}</a></h2><ul class="list">{"".join(li_prom(r) for r in rs)}{"".join(li_med(x) for x in ms)}{"" if rs or ms else "<li class=muted>Nada sobre este tema por ahora" + ("" if PI.get(p) else " (programa pendiente)") + ".</li>"}</ul></div>')
    body = f"""<h1>{e(t)}: qué prometen los partidos para el 29-N</h1>
<p class="muted">Frente Amplio, PP, PSOE y VOX, en orden alfabético. Compromisos de campaña y medidas concretas de sus programas, con fuente.</p>
<p><a class="btn" href="/#tema/{slug(t)}">Comparar en la web interactiva</a></p>
<div class="cols">{''.join(cols)}</div>"""
    URLS.append(page(f"tema/{slug(t)}/", f"{t}: qué prometen los partidos para el 29-N",
                     f"{t}: las promesas del Frente Amplio, el PP, el PSOE y VOX para las elecciones generales del 29-N, una al lado de otra y con fuente.", body,
                     [("Inicio", "/"), (t, None)]))

# 5) Índice
body = "<h1>Índice de promesas del 29-N</h1><p class=\"muted\">Todo lo recogido hasta el " + e(UPD) + ", por partido.</p>"
body += "<h2>Por tema</h2><p>" + " · ".join(f'<a href="/tema/{slug(t)}/">{e(t)}</a>' for t in usados) + "</p>"
for p in PARTIES:
    pp = P[p]
    body += f'<h2><a href="/partido/{pp["slug"]}/">{e(pp["n"])}</a></h2><ul class="list">' + "".join(li_prom(r) for r in sorted([r for r in DATA if r["p"] == p], key=lambda x: x["fecha"], reverse=True)) + "</ul>"
URLS.append(page("promesas/", "Índice de promesas del 29-N", "Todas las promesas del Frente Amplio, el PP, el PSOE y VOX para las elecciones generales del 29 de noviembre de 2026, con fecha, lugar y fuente.", body, [("Inicio", "/"), ("Índice", None)]))

# 5b) Balance 2023-2026 (página índice) y feed RSS
B23P = os.path.join(ROOT, "balance2023.json")
if os.path.exists(B23P):
    B23 = json.load(open(B23P, encoding="utf-8"))
    N23 = {"PP": "PP", "PSOE": "PSOE", "SUMAR": "Sumar (hoy en el Frente Amplio)", "VOX": "VOX"}
    body = "<h1>Balance de las promesas de 2023</h1><p class=\"muted\">Qué prometieron en 2023 el PP, el PSOE, Sumar y VOX sobre vivienda, empleo y pensiones, e impuestos, y qué se hizo en la legislatura 2023-2026. El PSOE y Sumar gobernaron; el PP y VOX estaban en la oposición. Cada promesa, con su comprobación y su prueba, en la web interactiva.</p><p><a class=\"btn\" href=\"/#balance\">Ver el balance con filtros</a></p>"
    for p23 in ["SUMAR", "PP", "PSOE", "VOX"]:
        xs = [b for b in B23 if b["p"] == p23]
        if not xs: continue
        from collections import Counter
        c = Counter(b["st"] for b in xs)
        body += f"<h2>{e(N23[p23])} · {e(xs[0]['papel'])}</h2><p class=\"muted\">" + " · ".join(f"{e(k)}: {v}" for k, v in c.most_common()) + "</p><ul class=\"list\">"
        body += "".join(f'<li><a href="/#{e(b["id"])}">{e(b["txt"][:220])}{"…" if len(b["txt"])>220 else ""}</a><small>{e(b["t"])} · {e(b["st"])} · {e(b["id"])}</small></li>' for b in xs) + "</ul>"
    URLS.append(page("balance-2023/", "Balance de las promesas de 2023", "Qué prometieron el PP, el PSOE, Sumar y VOX en 2023 y qué se hizo en la legislatura 2023-2026, con la prueba de cada promesa.", body, [("Inicio", "/"), ("Balance 2023", None)]))

from email.utils import format_datetime
from datetime import datetime, timezone
def rfc(d):
    y, m_, dd = map(int, d.split("-")); return format_datetime(datetime(y, m_, dd, 12, 0, tzinfo=timezone.utc))
items = []
mN = re.search(r"const NOVEDADES=\[(.*?)\n\];", SRC, re.S)
if mN:
    for f, t in re.findall(r'\["(\d{4}-\d\d-\d\d)","(.*?)"\]', mN.group(1)):
        items.append((f, t, f"{BASE}/#novedades", t))
for r in DATA:
    pp = P[r["p"]]
    items.append((r["fecha"], f"{pp['corto']}: {r['txt']}", f"{BASE}/promesa/{r['id']}/", f"Lo dijo {r.get('quien') or pp['n']} ({r.get('acto')}, {r.get('lugar')}). Estado: {r['st']}."))
items.sort(key=lambda x: x[0], reverse=True)
rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>', "<title>TrechoDeMenos · Novedades</title>", f"<link>{BASE}/</link>",
       "<description>Las promesas de los partidos para el 29-N, con fecha, lugar y fuente, y su cumplimiento.</description>", "<language>es-es</language>"]
for i, (f, t, l, d) in enumerate(items[:80]):
    rss.append(f"<item><title>{e(t)}</title><link>{e(l)}</link><guid isPermaLink=\"false\">{e(l)}#{i}-{f}</guid><pubDate>{rfc(f)}</pubDate><description>{e(d)}</description></item>")
rss.append("</channel></rss>")
open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8").write("\n".join(rss) + "\n")

# 6) sitemap y robots
hoy = date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"<url><loc>{BASE}/</loc><lastmod>{hoy}</lastmod></url>"]
sm += [f"<url><loc>{u}</loc><lastmod>{hoy}</lastmod></url>" for u in URLS]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print(f"{len(URLS)} páginas generadas ({len(DATA)} promesas, {len(PROWS)} medidas, {len(usados)} temas).")
