"""Карта организации: подразделения, их функции и точные ссылки на пункты.

Извлечение детерминированное — без модели. Причина простая: номер пункта и
принадлежность функции подразделению однозначно заданы нумерацией документа,
и выдумывать здесь нечего. Модель подключается дальше, на семантическом
сопоставлении функций (src/align.py), где она действительно нужна.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from .docparse import Clause, find, parse_docx

# "Департамент операционного аудита (ДОА)" -> ДОА
UNIT_IN_PARENS = re.compile(r"([А-ЯЁA-Z][^()]{8,120}?)\s*\((["
                            r"А-ЯЁA-Z]{2,10})\)")
# "а. Департамент ... (ДНМ)." — элементы перечисления внутри пункта 3.4
LIST_ITEM = re.compile(r"[а-я]\.\s*")
# "Директор ДНМ:" / "Директору ДОА подчиняются" / "Директоры ... ДИТААД и ДОА:"
DIRECTOR_RE = re.compile(r"Директор[ыуа]?\s+(?:департамента\s+)?(.*)", re.I)
CODE_RE = re.compile(r"\b([А-ЯЁ]{2,10})\b")

# Документы бывают на казахском и смешанные: добавляем казахские буквы.
# В казахском порядок слов обратный — «ОАД директоры:», а не «Директор ОАД:»,
# поэтому руководителя ищем по корню слова в любом месте заголовка пункта.
_KZ_UP = "ӘҒҚҢӨҰҮҺІ"
_KZ_LOW = "әғқңөұүһі"
UNIT_IN_PARENS = re.compile(rf"([А-ЯЁA-Z{_KZ_UP}][^()]{{8,120}}?)\s*\(([А-ЯЁA-Z{_KZ_UP}]{{2,10}})\)")
LIST_ITEM = re.compile(rf"(?<![A-Za-zА-Яа-я])[а-я{_KZ_LOW}a-z]\.\s*")
CODE_RE = re.compile(rf"\b([А-ЯЁ{_KZ_UP}]{{2,10}})\b")
DIRECTOR_RE = re.compile(r"директор|director", re.I)   # рус., каз., англ.


@dataclass
class Function:
    text: str
    cite: str
    number: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Unit:
    code: str                 # ДНМ
    name: str                 # Департамент непрерывного мониторинга ...
    cite: str                 # где объявлено
    functions: list[Function] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"code": self.code, "name": self.name, "cite": self.cite,
                "functions": [f.to_dict() for f in self.functions]}


def extract_units(clauses: list[Clause], composition_clause: str = "3.4") -> dict[str, Unit]:
    """Состав подразделений из пункта вида «X состоит из следующих подразделений»."""
    units: dict[str, Unit] = {}
    src = find(clauses, composition_clause)
    if src is None:
        return units

    body = src.text.split(":", 1)[-1]
    for chunk in LIST_ITEM.split(body):
        chunk = chunk.strip(" .;")
        if not chunk:
            continue
        m = UNIT_IN_PARENS.search(chunk)
        if not m:
            continue
        name, code = m.group(1).strip(" .,;"), m.group(2).strip()
        units[code] = Unit(code=code, name=name, cite=src.cite)
    return units


def _norm(s: str) -> str:
    return re.sub(rf"[^а-яёa-z{_KZ_LOW} ]", " ", s.lower())


def _owner_codes(text: str, units: dict[str, "Unit"]) -> list[str]:
    """Чьи функции описывает пункт.

    Руководителя называют то кодом («Директор ДНМ:»), то полным именем
    департамента («Директор департамента непрерывного мониторинга...:»),
    поэтому проверяем оба способа.
    """
    head = text.split(":", 1)[0]
    if not DIRECTOR_RE.search(head):
        return []

    found = [c for c in CODE_RE.findall(head) if c in units]
    if found:
        return found

    head_n = _norm(head)
    for code, unit in units.items():
        words = [w for w in _norm(unit.name).split() if len(w) > 4]
        if words and all(w in head_n for w in words[:4]):
            found.append(code)
    return found


def attach_functions(clauses: list[Clause], units: dict[str, Unit],
                     sections: tuple[str, ...] = ("5",)) -> dict[str, Unit]:
    """Функции подразделения = подпункты пункта, который вводит его руководителя.

    Пример: «5.4. Директор департамента непрерывного мониторинга ...:» — тогда
    все пункты 5.4.N становятся функциями ДНМ со ссылкой на свой номер.
    """

    for c in clauses:
        if not c.number or not any(c.number.startswith(s + ".") or c.number == s
                                   for s in sections):
            continue
        codes = _owner_codes(c.text, units)
        if not codes:
            continue
        prefix = c.number + "."
        children = [x for x in clauses if x.number.startswith(prefix)
                    and x.number.count(".") == c.number.count(".") + 1]
        for code in codes:
            seen = {f.number for f in units[code].functions}
            for ch in children:
                text = ch.text.strip(" ;")
                # Один и тот же пункт может «подвешиваться» к подразделению дважды:
                # в документе есть и «Директор ДНМ:», и «Директор ДНМ обязан...».
                if ch.number in seen or len(text) < 12:
                    continue
                seen.add(ch.number)
                units[code].functions.append(
                    Function(text=text, cite=ch.cite, number=ch.number))
    return units


def build(path: str, doc_name: str | None = None) -> tuple[dict[str, Unit], list[Clause]]:
    clauses = parse_docx(path, doc_name)
    units = extract_units(clauses)
    attach_functions(clauses, units)
    return units, clauses


if __name__ == "__main__":  # быстрая проверка на тестовом комплекте
    for p, label in [("data/samples/polozhenie_red8.docx", "ДО (ред.8)"),
                     ("data/samples/polozhenie_red9.docx", "ПОСЛЕ (ред.9)")]:
        units, _ = build(p)
        print(f"\n=== {label} — подразделений: {len(units)}")
        for u in units.values():
            print(f"  {u.code:8s} {u.name[:58]:58s} функций: {len(u.functions):2d}  [{u.cite}]")
