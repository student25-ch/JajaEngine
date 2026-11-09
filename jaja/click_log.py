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
"""查询-点击日志：L5 的训练数据来源。

日志格式（JSONL，一行一条）：
  {"ts": "2025-01-01T00:00:00+00:00", "query": "倒排索引",
   "doc_id": "002-inverted-index", "position": 1, "clicked": true,
   "features": {...}}
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import DATA_DIR

LOG_DIR = DATA_DIR / "ltr"
CLICK_LOG = LOG_DIR / "clicks.jsonl"


def _ensure_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_impression(query, results):
    """记录一次查询的曝光列表（未点击也记录，用于负样本）。"""
    _ensure_dir()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with CLICK_LOG.open("a", encoding="utf-8") as f:
        for rank, item in enumerate(results, 1):
            record = {
                "ts": now,
                "query": query,
                "doc_id": item.get("id"),
                "position": rank,
                "clicked": False,
                "features": item.get("features"),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_click(query, doc_id, position, features=None):
    """记录一次点击。与曝光记录通过 query+doc_id+position 对齐。"""
    _ensure_dir()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "ts": now,
        "query": query,
        "doc_id": doc_id,
        "position": position,
        "clicked": True,
        "features": features,
    }
    with CLICK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_log(path=None):
    """读取全部日志，返回记录列表。"""
    path = Path(path or CLICK_LOG)
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_dataset(records):
    """把日志聚合成训练样本：query -> [(doc_id, features, label)]。

    标签规则（简单但有效）：
      - 被点击的文档：label = 1
      - 排在被点击文档之前但未被点击：label = 0（位置偏差修正）
      - 其余未点击：label = 0
    """
    from collections import defaultdict

    by_query = defaultdict(list)
    for r in records:
        if r.get("features"):
            by_query[r["query"]].append(r)

    samples = []
    for query, rows in by_query.items():
        clicked_pos = {r["position"] for r in rows if r.get("clicked")}
        if not clicked_pos:
            continue
        max_clicked = max(clicked_pos)
        for r in rows:
            label = 1 if r.get("clicked") else 0
            # 位置偏差修正：点击位置之前的未点击项视为强负样本
            if not r.get("clicked") and r["position"] < max_clicked:
                label = 0
            samples.append((query, r["doc_id"], r["features"], label))
    return samples
