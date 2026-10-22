#!/usr/bin/env bash
# watch.sh - queue/ に置かれた質問ファイルを拾って ask3.sh を走らせる常駐スクリプト
#
#   ./watch.sh          # 5秒ごとに queue/*.txt を見る。Ctrl+C で終了
#
# queue/ に質問を書いた .txt を置くと、answers/<同じ名前>.md に3者の回答が出る。
# 処理済みの質問ファイルは queue/done/ に移す。
# これを動かしておけば、Claude 側から queue/ に質問を置くだけで3者に投げられる。

set -o pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
QUEUE="$BASE_DIR/queue"
DONE="$BASE_DIR/queue/done"
ANSWERS="$BASE_DIR/answers"
INTERVAL="${INTERVAL:-5}"

mkdir -p "$QUEUE" "$DONE" "$ANSWERS"
printf '監視開始: %s\n' "$QUEUE"
printf '回答先:   %s\n' "$ANSWERS"
printf '終了:     Ctrl+C\n\n'

while true; do
  for f in "$QUEUE"/*.txt; do
    [ -e "$f" ] || continue
    name="$(basename "$f" .txt)"
    printf '[%s] 受付: %s\n' "$(date '+%H:%M:%S')" "$name"
    if "$BASE_DIR/ask3.sh" -f "$f" -o "$ANSWERS/$name.md"; then
      printf '[%s] 完了: %s\n\n' "$(date '+%H:%M:%S')" "$name"
    else
      printf '[%s] 失敗: %s\n\n' "$(date '+%H:%M:%S')" "$name"
    fi
    mv "$f" "$DONE/" 2>/dev/null || true
  done
  sleep "$INTERVAL"
done
