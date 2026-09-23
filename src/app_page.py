"""Рабочий экран: постоянный сайдбар и разбор выводов.

Сайдбар зафиксирован и всегда раскрыт — он не перекрывает содержимое, а делит
экран с ним. Пункты не декоративные: каждый показывает свою группу выводов
и её количество, поэтому по сайдбару сразу видна структура результата.
"""
from __future__ import annotations

import json

from .pages import BASE_CSS

SIDEBAR_W = 248


def _icon(path: str) -> str:
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


ICONS = {
    "summary": _icon('<rect x="3" y="3" width="7" height="9" rx="1"/>'
                     '<rect x="14" y="3" width="7" height="5" rx="1"/>'
                     '<rect x="14" y="12" width="7" height="9" rx="1"/>'
                     '<rect x="3" y="16" width="7" height="5" rx="1"/>'),
    "lost": _icon('<path d="M10.3 5.2 3.6 17a2 2 0 0 0 1.7 3h13.4a2 2 0 0 0 1.7-3L13.7 5.2a2 2 0 0 0-3.4 0Z"/>'
                  '<path d="M12 9v4"/><path d="M12 17h.01"/>'),
    "agent": _icon('<path d="M20 6 9 17l-5-5"/>'),
    "dup": _icon('<rect x="9" y="9" width="12" height="12" rx="2"/>'
                 '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'),
    "moved": _icon('<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>'),
    "general": _icon('<circle cx="12" cy="12" r="9"/><path d="M3.6 9h16.8M3.6 15h16.8"/>'
                     '<path d="M12 3c3 4.5 3 13.5 0 18c-3-4.5-3-13.5 0-18Z"/>'),
    "conflict": _icon('<path d="M12 2v6m0 8v6M4.9 4.9l4.2 4.2m5.8 5.8 4.2 4.2M2 12h6m8 0h6"/>'),
    "units": _icon('<rect x="3" y="3" width="7" height="7" rx="1"/>'
                   '<rect x="14" y="3" width="7" height="7" rx="1"/>'
                   '<rect x="8" y="14" width="8" height="7" rx="1"/>'),
    "report": _icon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/>'
                    '<path d="M14 2v6h6"/><path d="M8 13h8M8 17h5"/>'),
    "home": _icon('<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><path d="M9 21v-8h6v8"/>'),
    "menu": _icon('<path d="M3 6h18M3 12h18M3 18h18"/>'),
    "download": _icon('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                      '<path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>'),
}

_STYLE = """
body{background:var(--surface)}
.side{position:fixed;left:0;top:0;bottom:0;width:%(w)spx;background:var(--card);
  border-right:1px solid var(--line);display:flex;flex-direction:column;z-index:40}
.side .top{height:62px;display:flex;align-items:center;gap:10px;padding:0 18px;
  border-bottom:1px solid var(--line);flex-shrink:0;font-weight:700;font-size:16px;
  letter-spacing:-.03em}
.side .top em{font-style:normal;font-size:11px;font-weight:500;color:var(--mut2);
  font-family:var(--mono);letter-spacing:0}
.side nav{flex:1;overflow-y:auto;padding:12px 10px}
.grp{font-size:11px;color:var(--mut2);letter-spacing:.06em;padding:14px 9px 6px;font-weight:500}
.it{display:flex;align-items:center;gap:11px;height:35px;padding:0 10px;border-radius:8px;
  cursor:pointer;color:var(--mut);background:none;border:0;font:inherit;font-size:14px;
  width:100%%;text-align:left;transition:background .12s,color .12s;margin-bottom:1px}
.it svg{width:16px;height:16px;flex-shrink:0}
.it:hover{background:var(--muted);color:var(--ink)}
.it.on{background:var(--ink);color:var(--bg);font-weight:500}
.it .lbl{flex:1;display:flex;align-items:center;justify-content:space-between;gap:8px}
.cnt{font-family:var(--mono);font-size:11px;color:var(--mut2)}
.it.on .cnt{color:var(--bg);opacity:.7}
.side .bottom{padding:10px;border-top:1px solid var(--line)}

.topbar{position:sticky;top:0;z-index:30;height:62px;background:var(--bg);
  border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;padding:0 26px}
.topbar .burger{display:none;background:none;border:0;cursor:pointer;color:var(--ink);padding:6px}
.topbar .burger svg{width:19px;height:19px}
.topbar h1{font-size:15px;font-weight:600;margin:0;letter-spacing:-.02em}
.topbar .sp{flex:1}
.topbar .btn svg{width:15px;height:15px}
main{margin-left:%(w)spx}
.wrap{padding:26px;max-width:1160px}

.lead{color:var(--mut);font-size:14px;margin:0 0 20px;max-width:74ch}
.panel{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  padding:18px;margin-bottom:18px}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:end}
label{display:block;font-size:12px;color:var(--mut);margin-bottom:7px;font-weight:500}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin-bottom:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px}
.stat span{font-size:13px;color:var(--mut);display:block;margin-bottom:6px}
.stat b{display:block;font-size:30px;font-weight:600;line-height:1.1;letter-spacing:-.035em;
  font-variant-numeric:tabular-nums}
.units{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.u{border:1px solid var(--line);border-radius:8px;padding:7px 12px;font-size:13.5px;background:var(--card)}
.u.new{border-color:var(--ok);background:var(--ok-bg);color:var(--ok);font-weight:500}
.f{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:var(--r);padding:16px 18px;margin-bottom:10px}
.f.high{border-left-color:var(--bad)}
.f.medium{border-left-color:var(--warn)}
.f.info{border-left-color:var(--ok)}
.f .meta{font-size:11.5px;color:var(--mut2);margin-bottom:6px}
.f h3{margin:0 0 6px;font-size:15.5px;letter-spacing:-.02em}
.f>p{margin:0 0 10px;color:var(--mut);font-size:14px}
.src{font-size:13.5px;border-top:1px solid var(--line);padding-top:8px;margin-top:8px;color:var(--mut)}
.src b{color:var(--link);font-family:var(--mono);font-size:12px}
.vf{margin:10px 0;padding:10px 13px;border-radius:9px;background:var(--ok-bg);color:var(--ok);
  font-size:13.5px;border:1px solid currentColor}
.vf.confirmed_lost{background:var(--bad-bg);color:var(--bad)}
.vf.uncertain{background:var(--warn-bg);color:var(--warn)}
.vf summary{cursor:pointer;font-size:12.5px;opacity:.85;margin-top:6px}
.tc{font-family:var(--mono);font-size:11px;margin-top:6px;color:var(--mut);line-height:1.5}
.tc b{color:var(--link)}
.rec{margin:10px 0;padding:10px 13px;border-radius:9px;background:var(--muted);
  color:var(--ink);font-size:13.5px;border:1px solid var(--line)}
.rec b{font-weight:600}
pre.conc{white-space:pre-wrap;font:14px/1.62 var(--sans);margin:0}
.mode{font-size:12.5px;color:var(--mut2);margin:14px 0 0}
.empty{color:var(--mut);padding:34px;text-align:center;background:var(--card);
  border:1px solid var(--line);border-radius:var(--r)}
.search{width:100%%;max-width:440px;font:inherit;font-size:14px;padding:10px 13px;margin-bottom:14px;
  border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink)}
.search::placeholder{color:var(--mut2)}
.found{font-size:13px;color:var(--mut2);margin:0 0 14px}
.scrim{display:none;position:fixed;inset:0;background:rgba(9,9,11,.4);z-index:35}

@media(max-width:900px){
  .side{transform:translateX(-100%%);transition:transform .2s ease}
  body.open .side{transform:none}
  body.open .scrim{display:block}
  main{margin-left:0}
  .topbar .burger{display:inline-flex}
  .topbar h1{font-size:14px}
  .wrap{padding:18px}
}
""" % {"w": SIDEBAR_W}

_SCRIPT = """
const $=s=>document.querySelector(s);
let data=null, filter='all', query='';

const NAV=[
  {k:'all', i:'summary', t:'Сводка'},
  {g:'Отклонения'},
  {k:'function_lost',        i:'lost',     t:'Потери функций'},
  {k:'false_positive',       i:'agent',    t:'Снято агентом'},
  {k:'duplication',          i:'dup',      t:'Дублирование'},
  {k:'conflict_of_interest', i:'conflict', t:'Конфликт интересов'},
  {g:'Перераспределение'},
  {k:'function_moved',       i:'moved',    t:'Передано'},
  {k:'function_generalized', i:'general',  t:'Стало общим'},
  {g:'Документы'},
  {k:'units',  i:'units',  t:'Подразделения'},
  {k:'report', i:'report', t:'Заключение'}
];

function match(f,q){
  q=q.toLowerCase();
  if((f.title+' '+f.detail).toLowerCase().includes(q)) return true;
  return f.sources.some(s=>(s.cite+' '+s.quote).toLowerCase().includes(q));
}

function count(kind){ return data ? data.findings.filter(f=>f.kind===kind).length : ''; }

function renderNav(){
  $('#nav').innerHTML = NAV.map(n=>{
    if(n.g) return '<div class="grp">'+n.g+'</div>';
    const plain=(n.k==='all'||n.k==='units'||n.k==='report');
    const c=plain?'':count(n.k);
    return '<button class="it '+(filter===n.k?'on':'')+'" data-k="'+n.k+'">'+ICONS[n.i]+
      '<span class="lbl">'+n.t+'<span class="cnt">'+c+'</span></span></button>';
  }).join('');
  document.querySelectorAll('.it[data-k]').forEach(b=>{
    b.onclick=()=>{ filter=b.dataset.k; query=''; document.body.classList.remove('open'); render(); };
  });
}

async function analyze(useSample){
  const fd=new FormData();
  if(!useSample){
    if($('#before').files[0]) fd.append('before',$('#before').files[0]);
    if($('#after').files[0]) fd.append('after',$('#after').files[0]);
  }
  $('#out').innerHTML='<div class="empty">Разбираю документы и перепроверяю выводы агентом — обычно около 45 секунд.</div>';
  $('#go').disabled=$('#demo').disabled=true;
  try{
    const r=await fetch('/api/analyze',{method:'POST',body:fd});
    const res=await r.json();
    if(res.error){
      $('#out').innerHTML='<div class="empty">'+res.error+'</div>';
      $('#go').disabled=$('#demo').disabled=false; return;
    }
    data=res; filter='all'; query='';
    $('#dl').style.display='inline-flex';
    render();
  }catch(e){
    $('#out').innerHTML='<div class="empty">Ошибка: '+e.message+'</div>';
  }
  $('#go').disabled=$('#demo').disabled=false;
}

function card(f,L){
  let v='';
  if(f.verification){
    let tr='';
    if(f.verification.trace.length){
      tr='<details><summary>показать работу агента ('+f.verification.trace.length+' вызова инструментов)</summary>'+
        f.verification.trace.map((t,i)=>'<div class="tc"><b>'+(i+1)+'. '+t.tool+'</b>('+
        JSON.stringify(t.args).slice(0,130)+') → '+String(t.result).slice(0,200)+'…</div>').join('')+'</details>';
    }
    v='<div class="vf '+f.verification.verdict+'">Агент-верификатор: '+f.verification.verdict_ru+
      (f.verification.evidence_cite?' · '+f.verification.evidence_cite:'')+tr+'</div>';
  }
  const rec=f.recommendation?'<div class="rec"><b>Рекомендация.</b> '+f.recommendation+'</div>':'';
  const src=f.sources.map(s=>'<div class="src"><b>'+s.cite+'</b> — '+s.quote.slice(0,260)+'</div>').join('');
  return '<div class="f '+f.severity+'"><div class="meta">'+(L.kind[f.kind]||f.kind)+
    ' · риск '+L.severity[f.severity]+' · уверенность '+f.confidence+'</div><h3>'+f.title+
    '</h3><p>'+f.detail+'</p>'+v+rec+src+'</div>';
}

function render(){
  renderNav();
  if(!data) return;
  const L=data.labels, before=data.units_before.map(u=>u.code);
  let body='';

  if(filter==='all'){
    body='<div class="stats">'+
      '<div class="stat"><span>Подразделений после</span><b>'+data.units_after.length+'</b></div>'+
      '<div class="stat"><span>Создано</span><b>'+count('unit_created')+'</b></div>'+
      '<div class="stat"><span>Дублирований</span><b>'+count('duplication')+'</b></div>'+
      '<div class="stat"><span>Конфликтов интересов</span><b>'+count('conflict_of_interest')+'</b></div>'+
      '<div class="stat"><span>Снято агентом</span><b>'+count('false_positive')+'</b></div>'+
      '<div class="stat"><span>Стало общим</span><b>'+count('function_generalized')+'</b></div></div>'+
      '<div class="units">'+data.units_after.map(u=>'<span class="u '+(before.includes(u.code)?'':'new')+'">'+
        u.code+' · функций '+u.functions.length+'</span>').join('')+'</div>'+
      '<div class="panel"><pre class="conc">'+data.conclusion+'</pre>'+
      '<p class="mode">Режим сопоставления: '+data.mode+' · '+data.before_doc+' → '+data.after_doc+'</p></div>'+
      data.findings.slice(0,8).map(f=>card(f,L)).join('');
  } else if(filter==='units'){
    body=data.units_after.map(u=>'<div class="f info"><div class="meta">'+
      (before.includes(u.code)?'сохранено':'создано')+' · '+u.cite+'</div><h3>'+u.code+' — '+u.name+
      '</h3><p>Закреплённых функций: '+u.functions.length+'</p>'+
      u.functions.slice(0,6).map(fn=>'<div class="src"><b>'+fn.cite+'</b> — '+
        fn.text.slice(0,200)+'</div>').join('')+'</div>').join('');
  } else if(filter==='report'){
    body='<div class="panel"><pre class="conc">'+data.conclusion+'</pre>'+
      '<p class="mode">Режим сопоставления: '+data.mode+' · '+data.before_doc+' → '+data.after_doc+'</p></div>';
  } else {
    let list=data.findings.filter(f=>f.kind===filter);
    const total=list.length;
    if(query) list=list.filter(f=>match(f,query));
    body='<input class="search" id="q" placeholder="Поиск по тексту вывода или номеру пункта" value="'+
      query.replace(/"/g,'&quot;')+'">'+
      (query?'<p class="found">Найдено '+list.length+' из '+total+'</p>':'')+
      (list.length ? list.map(f=>card(f,L)).join('')
                   : '<div class="empty">Ничего не найдено.</div>');
  }
  $('#out').innerHTML=body;

  const q=document.getElementById('q');
  if(q){
    q.oninput=()=>{ query=q.value; const pos=q.selectionStart; render();
      const nq=document.getElementById('q'); if(nq){ nq.focus(); nq.setSelectionRange(pos,pos); } };
  }
}

$('#go').onclick=()=>analyze(false);
$('#demo').onclick=()=>analyze(true);
$('#burger').onclick=()=>document.body.classList.toggle('open');
$('#scrim').onclick=()=>document.body.classList.remove('open');
renderNav();
"""

APP = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Сверка — рабочий экран</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap">
<style>%(base)s%(style)s</style></head><body>

<div class="scrim" id="scrim"></div>

<aside class="side">
  <div class="top">Сверка <em>v1</em></div>
  <nav id="nav"></nav>
  <div class="bottom"><a class="it" href="/">%(home)s<span class="lbl">На главную</span></a></div>
</aside>

<main>
  <div class="topbar">
    <button class="burger" id="burger">%(menu)s</button>
    <h1>Анализ организационной структуры и функционала</h1>
    <div class="sp"></div>
    <a class="btn outline sm" id="dl" href="/api/export" style="display:none">%(download)s Скачать заключение</a>
  </div>

  <div class="wrap">
    <p class="lead">Сравнение комплектов «до» и «после»: потери функций, дублирование и конфликт интересов — со ссылкой на пункт документа.</p>

    <div class="panel" id="uploader">
      <div class="row">
        <div><label>Комплект «до»</label><input type="file" id="before" accept=".docx"></div>
        <div><label>Комплект «после»</label><input type="file" id="after" accept=".docx"></div>
        <button class="btn" id="go">Сравнить</button>
        <button class="btn outline" id="demo">Контрольный комплект</button>
      </div>
    </div>

    <div id="out"><div class="empty">Нажмите «Контрольный комплект», чтобы увидеть разбор на документах из кейса.</div></div>
  </div>
</main>

<script>
const ICONS=%(icons)s;
%(script)s
</script>
</body></html>
""" % {"base": BASE_CSS, "style": _STYLE, "script": _SCRIPT,
       "icons": json.dumps(ICONS, ensure_ascii=False),
       "home": ICONS["home"], "menu": ICONS["menu"], "download": ICONS["download"]}
