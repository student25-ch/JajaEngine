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
"""Flask HTTP 服务。"""

import os

from flask import Flask, jsonify, request, send_from_directory

from .config import DEFAULT_PAGE_SIZE, WEB_DIR
from .click_log import log_click, log_impression
from .engine import JajaEngine

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/static")
_engine = JajaEngine()
_engine_error = None


def get_engine():
    global _engine_error
    if not _engine.loaded:
        try:
            _engine.load()
        except FileNotFoundError as exc:
            _engine_error = str(exc)
            raise
    return _engine


def _int_arg(name, default):
    try:
        return int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/search")
def api_search():
    try:
        engine = get_engine()
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    result = engine.search(
        request.args.get("q", "").strip(),
        page=_int_arg("page", 1),
        size=_int_arg("size", DEFAULT_PAGE_SIZE),
    )
    try:
        log_impression(result["query"], result["results"])
    except Exception:
        pass
    return jsonify(result)


@app.get("/api/stats")
def api_stats():
    try:
        return jsonify(get_engine().stats())
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503




@app.post("/api/click")
def api_click():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"ok": False, "error": "invalid json"}), 400
    try:
        log_click(
            data.get("query", ""),
            data.get("doc_id", ""),
            int(data.get("position", 0)),
            data.get("features"),
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True})

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "engine": "JajaEngine"})


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    debug = os.environ.get("DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
