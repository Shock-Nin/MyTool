#!/bin/zsh
# ローカルLLMの記憶を今すぐ反映する（ダブルクリックで実行）
#   - Ollama の記憶入りモデル my-assistant … Mac・Windows VM・VPS の3台（Tailscale 経由）
#   - Bionic 用テキスト（export/lmstudio_system_prompt.txt）
# アプリの起動はしない（Mac の Ollama が止まっていて反映が必要なときだけ、画面を出さずに起動する）。
# 普段は install_auto_sync.command で登録した自動実行（記憶が変わったとき・ログイン時）が同じことをする。
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
python3 export_to_apps.py "$@"
