"""Детерминированный движок правил с трассировкой.

Идея: модель заполняет анкету (form), а балл и вердикт считает код.
Правила лежат в JSON, поэтому под новую задачу меняется таблица, а не логика.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

OPS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in b,
    "is_true": lambda a, _: bool(a),
}


@dataclass
class Step:
    rule_id: str
    title: str
    matched: bool
    delta: float
    basis: str
    why: str


@dataclass
class Result:
    subject: str
    base: float
    score: float
    cutoff: float
    verdict: str
    severity: str
    needs_human: bool
    steps: list[Step] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["steps"] = [asdict(s) for s in self.steps]
        return d


def _match(form: dict, cond: dict) -> tuple[bool, str]:
    field_name, op, expected = cond["field"], cond["op"], cond.get("value")
    actual = form.get(field_name)
    ok = OPS[op](actual, expected)
    return ok, f"{field_name}={actual!r} {op} {expected!r}"


def evaluate(form: dict, config: dict, min_confidence: float = 0.6) -> Result:
    """form — заполненная анкета; config — таблица базовых баллов и правил."""
    subject_type = form.get("type", "UNKNOWN")
    base_table = config["base_scores"]
    base = float(base_table.get(subject_type, config.get("base_default", 0.0)))

    score = base
    steps = [Step("base", f"Базовый балл для типа {subject_type}", True, base,
                  config.get("base_basis", ""), f"type={subject_type}")]

    for rule in config["rules"]:
        conds = rule.get("when", [])
        results = [_match(form, c) for c in conds]
        matched = all(ok for ok, _ in results)
        delta = float(rule.get("score", 0.0)) if matched else 0.0
        score += delta
        steps.append(Step(rule["id"], rule["title"], matched, delta,
                          rule.get("basis", ""), "; ".join(w for _, w in results)))

    floor = config.get("min_scores", {}).get(subject_type)
    if floor is not None:
        score = max(score, float(floor))
    score = round(score, 2)

    cutoff = float(config.get("cutoff", 0.0))
    low_conf = float(form.get("confidence", 1.0)) < min_confidence
    if low_conf:
        verdict, severity = "Недостаточно данных — нужен человек", "unknown"
    elif score < cutoff:
        verdict, severity = "Требуется детальная проверка", "stop"
    else:
        verdict, severity = "Детальная проверка не требуется", "ok"

    return Result(str(form.get("id", "—")), base, score, cutoff,
                  verdict, severity, low_conf, steps)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_trace(result: Result) -> str:
    """Человекочитаемая трассировка — её же показываем в интерфейсе."""
    lines = [f"Объект {result.subject}", "-" * 56]
    for s in result.steps:
        if not s.matched and s.delta == 0 and s.rule_id != "base":
            continue
        mark = f"{s.delta:+.2f}" if s.rule_id != "base" else f"{s.delta:.2f}"
        basis = f"  [{s.basis}]" if s.basis else ""
        lines.append(f"  {mark:>6}  {s.title}{basis}")
    lines += ["-" * 56,
              f"  ИТОГ {result.score:.2f} при пороге {result.cutoff:.2f} -> {result.verdict}"]
    return "\n".join(lines)
