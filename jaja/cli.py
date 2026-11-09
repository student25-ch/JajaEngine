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

"""命令行入口：build / search / serve。"""

import argparse
import sys

from .config import DEFAULT_PAGE_SIZE, DOCS_DIR, INDEX_PATH
from .engine import JajaEngine
from .indexer import Indexer


def cmd_build(args):
    stats = Indexer(docs_dir=args.docs, index_path=args.index).build()
    return 0 if stats["docs"] else 1


def cmd_search(args):
    engine = JajaEngine(index_path=args.index).load()
    result = engine.search(args.query, page=args.page, size=args.size)
    if not result["results"]:
        print(f'没有找到与 "{args.query}" 相关的内容。')
        return 0
    print(f'查询 "{result["query"]}" — 共 {result["total"]} 条，耗时 {result["took_ms"]} ms\n')
    base = (args.page - 1) * args.size
    for i, item in enumerate(result["results"], 1):
        snippet = item["snippet"].replace("<mark>", "[").replace("</mark>", "]")
        print(f'{base + i:>3}. {item["title"]}  (score={item["score"]})')
        print(f'     {snippet}\n')
    return 0


def cmd_serve(args):
    from .server import app
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="jaja", description="JajaEngine —— 轻量开源搜索引擎 (by student25-ch)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="构建倒排索引")
    p_build.add_argument("--docs", default=str(DOCS_DIR))
    p_build.add_argument("--index", default=str(INDEX_PATH))
    p_build.set_defaults(func=cmd_build)

    p_search = sub.add_parser("search", help="命令行搜索")
    p_search.add_argument("query")
    p_search.add_argument("-n", "--size", type=int, default=DEFAULT_PAGE_SIZE)
    p_search.add_argument("-p", "--page", type=int, default=1)
    p_search.add_argument("--index", default=str(INDEX_PATH))
    p_search.set_defaults(func=cmd_search)

    p_serve = sub.add_parser("serve", help="启动 Web 服务")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("-p", "--port", type=int, default=8000)
    p_serve.add_argument("--debug", action="store_true")
    p_serve.set_defaults(func=cmd_serve)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
