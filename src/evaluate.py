"""Проверка на контрольном комплекте: что агент обязан найти и что он нашёл.

ТЗ, раздел «Простая проверка решения»: команда демонстрирует решение на
комплекте, где заранее известны несколько изменений, и проверяется, обнаружил
ли агент эти случаи и указал ли корректные источники.

Запуск:  python -m src.evaluate            (с агентом-верификатором)
         python -m src.evaluate --fast     (без агента, без сети)
"""
from __future__ import annotations

import sys

from .compare import run

BEFORE = "data/samples/polozhenie_red8.docx"
AFTER = "data/samples/polozhenie_red9.docx"

# Контрольные случаи: что известно заранее из сравнения редакций №8 и №9.
EXPECTED = [
    {"name": "Создан департамент ИТ-аудита и анализа данных (ДИТААД)",
     "check": lambda r: any("ДИТААД" in f.title for f in r.by_kind("unit_created")),
     "cite": lambda r: next((f.sources[0].cite for f in r.by_kind("unit_created")
                             if "ДИТААД" in f.title), "")},
    {"name": "Создан департамент операционного аудита (ДОА)",
     "check": lambda r: any("ДОА" in f.title for f in r.by_kind("unit_created")),
     "cite": lambda r: next((f.sources[0].cite for f in r.by_kind("unit_created")
                             if "ДОА" in f.title), "")},
    {"name": "Департамент ДНМ сохранён",
     "check": lambda r: any("ДНМ" in f.title for f in r.by_kind("unit_kept")),
     "cite": lambda r: next((f.sources[0].cite for f in r.by_kind("unit_kept")
                             if "ДНМ" in f.title), "")},
    {"name": "Департамент ДККМ сохранён",
     "check": lambda r: any("ДККМ" in f.title for f in r.by_kind("unit_kept")),
     "cite": lambda r: next((f.sources[0].cite for f in r.by_kind("unit_kept")
                             if "ДККМ" in f.title), "")},
    {"name": "Состав вырос с 2 до 4 подразделений",
     "check": lambda r: len(r.units_before) == 2 and len(r.units_after) == 4,
     "cite": lambda r: r.units_after[0]["cite"] if r.units_after else ""},
    {"name": "Обнаружено перераспределение функций между подразделениями",
     "check": lambda r: len(r.by_kind("function_moved")) > 0,
     "cite": lambda r: (r.by_kind("function_moved")[0].sources[1].cite
                        if r.by_kind("function_moved") else "")},
    {"name": "Обнаружено дублирование функций у разных подразделений",
     "check": lambda r: len(r.by_kind("duplication")) > 0,
     "cite": lambda r: (r.by_kind("duplication")[0].sources[0].cite
                        if r.by_kind("duplication") else "")},
]


def main() -> int:
    verify = "--fast" not in sys.argv
    report = run(BEFORE, AFTER, verify=verify)

    print(f"Комплект: {report.before_doc} -> {report.after_doc}")
    print(f"Режим сопоставления: {report.mode}; "
          f"агент-верификатор: {'включён' if verify else 'отключён'}\n")

    print(f"{'КОНТРОЛЬНЫЙ СЛУЧАЙ':62s} {'РЕЗУЛЬТАТ':10s} ИСТОЧНИК")
    print("-" * 110)
    passed = 0
    for case in EXPECTED:
        ok = bool(case["check"](report))
        passed += ok
        print(f"{case['name']:62s} {'найдено' if ok else 'НЕ НАЙДЕНО':10s} {case['cite'](report)}")

    print("-" * 110)
    print(f"Найдено контрольных случаев: {passed} из {len(EXPECTED)}\n")

    # Полнота ссылок — ключевое требование ТЗ (must-have 4).
    with_src = sum(1 for f in report.findings
                   if f.sources and any("п. " in s.cite for s in f.sources))
    print(f"Выводов всего: {len(report.findings)}")
    print(f"Из них со ссылкой на конкретный пункт: {with_src} "
          f"({100 * with_src // max(1, len(report.findings))}%)")

    # Работа агента-верификатора.
    checked = [f for f in report.findings if f.verification]
    if checked:
        removed = [f for f in checked if f.verification["verdict"] == "found_elsewhere"]
        confirmed = [f for f in checked if f.verification["verdict"] == "confirmed_lost"]
        unclear = [f for f in checked if f.verification["verdict"] == "uncertain"]
        print(f"\nАгент-верификатор проверил подозрений: {len(checked)}")
        print(f"  снято как ложная тревога: {len(removed)} (у каждого указан пункт-подтверждение)")
        print(f"  потеря подтверждена:      {len(confirmed)}")
        print(f"  честно не уверен:         {len(unclear)}")
        calls = sum(len(f.verification["trace"]) for f in checked)
        print(f"  вызовов инструментов:     {calls}")

    by_kind: dict[str, int] = {}
    for f in report.findings:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
    print("\nВыводы по типам:")
    for kind, n in sorted(by_kind.items(), key=lambda p: -p[1]):
        print(f"  {kind:22s} {n}")

    return 0 if passed == len(EXPECTED) else 1


if __name__ == "__main__":
    raise SystemExit(main())
