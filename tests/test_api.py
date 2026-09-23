"""Тесты HTTP-слоя: приём файлов, изоляция результатов, безопасность заголовков."""
import io
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

from src import app as appmod

client = TestClient(appmod.app)
SAMPLE = "data/samples/polozhenie_red9.docx"


def _upload(name, data):
    return (name, io.BytesIO(data), "application/octet-stream")


def test_pages_render():
    assert client.get("/").status_code == 200
    assert client.get("/app").status_code == 200


def test_rejects_non_docx_extension():
    r = client.post("/api/analyze", files={"before": _upload("a.pdf", b"%PDF"),
                                           "after": _upload("b.pdf", b"%PDF")})
    assert r.status_code == 400
    assert "docx" in r.json()["error"]


def test_rejects_fake_docx():
    r = client.post("/api/analyze", files={"before": _upload("a.docx", b"not a zip"),
                                           "after": _upload("b.docx", b"not a zip")})
    assert r.status_code == 400


def test_rejects_empty_file():
    r = client.post("/api/analyze", files={"before": _upload("a.docx", b""),
                                           "after": _upload("b.docx", b"")})
    assert r.status_code == 400
    assert "пустой" in r.json()["error"]


def test_rejects_oversized_upload(monkeypatch):
    monkeypatch.setattr(appmod, "MAX_UPLOAD_BYTES", 1024)
    big = b"x" * 4096
    r = client.post("/api/analyze", files={"before": _upload("a.docx", big),
                                           "after": _upload("b.docx", big)})
    assert r.status_code == 400
    assert "больше" in r.json()["error"]


def test_rejects_zip_bomb(monkeypatch):
    monkeypatch.setattr(appmod, "MAX_UNPACKED_BYTES", 1000)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document/>" + " " * 100_000)
    data = buf.getvalue()
    r = client.post("/api/analyze", files={"before": _upload("a.docx", data),
                                           "after": _upload("b.docx", data)})
    assert r.status_code == 400
    assert "распаковки" in r.json()["error"]


def test_temp_files_are_removed(monkeypatch):
    created = []
    real_mkstemp = appmod.tempfile.mkstemp

    def spy(*a, **kw):
        fd, path = real_mkstemp(*a, **kw)
        created.append(path)
        return fd, path

    monkeypatch.setattr(appmod.tempfile, "mkstemp", spy)
    with open(SAMPLE, "rb") as f:
        data = f.read()
    r = client.post("/api/analyze", files={"before": _upload("a.docx", data),
                                           "after": _upload("b.docx", data)})
    assert r.status_code == 200
    assert created, "файлы должны были сохраняться во временную папку"
    assert not any(os.path.exists(p) for p in created), "временные файлы не удалены"


def test_export_requires_known_report_id():
    assert client.get("/api/export", params={"id": "0" * 32}).status_code == 404
    assert client.get("/api/export", params={"id": "short"}).status_code == 422
    assert client.get("/api/export").status_code == 422


def test_export_returns_docx_for_own_report():
    r = client.post("/api/analyze")
    assert r.status_code == 200
    report_id = r.json()["report_id"]
    e = client.get("/api/export", params={"id": report_id})
    assert e.status_code == 200
    assert e.content[:2] == b"PK"


@pytest.mark.parametrize("name", ['evil".docx', "a\r\nSet-Cookie: x=1.docx", "../../etc.docx"])
def test_filename_is_sanitized(name):
    safe = appmod._safe_filename(name)
    assert '"' not in safe and "\r" not in safe and "\n" not in safe and "/" not in safe
    assert safe.endswith(".docx")
