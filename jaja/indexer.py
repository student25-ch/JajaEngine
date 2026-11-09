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
"""倒排索引构建与持久化。"""

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import BIGRAM, DOCS_DIR, INDEX_PATH, K1, B, TITLE_BOOST
from .tokenizer import split_title, tokenize


class Indexer:
    def __init__(self, docs_dir=None, index_path=None,
                 k1=K1, b=B, title_boost=TITLE_BOOST, bigram=BIGRAM):
        self.docs_dir = Path(docs_dir or DOCS_DIR)
        self.index_path = Path(index_path or INDEX_PATH)
        self.k1 = k1
        self.b = b
        self.title_boost = title_boost
        self.bigram = bigram

    def iter_documents(self):
        if not self.docs_dir.exists():
            return
        for path in sorted(self.docs_dir.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            title, body = split_title(raw, path.stem)
            yield {"id": path.stem, "title": title, "body": body, "file": path.name}

    def build(self, verbose=True):
        docs = []
        postings = {}
        for doc in self.iter_documents():
            title_tokens = tokenize(doc["title"], self.bigram)
            body_tokens = tokenize(doc["body"], self.bigram)
            tokens = title_tokens * self.title_boost + body_tokens
            if not tokens:
                continue
            doc_idx = len(docs)
            docs.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": (doc["title"] + "\n" + doc["body"]).strip(),
                "file": doc["file"],
                "length": len(tokens),
            })
            for term in tokens:
                bucket = postings.setdefault(term, {})
                bucket[doc_idx] = bucket.get(doc_idx, 0) + 1

        total_len = sum(d["length"] for d in docs)
        avgdl = (total_len / len(docs)) if docs else 0.0

        payload = {
            "version": 1,
            "engine": "JajaEngine",
            "author": "student25-ch",
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "k1": self.k1, "b": self.b, "bigram": self.bigram,
            "avgdl": round(avgdl, 4),
            "docs": docs, "postings": postings,
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        stats = {"docs": len(docs), "terms": len(postings),
                 "avgdl": round(avgdl, 2), "index_path": str(self.index_path)}
        if verbose:
            print(f"[JajaEngine] 索引完成：{stats['docs']} 篇文档，"
                  f"{stats['terms']} 个词条，平均长度 {stats['avgdl']}")
        return stats
