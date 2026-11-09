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

"""编辑距离纠错：基于索引词表，零外部依赖。"""


def _edit_distance(a, b, max_dist=1):
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        row_min = i
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            val = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            cur.append(val)
            if val < row_min:
                row_min = val
        if row_min > max_dist:
            return max_dist + 1
        prev = cur
    return prev[-1]


def correct(term, vocabulary, max_dist=1):
    """在词表里找编辑距离最小的词；找不到返回 None。"""
    if term in vocabulary:
        return None
    best, best_dist = None, max_dist + 1
    for word in vocabulary:
        if abs(len(word) - len(term)) > max_dist:
            continue
        d = _edit_distance(term, word, max_dist)
        if d < best_dist:
            best, best_dist = word, d
            if d == 1:
                break
    return best


def suggest(query, vocabulary, max_dist=1):
    """对整串查询的每个 token 做纠错，返回 {错误词: 建议词}。"""
    from .tokenizer import tokenize
    out = {}
    for tok in tokenize(query):
        fixed = correct(tok, vocabulary, max_dist)
        if fixed:
            out[tok] = fixed
    return out
