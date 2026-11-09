# JajaEngine —— 轻量开源搜索引擎
# Copyright (C) 2025 student25-ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""训练 L5 线性重排模型。

方法：逻辑回归 + 梯度下降，纯 Python 实现，零依赖。
输入：data/ltr/clicks.jsonl
输出：data/ltr/model.json
"""

import json
import random
from collections import Counter
from datetime import datetime, timezone

from .click_log import build_dataset, load_log
from .config import DATA_DIR
from .features import FEATURE_NAMES, to_vector

MODEL_PATH = DATA_DIR / "ltr" / "model.json"
LEARNING_RATE = 0.05
EPOCHS = 200
L2 = 0.01


def _sigmoid(z):
    if z >= 0:
        ez = pow(2.718281828, -z)
        return 1.0 / (1.0 + ez)
    ez = pow(2.718281828, z)
    return ez / (1.0 + ez)


def _vector(features):
    return to_vector(features)


def train(records=None, epochs=EPOCHS, lr=LEARNING_RATE, l2=L2, verbose=True):
    """训练并返回 (weights_dict, bias, metrics)。"""
    records = records if records is not None else load_log()
    samples = build_dataset(records)
    if not samples:
        return None, 0.0, {"error": "无训练样本，先积累点击日志"}

    X = [_vector(f) for _, _, f, _ in samples]
    y = [label for _, _, _, label in samples]

    # 类别不均衡：按正负样本比例调权重
    counts = Counter(y)
    pos_w = len(y) / (2.0 * counts.get(1, 1))
    neg_w = len(y) / (2.0 * counts.get(0, 1))
    sample_w = [pos_w if label == 1 else neg_w for label in y]

    n_features = len(FEATURE_NAMES)
    w = [0.0] * n_features
    b = 0.0
    order = list(range(len(X)))

    for epoch in range(epochs):
        random.shuffle(order)
        for idx in order:
            xi, yi, wi = X[idx], y[idx], sample_w[idx]
            z = b + sum(wj * xj for wj, xj in zip(w, xi))
            p = _sigmoid(z)
            err = (p - yi) * wi
            for j in range(n_features):
                w[j] -= lr * (err * xi[j] + l2 * w[j])
            b -= lr * err

    # 评估
    correct = 0
    for xi, yi in zip(X, y):
        p = _sigmoid(b + sum(wj * xj for wj, xj in zip(w, xi)))
        pred = 1 if p >= 0.5 else 0
        if pred == yi:
            correct += 1
    accuracy = correct / len(y)

    weights = {name: round(val, 6) for name, val in zip(FEATURE_NAMES, w)}
    metrics = {
        "samples": len(y),
        "positives": counts.get(1, 0),
        "negatives": counts.get(0, 0),
        "accuracy": round(accuracy, 4),
        "epochs": epochs,
    }
    if verbose:
        print(f"[L5] 训练完成：{len(y)} 样本，准确率 {accuracy:.2%}")
        for name in FEATURE_NAMES:
            print(f"     {name:15s} {weights[name]:+.4f}")
    return weights, round(b, 6), metrics


def save_model(weights, bias, metrics, path=None):
    path = path or MODEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": weights,
        "bias": bias,
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feature_names": FEATURE_NAMES,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main():
    print("[L5] 读取点击日志…")
    weights, bias, metrics = train()
    if weights is None:
        print(f"[L5] 跳过训练：{metrics.get('error')}")
        return 1
    path = save_model(weights, bias, metrics)
    print(f"[L5] 模型已保存：{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
