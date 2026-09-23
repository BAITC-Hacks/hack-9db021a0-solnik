"""Сопоставление комплектов «до» и «после»: потери, дублирование, конфликты.

Каждый вывод обязан нести источник — документ и пункт (ТЗ, must-have 4) —
и уровень уверенности. Ничего, что не подтверждено текстом, сюда не попадает
(ТЗ, раздел «Ограничения»).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict

from .agent import DocumentTools, verify_loss
from .align import Similarity, THRESHOLDS
from .recommend import attach as attach_recommendations
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
    verification: dict | None = None   # решение агента-верификатора
    recommendation: str | None = None  # предложение по устранению пересечения

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


def _after_pool(after: dict[str, Unit], after_clauses) -> tuple[list[str], list[tuple[str, object]]]:
    """Все пункты комплекта «после» плюс отметка, чьей функцией пункт является.

    Искать соответствие только среди функций директоров нельзя: функция могла
    переехать в общий раздел — например, к обязанностям работников блока.
    Тогда она никуда не потерялась, и помечать её потерей неверно.
    """
    owner: dict[str, str] = {}
    for code, unit in after.items():
        for fn in unit.functions:
            owner[fn.number] = code

    texts, meta = [], []
    for c in after_clauses:
        if not c.number or len(c.text) < 12:
            continue
        texts.append(c.text)
        meta.append((owner.get(c.number, ""), c))
    return texts, meta


def compare_functions(before: dict[str, Unit], after: dict[str, Unit],
                      after_clauses=None) -> tuple[list[Finding], str]:
    """Потеря функции — функция из «до» без достаточно близкой пары в «после».

    Возвращает выводы и фактический режим сопоставления (embeddings / lexical),
    чтобы в отчёте было видно, на чём именно посчитано.
    """
    b_texts, b_meta = _flatten(before)
    if after_clauses:
        a_texts, a_meta = _after_pool(after, after_clauses)
    else:
        a_texts, a_meta = _flatten(after)
    if not b_texts or not a_texts:
        return [], "lexical"

    sim = Similarity(b_texts, a_texts)
    th = THRESHOLDS[sim.mode]
    findings: list[Finding] = []

    # Пункт с тем же адресом и тем же текстом в комплекте «после» означает,
    # что формулировка не менялась. Нужно, чтобы сравнение документа с самим
    # собой не выдавало мнимых передач функций.
    unchanged = {(c.cite, c.text) for _, c in a_meta}

    for i, (b_code, b_fn) in enumerate(b_meta):
        if (b_fn.cite, b_fn.text) in unchanged:
            continue
        j, score = sim.best_for_left(i)
        if j < 0:
            continue
        a_code, a_fn = a_meta[j]

        if score >= th["match"]:
            # тот же самый пункт того же документа — изменения нет
            if a_fn.cite == b_fn.cite:
                continue
            if a_code and a_code != b_code:            # функция ушла в другое подразделение
                findings.append(Finding(
                    kind="function_moved", severity="medium",
                    title=f"Функция перешла из {b_code} в {a_code}",
                    detail=f"«{b_fn.text[:150]}» — в новой редакции закреплена за {a_code}. "
                           f"Проверить, что передача зафиксирована распорядительным документом.",
                    confidence=round(score, 2),
                    sources=[Source("до", b_fn.cite, b_fn.text),
                             Source("после", a_fn.cite, a_fn.text)]))
            elif not a_code:                           # переехала в общий раздел документа
                findings.append(Finding(
                    kind="function_generalized", severity="info",
                    title=f"Функция {b_code} перенесена в общий раздел",
                    detail=f"В новой редакции формулировка закреплена не за подразделением, "
                           f"а в общем пункте {a_fn.cite}. Ответственность стала общей — "
                           f"проверить, что это соответствует замыслу реорганизации.",
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


# Роли, которые подразделение может выполнять, и признаки этих ролей в тексте.
# Формулировки положений устойчивы, поэтому роль опознаётся по корню слова.
ROLE_MARKERS = {
    "проведение проверок": ("проводит проверк", "проводят проверк", "руководство курируемых",
                            "плановых и внеплановых", "аудиторских задани", "выполнение плана работ"),
    # Намеренно узкие формулировки: «контроль качества выполненных работ» —
    # это не оценка качества самого аудита, и конфликтом не является.
    "оценка качества аудита": ("качества деятельности внутреннего аудита",
                               "качества работы внутреннего аудита",
                               "контроля качества аудита",
                               "программу оценки и повышения качества",
                               "программы оценки и повышения качества",
                               "мониторинг качества деятельности"),
    "разработка методологии": ("разрабатывает методическ", "актуализирует внд",
                               "разрабатывает и внедряет программу",
                               "методологическое обеспечение"),
    "распоряжение кадрами": ("поощрению и наложению взысканий", "профессионального уровня работников"),
}

# Пары ролей, совмещение которых в одном подразделении создаёт конфликт интересов.
INCOMPATIBLE_ROLES = [
    ("проведение проверок", "оценка качества аудита",
     "подразделение одновременно проводит проверки и оценивает их качество — "
     "оценка перестаёт быть независимой"),
    ("разработка методологии", "оценка качества аудита",
     "подразделение само разрабатывает методологию и само же проверяет её соблюдение — "
     "контроль замыкается на разработчика"),
]


def _roles_of(unit: Unit) -> dict[str, object]:
    """Какие роли подразделение выполняет и каким пунктом это подтверждается."""
    found: dict[str, object] = {}
    for fn in unit.functions:
        low = fn.text.lower()
        for role, markers in ROLE_MARKERS.items():
            if role in found:
                continue
            if any(m in low for m in markers):
                found[role] = fn
    return found


def find_conflicts(after: dict[str, Unit]) -> list[Finding]:
    """Конфликт интересов — совмещение несовместимых ролей в одном подразделении."""
    findings: list[Finding] = []
    for code, unit in after.items():
        roles = _roles_of(unit)
        for role_a, role_b, reason in INCOMPATIBLE_ROLES:
            if role_a in roles and role_b in roles:
                fn_a, fn_b = roles[role_a], roles[role_b]
                findings.append(Finding(
                    kind="conflict_of_interest", severity="high",
                    title=f"Потенциальный конфликт интересов в {code}",
                    detail=f"{unit.name}: {reason}. Совмещаются роли «{role_a}» и «{role_b}». "
                           f"Требуется разделение ролей или независимая оценка.",
                    confidence=0.7,
                    sources=[Source(role_a, fn_a.cite, fn_a.text),
                             Source(role_b, fn_b.cite, fn_b.text)]))
    return findings


VERDICT_RU = {
    "confirmed_lost": "потеря подтверждена агентом",
    "found_elsewhere": "функция найдена в другом пункте — ложная тревога",
    "uncertain": "агент не смог подтвердить — нужна проверка человеком",
}


def verify_findings(findings: list[Finding], after_clauses, after_units,
                    limit: int = 12, workers: int = 6) -> list[Finding]:
    """Второй круг: агент ищет подтверждение каждой возможной потере.

    Подтверждённые потери остаются высоким риском, найденные в другом месте
    понижаются до справочных, неопределённые честно помечаются как требующие
    человека. Ничего не удаляется: пользователь видит и вывод, и его проверку.
    """
    tools = DocumentTools(after_clauses, after_units)
    targets = [f for f in findings if f.kind == "function_lost"][:limit]
    if not targets:
        return findings

    def check(f: Finding):
        quote = f.sources[0].quote if f.sources else f.title
        unit = f.title.split()[-1]
        return f, verify_loss(quote, unit, tools)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f, v in pool.map(check, targets):
            if v is None:
                continue
            f.verification = v.to_dict()
            f.verification["verdict_ru"] = VERDICT_RU.get(v.verdict, v.verdict)
            if v.verdict == "found_elsewhere":
                f.kind = "false_positive"
                f.severity = "info"
                f.title = f.title.replace("Возможная потеря функции",
                                          "Снято агентом: функция сохранена")
                f.detail = (f"Первичное сопоставление отметило возможную потерю, но агент нашёл "
                            f"функцию в комплекте «после»: {v.evidence_cite}. {v.reason}")
                if v.evidence_cite:
                    f.sources.append(Source("подтверждение агента", v.evidence_cite, v.reason))
            elif v.verdict == "confirmed_lost":
                f.severity = "high"
                f.detail += f" Проверено агентом: {v.reason}"
            else:
                f.severity = "medium"
                f.detail += f" Агент не смог подтвердить: {v.reason}"
    return findings


def run(before_path: str, after_path: str, verify: bool = True,
        before_name: str | None = None, after_name: str | None = None) -> Report:
    before, before_clauses = build(before_path, before_name)
    after, after_clauses = build(after_path, after_name)

    findings = compare_units(before, after)
    fn_findings, mode = compare_functions(before, after, after_clauses)
    findings += fn_findings
    findings += find_duplication(after)
    findings += find_conflicts(after)

    if verify:
        findings = verify_findings(findings, after_clauses, after)
        findings = attach_recommendations(findings)

    order = {"high": 0, "medium": 1, "info": 2}
    findings.sort(key=lambda f: (order[f.severity], -f.confidence))

    return Report(
        before_doc=before_name or before_path.split("/")[-1],
        after_doc=after_name or after_path.split("/")[-1],
        mode=mode,
        units_before=[u.to_dict() for u in before.values()],
        units_after=[u.to_dict() for u in after.values()],
        findings=findings)


if __name__ == "__main__":
    import sys
    rep = run("data/samples/polozhenie_red8.docx", "data/samples/polozhenie_red9.docx",
              verify="--no-verify" not in sys.argv)
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
