"""Конфигурация: загрузка .env и единый клиент OpenAI.

Все обращения к модели идут через openai_client(): у клиента заданы таймаут
и число повторов, поэтому зависший запрос не подвешивает разбор навсегда.

ORGTRACE_OFFLINE=1 полностью отключает сеть: .env не читается, клиент не
создаётся, сопоставление идёт в резервном режиме. Так работают тесты — быстро
и без внешних зависимостей.
"""
from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

OPENAI_TIMEOUT_S = float(os.getenv("OPENAI_TIMEOUT_S", "40"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))


def offline() -> bool:
    return os.getenv("ORGTRACE_OFFLINE", "").strip() in {"1", "true", "yes"}


def load_env(path: str | Path | None = None) -> None:
    if offline():
        return
    env_path = Path(path) if path else _ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def openai_client():
    """Клиент OpenAI или None, если ключа нет, включён офлайн или SDK недоступен."""
    if offline():
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    return OpenAI(api_key=key, timeout=OPENAI_TIMEOUT_S, max_retries=OPENAI_MAX_RETRIES)


load_env()
