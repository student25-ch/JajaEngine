# JajaEngine — 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""查询改写：停用词过滤、意图识别、关键词提权。"""

from pathlib import Path

from .config import DATA_DIR

STOPWORDS_PATH = DATA_DIR / "lexicon" / "stopwords.txt"

_STOPWORDS = None

INTENT_PATTERNS = {
    "how": ["怎么", "如何", "怎样", "how"],
    "what": ["是什么", "什么是", "what"],
    "why": ["为什么", "why"],
    "which": ["哪个", "哪些", "which"],
}


def _stopwords():
    global _STOPWORDS
    if _STOPWORDS is None:
        _STOPWORDS = set()
        if STOPWORDS_PATH.exists():
            for line in STOPWORDS_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    _STOPWORDS.add(line.lower())
    return _STOPWORDS


def detect_intent(query):
    low = query.lower()
    for intent, words in INTENT_PATTERNS.items():
        if any(w in low for w in words):
            return intent
    return None


def rewrite(query):
    """返回 (clean_query, dropped_terms, intent)。"""
    intent = detect_intent(query)
    stop = _stopwords()
    tokens, dropped = [], []
    for tok in query.split():
        if tok.lower() in stop:
            dropped.append(tok)
        else:
            tokens.append(tok)
    clean = " ".join(tokens) if tokens else query
    return clean, dropped, intent
