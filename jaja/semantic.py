# JajaEngine —— 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
# SPDX-License-Identifier: GPL-3.0-or-later
"""L4 语义召回：句向量索引 + 余弦相似度。

依赖可选：pip install sentence-transformers
缺失时所有函数静默降级，不影响主流程。
"""

import json
from pathlib import Path

from .config import DATA_DIR

VEC_PATH = DATA_DIR / "vectors.npy"
IDS_PATH = DATA_DIR / "vectors.ids.json"
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_MODEL = None
_AVAILABLE = None


def available():
    """检测 sentence-transformers 是否可导入。"""
    global _AVAILABLE
    if _AVAILABLE is None:
        try:
            import sentence_transformers  # noqa: F401
            import numpy  # noqa: F401
            _AVAILABLE = True
        except ImportError:
            _AVAILABLE = False
    return _AVAILABLE


def _model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def build_vectors(docs, out_path=None):
    """为每篇文档编码，保存 .npy 与 id 列表。"""
    if not available():
        raise RuntimeError("需要安装 sentence-transformers 与 numpy")
    import numpy as np

    out_path = Path(out_path or VEC_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    texts = [(d["title"] + "。" + d.get("content", "")[:500]).strip() for d in docs]
    vecs = _model().encode(texts, normalize_embeddings=True,
                           show_progress_bar=True)
    np.save(out_path, vecs.astype("float32"))
    ids = [d["id"] for d in docs]
    Path(str(out_path) + ".ids.json").write_text(
        json.dumps(ids, ensure_ascii=False), encoding="utf-8"
    )
    return out_path


def semantic_search(query, vec_path=None, top_k=20, min_sim=0.5):
    """返回 [(doc_id, sim)]，低于 min_sim 的丢弃。"""
    if not available():
        return []
    import numpy as np

    vec_path = Path(vec_path or VEC_PATH)
    ids_path = Path(str(vec_path) + ".ids.json")
    if not vec_path.exists() or not ids_path.exists():
        return []

    vecs = np.load(vec_path)
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    qv = _model().encode([query], normalize_embeddings=True)[0]
    sims = vecs @ qv
    order = np.argsort(-sims)[:top_k]
    return [(ids[i], float(sims[i])) for i in order if sims[i] >= min_sim]
