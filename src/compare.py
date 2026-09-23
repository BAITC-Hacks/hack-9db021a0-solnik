"""Сопоставление комплектов «до» и «после»: потери, дублирование, конфликты.

Каждый вывод обязан нести источник — документ и пункт (ТЗ, must-have 4) —
и уровень уверенности. Ничего, что не подтверждено текстом, сюда не попадает
(ТЗ, раздел «Ограничения»).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .align import Similarity, THRESHOLDS
from .orgmap import Unit, build


@dataclass
class Source:
    label: str
    cite: str
    quote: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    kind: str          # unit_created | unit_kept | unit_removed | function_lost |
                       # function_moved | duplication | conflict_of_interest
    severity: str      # high | medium | info
    title: str
    detail: str
    confidence: float
    sources: list[Source] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sources"] = [s.to_dict() for s in self.sources]
        return d


@dataclass
class Report:
    before_doc: str
    after_doc: str
    mode: str
    units_before: list[dict]
    units_after: list[dict]
    findings: list[Finding]

    def to_dict(self) -> dict:
        return {"before_doc": self.before_doc, "after_doc": self.after_doc,
                "mode": self.mode, "units_before": self.units_before,
                "units_after": self.units_after,
                "findings": [f.to_dict() for f in self.findings]}

    def by_kind(self, kind: str) -> list[Finding]:
        return [f for f in self.findings if f.kind == kind]


def _flatten(units: dict[str, Unit]) -> tuple[list[str], list[tuple[str, object]]]:
    """Все функции всех подразделений одним списком: тексты и (код, функция)."""
    texts, meta = [], []
    for code, unit in units.items():
        for fn in unit.functions:
            texts.append(fn.text)
            meta.append((code, fn))
    return texts, meta


def compare_units(before: dict[str, Unit], after: dict[str, Unit]) -> list[Finding]:
    findings: list[Finding] = []

    for code, unit in after.items():
        if code not in before:
            findings.append(Finding(
                kind="unit_created", severity="info",
                title=f"Создано подразделение {code}",
                detail=f"{unit.name} отсутствует в комплекте «до» и появляется в комплекте «после».",
                confidence=1.0,
                sources=[Source("после", unit.cite, unit.name)]))

    for code, unit in before.items():
        if code not in after:
            findings.append(Finding(
                kind="unit_removed", severity="high",
                title=f"Подразделение {code} отсутствует в новой структуре",
                detail=f"{unit.name} есть в комплекте «до», но не заявлено в составе «после». "
                       f"Требуется проверить, кому переданы его функции.",
                confidence=1.0,
                sources=[Source("до", unit.cite, unit.name)]))
        else:
            findings.append(Finding(
                kind="unit_kept", severity="info",
                title=f"Подразделение {code} сохранено",
                detail=f"{unit.name} присутствует в обоих комплектах.",
                confidence=1.0,
                sources=[Source("до", unit.cite, unit.name),
                         Source("после", after[code].cite, after[code].name)]))
    return findings


def compare_functions(before: dict[str, Unit], after: dict[str, Unit]) -> tuple[list[Finding], str]:
    """Потеря функции — функция из «до» без достаточно близкой пары в «после».

    Возвращает выводы и фактический режим сопоставления (embeddings / lexical),
    чтобы в отчёте было видно, на чём именно посчитано.
    """
    b_texts, b_meta = _flatten(before)
    a_texts, a_meta = _flatten(after)
    if not b_texts or not a_texts:
        return [], "lexical"

    sim = Similarity(b_texts, a_texts)
    th = THRESHOLDS[sim.mode]
    findings: list[Finding] = []

    for i, (b_code, b_fn) in enumerate(b_meta):
        j, score = sim.best_for_left(i)
        if j < 0:
            continue
        a_code, a_fn = a_meta[j]

        if score >= th["match"]:
            if a_code != b_code:                       # функция ушла в другое подразделение
                findings.append(Finding(
                    kind="function_moved", severity="medium",
                    title=f"Функция перешла из {b_code} в {a_code}",
                    detail=f"«{b_fn.text[:150]}» — в новой редакции закреплена за {a_code}. "
                           f"Проверить, что передача зафиксирована распорядительным документом.",
                    confidence=round(score, 2),
                    sources=[Source("до", b_fn.cite, b_fn.text),
                             Source("после", a_fn.cite, a_fn.text)]))
            continue

        severity = "high" if score < th["weak"] else "medium"
        detail = (f"Функция подразделения {b_code} не находит соответствия в комплекте «после». "
                  f"Ближайшая формулировка — {a_fn.cite} (близость {score:.2f}), "
                  f"этого недостаточно для вывода о сохранении функции.")
        findings.append(Finding(
            kind="function_lost", severity=severity,
            title=f"Возможная потеря функции у {b_code}",
            detail=detail,
            confidence=round(1.0 - score, 2),
            sources=[Source("до", b_fn.cite, b_fn.text),
                     Source("после (ближайшее)", a_fn.cite, a_fn.text)]))
    return findings, sim.mode


def find_duplication(after: dict[str, Unit]) -> list[Finding]:
    """Дублирование — близкие функции у разных подразделений новой структуры."""
    texts, meta = _flatten(after)
    if len(texts) < 2:
        return []

    sim = Similarity(texts, texts)
    th = THRESHOLDS[sim.mode]["duplicate"]
    findings, seen = [], set()

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            code_i, fn_i = meta[i]
            code_j, fn_j = meta[j]
            if code_i == code_j:
                continue
            # Один и тот же пункт, закреплённый сразу за двумя подразделениями
            # («Директоры ДИТААД и ДОА: ...»), — это общая функция, а не дубль.
            if fn_i.cite == fn_j.cite:
                continue
            score = sim.score(i, j)
            if score < th:
                continue
            key = tuple(sorted((fn_i.cite, fn_j.cite)))
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding(
                kind="duplication", severity="medium",
                title=f"Дублирование функции: {code_i} и {code_j}",
                detail=f"Схожие формулировки закреплены за двумя подразделениями "
                       f"(близость {score:.2f}). Требуется разграничить зоны ответственности.",
                confidence=round(score, 2),
                sources=[Source(code_i, fn_i.cite, fn_i.text),
                         Source(code_j, fn_j.cite, fn_j.text)]))
    return findings


# Признаки несовместимых ролей у одного подразделения: (метка, ключевые слова)
CONFLICT_ROLES = [
    ("выполнение проверок", ("провед", "проверк", "аудиторск", "задани")),
    ("контроль качества своей работы", ("контрол", "качеств", "оценк", "программ")),
]


def find_conflicts(after: dict[str, Unit]) -> list[Finding]:
    """Конфликт интересов — одно подразделение и исполняет, и оценивает качество."""
    findings: list[Finding] = []
    for code, unit in after.items():
        hits: dict[str, object] = {}
        for role, keys in CONFLICT_ROLES:
            for fn in unit.functions:
                low = fn.text.lower()
                if sum(k in low for k in keys) >= 2:
                    hits.setdefault(role, fn)
                    break
        if len(hits) == len(CONFLICT_ROLES):
            srcs = [Source(role, fn.cite, fn.text) for role, fn in hits.items()]
            findings.append(Finding(
                kind="conflict_of_interest", severity="high",
                title=f"Потенциальный конфликт интересов в {code}",
                detail=f"{unit.name} одновременно выполняет проверки и оценивает качество работы. "
                       f"Совмещение исполнения и контроля требует разделения ролей.",
                confidence=0.6,
                sources=srcs))
    return findings


def run(before_path: str, after_path: str) -> Report:
    before, _ = build(before_path)
    after, _ = build(after_path)

    findings = compare_units(before, after)
    fn_findings, mode = compare_functions(before, after)
    findings += fn_findings
    findings += find_duplication(after)
    findings += find_conflicts(after)

    order = {"high": 0, "medium": 1, "info": 2}
    findings.sort(key=lambda f: (order[f.severity], -f.confidence))

    return Report(
        before_doc=before_path.split("/")[-1],
        after_doc=after_path.split("/")[-1],
        mode=mode,
        units_before=[u.to_dict() for u in before.values()],
        units_after=[u.to_dict() for u in after.values()],
        findings=findings)


if __name__ == "__main__":
    rep = run("data/samples/polozhenie_red8.docx", "data/samples/polozhenie_red9.docx")
    print(f"режим сопоставления: {rep.mode}")
    counts: dict[str, int] = {}
    for f in rep.findings:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    print("итого выводов:", len(rep.findings), counts)
    for f in rep.findings[:12]:
        print(f"\n[{f.severity:6s}] {f.title}  (уверенность {f.confidence})")
        print("   ", f.detail[:170])
        for s in f.sources[:2]:
            print(f"    источник [{s.label}] {s.cite}: {s.quote[:100]}")
