"""Рекомендации по устранению пересечений функций.

ТЗ, раздел «Опционально», пункт 3: формирование рекомендаций по перераспределению
функций и устранению выявленных пересечений.

Модель не решает, что записано в документе, — она предлагает, какому из двух
подразделений функция подходит ближе, опираясь на их названия и на текст
пунктов, которые уже извлечены кодом. Если модель недоступна, работает
разбор по названию подразделения: у кого больше общих слов с формулировкой.
"""
from __future__ import annotations

import json
import os

from .align import tokens
from .config import openai_client

SYSTEM = """Ты помогаешь распределить функции между подразделениями после реорганизации.

Дана пара подразделений, у которых одна и та же функция записана дважды.
Предложи, за кем её логичнее закрепить, и одной фразой объясни почему.

Правила:
- Опирайся только на переданные названия подразделений и текст функции.
- Не придумывай функции, которых нет в переданных данных.
- Если по названию выбрать нельзя, поставь unit "обоим" и предложи разграничить
  зоны ответственности вместо выбора одного подразделения.
Ответь строго JSON-массивом вида
[{"id": 0, "unit": "КОД", "reason": "одна фраза"}]."""


def _fallback(pair: dict) -> dict:
    """Без модели: у кого название ближе к формулировке функции."""
    fn_tokens = set(tokens(pair["function"]))
    best, best_score = "обоим", 0
    for code, name in ((pair["code_a"], pair["name_a"]), (pair["code_b"], pair["name_b"])):
        score = len(fn_tokens & set(tokens(name)))
        if score > best_score:
            best, best_score = code, score
    if best_score == 0:
        return {"unit": "обоим",
                "reason": "По названиям подразделений выбор не очевиден — "
                          "требуется разграничить зоны ответственности."}
    return {"unit": best,
            "reason": f"Формулировка ближе к профилю подразделения {best} по его наименованию."}


def recommend(pairs: list[dict], limit: int = 10) -> dict[int, dict]:
    """pairs: [{id, code_a, name_a, code_b, name_b, function}] -> {id: {unit, reason}}."""
    if not pairs:
        return {}
    pairs = pairs[:limit]
    result = {p["id"]: _fallback(p) for p in pairs}

    client = openai_client()
    if client is None:
        return result

    try:
        model = os.getenv("OPENAI_MODEL", "gpt-5")
        payload = [{"id": p["id"],
                    "подразделение_A": f'{p["code_a"]} — {p["name_a"]}',
                    "подразделение_B": f'{p["code_b"]} — {p["name_b"]}',
                    "функция": p["function"][:400]} for p in pairs]
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        items = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), [])
        valid = {p["id"]: {p["code_a"], p["code_b"], "обоим"} for p in pairs}
        for item in items:
            i = item.get("id")
            unit = str(item.get("unit", "")).strip()
            reason = str(item.get("reason", "")).strip()
            # Ответ принимается, только если назван один из этих двух подразделений.
            if i in result and unit in valid.get(i, set()) and reason:
                result[i] = {"unit": unit, "reason": reason}
    except Exception:
        pass
    return result


def attach(findings: list, unit_names: dict[str, str] | None = None) -> list:
    """Добавляет рекомендацию каждому выводу о дублировании.

    unit_names — код подразделения -> полное наименование. Без него модель
    видит только коды и не может судить о профиле подразделения.
    """
    names = unit_names or {}
    dups = [f for f in findings if f.kind == "duplication" and len(f.sources) >= 2]
    if not dups:
        return findings

    pairs = []
    for i, f in enumerate(dups):
        a, b = f.sources[0], f.sources[1]
        pairs.append({"id": i, "code_a": a.label, "name_a": names.get(a.label, a.label),
                      "code_b": b.label, "name_b": names.get(b.label, b.label),
                      "function": a.quote})

    recs = recommend(pairs)
    for i, f in enumerate(dups):
        rec = recs.get(i)
        if not rec:
            continue
        f.recommendation = (
            f"Оставить за {rec['unit']}. {rec['reason']}" if rec["unit"] != "обоим"
            else f"Разграничить зоны ответственности. {rec['reason']}")
    return findings
