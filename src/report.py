"""Итоговое аналитическое заключение (ТЗ, must-have 5).

Факты в заключение попадают только из результатов сравнения. Модель, если она
доступна, переписывает их связным текстом, но не добавляет ничего от себя:
в промпте прямо запрещено вводить сведения, которых нет в переданных данных.
Без ключа заключение собирается шаблоном — смысл тот же, стиль суше.
"""
from __future__ import annotations

import os

from .config import load_env  # noqa: F401  загрузка .env

from .compare import Report


def _facts(report: Report) -> str:
    created = report.by_kind("unit_created")
    removed = report.by_kind("unit_removed")
    kept = report.by_kind("unit_kept")
    lost = report.by_kind("function_lost")
    moved = report.by_kind("function_moved")
    dup = report.by_kind("duplication")
    conf = report.by_kind("conflict_of_interest")

    lines = [
        f"Сравнены комплекты: «до» — {report.before_doc}, «после» — {report.after_doc}.",
        f"Подразделений в новой структуре: {len(report.units_after)} "
        f"(было {len(report.units_before)}).",
        "Создано: " + (", ".join(f.title.split()[-1] for f in created) or "нет"),
        "Сохранено: " + (", ".join(f.title.split()[-2] for f in kept) or "нет"),
        "Отсутствует в новой структуре: " + (", ".join(f.title.split()[1] for f in removed) or "нет"),
        f"Возможных потерь функций: {len(lost)} (высокий риск: "
        f"{sum(1 for f in lost if f.severity == 'high')}).",
        f"Функций передано между подразделениями: {len(moved)}.",
        f"Признаков дублирования: {len(dup)}.",
        f"Признаков конфликта интересов: {len(conf)}.",
    ]

    for f in (lost[:5] + dup[:3] + conf[:2]):
        cites = "; ".join(s.cite for s in f.sources[:2])
        lines.append(f"- {f.title}: {f.detail[:200]} [{cites}]")
    return "\n".join(lines)


TEMPLATE_TAIL = (
    "\nВыводы носят рекомендательный характер и требуют проверки ответственным "
    "сотрудником. Каждый пункт сопровождается ссылкой на исходный документ."
)


def render_conclusion(report: Report) -> str:
    facts = _facts(report)
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return facts + TEMPLATE_TAIL

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.getenv("OPENAI_MODEL", "gpt-5")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content":
                 "Ты помогаешь сотруднику, который анализирует реорганизацию подразделений. "
                 "Напиши деловое аналитическое заключение на русском по переданным фактам. "
                 "Строгое правило: используй только переданные факты и ссылки на пункты. "
                 "Ничего не добавляй от себя, не додумывай названия и номера пунктов. "
                 "Структура: что изменилось в структуре; на что обратить внимание в первую "
                 "очередь; какие риски потери или дублирования функций; что проверить вручную. "
                 "Без воды, 200-280 слов."},
                {"role": "user", "content": facts},
            ],
        )
        return (resp.choices[0].message.content or facts) + TEMPLATE_TAIL
    except Exception:
        return facts + TEMPLATE_TAIL


if __name__ == "__main__":
    from .compare import run
    rep = run("data/samples/polozhenie_red8.docx", "data/samples/polozhenie_red9.docx")
    print(render_conclusion(rep))
