#!/usr/bin/env python3
"""Añade a index.html las secciones «Balance 2023» y «Novedades» (idempotente)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(p, encoding="utf-8").read()
if 'id="v-balance"' in s:
    print("ya aplicado"); sys.exit(0)

def rep(a, b):
    global s
    assert s.count(a) == 1, ("no encontrado o repetido", a[:80])
    s = s.replace(a, b)

# Cabecera: RSS
rep('<link rel="icon"', '<link rel="alternate" type="application/rss+xml" title="TrechoDeMenos · Novedades" href="https://trechodemenos.es/feed.xml">\n<link rel="icon"')

# Menú
rep('<a href="#votaciones">Votaciones</a><a href="#metodo" class="last">', '<a href="#votaciones">Votaciones</a><a href="#balance">Balance 2023</a><a href="#metodo" class="last">')

# Secciones
rep('''  <section class="view" id="v-votaciones" aria-labelledby="h-vot">''', '''  <section class="view" id="v-balance" aria-labelledby="h-bal">
    <h2 id="h-bal">Balance 2023-2026</h2>
    <p class="lede">Qué prometieron en 2023 el PP, el PSOE, Sumar y VOX, y qué se hizo durante la legislatura que acaba de terminar. Cada promesa, con el texto de su programa, su estado y la prueba oficial enlazada.</p>
    <div class="note"><strong>Cómo leerlo.</strong> Por ahora están los tres primeros temas (vivienda, empleo y pensiones, e impuestos); el resto llegará tras el 29-N. Se recoge el texto tal como aparece en cada programa de 2023, por eso cada partido tiene un número distinto de promesas: depende de cuánto detalla su programa. Importa el papel de cada uno: el PSOE y Sumar gobernaron y podían aprobar sus promesas; el PP y VOX estaban en la oposición y solo podían impulsarlas en el Congreso o el Senado (por eso existe el estado «Impulsada sin éxito»). Los estados se explican en <a href="#metodo">Método</a>.</div>
    <div class="bsum" id="bsum"></div>
    <div class="chips" id="bchips-p" role="group" aria-label="Filtrar por partido"></div>
    <div class="chips" id="bchips-t" role="group" aria-label="Filtrar por tema"></div>
    <div class="chips" id="bchips-s" role="group" aria-label="Filtrar por estado"></div>
    <p class="count" id="bcount"></p>
    <div class="plist2" id="b23list"><p class="sub">Cargando…</p></div>
  </section>

  <section class="view" id="v-novedades" aria-labelledby="h-nov">
    <h2 id="h-nov">Novedades</h2>
    <p class="sub">Lo que se ha ido añadiendo a la web, del más reciente al más antiguo. También puedes seguirlo con un lector de noticias: <a href="https://trechodemenos.es/feed.xml">feed RSS</a>.</p>
    <div id="nlist"></div>
  </section>

  <section class="view" id="v-votaciones" aria-labelledby="h-vot">''')

# Inicio: accesos
rep('''    <p><a href="#temas" class="cgo">Comparar a los cuatro por tema →</a></p>''',
    '''    <p><a href="#temas" class="cgo">Comparar a los cuatro por tema →</a> &nbsp; <a href="#novedades" class="cgo">Novedades →</a></p>
    <div class="note"><strong>Nuevo: balance 2023-2026.</strong> Qué prometieron los partidos en 2023 y qué se hizo, con la prueba de cada promesa. <a href="#balance">Ver el balance →</a></div>''')

# Pie
rep('Próximamente: las promesas de los programas de 2023 y su balance.', 'Ya puedes ver el <a href="#balance">balance de las promesas de 2023</a>.')
rep('<a href="#erratas">Fe de erratas</a>', '<a href="#erratas">Fe de erratas</a><a href="#novedades">Novedades</a><a href="https://trechodemenos.es/feed.xml">RSS</a>')

# Estilos
rep('ul.erratas{', '''.bsum{overflow-x:auto;margin:14px 0}.bsum table{border-collapse:collapse;font-size:14px;min-width:560px;width:100%}
.bsum th,.bsum td{border-bottom:1px solid var(--rule);padding:6px 8px;text-align:right}.bsum th:first-child,.bsum td:first-child{text-align:left}
.bsum td b{font-weight:700}.bsum .pp{font-size:12px;color:var(--muted)}
.btxt{white-space:pre-line}.btxt.cut{max-height:7.5em;overflow:hidden;-webkit-mask-image:linear-gradient(#000 60%,transparent)}
.bmore{font:inherit;font-size:14px;background:none;border:0;padding:0;text-decoration:underline;cursor:pointer;color:var(--ink)}
.role{font-family:var(--f-mono);font-size:11.5px;border:1.5px solid var(--rule);border-radius:4px;padding:0 6px}
.nday{border-left:4px solid var(--hl);padding:2px 0 2px 12px;margin:0 0 16px}.nday h3{margin:0 0 4px;font-size:16px}.nday ul{margin:0;padding-left:18px}
ul.erratas{''')

JS = r'''
/* Balance 2023-2026 (se carga aparte para no hacer pesada la página) */
const P23={PP:{n:"PP",ini:"PP"},PSOE:{n:"PSOE",ini:"PSOE"},SUMAR:{n:"Sumar (hoy en el Frente Amplio)",ini:"SUMAR"},VOX:{n:"VOX",ini:"VOX"}};
const T23=["Vivienda","Empleo y pensiones","Impuestos"];
const ST23=["Cumplida","Parcial","Impulsada sin éxito","Incumplida","Sin evidencia","No medible"];
let B23=null, bstate={p:"todos",t:"todos",s:"todos",open:""};
async function loadB23(){
  if(B23) return B23;
  for(const u of ["balance2023.json","https://trechodemenos.es/balance2023.json"]){
    try{ const r=await fetch(u,{cache:"no-cache"}); if(r.ok){ B23=await r.json(); return B23; } }catch(_){}
  }
  throw new Error("no se pudo cargar");
}
function b23HTML(b){
  const k=KEY[b.st]||"pend", largo=b.txt.length>420;
  return `<article class="prom" id="${esc(b.id)}">
    <div class="pwho"><span class="ini">${esc(P23[b.p].ini)}</span>${esc(P23[b.p].n)} <span class="role" title="Papel del partido en la legislatura 2023-2026">${esc(b.papel)}</span></div>
    <p class="ptxt btxt${largo?" cut":""}">«${esc(b.txt)}»</p>
    ${largo?`<button type="button" class="bmore">Leer entero</button>`:""}
    <div class="pmeta"><span>Programa de 2023${b.pag?`, pág. ${esc(b.pag)}`:""}</span><span>${esc(b.t)}</span><span class="st" style="--c:var(--${k})">${esc(b.st)}</span></div>
    <details class="more"${bstate.open===b.id?" open":""}><summary>Ver comprobación y prueba</summary><div class="dbody">
      ${b.nota?`<p>${glos(esc(b.nota))}</p>`:""}
      ${b.fin?`<p><strong>${esc(b.fin)}.</strong> ${glos(esc(b.freno))}</p>`:(b.freno?`<p>${glos(esc(b.freno))}</p>`:"")}
      <div class="dlinks">${b.prueba?`<a href="${esc(b.prueba)}" target="_blank" rel="noopener">Prueba${b.tp?" · "+esc(b.tp):""}</a>`:""}${b.fuente?`<a href="${esc(b.fuente)}" target="_blank" rel="noopener">Programa de 2023</a>`:""}${b.fv?`<span class="muted">Comprobado el ${fmt(b.fv)}</span>`:""}<a class="pid" href="#${esc(b.id)}">${esc(b.id)}</a></div>
    </div></details>
  </article>`;
}
async function renderBalance(){
  const L=document.getElementById("b23list");
  try{ await loadB23(); }catch(e){ L.innerHTML=`<p class="sub">No se ha podido cargar el balance. Prueba a recargar la página.</p>`; return; }
  const parties=["SUMAR","PP","PSOE","VOX"].filter(p=>B23.some(b=>b.p===p));
  // Resumen por partido y estado
  document.getElementById("bsum").innerHTML=`<table><thead><tr><th>Partido (papel)</th>${ST23.map(s=>`<th>${esc(s)}</th>`).join("")}<th>Total</th></tr></thead><tbody>${
    parties.map(p=>{const xs=B23.filter(b=>b.p===p);return `<tr><td><b>${esc(P23[p].n)}</b> <span class="pp">${esc(xs[0].papel)}</span></td>${ST23.map(s=>{const n=xs.filter(b=>b.st===s).length;return `<td>${n?`<a href="#balance" data-bp="${p}" data-bs="${esc(s)}">${n}</a>`:'<span class="muted">0</span>'}</td>`;}).join("")}<td><b>${xs.length}</b></td></tr>`;}).join("")
  }</tbody></table>`;
  const chip=(grp,val,lab,n)=>`<button type="button" class="chip" data-g="${grp}" data-v="${esc(val)}" aria-pressed="${bstate[grp]===val}">${esc(lab)}${n!=null?` <b>${n}</b>`:""}</button>`;
  document.getElementById("bchips-p").innerHTML=chip("p","todos","Todos los partidos",B23.length)+parties.map(p=>chip("p",p,P23[p].n,B23.filter(b=>b.p===p).length)).join("");
  document.getElementById("bchips-t").innerHTML=chip("t","todos","Todos los temas")+T23.map(t=>chip("t",t,t,B23.filter(b=>b.t===t&&(bstate.p==="todos"||b.p===bstate.p)).length)).join("");
  document.getElementById("bchips-s").innerHTML=chip("s","todos","Todos los estados")+ST23.map(s=>chip("s",s,s,B23.filter(b=>b.st===s&&(bstate.p==="todos"||b.p===bstate.p)&&(bstate.t==="todos"||b.t===bstate.t)).length)).join("");
  const xs=B23.filter(b=>(bstate.p==="todos"||b.p===bstate.p)&&(bstate.t==="todos"||b.t===bstate.t)&&(bstate.s==="todos"||b.st===bstate.s))
    .sort((a,b)=>parties.indexOf(a.p)-parties.indexOf(b.p)||T23.indexOf(a.t)-T23.indexOf(b.t));
  document.getElementById("bcount").textContent=`${xs.length} ${xs.length===1?"promesa":"promesas"}`;
  L.innerHTML=xs.map(b23HTML).join("")||`<p class="none">No hay promesas con estos filtros.</p>`;
  if(bstate.open){ const el=document.getElementById(bstate.open); if(el) setTimeout(()=>el.scrollIntoView({block:"start"}),30); bstate.open=""; }
}
document.addEventListener("click",e=>{
  const c=e.target.closest("#v-balance .chip"); if(c){ bstate[c.dataset.g]=c.dataset.v; renderBalance(); return; }
  const a=e.target.closest("#bsum a[data-bp]"); if(a){ e.preventDefault(); bstate={p:a.dataset.bp,t:"todos",s:a.dataset.bs,open:""}; renderBalance(); document.getElementById("bcount").scrollIntoView({block:"start"}); return; }
  const m=e.target.closest(".bmore"); if(m){ const t=m.previousElementSibling; t.classList.remove("cut"); m.remove(); }
});

/* Novedades: hitos de la web y compromisos de campaña por día */
const NOVEDADES=[
 ["2026-11-15","Balance de la legislatura 2023-2026: 281 promesas de 2023 sobre vivienda, empleo y pensiones, e impuestos, con su estado y su prueba."],
 ["2026-11-15","Programa del PSOE: 167 medidas concretas de 500, cruzadas con lo que ha dicho en campaña."],
 ["2026-11-15","Nueva sección «Para ti»: las medidas que te afectan según tu situación. Botones para compartir cada promesa."],
 ["2026-11-15","Quiénes somos y fe de erratas, en Método. Nuevo contacto: info@trechodemenos.es."],
 ["2026-11-14","Cada promesa y cada medida tiene su propia página. Glosario de términos parlamentarios en Votaciones."],
 ["2026-11-14","Votaciones del Congreso ampliadas y ordenadas por tema, con datos oficiales."],
 ["2026-11-13","Programa de VOX: 56 medidas concretas de 115."],
 ["2026-11-12","Programa del PP: 102 medidas concretas de 249."]
];
function renderNovedades(){
  const dias={};
  NOVEDADES.forEach(([f,t])=>{(dias[f]=dias[f]||{h:[],c:[]}).h.push(t);});
  ROWS.forEach(r=>{(dias[r.fecha]=dias[r.fecha]||{h:[],c:[]}).c.push(r);});
  document.getElementById("nlist").innerHTML=Object.keys(dias).sort().reverse().map(f=>{
    const d=dias[f], porP=PARTIES.map(p=>[p,d.c.filter(r=>r.p===p).length]).filter(x=>x[1]);
    return `<div class="nday"><h3>${fmt(f)}</h3><ul>${d.h.map(t=>`<li>${esc(t)}</li>`).join("")}${d.c.length?`<li>${d.c.length} ${d.c.length===1?"compromiso de campaña":"compromisos de campaña"} (${porP.map(([p,n])=>`${esc(CAND[p].a)} ${n}`).join(", ")}): ${d.c.map(r=>`<a href="#${esc(r.id)}">${esc(r.id)}</a>`).join(", ")}</li>`:""}</ul></div>`;
  }).join("");
}
'''
rep('/* Búsqueda global */', JS + '\n/* Búsqueda global */')

# Rutas
rep('  if(a==="votaciones"){', '''  if(a==="balance"){ show("v-balance","balance"); window.scrollTo(0,0); renderBalance(); return; }
  if(a==="novedades"){ renderNovedades(); show("v-novedades",""); window.scrollTo(0,0); return; }
  if(/^(pp|psoe|sumar|vox)-(viv|emp|imp)-\\d+$/.test(h)){ bstate={p:"todos",t:"todos",s:"todos",open:raw.toUpperCase()}; show("v-balance","balance"); renderBalance(); return; }
  if(a==="votaciones"){''')

# Método: nota sobre el balance
rep('''    <h3>Estados de una promesa</h3>''', '''    <h3 id="m-balance">Balance 2023-2026</h3>
    <p>Para el balance se recogen las promesas de los programas de 2023 tema a tema, con el texto tal como aparece en el programa. Cada una se comprueba con documentos oficiales (BOE, Diario de Sesiones, Boletín de las Cortes, datos del INE o de la Seguridad Social) y, cuando no los hay, con prensa que cite la fuente. Si no se encuentra prueba ni a favor ni en contra, queda como «Sin evidencia», que no es lo mismo que «Incumplida». Se tiene en cuenta el papel de cada partido: quien está en la oposición no puede aprobar leyes por sí solo.</p>

    <h3>Estados de una promesa</h3>''')

open(p, "w", encoding="utf-8").write(s)
print("aplicado")
