"""Разбор организационных документов в пронумерованные пункты.

Главное требование ТЗ (must-have 4): каждый вывод должен ссылаться на документ
и конкретный пункт. Поэтому парсер с самого начала сохраняет номер пункта,
путь по разделам и порядковый индекс — цитата собирается без догадок.

Поддержка: .docx (основной), .pdf и .xlsx подключаются той же схемой Clause.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, asdict

# 1.  / 2.3.1.  / 5.10.  — нумерация пунктов в положениях
NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
# маркеры перечислений внутри пункта: 1) , 2) , -
ENUM_RE = re.compile(r"^(\d+\)|[-–—])\s+(.*)$")

_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'"}


@dataclass
class Clause:
    """Один пункт документа — минимальная единица, на которую можно сослаться."""
    doc: str          # имя документа
    number: str       # "3.4" или "" для ненумерованных абзацев
    text: str         # текст пункта
    section: str      # ближайший раздел верхнего уровня, например "3. Структура..."
    index: int        # порядковый номер абзаца в документе
    items: list[str]  # перечисления внутри пункта (подпункты)

    @property
    def cite(self) -> str:
        return f"{self.doc}, п. {self.number}" if self.number else f"{self.doc}, абз. {self.index}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cite"] = self.cite
        return d


def _raw_paragraphs(path: str) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", " ", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    for ent, ch in _ENTITIES.items():
        xml = xml.replace(ent, ch)
    return [re.sub(r"\s+", " ", p).strip() for p in xml.split("\n")]


def parse_docx(path: str, doc_name: str | None = None) -> list[Clause]:
    doc = doc_name or path.replace("\\", "/").split("/")[-1]
    clauses: list[Clause] = []
    section = ""
    current: Clause | None = None

    for i, para in enumerate(p for p in _raw_paragraphs(path) if p):
        m = NUM_RE.match(para)
        if m:
            number, text = m.group(1), m.group(2).strip()
            if "." not in number:                      # раздел верхнего уровня
                section = f"{number}. {text}"
            current = Clause(doc, number, text, section, i, [])
            clauses.append(current)
            continue

        e = ENUM_RE.match(para)
        if e and current is not None:                  # подпункт продолжает пункт
            current.items.append(e.group(2).strip())
            continue

        if current is not None and len(para) > 1:      # продолжение того же пункта
            current.text = f"{current.text} {para}".strip()
        else:
            clauses.append(Clause(doc, "", para, section, i, []))
            current = None

    return clauses


def find(clauses: list[Clause], number: str) -> Clause | None:
    for c in clauses:
        if c.number == number:
            return c
    return None


def by_section(clauses: list[Clause], prefix: str) -> list[Clause]:
    """Все пункты раздела: by_section(cl, "3") -> 3., 3.1, 3.4.2 ..."""
    return [c for c in clauses if c.number == prefix or c.number.startswith(prefix + ".")]
