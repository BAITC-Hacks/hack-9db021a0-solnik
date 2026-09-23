"""Тесты работают без сети: ключ OpenAI не читается, сопоставление идёт
в резервном режиме. Переменная выставляется до импорта модулей проекта."""
import os

os.environ["ORGTRACE_OFFLINE"] = "1"
os.environ.pop("OPENAI_API_KEY", None)
