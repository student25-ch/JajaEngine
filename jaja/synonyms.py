# JajaEngine —— 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
# SPDX-License-Identifier: GPL-3.0-or-later
"""同义词表：从 data/lexicon/synonyms.txt 加载，双向扩展。"""

from pathlib import Path

from .config import DATA_DIR

SYNONYMS_PATH = DATA_DIR / "lexicon" / "synonyms.txt"

# term -> {同义词}
_EXPAND = {}
_LOADED = False


def _load():
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    if not SYNONYMS_PATH.exists():
        return
    for line in SYNONYMS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        group = [w.lower() for w in line.split() if w]
        merged = set(group)
        for word in group:
            _EXPAND.setdefault(word, set()).update(merged)


def expand(term, weight=0.6):
    """返回 [(同义词, 权重)]，含原词权重 1.0。"""
    _load()
    t = term.lower()
    result = [(t, 1.0)]
    for syn in _EXPAND.get(t, ()):
        if syn != t:
            result.append((syn, weight))
    return result


def groups():
    """返回原始分组，供调试。"""
    _load()
    seen = set()
    out = []
    for word, syns in _EXPAND.items():
        key = frozenset(syns)
        if key in seen:
            continue
        seen.add(key)
        out.append(sorted(syns))
    return out
