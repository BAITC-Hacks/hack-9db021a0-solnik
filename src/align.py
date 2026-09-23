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

from .config import load_env  # noqa: F401  загрузка .env
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


def _embed(texts: list[str]) -> list[list[float]] | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key or not texts:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        out: list[list[float]] = []
        for i in range(0, len(texts), 128):          # батчами, чтобы не упереться в лимит
            resp = client.embeddings.create(model=model, input=texts[i:i + 128])
            out.extend(d.embedding for d in resp.data)
        return out
    except Exception:
        return None                                   # молча уходим в резервный режим


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


# Пороги подобраны на контрольном комплекте ред.8 / ред.9.
THRESHOLDS = {
    "embeddings": {"match": 0.62, "weak": 0.50, "duplicate": 0.72},
    "lexical": {"match": 0.45, "weak": 0.33, "duplicate": 0.55},
}
