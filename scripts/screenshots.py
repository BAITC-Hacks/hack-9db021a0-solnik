"""Снимки интерфейса для README и стартовой страницы.

Запуск при работающем сервере (python -m uvicorn src.app:app --port 8000):
    python scripts/screenshots.py

Снимает главную и рабочий экран после разбора контрольного комплекта,
сохраняет в docs/screenshots/, а снимок сводки кладёт в static/app-preview.jpg —
его показывает рамка на стартовой странице.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.getenv("ORGTRACE_URL", "http://127.0.0.1:8000")
OUT = Path("docs/screenshots")
VIEW = {"width": 1440, "height": 900}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEW, device_scale_factor=1.5, color_scheme="light",
                                locale="ru-RU")

        # рабочий экран: разбор контрольного комплекта
        page.goto(BASE + "/app", wait_until="networkidle")
        page.click("#demo")
        page.wait_for_selector(".stats", timeout=240_000)
        page.wait_for_timeout(400)
        page.screenshot(path=OUT / "app-summary.png")
        print("app-summary.png")

        # снимок сводки — в рамку на главной
        try:
            from PIL import Image
            Image.open(OUT / "app-summary.png").convert("RGB").save(
                "static/app-preview.jpg", quality=88, optimize=True)
            print("static/app-preview.jpg")
        except ImportError:
            print("Pillow не установлен — static/app-preview.jpg не обновлён", file=sys.stderr)

        def open_section(kind: str) -> bool:
            btn = page.locator(f'.it[data-k="{kind}"]')
            if btn.count() == 0:
                return False
            btn.first.click()
            page.wait_for_timeout(300)
            return page.locator("#out .f").count() > 0

        # конфликт интересов
        if open_section("conflict_of_interest"):
            page.locator("#out .f").first.screenshot(path=OUT / "conflict.png")
            print("conflict.png")

        # работа агента: первая карточка с вердиктом верификатора
        for kind in ("false_positive", "function_lost"):
            if open_section(kind) and page.locator("#out .f .vf").count() > 0:
                card = page.locator("#out .f").filter(has=page.locator(".vf")).first
                details = card.locator("details")
                if details.count():
                    details.first.evaluate("el => el.open = true")
                    page.wait_for_timeout(200)
                card.screenshot(path=OUT / "agent.png")
                print(f"agent.png ({kind})")
                break

        # дублирование с рекомендацией
        if open_section("duplication"):
            card = page.locator("#out .f").filter(has=page.locator(".rec")).first
            if card.count():
                card.screenshot(path=OUT / "recommendation.png")
                print("recommendation.png")

        # подразделения
        if open_section("units"):
            page.screenshot(path=OUT / "units.png")
            print("units.png")

        # главная снимается последней: в рамке уже свежий снимок рабочего экрана
        page.goto(BASE + "/", wait_until="networkidle")
        page.screenshot(path=OUT / "landing.png")
        print("landing.png")
        for sel, name in (("#trust", "landing-features.png"), (".cta2", "landing-cta.png")):
            if page.locator(sel).count():
                page.locator(sel).screenshot(path=OUT / name)
                print(name)

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
