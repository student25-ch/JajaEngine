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

"""离线评估：时间切分，计算 NDCG@10 / MRR@10 / CTR@10。

用法：
    python scripts/eval_offline.py
    python scripts/eval_offline.py --ratio 0.2
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jaja.click_log import load_log  # noqa: E402


def _parse_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min


def _group(records):
    """按 (query, 时间窗口) 聚合为一次搜索会话。"""
    by_query = defaultdict(list)
    for r in records:
        if not r.get("features"):
            continue
        by_query[r["query"]].append(r)
    return by_query


def _dcg(gains, k=10):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains[:k]))


def _ndcg(clicked_positions, k=10):
    """clicked_positions: 被点击文档的实际排名集合（1-based）。"""
    if not clicked_positions:
        return 0.0
    gains = [1 if (i + 1) in clicked_positions else 0 for i in range(k)]
    ideal = sorted(gains, reverse=True)
    dcg = _dcg(gains, k)
    idcg = _dcg(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def _mrr(clicked_positions):
    if not clicked_positions:
        return 0.0
    return 1.0 / min(clicked_positions)


def evaluate(records, cutoff_ratio=0.2):
    """时间切分：前 80% 训练，后 20% 评估。"""
    records = [r for r in records if r.get("features")]
    if len(records) < 10:
        return {"error": f"样本过少（{len(records)}），至少需要 10 条"}

    records.sort(key=lambda r: _parse_ts(r.get("ts", "")))
    split = int(len(records) * (1 - cutoff_ratio))
    test = records[split:]

    by_query = _group(test)
    ndcgs, mrrs, ctrs = [], [], []
    for query, rows in by_query.items():
        clicked = {r["position"] for r in rows if r.get("clicked")}
        if not clicked:
            continue
        # 用日志中的 position 作为“实际排名”
        ndcgs.append(_ndcg(clicked, 10))
        mrrs.append(_mrr(clicked))
        ctrs.append(len(clicked) / max(len({r["position"] for r in rows}), 1))

    def avg(xs):
        return round(sum(xs) / len(xs), 4) if xs else 0.0

    return {
        "test_queries": len(by_query),
        "evaluated": len(ndcgs),
        "ndcg@10": avg(ndcgs),
        "mrr@10": avg(mrrs),
        "ctr@10": avg(ctrs),
        "cutoff_ratio": cutoff_ratio,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratio", type=float, default=0.2,
                        help="测试集比例，默认 0.2")
    parser.add_argument("--log", default=None, help="日志路径")
    args = parser.parse_args()

    records = load_log(args.log)
    print(f"[eval] 读取 {len(records)} 条日志")
    result = evaluate(records, args.ratio)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
