#!/usr/bin/env bash
# watch.sh - queue/ に置かれた質問ファイルを拾って ask3.sh を走らせる常駐スクリプト
#
#   ./watch.sh          # 5秒ごとに queue/*.txt を見る。Ctrl+C で終了
#
# queue/ に質問を書いた .txt を置くと、answers/<同じ名前>.md に3者の回答が出る。
# 処理済みの質問ファイルは queue/done/ に移す。
# これを動かしておけば、Claude 側から queue/ に質問を置くだけで3者に投げられる。
#
# あわせて profile/update_profile.py --watch を子プロセスで常駐させる
# （MyAI/profile の PDF・Excel を保存すると、数秒後にプロフィールを作り直す）。
#   - 落ちたら60秒おきに起動し直す。watch.sh が終わると一緒に止まる
#   - 止めたいときは PROFILE_WATCH=0 で起動する

set -o pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
QUEUE="$BASE_DIR/queue"
DONE="$BASE_DIR/queue/done"
ANSWERS="$BASE_DIR/answers"
INTERVAL="${INTERVAL:-5}"
PROFILE_PY="$(cd "$BASE_DIR/.." && pwd)/profile/update_profile.py"
PROFILE_WATCH="${PROFILE_WATCH:-1}"
PROFILE_RETRY="${PROFILE_RETRY:-60}"   # プロフィール監視が落ちたときに起動し直す間隔（秒）
PROFILE_PID=""
PROFILE_STARTED=-9999

start_profile_watch() {
  [ "$PROFILE_WATCH" = "1" ] || return 0
  if [ -n "$PROFILE_PID" ] && kill -0 "$PROFILE_PID" 2>/dev/null; then
    return 0                                            # 動いている
  fi
  [ $((SECONDS - PROFILE_STARTED)) -ge "$PROFILE_RETRY" ] || return 0
  if [ -n "$PROFILE_PID" ]; then
    printf '[%s] プロフィール監視が止まっていたので起動し直します\n' "$(date '+%H:%M:%S')"
  fi
  PROFILE_STARTED=$SECONDS
  if ! command -v python3 >/dev/null 2>&1 || [ ! -f "$PROFILE_PY" ]; then
    printf '[%s] プロフィール監視を起動できません（python3: %s / %s）\n' \
      "$(date '+%H:%M:%S')" "$(command -v python3 || echo なし)" "$PROFILE_PY"
    return 0
  fi
  PYTHONIOENCODING=utf-8 python3 -u "$PROFILE_PY" --watch &
  PROFILE_PID=$!
  printf '[%s] プロフィール監視を起動: pid %s（%s）\n' "$(date '+%H:%M:%S')" "$PROFILE_PID" "$(command -v python3)"
}

stop_profile_watch() {
  [ -n "$PROFILE_PID" ] && kill "$PROFILE_PID" 2>/dev/null
  PROFILE_PID=""
}
trap stop_profile_watch EXIT
trap 'exit 0' INT TERM

mkdir -p "$QUEUE" "$DONE" "$ANSWERS"
printf '監視開始: %s\n' "$QUEUE"
printf '回答先:   %s\n' "$ANSWERS"
printf '終了:     Ctrl+C\n\n'

# 前回の watch.sh が強制終了されて残ったプロフィール監視があれば止める（二重起動を防ぐ）
pkill -f "profile/update_profile.py --watch" 2>/dev/null

while true; do
  start_profile_watch
  for f in "$QUEUE"/*.txt; do
    [ -e "$f" ] || continue
    name="$(basename "$f" .txt)"
    printf '[%s] 受付: %s\n' "$(date '+%H:%M:%S')" "$name"
    # 名前が .9 で終わる質問（例: foo.9.txt）はローカル9人（ask9.sh）、それ以外は ask3.sh
    case "$name" in
      *.9) script="$BASE_DIR/ask9.sh" ;;
      *)   script="$BASE_DIR/ask3.sh" ;;
    esac
    if "$script" -f "$f" -o "$ANSWERS/$name.md"; then
      printf '[%s] 完了: %s\n\n' "$(date '+%H:%M:%S')" "$name"
    else
      printf '[%s] 失敗: %s\n\n' "$(date '+%H:%M:%S')" "$name"
    fi
    mv "$f" "$DONE/" 2>/dev/null || true
  done
  sleep "$INTERVAL"
done
