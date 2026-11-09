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
"""分词器：英文按词、中文 unigram + bigram，零依赖。"""

import re

_CJK = r"\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff"
_TOKEN_RE = re.compile(rf"[A-Za-z0-9_]+|[{_CJK}]+")


def tokenize(text, bigram=True):
    if not text:
        return []
    tokens = []
    for match in _TOKEN_RE.finditer(text):
        piece = match.group(0)
        if piece[0].isascii():
            tokens.append(piece.lower())
        else:
            tokens.extend(_cjk_tokens(piece, bigram))
    return tokens


def _cjk_tokens(piece, bigram):
    out = list(piece)
    if bigram and len(piece) > 1:
        out.extend(piece[i:i + 2] for i in range(len(piece) - 1))
    return out


def split_title(raw, fallback):
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip(), "\n".join(lines[i + 1:]).strip()
        break
    return fallback, raw.strip()
