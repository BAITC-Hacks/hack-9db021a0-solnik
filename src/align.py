"""Семантическое сопоставление функций.

Два режима:
  * embeddings — OpenAI text-embedding, когда есть ключ (основной);
  * lexical — косинус на взвешенных токенах, без сети (резерв).

Резерв существует не для красоты: в зале на 2500 человек сеть может лечь,
и демонстрация обязана пережить это без потери смысла.
"""
from __future__ import annotations

import math
import os
import threading

from .config import openai_client
import re
from collections import Counter

_STOP = {
    "и", "в", "во", "не", "что", "он", "на", "с", "со", "как", "а", "то", "все",
    "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы",
    "по", "только", "ее", "мне", "было", "вот", "от", "для", "о", "из", "ему",
    "при", "об", "или", "их", "также", "том", "быть", "если", "иных", "иные",
    "настоящего", "настоящим", "положения", "положением", "рамках", "числе",
    "осуществляет", "осуществляют", "обеспечивает", "проводит", "а-также",
}
TOKEN_RE = re.compile(r"[а-яёa-z]{3,}")


def tokens(text: str) -> list[str]:
    """Грубая нормализация: срезаем окончания, чтобы «аудита» и «аудит» совпали."""
    out = []
    for w in TOKEN_RE.findall(text.lower()):
        if w in _STOP:
            continue
        out.append(w[:7] if len(w) > 8 else w)
    return out


def _tf(text: str) -> Counter:
    return Counter(tokens(text))


def _cos(a: Counter, b: Counter, idf: dict[str, float]) -> float:
    common = set(a) & set(b)
    if not common:
        return 0.0
    num = sum(a[t] * b[t] * idf.get(t, 1.0) ** 2 for t in common)
    na = math.sqrt(sum((a[t] * idf.get(t, 1.0)) ** 2 for t in a))
    nb = math.sqrt(sum((b[t] * idf.get(t, 1.0)) ** 2 for t in b))
    return num / (na * nb) if na and nb else 0.0


def _idf(corpus: list[str]) -> dict[str, float]:
    n = len(corpus) or 1
    df: Counter = Counter()
    for text in corpus:
        df.update(set(tokens(text)))
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


# Одни и те же пункты встречаются в нескольких стадиях разбора (сопоставление,
# поиск дублей, индекс агента). Кеш по тексту убирает повторные запросы.
_EMBED_CACHE: dict[tuple[str, str], list[float]] = {}
_EMBED_LOCK = threading.Lock()


def _embed(texts: list[str]) -> list[list[float]] | None:
    client = openai_client()
    if client is None or not texts:
        return None
    model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    # пустые строки API не принимает — заменяем пробелом
    texts = [t if t.strip() else " " for t in texts]

    with _EMBED_LOCK:
        missing = list(dict.fromkeys(t for t in texts if (model, t) not in _EMBED_CACHE))
    try:
        for i in range(0, len(missing), 128):        # батчами, чтобы не упереться в лимит
            batch = missing[i:i + 128]
            resp = client.embeddings.create(model=model, input=batch)
            with _EMBED_LOCK:
                for text, d in zip(batch, resp.data):
                    _EMBED_CACHE[(model, text)] = d.embedding
    except Exception:
        return None                                   # уходим в резервный режим
    with _EMBED_LOCK:
        return [_EMBED_CACHE[(model, t)] for t in texts]


def _cos_vec(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return num / (na * nb) if na and nb else 0.0


class Similarity:
    """Матрица близости между двумя наборами текстов."""

    def __init__(self, left: list[str], right: list[str]):
        self.left, self.right = left, right
        vecs = _embed(left + right)
        if vecs:
            self.mode = "embeddings"
            self._l = vecs[:len(left)]
            self._r = vecs[len(left):]
        else:
            self.mode = "lexical"
            idf = _idf(left + right)
            self._idf = idf
            self._l = [_tf(t) for t in left]
            self._r = [_tf(t) for t in right]

    def score(self, i: int, j: int) -> float:
        if self.mode == "embeddings":
            return _cos_vec(self._l[i], self._r[j])
        return _cos(self._l[i], self._r[j], self._idf)

    def best_for_left(self, i: int) -> tuple[int, float]:
        if not self.right:
            return -1, 0.0
        scores = [(j, self.score(i, j)) for j in range(len(self.right))]
        return max(scores, key=lambda p: p[1])

    def best_for_right(self, j: int) -> tuple[int, float]:
        if not self.left:
            return -1, 0.0
        scores = [(i, self.score(i, j)) for i in range(len(self.left))]
        return max(scores, key=lambda p: p[1])


# Пороги подобраны на контрольном комплекте ред.8 / ред.9 — единственном
# размеченном наборе. На других документах их может понадобиться подстроить,
# поэтому каждый порог переопределяется переменной окружения, например
# ORGTRACE_EMBEDDINGS_MATCH=0.6. Ошибки порога на стороне потерь частично
# гасит агент-верификатор: каждое подозрение на потерю он проверяет по документу.
_DEFAULT_THRESHOLDS = {
    "embeddings": {"match": 0.62, "weak": 0.50, "duplicate": 0.72},
    "lexical": {"match": 0.45, "weak": 0.33, "duplicate": 0.55},
}


def _load_thresholds() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for mode, values in _DEFAULT_THRESHOLDS.items():
        out[mode] = {}
        for name, default in values.items():
            raw = os.getenv(f"ORGTRACE_{mode.upper()}_{name.upper()}")
            try:
                value = float(raw) if raw else default
            except ValueError:
                value = default
            out[mode][name] = min(max(value, 0.0), 1.0)
    return out


THRESHOLDS = _load_thresholds()


class Index:
    """Поисковый индекс по корпусу: векторы считаются один раз.

    Инструмент агента вызывается многократно, и без индекса каждый вызов
    заново отправлял бы весь документ в эмбеддинги — это и было главным
    источником задержки.
    """

    def __init__(self, texts: list[str]):
        self.texts = texts
        vecs = _embed(texts)
        if vecs:
            self.mode = "embeddings"
            self._vecs = vecs
        else:
            self.mode = "lexical"
            self._idf = _idf(texts)
            self._tf = [_tf(t) for t in texts]

    def search(self, query: str, limit: int = 4) -> list[tuple[int, float]]:
        if self.mode == "embeddings":
            qv = _embed([query])
            if not qv:
                return []
            scores = [(i, _cos_vec(qv[0], v)) for i, v in enumerate(self._vecs)]
        else:
            q = _tf(query)
            scores = [(i, _cos(q, t, self._idf)) for i, t in enumerate(self._tf)]
        scores.sort(key=lambda p: p[1], reverse=True)
        return scores[:limit]
