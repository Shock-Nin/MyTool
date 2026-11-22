#!/bin/zsh
# 記憶の自動反映を登録する（1回だけダブルクリック。もう一度実行すると登録し直す）
#   - llm/data（llm_memory.json など）が変わったときと、ログイン時に
#     export_to_apps.py --if-needed を実行する（反映が必要なときだけ動く）
#   - つながらなかった VM・VPS には、次に記憶が変わったときかログイン時に送り直す
#     （すぐ送りたいときは update_llm.command をダブルクリック）
#   - ログ: ~/Library/Logs/llm-sync.log
#   - 解除: ./install_auto_sync.command --remove
cd "$(dirname "$0")"
DIR="$PWD"
LABEL="com.mytool.llm-sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/llm-sync.log"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
if [[ "$1" == "--remove" ]]; then
  rm -f "$PLIST"
  echo "自動反映を解除しました"
  exit 0
fi

export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
PY="$(command -v python3)"
OL="$(command -v ollama)"
if [[ -z "$PY" || -z "$OL" ]]; then
  echo "python3 または ollama が見つかりません（python3: ${PY:-なし} / ollama: ${OL:-なし}）"
  exit 1
fi
PATHS="${OL:h}:${PY:h}:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$DIR/export_to_apps.py</string>
    <string>--if-needed</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$PATHS</string>
    <key>PYTHONIOENCODING</key><string>utf-8</string>
  </dict>
  <key>WatchPaths</key><array><string>$DIR/data</string></array>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLIST

if launchctl bootstrap "gui/$(id -u)" "$PLIST"; then
  echo "自動反映を登録しました（記憶が変わったとき・ログイン時）"
  echo "python3: $PY"
  echo "ollama : $OL"
  echo "ログ   : $LOG"
else
  echo "登録に失敗しました"
  exit 1
fi
