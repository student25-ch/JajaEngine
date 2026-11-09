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

"""全局路径与默认参数。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
INDEX_PATH = DATA_DIR / "index.json"
WEB_DIR = ROOT / "web"

K1 = 1.5
B = 0.75
TITLE_BOOST = 3
BIGRAM = True
SNIPPET_LEN = 180
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
