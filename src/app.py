"""Веб-интерфейс: загрузка комплектов «до» и «после», просмотр выводов.

Артефакты по ТЗ: интерфейс для загрузки документов и просмотра результатов.
"""
from __future__ import annotations

import os
import tempfile
import traceback
import zipfile

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .compare import run
from .export import build_docx
from .app_page import APP as WORKSPACE_PAGE
from .pages import MOCK_PREVIEW, render_landing
from .report import render_conclusion

app = FastAPI(title="Анализ организационной структуры и функционала")
app.mount("/static", StaticFiles(directory="static"), name="static")

SAMPLE_BEFORE = "data/samples/polozhenie_red8.docx"
SAMPLE_AFTER = "data/samples/polozhenie_red9.docx"

# Разбор занимает около 45 секунд, поэтому выгрузка использует последний
# результат, а не пересчитывает его заново.
_LAST: dict = {}

KIND_RU = {
    "unit_created": "Создано подразделение",
    "unit_removed": "Подразделение исчезло",
    "unit_kept": "Подразделение сохранено",
    "function_lost": "Возможная потеря функции",
    "function_moved": "Функция передана",
    "duplication": "Дублирование",
    "conflict_of_interest": "Конфликт интересов",
    "false_positive": "Снято агентом",
    "function_generalized": "Функция стала общей",
}
SEV_RU = {"high": "высокий", "medium": "средний", "info": "справочно"}


class DocumentError(Exception):
    """Понятная пользователю причина, по которой документ не принят."""


def _save(upload: UploadFile) -> str:
    name = upload.filename or "doc.docx"
    if not name.lower().endswith(".docx"):
        raise DocumentError(f"Файл «{name}» не в формате .docx. "
                            f"Сейчас поддерживается Word (.docx).")
    data = upload.file.read()
    if not data:
        raise DocumentError(f"Файл «{name}» пустой.")

    fd, path = tempfile.mkstemp(suffix=".docx")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    if not zipfile.is_zipfile(path):
        raise DocumentError(f"Файл «{name}» повреждён или не является документом Word.")
    with zipfile.ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            raise DocumentError(f"В файле «{name}» нет текста документа Word.")
    return path


SCREENSHOT = "static/app-preview.png"


@app.get("/", response_class=HTMLResponse)
def landing() -> str:
    """Стартовая страница: что делает сервис и переход в рабочий экран.

    В рамку подставляется настоящий скриншот рабочего экрана, если он положен
    в static/app-preview.png; иначе показывается встроенный макет интерфейса.
    """
    if os.path.exists(SCREENSHOT):
        preview = ('<img src="/static/app-preview.png" alt="Рабочий экран сервиса: '
                   'разбор комплектов документов">')
    else:
        preview = MOCK_PREVIEW
    return render_landing(preview)


@app.get("/app", response_class=HTMLResponse)
def workspace() -> str:
    """Рабочий экран: загрузка комплектов и разбор выводов."""
    return WORKSPACE_PAGE


@app.post("/api/analyze")
async def analyze(before: UploadFile = File(None), after: UploadFile = File(None)):
    try:
        before_path = _save(before) if before else SAMPLE_BEFORE
        after_path = _save(after) if after else SAMPLE_AFTER
    except DocumentError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    # имя для ссылок берём исходное, а не путь во временной папке
    before_name = before.filename if before else os.path.basename(SAMPLE_BEFORE)
    after_name = after.filename if after else os.path.basename(SAMPLE_AFTER)

    try:
        report = run(before_path, after_path,
                     before_name=before_name, after_name=after_name)
    except Exception:
        traceback.print_exc()
        return JSONResponse(
            {"error": "Не удалось разобрать документы. Проверьте, что это положения "
                      "с нумерацией пунктов, а не сканы или таблицы."}, status_code=400)

    conclusion = render_conclusion(report)
    _LAST["report"] = report
    _LAST["conclusion"] = conclusion

    data = report.to_dict()
    data["conclusion"] = conclusion
    data["labels"] = {"kind": KIND_RU, "severity": SEV_RU}
    return JSONResponse(data)


@app.get("/api/export")
def export_docx():
    """Выгрузка итогового заключения в Word по последнему разбору."""
    report = _LAST.get("report")
    if report is None:
        return JSONResponse({"error": "Сначала выполните анализ."}, status_code=400)
    blob = build_docx(report, _LAST.get("conclusion", ""))
    name = "zakluchenie_" + report.after_doc.replace(".docx", "") + ".docx"
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{name}"'})


PAGE = """
<!doctype html><meta charset="utf-8">
<title>Анализ организационной структуры и функционала</title>
<style>
:root{--bg:#eef1f1;--card:#fff;--ink:#0f1b1d;--mut:#5a6a6c;--line:#c8d2d1;--acc:#0b6f80;
--hi:#9b3520;--hibg:#f6e3dd;--md:#8a6510;--mdbg:#f2e8cf;--ok:#2e6b45;--okbg:#e0ece4}
@media(prefers-color-scheme:dark){:root{--bg:#0b1315;--card:#131f21;--ink:#e4edec;--mut:#93a6a7;
--line:#2a3a3d;--acc:#48b9cc;--hi:#e2785c;--hibg:#33201b;--md:#d7ae4e;--mdbg:#2c2517;--ok:#6fc08f;--okbg:#182e22}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,sans-serif;padding:24px 18px 60px}
.wrap{max-width:1000px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--mut);margin:0 0 22px;font-size:14px}
.panel{background:var(--card);border:1px solid var(--line);padding:16px 18px;margin-bottom:18px}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:end}
label{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin-bottom:5px}
input[type=file]{font:inherit;max-width:100%}
button{font:inherit;font-weight:600;background:var(--acc);color:#fff;border:0;padding:10px 20px;cursor:pointer}
button.ghost{background:transparent;color:var(--acc);border:1px solid var(--acc)}
button:disabled{opacity:.55;cursor:default}
.stats{display:flex;gap:1px;background:var(--line);border:1px solid var(--line);flex-wrap:wrap}
.stat{background:var(--card);padding:11px 16px;flex:1 1 130px}
.stat b{display:block;font-size:23px;line-height:1.2}
.stat span{font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.units{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.u{border:1px solid var(--line);padding:6px 11px;font-size:13px}
.u.new{border-color:var(--ok);background:var(--okbg);color:var(--ok);font-weight:600}
.f{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--line);padding:13px 16px;margin-bottom:9px}
.f.high{border-left-color:var(--hi)} .f.medium{border-left-color:var(--md)}
.f h3{margin:0 0 4px;font-size:15.5px}
.f .meta{font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;margin-bottom:7px}
.f p{margin:0 0 9px;color:var(--mut);font-size:14px}
.src{font-size:13px;border-top:1px dashed var(--line);padding-top:7px;margin-top:7px}
.src b{color:var(--acc);font-family:ui-monospace,Consolas,monospace;font-size:12px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 12px}
.tab{border:1px solid var(--line);background:var(--card);padding:6px 12px;font-size:13px;cursor:pointer}
.tab.on{background:var(--acc);color:#fff;border-color:var(--acc)}
pre.conc{white-space:pre-wrap;font:14px/1.6 "Segoe UI",system-ui,sans-serif;margin:0}
.mode{font-size:12px;color:var(--mut)}
.vf{margin:8px 0;padding:8px 11px;background:var(--okbg);color:var(--ok);font-size:13px;border-left:3px solid var(--ok)}
.vf.confirmed_lost{background:var(--hibg);color:var(--hi);border-left-color:var(--hi)}
.vf.uncertain{background:var(--mdbg);color:var(--md);border-left-color:var(--md)}
.vf details{margin-top:6px}
.vf summary{cursor:pointer;font-size:12px;opacity:.85}
.tc{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;margin-top:5px;color:var(--mut);line-height:1.45}
.tc b{color:var(--acc)}
</style>
<div class="wrap">
<a href="/" style="color:var(--acc);font-size:13px;text-decoration:none">← на главную</a>
<h1>Анализ организационной структуры и функционала</h1>
<p class="sub">Сравнение комплектов «до» и «после» реорганизации: потеря функций, дублирование, конфликт интересов — со ссылкой на пункт документа.</p>

<div class="panel">
  <div class="row">
    <div><label>Комплект «до»</label><input type="file" id="before" accept=".docx"></div>
    <div><label>Комплект «после»</label><input type="file" id="after" accept=".docx"></div>
    <button id="go">Сравнить</button>
    <button id="demo" class="ghost">Контрольный комплект</button>
  </div>
</div>

<div id="out"></div>
</div>
<script>
const $=s=>document.querySelector(s);
let data=null, filter='all';

async function analyze(useSample){
  const fd=new FormData();
  if(!useSample){
    if($('#before').files[0]) fd.append('before',$('#before').files[0]);
    if($('#after').files[0]) fd.append('after',$('#after').files[0]);
  }
  $('#out').innerHTML='<div class="panel">Анализирую документы…</div>';
  $('#go').disabled=$('#demo').disabled=true;
  try{
    const r=await fetch('/api/analyze',{method:'POST',body:fd});
    data=await r.json(); render();
  }catch(e){ $('#out').innerHTML='<div class="panel">Ошибка: '+e.message+'</div>'; }
  $('#go').disabled=$('#demo').disabled=false;
}

function count(kind){ return data.findings.filter(f=>f.kind===kind).length; }

function render(){
  const L=data.labels, before=data.units_before.map(u=>u.code);
  const units=data.units_after.map(u=>
    `<span class="u ${before.includes(u.code)?'':'new'}">${u.code} · функций ${u.functions.length}</span>`).join('');
  const kinds=['all','function_lost','false_positive','duplication','function_moved','function_generalized','unit_created'];
  const tabs=kinds.map(k=>`<button class="tab ${filter===k?'on':''}" data-k="${k}">${
    k==='all'?'Все выводы ('+data.findings.length+')':(L.kind[k]||k)+' ('+count(k)+')'}</button>`).join('');

  const list=data.findings.filter(f=>filter==='all'||f.kind===filter).map(f=>`
    <div class="f ${f.severity}">
      <div class="meta">${L.kind[f.kind]||f.kind} · риск ${L.severity[f.severity]} · уверенность ${f.confidence}</div>
      <h3>${f.title}</h3><p>${f.detail}</p>
      ${f.verification?`<div class="vf ${f.verification.verdict}">Агент-верификатор: ${f.verification.verdict_ru}
        ${f.verification.evidence_cite?' · '+f.verification.evidence_cite:''}
        ${f.verification.trace.length?`<details><summary>показать работу агента (${f.verification.trace.length} вызова инструментов)</summary>
          ${f.verification.trace.map((t,i)=>`<div class="tc"><b>${i+1}. ${t.tool}</b>(${JSON.stringify(t.args).slice(0,150)})
          <span>→ ${String(t.result).slice(0,220)}…</span></div>`).join('')}</details>`:''}
      </div>`:''}
      ${f.sources.map(s=>`<div class="src"><b>${s.cite}</b> — ${s.quote.slice(0,260)}</div>`).join('')}
    </div>`).join('') || '<div class="panel">Ничего не найдено.</div>';

  $('#out').innerHTML=`
    <div class="stats">
      <div class="stat"><b>${data.units_after.length}</b><span>подразделений после</span></div>
      <div class="stat"><b>${count('unit_created')}</b><span>создано</span></div>
      <div class="stat"><b>${count('function_lost')}</b><span>возможных потерь</span></div>
      <div class="stat"><b>${count('duplication')}</b><span>дублирований</span></div>
      <div class="stat"><b>${count('function_moved')}</b><span>передано</span></div>
      <div class="stat"><b>${count('false_positive')}</b><span>снято агентом</span></div>
    </div>
    <div class="units">${units}</div>
    <div class="panel" style="margin-top:18px"><pre class="conc">${data.conclusion}</pre>
      <p class="mode" style="margin:12px 0 0">Режим сопоставления: ${data.mode}. Документы: ${data.before_doc} → ${data.after_doc}</p></div>
    <div class="tabs">${tabs}</div>
    ${list}`;

  document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{filter=t.dataset.k;render();});
}

$('#go').onclick=()=>analyze(false);
$('#demo').onclick=()=>analyze(true);
</script>
"""
