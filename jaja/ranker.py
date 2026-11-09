# JajaEngine —— 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
# SPDX-License-Identifier: GPL-3.0-or-later
"""L5 重排器：线性逻辑回归，支持 sklearn 模型文件切换。

模型文件 data/ltr/model.json 格式：
  {"type": "linear", "weights": {...}, "bias": 0.0}
  {"type": "sklearn", "path": "data/ltr/sklearn.pkl"}   # 预留
"""

import json
import math
import pickle
from pathlib import Path

from .config import DATA_DIR
from .features import FEATURE_NAMES, to_vector

MODEL_PATH = DATA_DIR / "ltr" / "model.json"
MIN_SAMPLES = 100  # 样本不足时不启用，避免过拟合


class Ranker:
    def __init__(self, model_path=None):
        self.model_path = Path(model_path or MODEL_PATH)
        self.weights = {}
        self.bias = 0.0
        self.trained_at = None
        self.samples = 0
        self.type = "none"
        self._sk = None
        self.enabled = False
        self._load()

    def _load(self):
        if not self.model_path.exists():
            return
        try:
            data = json.loads(self.model_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        self.type = data.get("type", "linear")
        self.trained_at = data.get("trained_at")
        self.samples = int(data.get("samples", 0))

        if self.type == "sklearn":
            p = Path(data.get("path", ""))
            if p.exists():
                with p.open("rb") as f:
                    self._sk = pickle.load(f)
                self.enabled = True
            return

        self.weights = data.get("weights", {})
        self.bias = float(data.get("bias", 0.0))
        # 样本不足时不启用，防止小数据过拟合
        self.enabled = bool(self.weights) and self.samples >= MIN_SAMPLES

    def score(self, feature_dict):
        if not self.enabled:
            return feature_dict.get("bm25", 0.0)
        if self.type == "sklearn" and self._sk is not None:
            vec = [to_vector(feature_dict)]
            return float(self._sk.predict_proba(vec)[0][1])
        vec = to_vector(feature_dict)
        z = self.bias + sum(
            self.weights.get(name, 0.0) * v
            for name, v in zip(FEATURE_NAMES, vec)
        )
        return 1.0 / (1.0 + math.exp(-z))

    def rerank(self, candidates):
        if not self.enabled:
            return candidates
        for item in candidates:
            item["ltr_score"] = round(self.score(item.get("features", {})), 6)
        return sorted(candidates, key=lambda x: -x["ltr_score"])

    def info(self):
        return {
            "enabled": self.enabled,
            "type": self.type,
            "weights": self.weights,
            "bias": self.bias,
            "samples": self.samples,
            "trained_at": self.trained_at,
            "min_samples": MIN_SAMPLES,
        }
