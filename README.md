# JajaEngine

> 轻量、可读、零依赖（除 Web 层外）的开源中文搜索引擎。
> 维护者：**student25-ch** · 许可证：**GPLv3**

## 快速开始

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m jaja.cli build
python -m jaja.cli serve --port 8000
