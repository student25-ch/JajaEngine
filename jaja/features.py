# JajaEngine —— 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
# SPDX-License-Identifier: GPL-3.0-or-later
"""L5 排序特征提取：13 个可解释特征。"""

import math
from datetime import datetime, timezone

FEATURE_NAMES = [
    "bm25", "title_hit", "title_cover", "body_cover", "tf_sum",
    "doc_len_norm", "avgdl_ratio", "phrase_hit", "freshness",
    "link_count", "semantic", "query_len", "synonym_hit",
]

FRESHNESS_HALF_LIFE_DAYS = 365.0


def _freshness(doc):
    ts = doc.get("modified_at") or doc.get("built_at")
    if not ts:
        return 0.5
    try:
        then = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return 0.5
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    days = max(0.0, (datetime.now(timezone.utc) - then).total_seconds() / 86400)
    return math.exp(-days / FRESHNESS_HALF_LIFE_DAYS)


def featurize(doc, query_terms, bm25_score, max_bm25,
              phrase_hit=False, link_count=0, semantic=0.0,
              synonym_hit=0.0):
    title = (doc.get("title") or "").lower()
    content = (doc.get("content") or "").lower()
    terms = [t.lower() for t in query_terms if t]
    n = len(terms) or 1

    title_hit = 1.0 if any(t in title for t in terms) else 0.0
    title_cover = sum(1 for t in terms if t in title) / n
    body_cover = sum(1 for t in terms if t in content) / n
    tf_sum = sum(content.count(t) for t in terms)
    dl = doc.get("length") or 1

    return {
        "bm25": (bm25_score / max_bm25) if max_bm25 > 0 else 0.0,
        "title_hit": title_hit,
        "title_cover": title_cover,
        "body_cover": body_cover,
        "tf_sum": math.log1p(tf_sum) / 10.0,
        "doc_len_norm": 1.0 - min(dl / 500.0, 1.0),
        "avgdl_ratio": min(dl / 500.0, 2.0),
        "phrase_hit": 1.0 if phrase_hit else 0.0,
        "freshness": _freshness(doc),
        "link_count": math.log1p(link_count) / 5.0,
        "semantic": float(semantic),
        "query_len": min(n / 5.0, 1.0),
        "synonym_hit": float(synonym_hit),
    }


def to_vector(feature_dict):
    return [feature_dict.get(name, 0.0) for name in FEATURE_NAMES]
