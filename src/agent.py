"""Агент-верификатор: перепроверяет находки, обращаясь к документам инструментами.

Зачем отдельный агент. Сопоставление по близости даёт кандидатов, но близость
не понимает, что функция могла переехать в другой раздел, быть переформулирована
или поглощена более общей формулировкой. Поэтому каждый кандидат на потерю
проходит второй круг: модель сама ищет подтверждение в комплекте «после»,
вызывая инструменты, и выносит решение с обязательной ссылкой на пункт.

Агент не может сослаться на несуществующий пункт: цитату он получает только
из инструмента, а решение без ссылки отбрасывается на проверке.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict

from .config import load_env  # noqa: F401
from .align import Index
from .docparse import Clause
from .orgmap import Unit

VERDICTS = {"confirmed_lost", "found_elsewhere", "uncertain"}


@dataclass
class ToolCall:
    tool: str
    args: dict
    result: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verification:
    verdict: str
    reason: str
    evidence_cite: str
    trace: list[ToolCall] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["trace"] = [t.to_dict() for t in self.trace]
        return d


class DocumentTools:
    """Инструменты агента. Единственный источник цитат для модели."""

    def __init__(self, clauses: list[Clause], units: dict[str, Unit]):
        self.clauses = clauses
        self.units = units
        self._texts = [c.text for c in clauses]
        self.index = Index(self._texts)      # векторы считаются один раз на документ

    def search_clauses(self, query: str, limit: int = 4) -> str:
        out = []
        for j, score in self.index.search(query, max(1, min(int(limit), 6))):
            c = self.clauses[j]
            out.append({"cite": c.cite, "score": round(score, 2), "text": c.text[:400]})
        return json.dumps(out, ensure_ascii=False)

    def get_clause(self, number: str) -> str:
        for c in self.clauses:
            if c.number == number:
                return json.dumps({"cite": c.cite, "text": c.text}, ensure_ascii=False)
        return json.dumps({"error": f"пункт {number} не найден"}, ensure_ascii=False)

    def list_units(self) -> str:
        data = [{"code": u.code, "name": u.name, "functions": len(u.functions)}
                for u in self.units.values()]
        return json.dumps(data, ensure_ascii=False)

    def call(self, name: str, args: dict) -> str:
        if name == "search_clauses":
            return self.search_clauses(args.get("query", ""), int(args.get("limit", 4)))
        if name == "get_clause":
            return self.get_clause(str(args.get("number", "")))
        if name == "list_units":
            return self.list_units()
        return json.dumps({"error": f"неизвестный инструмент {name}"}, ensure_ascii=False)


TOOL_SCHEMA = [
    {"type": "function", "function": {
        "name": "search_clauses",
        "description": "Найти в комплекте «после» пункты, близкие по смыслу к запросу.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "формулировка функции"},
            "limit": {"type": "integer", "description": "сколько пунктов вернуть, 1-6"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_clause",
        "description": "Получить точный текст пункта по его номеру, например 5.4.3.",
        "parameters": {"type": "object", "properties": {
            "number": {"type": "string"}}, "required": ["number"]}}},
    {"type": "function", "function": {
        "name": "list_units",
        "description": "Список подразделений новой структуры и число их функций.",
        "parameters": {"type": "object", "properties": {}}}},
]

SYSTEM = """Ты проверяешь вывод о возможной потере функции при реорганизации.

Дана функция из комплекта «до». Нужно установить, сохранилась ли она в комплекте
«после» — возможно, в другом подразделении, другом разделе или в другой
формулировке. Используй инструменты, чтобы найти подтверждение в тексте.

Правила:
- Опирайся только на текст, полученный инструментами. Не придумывай пункты.
- Сделай минимум один поиск, прежде чем решать.
- Если нашёл функцию — verdict "found_elsewhere" и обязательно укажи cite найденного пункта.
- Если убедился, что соответствия нет — verdict "confirmed_lost".
- Если данных не хватает — verdict "uncertain". Это нормальный ответ, лучше него не выдумывать.

Ответь вызовом функции submit_verdict."""

SUBMIT_SCHEMA = {"type": "function", "function": {
    "name": "submit_verdict",
    "description": "Вынести решение по проверяемой функции.",
    "parameters": {"type": "object", "properties": {
        "verdict": {"type": "string", "enum": sorted(VERDICTS)},
        "reason": {"type": "string", "description": "1-2 предложения по-русски"},
        "evidence_cite": {"type": "string",
                          "description": "пункт-подтверждение, пусто если его нет"}},
        "required": ["verdict", "reason"]}}}


def verify_loss(function_text: str, unit_code: str, tools: DocumentTools,
                max_steps: int = 4) -> Verification | None:
    """Один цикл агента: поиск по инструментам -> решение."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.getenv("OPENAI_MODEL", "gpt-5")
    except Exception:
        return None

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content":
         f"Подразделение «до»: {unit_code}\nФункция: {function_text}\n"
         f"Проверь, сохранилась ли эта функция в комплекте «после»."},
    ]
    trace: list[ToolCall] = []

    for _ in range(max_steps):
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages,
                tools=TOOL_SCHEMA + [SUBMIT_SCHEMA])
        except Exception:
            return None

        msg = resp.choices[0].message
        calls = msg.tool_calls or []
        if not calls:
            return Verification("uncertain", (msg.content or "").strip()[:300], "", trace)

        messages.append(msg.model_dump(exclude_none=True))
        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if name == "submit_verdict":
                verdict = args.get("verdict", "uncertain")
                if verdict not in VERDICTS:
                    verdict = "uncertain"
                cite = (args.get("evidence_cite") or "").strip()
                # Решение «функция нашлась» без ссылки на пункт не принимается.
                if verdict == "found_elsewhere" and not cite:
                    verdict = "uncertain"
                return Verification(verdict, (args.get("reason") or "").strip(), cite, trace)

            result = tools.call(name, args)
            trace.append(ToolCall(name, args, result[:500]))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return Verification("uncertain", "Агент не завершил проверку за отведённые шаги.", "", trace)
