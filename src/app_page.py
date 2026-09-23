"""Рабочий экран: сворачивающийся сайдбар с иконками и разбор выводов.

Сайдбар свёрнут до полосы иконок и раскрывается при наведении. Пункты — это
не декоративное меню, а разделы разбора: каждый показывает свою группу выводов
и её количество, поэтому по сайдбару сразу видно структуру результата.
"""
from __future__ import annotations

import json

from .pages import BASE_CSS


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
    "units": _icon('<rect x="3" y="3" width="7" height="7" rx="1"/>'
                   '<rect x="14" y="3" width="7" height="7" rx="1"/>'
                   '<rect x="8" y="14" width="8" height="7" rx="1"/>'),
    "report": _icon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/>'
                    '<path d="M14 2v6h6"/><path d="M8 13h8M8 17h5"/>'),
    "upload": _icon('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                    '<path d="m7 10 5-5 5 5"/><path d="M12 5v12"/>'),
    "home": _icon('<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><path d="M9 21v-8h6v8"/>'),
}

_STYLE = """
body{display:flex;min-height:100vh}
.side{position:fixed;left:0;top:0;bottom:0;width:53px;background:var(--card);
  border-right:1px solid var(--line);display:flex;flex-direction:column;z-index:30;
  overflow:hidden;transition:width .2s ease}
.side:hover,.side:focus-within{width:242px;box-shadow:14px 0 36px rgba(8,20,22,.09)}
.side .top{height:53px;display:flex;align-items:center;gap:11px;padding:0 15px;
  border-bottom:1px solid var(--line);flex-shrink:0}
.side .top i{width:19px;height:19px;border:2px solid var(--acc);border-radius:5px;
  position:relative;flex-shrink:0;display:block}
.side .top i::after{content:"";position:absolute;left:3px;right:3px;top:3.5px;height:1.5px;
  background:var(--acc);box-shadow:0 4px 0 var(--acc)}
.side nav{flex:1;overflow-y:auto;padding:9px 8px;display:flex;flex-direction:column;gap:2px}
.side .sep{height:1px;background:var(--line);margin:8px 6px;flex-shrink:0}
.side .bottom{padding:9px 8px;border-top:1px solid var(--line)}
.it{display:flex;align-items:center;gap:12px;height:34px;padding:0 7px;border-radius:8px;
  cursor:pointer;color:var(--mut);background:none;border:0;font:inherit;font-size:13.5px;
  width:100%;text-align:left;transition:background .12s,color .12s}
.it svg{width:17px;height:17px;flex-shrink:0}
.it:hover{background:var(--muted);color:var(--ink)}
.it.on{background:var(--muted);color:var(--acc);font-weight:500}
.lbl{white-space:nowrap;opacity:0;transition:opacity .16s ease;flex:1;display:flex;
  align-items:center;justify-content:space-between;gap:8px}
.side:hover .lbl,.side:focus-within .lbl{opacity:1}
.cnt{font-family:var(--mono);font-size:11px;color:var(--mut2)}
.it.on .cnt{color:var(--acc)}
main{flex:1;margin-left:53px;padding:26px 30px 70px;max-width:1120px}
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
  flex-wrap:wrap;margin-bottom:20px}
h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.head p{margin:0;color:var(--mut);font-size:13.5px;max-width:64ch}
.panel{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  padding:16px 18px;margin-bottom:16px;box-shadow:0 1px 2px rgba(2,8,23,.04)}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:end}
label{display:block;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;
  color:var(--mut2);margin-bottom:6px}
input[type=file]{font:inherit;font-size:13px;max-width:100%}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:var(--r);
  overflow:hidden;margin-bottom:16px}
.stat{background:var(--card);padding:13px 16px}
.stat b{display:block;font-size:24px;font-weight:600;line-height:1.2;font-variant-numeric:tabular-nums}
.stat span{font-size:11px;color:var(--mut2);text-transform:uppercase;letter-spacing:.05em}
.units{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:16px}
.u{border:1px solid var(--line);border-radius:8px;padding:6px 11px;font-size:13px;background:var(--card)}
.u.new{border-color:var(--ok);background:var(--ok-bg);color:var(--ok);font-weight:500}
.f{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:10px;padding:14px 17px;margin-bottom:9px;box-shadow:0 1px 2px rgba(2,8,23,.04)}
.f.high{border-left-color:var(--bad)}
.f.medium{border-left-color:var(--warn)}
.f.info{border-left-color:var(--ok)}
.f .meta{font-size:11px;color:var(--mut2);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.f h3{margin:0 0 5px;font-size:15px}
.f>p{margin:0 0 9px;color:var(--mut);font-size:13.5px}
.src{font-size:13px;border-top:1px dashed var(--line);padding-top:7px;margin-top:7px;color:var(--mut)}
.src b{color:var(--acc);font-family:var(--mono);font-size:11.5px}
.vf{margin:9px 0;padding:9px 12px;border-radius:8px;background:var(--ok-bg);color:var(--ok);
  font-size:13px;border-left:3px solid currentColor}
.vf.confirmed_lost{background:var(--bad-bg);color:var(--bad)}
.vf.uncertain{background:var(--warn-bg);color:var(--warn)}
.vf summary{cursor:pointer;font-size:12px;opacity:.85;margin-top:5px}
.tc{font-family:var(--mono);font-size:11px;margin-top:5px;color:var(--mut);line-height:1.5}
.tc b{color:var(--acc)}
pre.conc{white-space:pre-wrap;font:14px/1.62 var(--sans);margin:0}
.mode{font-size:12px;color:var(--mut2);margin:12px 0 0}
.empty{color:var(--mut);padding:28px;text-align:center}
@media(max-width:700px){main{padding:20px 16px 60px}}
"""

_SCRIPT = """
const $=s=>document.querySelector(s);
let data=null, filter='all';

const NAV=[
  {k:'all', i:'summary', t:'Сводка'},
  {k:'sep'},
  {k:'function_lost',        i:'lost',    t:'Потери функций'},
  {k:'false_positive',       i:'agent',   t:'Снято агентом'},
  {k:'duplication',          i:'dup',     t:'Дублирование'},
  {k:'function_moved',       i:'moved',   t:'Передано'},
  {k:'function_generalized', i:'general', t:'Стало общим'},
  {k:'conflict_of_interest', i:'lost',    t:'Конфликт интересов'},
  {k:'sep'},
  {k:'units',  i:'units',  t:'Подразделения'},
  {k:'report', i:'report', t:'Заключение'}
];

function count(kind){ return data ? data.findings.filter(f=>f.kind===kind).length : ''; }

function renderNav(){
  $('#nav').innerHTML = NAV.map(n=>{
    if(n.k==='sep') return '<div class="sep"></div>';
    const plain = (n.k==='all'||n.k==='units'||n.k==='report');
    const c = plain ? '' : count(n.k);
    return '<button class="it '+(filter===n.k?'on':'')+'" data-k="'+n.k+'">'+ICONS[n.i]+
      '<span class="lbl">'+n.t+'<span class="cnt">'+c+'</span></span></button>';
  }).join('');
  document.querySelectorAll('.it[data-k]').forEach(b=>{
    b.onclick=()=>{ filter=b.dataset.k; render(); };
  });
}

async function analyze(useSample){
  const fd=new FormData();
  if(!useSample){
    if($('#before').files[0]) fd.append('before',$('#before').files[0]);
    if($('#after').files[0]) fd.append('after',$('#after').files[0]);
  }
  $('#out').innerHTML='<div class="panel empty">Разбираю документы и перепроверяю выводы агентом — обычно около 45 секунд.</div>';
  $('#go').disabled=$('#demo').disabled=true;
  try{
    const r=await fetch('/api/analyze',{method:'POST',body:fd});
    const res=await r.json();
    if(res.error){
      $('#out').innerHTML='<div class="panel empty">'+res.error+'</div>';
      $('#go').disabled=$('#demo').disabled=false; return;
    }
    data=res; filter='all'; render();
  }catch(e){
    $('#out').innerHTML='<div class="panel empty">Ошибка: '+e.message+'</div>';
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
  const src=f.sources.map(s=>'<div class="src"><b>'+s.cite+'</b> — '+s.quote.slice(0,260)+'</div>').join('');
  return '<div class="f '+f.severity+'"><div class="meta">'+(L.kind[f.kind]||f.kind)+
    ' · риск '+L.severity[f.severity]+' · уверенность '+f.confidence+'</div><h3>'+f.title+
    '</h3><p>'+f.detail+'</p>'+v+src+'</div>';
}

function render(){
  renderNav();
  if(!data) return;
  const L=data.labels, before=data.units_before.map(u=>u.code);
  let body='';

  if(filter==='all'){
    body='<div class="stats">'+
      '<div class="stat"><b>'+data.units_after.length+'</b><span>подразделений</span></div>'+
      '<div class="stat"><b>'+count('unit_created')+'</b><span>создано</span></div>'+
      '<div class="stat"><b>'+count('function_lost')+'</b><span>возможных потерь</span></div>'+
      '<div class="stat"><b>'+count('false_positive')+'</b><span>снято агентом</span></div>'+
      '<div class="stat"><b>'+count('duplication')+'</b><span>дублирований</span></div>'+
      '<div class="stat"><b>'+count('function_generalized')+'</b><span>стало общим</span></div></div>'+
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
    const list=data.findings.filter(f=>f.kind===filter);
    body=list.length ? list.map(f=>card(f,L)).join('')
                     : '<div class="panel empty">В этой категории выводов нет.</div>';
  }
  $('#out').innerHTML=body;
}

$('#go').onclick=()=>analyze(false);
$('#demo').onclick=()=>analyze(true);
renderNav();
"""

APP = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Сверка — рабочий экран</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>%(base)s%(style)s</style></head><body>

<aside class="side">
  <div class="top"><i></i><span class="lbl" style="font-weight:600;font-size:14px;color:var(--ink)">Сверка</span></div>
  <nav id="nav"></nav>
  <div class="bottom">
    <button class="it" id="toUpload">%(upload)s<span class="lbl">Другие документы</span></button>
    <a class="it" href="/">%(home)s<span class="lbl">На главную</span></a>
  </div>
</aside>

<main>
  <div class="head">
    <div>
      <h1>Анализ организационной структуры и функционала</h1>
      <p>Сравнение комплектов «до» и «после»: потери функций, дублирование и конфликт интересов — со ссылкой на пункт документа.</p>
    </div>
    <a class="btn outline sm" href="/">← Главная</a>
  </div>

  <div class="panel" id="uploader">
    <div class="row">
      <div><label>Комплект «до»</label><input type="file" id="before" accept=".docx"></div>
      <div><label>Комплект «после»</label><input type="file" id="after" accept=".docx"></div>
      <button class="btn" id="go">Сравнить</button>
      <button class="btn outline" id="demo">Контрольный комплект</button>
    </div>
  </div>

  <div id="out"><div class="panel empty">Нажмите «Контрольный комплект», чтобы увидеть разбор на документах из кейса.</div></div>
</main>

<script>
const ICONS=%(icons)s;
%(script)s
document.getElementById('toUpload').onclick=()=>
  document.getElementById('uploader').scrollIntoView({block:'center',behavior:'smooth'});
</script>
</body></html>
""" % {"base": BASE_CSS, "style": _STYLE, "script": _SCRIPT,
       "icons": json.dumps(ICONS, ensure_ascii=False),
       "upload": ICONS["upload"], "home": ICONS["home"]}
