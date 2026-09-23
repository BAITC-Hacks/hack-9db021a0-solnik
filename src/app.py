"""Веб-интерфейс: загрузка комплектов «до» и «после», просмотр выводов.

Артефакты по ТЗ: интерфейс для загрузки документов и просмотра результатов.

Защитные меры для загрузок:
  * лимит размера файла и лимит распакованного размера — .docx это zip-архив,
    и без второго лимита маленький файл может распаковаться в гигабайты;
  * временные файлы удаляются сразу после разбора;
  * каждый разбор получает свой идентификатор, и выгрузка возвращает
    заключение только по нему — чужие результаты недоступны;
  * имя файла в заголовке ответа очищается от служебных символов.
"""
from __future__ import annotations

import os
import re
import tempfile
import threading
import traceback
import uuid
import zipfile
from collections import OrderedDict
from urllib.parse import quote

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .app_page import APP as WORKSPACE_PAGE
from .compare import run
from .export import build_docx
from .pages import MOCK_PREVIEW, render_landing
from .report import render_conclusion

app = FastAPI(title="OrgTrace — анализ организационной структуры и функционала")
app.mount("/static", StaticFiles(directory="static"), name="static")

SAMPLE_BEFORE = "data/samples/polozhenie_red8.docx"
SAMPLE_AFTER = "data/samples/polozhenie_red9.docx"
SCREENSHOTS = ("static/app-preview.jpg", "static/app-preview.png")

MAX_UPLOAD_BYTES = 20 * 1024 * 1024        # положение с приложениями укладывается с запасом
MAX_UNPACKED_BYTES = 200 * 1024 * 1024     # защита от zip-бомбы
MAX_STORED_REPORTS = 20

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

# Разбор занимает до минуты, поэтому выгрузка берёт готовый результат по
# идентификатору, а не пересчитывает. Хранятся последние результаты.
_reports: "OrderedDict[str, tuple]" = OrderedDict()
_reports_lock = threading.Lock()


class DocumentError(Exception):
    """Понятная пользователю причина, по которой документ не принят."""


def _save(upload: UploadFile) -> str:
    """Проверяет загруженный файл и сохраняет во временную папку."""
    name = upload.filename or "doc.docx"
    if not name.lower().endswith(".docx"):
        raise DocumentError(f"Файл «{name}» не в формате .docx. Сейчас поддерживается Word (.docx).")

    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise DocumentError(f"Файл «{name}» пустой.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError(f"Файл «{name}» больше {MAX_UPLOAD_BYTES // (1024 * 1024)} МБ.")

    fd, path = tempfile.mkstemp(suffix=".docx")
    with os.fdopen(fd, "wb") as f:
        f.write(data)

    try:
        if not zipfile.is_zipfile(path):
            raise DocumentError(f"Файл «{name}» повреждён или не является документом Word.")
        with zipfile.ZipFile(path) as z:
            infos = {i.filename: i for i in z.infolist()}
            if "word/document.xml" not in infos:
                raise DocumentError(f"В файле «{name}» нет текста документа Word.")
            if sum(i.file_size for i in infos.values()) > MAX_UNPACKED_BYTES:
                raise DocumentError(f"Файл «{name}» после распаковки слишком большой.")
    except DocumentError:
        _remove(path)
        raise
    return path


def _remove(path: str | None) -> None:
    if path and path not in (SAMPLE_BEFORE, SAMPLE_AFTER):
        try:
            os.remove(path)
        except OSError:
            pass


def _store(report, conclusion: str) -> str:
    report_id = uuid.uuid4().hex
    with _reports_lock:
        _reports[report_id] = (report, conclusion)
        while len(_reports) > MAX_STORED_REPORTS:
            _reports.popitem(last=False)
    return report_id


def _safe_filename(name: str) -> str:
    """Имя для заголовка Content-Disposition без кавычек и переводов строк."""
    base = os.path.splitext(os.path.basename(name))[0]
    base = re.sub(r"[^\w\-. ]+", "_", base, flags=re.UNICODE).strip() or "report"
    return f"zakluchenie_{base[:80]}.docx"


@app.get("/", response_class=HTMLResponse)
def landing() -> str:
    """Стартовая страница. В рамку подставляется снимок рабочего экрана,
    если он лежит в static/, иначе — встроенный макет интерфейса."""
    shot = next((p for p in SCREENSHOTS if os.path.exists(p)), None)
    if shot:
        preview = f'<img src="/{shot}" alt="Рабочий экран OrgTrace: разбор комплектов документов">'
    else:
        preview = MOCK_PREVIEW
    return render_landing(preview)


@app.get("/app", response_class=HTMLResponse)
def workspace() -> str:
    """Рабочий экран: загрузка комплектов и разбор выводов."""
    return WORKSPACE_PAGE


# Обработчик намеренно синхронный: FastAPI выполняет его в пуле потоков.
# Асинхронный вариант с минутным разбором внутри блокировал бы цикл событий,
# и на время анализа сервер переставал отвечать всем остальным запросам.
@app.post("/api/analyze")
def analyze(before: UploadFile = File(None), after: UploadFile = File(None)):
    before_path = after_path = None
    try:
        try:
            before_path = _save(before) if before else SAMPLE_BEFORE
            after_path = _save(after) if after else SAMPLE_AFTER
        except DocumentError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        # имя для ссылок берём исходное, а не путь во временной папке
        before_name = os.path.basename(before.filename) if before else os.path.basename(SAMPLE_BEFORE)
        after_name = os.path.basename(after.filename) if after else os.path.basename(SAMPLE_AFTER)

        try:
            report = run(before_path, after_path, before_name=before_name, after_name=after_name)
        except Exception:
            traceback.print_exc()
            return JSONResponse(
                {"error": "Не удалось разобрать документы. Проверьте, что это положения "
                          "с нумерацией пунктов, а не сканы или таблицы."}, status_code=400)
    finally:
        _remove(before_path)
        _remove(after_path)

    conclusion = render_conclusion(report)
    data = report.to_dict()
    data["report_id"] = _store(report, conclusion)
    data["conclusion"] = conclusion
    data["labels"] = {"kind": KIND_RU, "severity": SEV_RU}
    return JSONResponse(data)


@app.get("/api/export")
def export_docx(id: str = Query(..., min_length=32, max_length=32)):
    """Выгрузка заключения в Word по идентификатору конкретного разбора."""
    with _reports_lock:
        item = _reports.get(id)
    if item is None:
        return JSONResponse({"error": "Результат не найден — выполните анализ заново."},
                            status_code=404)
    report, conclusion = item
    blob = build_docx(report, conclusion)
    fname = _safe_filename(report.after_doc)
    ascii_name = fname.encode("ascii", "ignore").decode() or "report.docx"
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition":
                 f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(fname)}"})
