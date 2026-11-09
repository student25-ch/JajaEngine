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

"""查询解析 + BM25 排序 + 摘要高亮。"""

import html
import json
import math
import re
import time
from pathlib import Path

from .config import B, DEFAULT_PAGE_SIZE, INDEX_PATH, K1, MAX_PAGE_SIZE, SNIPPET_LEN
from .tokenizer import tokenize
from .abtest import assign
from .features import featurize
from .query_rewrite import rewrite
from .ranker import Ranker
from .semantic import semantic_search
from .spell import suggest
from .synonyms import expand

_PHRASE_RE = re.compile(r'"([^"]*)"')


_ranker = Ranker()


class JajaEngine:
    def __init__(self, index_path=None, snippet_len=SNIPPET_LEN):
        self.index_path = Path(index_path or INDEX_PATH)
        self.snippet_len = snippet_len
        self.docs = []
        self.postings = {}
        self.avgdl = 0.0
        self.k1 = K1
        self.b = B
        self.bigram = True
        self.built_at = None
        self.loaded = False

    def load(self):
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"索引不存在：{self.index_path}\n请先运行：python -m jaja.cli build"
            )
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.docs = data.get("docs", [])
        self.postings = {
            term: {int(di): tf for di, tf in bucket.items()}
            for term, bucket in data.get("postings", {}).items()
        }
        self.avgdl = float(data.get("avgdl") or 0.0)
        self.k1 = float(data.get("k1", K1))
        self.b = float(data.get("b", B))
        self.bigram = bool(data.get("bigram", True))
        self.built_at = data.get("built_at")
        self.loaded = True
        return self

    def stats(self):
        return {"docs": len(self.docs), "terms": len(self.postings),
                "avgdl": round(self.avgdl, 2), "built_at": self.built_at}

    def _parse(self, query):
        phrases = [p.strip() for p in _PHRASE_RE.findall(query) if p.strip()]
        rest = _PHRASE_RE.sub(" ", query)
        must, minus, normal = [], [], []
        for word in rest.split():
            if word.startswith("+") and len(word) > 1:
                must.append(word[1:])
            elif word.startswith("-") and len(word) > 1:
                minus.append(word[1:])
            else:
                normal.append(word)
        return phrases, must, minus, normal

    def _idf(self, df):
        n = len(self.docs)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query, page=1, size=DEFAULT_PAGE_SIZE):
        t0 = time.perf_counter()
        query = (query or "").strip()
        page = max(1, int(page or 1))
        size = max(1, min(int(size or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
        empty = {"query": query, "total": 0, "page": page, "size": size,
                 "took_ms": 0.0, "terms": [], "results": [],
                 "suggestions": {}, "intent": None, "ab": "baseline"}
        if not query or not self.docs:
            return empty

        # L3 查询改写
        clean, dropped, intent = rewrite(query)
        phrases, must, minus, normal = self._parse(clean)
        raw_terms = tokenize(" ".join(normal + must + phrases), self.bigram)
        if not raw_terms:
            return empty

        # L2 拼写纠错
        vocab = list(self.postings.keys())
        suggestions = suggest(clean, vocab)

        # L1 同义词加权扩展
        term_weights = {}
        for t in raw_terms:
            for syn, w in expand(t):
                term_weights[syn] = max(term_weights.get(syn, 0.0), w)

        # BM25（带权重）
        scores = {}
        for term, w in term_weights.items():
            bucket = self.postings.get(term)
            if not bucket:
                continue
            idf = self._idf(len(bucket)) * w
            for di, tf in bucket.items():
                dl = self.docs[di]["length"] or 1
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                scores[di] = scores.get(di, 0.0) + idf * tf * (self.k1 + 1) / denom

        candidates = set(scores)
        if not candidates:
            if not (must or phrases):
                return empty
            candidates = set(range(len(self.docs)))

        # 必须词
        for word in must:
            need = tokenize(word, self.bigram)
            if not need:
                continue
            candidates = {di for di in candidates
                          if all(di in self.postings.get(t, {}) for t in need)}

        # 排除词
        for word in minus:
            ban = tokenize(word, self.bigram)
            if not ban:
                continue
            candidates = {di for di in candidates
                          if not any(di in self.postings.get(t, {}) for t in ban)}

        # 短语
        for phrase in phrases:
            needle = phrase.lower()
            candidates = {di for di in candidates
                          if needle in self.docs[di]["content"].lower()}

        # L4 语义召回（缺失自动跳过）
        sem_hits = {}
        try:
            sem_hits = dict(semantic_search(clean))
        except Exception:
            sem_hits = {}

        # 13 维特征
        max_bm25 = max(scores.values()) if scores else 0.0
        items = []
        for di in candidates:
            doc = self.docs[di]
            syn_hit = 1.0 if any(s != t for t in raw_terms
                                 for s, _ in expand(t)) else 0.0
            feats = featurize(
                doc, raw_terms, scores.get(di, 0.0), max_bm25,
                phrase_hit=bool(phrases),
                semantic=sem_hits.get(doc["id"], 0.0),
                synonym_hit=syn_hit,
            )
            items.append({
                "doc_idx": di,
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "features": feats,
                "bm25": scores.get(di, 0.0),
            })

        # A/B 分流 → L5 重排 或 基线
        ab = assign(clean)
        if ab == "l5":
            items = _ranker.rerank(items)
        else:
            items.sort(key=lambda x: -x["bm25"])

        total = len(items)
        start = (page - 1) * size
        page_items = items[start:start + size]

        highlight_terms = [t for t in raw_terms if len(t) >= 2] or raw_terms
        results = []
        for item in page_items:
            results.append({
                "id": item["id"],
                "title": item["title"],
                "score": round(item.get("ltr_score", item["bm25"]), 4),
                "snippet": self._snippet(item["content"], highlight_terms),
                "features": item["features"],
            })

        return {
            "query": query,
            "clean_query": clean,
            "total": total,
            "page": page,
            "size": size,
            "took_ms": round((time.perf_counter() - t0) * 1000, 2),
            "terms": list(term_weights.keys()),
            "results": results,
            "suggestions": suggestions,
            "intent": intent,
            "dropped_terms": dropped,
            "ab": ab,
        }

    def _snippet(self, text, terms):
        text = " ".join(text.split())
        if not text:
            return ""
        low = text.lower()
        hit = -1
        for term in terms:
            pos = low.find(term.lower())
            if pos != -1 and (hit == -1 or pos < hit):
                hit = pos
        if hit == -1:
            hit = 0
        start = max(0, hit - self.snippet_len // 3)
        end = min(len(text), start + self.snippet_len)
        frag = text[start:end].strip()
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        return prefix + self._highlight(html.escape(frag), terms) + suffix

    @staticmethod
    def _highlight(escaped, terms):
        terms = sorted({t for t in terms if t}, key=len, reverse=True)
        if not terms:
            return escaped
        pattern = re.compile("|".join(re.escape(t) for t in terms), re.IGNORECASE)
        return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped)
