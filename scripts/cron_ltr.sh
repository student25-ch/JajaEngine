#!/usr/bin/env bash
# JajaEngine 每日训练：被 cron 或 systemd 调用
set -euo pipefail

cd "$(dirname "$0")/.."

LOG=data/logs/cron_ltr.log
mkdir -p data/logs

echo "[$(date -Iseconds)] 开始训练" >> "$LOG"

# 日志不足 100 条时跳过
if [ -f data/ltr/clicks.jsonl ]; then
  LINES=$(wc -l < data/ltr/clicks.jsonl | tr -d ' ')
else
  LINES=0
fi

if [ "$LINES" -lt 100 ]; then
  echo "[$(date -Iseconds)] 日志仅 $LINES 条，跳过训练" >> "$LOG"
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

"$PY" -m jaja.train_ltr >> "$LOG" 2>&1 || {
  echo "[$(date -Iseconds)] 训练失败" >> "$LOG"
  exit 1
}

"$PY" scripts/eval_offline.py >> "$LOG" 2>&1 || true

echo "[$(date -Iseconds)] 训练完成" >> "$LOG"
