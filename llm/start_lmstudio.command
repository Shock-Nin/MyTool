#!/bin/zsh
# Ollama と LM Studio を開き、記憶を両方に反映する
# （ダブルクリックで実行。Dock に置いておくと便利）
cd "$(dirname "$0")"

# Ollama アプリを開き、サーバーが応答するまで最大30秒待つ（モデル更新に必要）
open -a "Ollama"
for i in {1..30}; do
  curl -s -o /dev/null http://localhost:11434/api/version && break
  sleep 1
done

python3 export_to_apps.py
open -a "LM Studio"
