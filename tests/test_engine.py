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
import pytest

from jaja.engine import JajaEngine
from jaja.indexer import Indexer


@pytest.fixture()
def engine(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "a.md").write_text(
        "# 倒排索引\n倒排索引是搜索引擎的核心数据结构，用于快速定位候选文档。",
        encoding="utf-8",
    )
    (docs_dir / "b.md").write_text(
        "# 爬虫\n网络爬虫负责抓取网页，抓取后进入索引流程。",
        encoding="utf-8",
    )
    (docs_dir / "c.md").write_text(
        "# 排序\nBM25 是最经典的排序算法，用于给文档打分。",
        encoding="utf-8",
    )

    index_path = tmp_path / "index.json"
    Indexer(docs_dir=docs_dir, index_path=index_path).build(verbose=False)
    return JajaEngine(index_path=index_path).load()


def test_hit_and_rank(engine):
    result = engine.search("倒排索引")
    assert result["total"] >= 1
    assert result["results"][0]["id"] == "a"
    assert "<mark>" in result["results"][0]["snippet"]


def test_no_hit(engine):
    assert engine.search("量子计算")["total"] == 0


def test_phrase_search(engine):
    result = engine.search('"搜索引擎的核心"')
    assert result["total"] == 1
    assert result["results"][0]["id"] == "a"


def test_exclude_operator(engine):
    result = engine.search("索引 -爬虫")
    ids = [r["id"] for r in result["results"]]
    assert "b" not in ids
    assert "a" in ids


def test_must_operator(engine):
    result = engine.search("+排序 算法")
    ids = [r["id"] for r in result["results"]]
    assert ids == ["c"]


def test_pagination(engine):
    first = engine.search("索引", page=1, size=1)
    assert first["size"] == 1
    assert len(first["results"]) <= 1
