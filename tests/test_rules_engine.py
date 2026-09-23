from src.rules_engine import evaluate

CONFIG = {
    "base_scores": {"A": 2.0, "B": 0.9},
    "min_scores": {"B": 0.2},
    "cutoff": 2.0,
    "rules": [
        {"id": "soft", "title": "Ослабленный уровень", "score": -0.6, "basis": "п.1",
         "when": [{"field": "soft_level", "op": "is_true"}]},
        {"id": "modern", "title": "Современные нормы", "score": 1.7, "basis": "п.2",
         "when": [{"field": "year", "op": "gte", "value": 2000}]},
    ],
}


def test_base_only():
    r = evaluate({"id": "1", "type": "A", "year": 1990}, CONFIG)
    assert r.score == 2.0 and r.severity == "ok"


def test_modifier_lowers_below_cutoff():
    r = evaluate({"id": "2", "type": "B", "soft_level": True, "year": 1962}, CONFIG)
    assert r.score == 0.3 and r.severity == "stop"


def test_floor_applied():
    cfg = dict(CONFIG, rules=CONFIG["rules"] + [
        {"id": "x", "title": "Ещё минус", "score": -5.0,
         "when": [{"field": "type", "op": "eq", "value": "B"}]}])
    r = evaluate({"id": "3", "type": "B"}, cfg)
    assert r.score == 0.2


def test_low_confidence_defers_to_human():
    r = evaluate({"id": "4", "type": "A", "year": 2020, "confidence": 0.3}, CONFIG)
    assert r.needs_human and r.severity == "unknown"


def test_trace_records_every_rule():
    r = evaluate({"id": "5", "type": "A", "year": 2020}, CONFIG)
    assert len(r.steps) == 3 and r.steps[0].rule_id == "base"
