"""Защиты агента-верификатора, проверяемые без сети поддельным клиентом.

Главное свойство: агент не может сослаться на пункт, который он не получил
через инструменты в этой же проверке, и не может вынести решение, не
обратившись к документу. Это закрывает подмену источника текстом документа.
"""
import json
from types import SimpleNamespace

import pytest

from src import agent
from src.agent import DocumentTools, _collect_cites, _resolve_cite, verify_loss
from src.orgmap import build

AFTER = "data/samples/polozhenie_red9.docx"


def _call(name, args, cid="c1"):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(args)))


def _msg(calls):
    m = SimpleNamespace(tool_calls=calls, content=None)
    m.model_dump = lambda **kw: {"role": "assistant", "content": None}
    return SimpleNamespace(choices=[SimpleNamespace(message=m)])


class FakeClient:
    """Отдаёт заранее заданную последовательность ответов модели."""

    def __init__(self, script):
        self._script = iter(script)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        return next(self._script)


@pytest.fixture(scope="module")
def tools():
    units, clauses = build(AFTER)
    return DocumentTools(clauses, units)


def _run(monkeypatch, tools, script):
    monkeypatch.setattr(agent, "openai_client", lambda: FakeClient(script))
    return verify_loss("использовать конфиденциальную информацию", "ДККМ", tools)


def test_collect_and_resolve_cites():
    seen = {}
    _collect_cites(json.dumps([{"cite": "doc.docx, п. 5.6.2", "text": "x"}]), seen)
    assert _resolve_cite("п. 5.6.2", seen) == "doc.docx, п. 5.6.2"
    assert _resolve_cite("doc.docx, п. 9.9.9", seen) is None
    assert _resolve_cite("", seen) is None


def test_verdict_without_looking_at_document_is_rejected(monkeypatch, tools):
    v = _run(monkeypatch, tools, [
        _msg([_call("submit_verdict", {"verdict": "found_elsewhere", "reason": "есть",
                                       "evidence_cite": "п. 5.6.2"})]),
    ])
    assert v.verdict == "uncertain"


def test_citing_clause_not_retrieved_is_rejected(monkeypatch, tools):
    v = _run(monkeypatch, tools, [
        _msg([_call("get_clause", {"number": "3.4"})]),
        _msg([_call("submit_verdict", {"verdict": "found_elsewhere", "reason": "нашёл",
                                       "evidence_cite": "п. 5.6.2"}, "c2")]),
    ])
    assert v.verdict == "uncertain"
    assert v.evidence_cite == ""


def test_citing_retrieved_clause_is_accepted(monkeypatch, tools):
    v = _run(monkeypatch, tools, [
        _msg([_call("get_clause", {"number": "5.6.2"})]),
        _msg([_call("submit_verdict", {"verdict": "found_elsewhere", "reason": "совпадает",
                                       "evidence_cite": "5.6.2"}, "c2")]),
    ])
    assert v.verdict == "found_elsewhere"
    assert v.evidence_cite.endswith("п. 5.6.2")   # ссылка приведена к полному виду


def test_unknown_verdict_becomes_uncertain(monkeypatch, tools):
    v = _run(monkeypatch, tools, [
        _msg([_call("get_clause", {"number": "5.6.2"})]),
        _msg([_call("submit_verdict", {"verdict": "delete_everything", "reason": "!"}, "c2")]),
    ])
    assert v.verdict == "uncertain"


def test_thresholds_can_be_overridden(monkeypatch):
    from src import align
    monkeypatch.setenv("ORGTRACE_EMBEDDINGS_MATCH", "0.7")
    monkeypatch.setenv("ORGTRACE_LEXICAL_WEAK", "мусор")
    th = align._load_thresholds()
    assert th["embeddings"]["match"] == 0.7
    assert th["lexical"]["weak"] == 0.33          # некорректное значение не ломает разбор


def test_last_step_forces_verdict(monkeypatch, tools):
    """На последнем шаге агенту закрывают поиск и требуют вынести решение."""
    calls_kwargs = []

    class Recording(FakeClient):
        def _create(self, **kw):
            calls_kwargs.append(kw)
            return super()._create(**kw)

    script = [_msg([_call("search_clauses", {"query": "x"}, f"s{i}")]) for i in range(5)]
    script.append(_msg([_call("submit_verdict", {"verdict": "uncertain", "reason": "мало данных"}, "v")]))
    monkeypatch.setattr(agent, "openai_client", lambda: Recording(script))
    v = verify_loss("функция", "ДНМ", tools, max_steps=6)

    assert v.verdict == "uncertain"
    assert "tool_choice" not in calls_kwargs[0]
    assert calls_kwargs[-1]["tool_choice"]["function"]["name"] == "submit_verdict"
