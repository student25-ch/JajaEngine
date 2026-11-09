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

"""A/B 分流：按 query hash 稳定分组，便于长期对比。"""

import hashlib
import json
from pathlib import Path

from .config import DATA_DIR

ASSIGN_PATH = DATA_DIR / "ltr" / "ab_assign.json"
DEFAULT_RATIO = 0.1  # 10% 流量走 L5


def _bucket(query):
    h = int(hashlib.md5(query.encode("utf-8")).hexdigest(), 16)
    return (h % 10000) / 10000.0


def assign(query, ratio=None):
    """返回 'l5' 或 'baseline'。稳定：同一 query 永远同一组。"""
    r = ratio if ratio is not None else _current_ratio()
    return "l5" if _bucket(query) < r else "baseline"


def _current_ratio():
    if ASSIGN_PATH.exists():
        try:
            data = json.loads(ASSIGN_PATH.read_text(encoding="utf-8"))
            return float(data.get("ratio", DEFAULT_RATIO))
        except (json.JSONDecodeError, ValueError):
            pass
    return DEFAULT_RATIO


def set_ratio(ratio, note=""):
    """调整分流比例，便于灰度放量。"""
    ratio = max(0.0, min(1.0, float(ratio)))
    ASSIGN_PATH.parent.mkdir(parents=True, exist_ok=True)
    ASSIGN_PATH.write_text(
        json.dumps({"ratio": ratio, "note": note}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ratio


def info():
    return {"ratio": _current_ratio(), "default": DEFAULT_RATIO}
