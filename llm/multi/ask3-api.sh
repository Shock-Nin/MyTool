#!/usr/bin/env bash
# ask3-api.sh - 本家3社のクラウドAPIに同じ質問を並列で投げ、回答を1枚にまとめる
#
#   ./ask3-api.sh "質問文"
#   ./ask3-api.sh -f question.md -o ~/Desktop/answer.md
#
# 必要な環境変数 (ある分だけ使う。1つでも入っていれば動く)
#   OPENAI_API_KEY   https://platform.openai.com/api-keys
#   GEMINI_API_KEY   https://aistudio.google.com/apikey
#   GITHUB_TOKEN     https://github.com/settings/personal-access-tokens
#                    (fine-grained PAT に Models: read を付ける / GitHub Models 経由)
#
# ~/.zshrc に書くか、1Password などから流し込んで使う:
#   export OPENAI_API_KEY="sk-..."
#
# モデルは環境変数で差し替えられる: OPENAI_MODEL GEMINI_MODEL GITHUB_MODEL

set -o pipefail

OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-pro}"
GITHUB_MODEL="${GITHUB_MODEL:-openai/gpt-4o}"
TIMEOUT="${TIMEOUT:-300}"

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNS_DIR="${RUNS_DIR:-$BASE_DIR/runs-api}"

die() { printf 'エラー: %s\n' "$1" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || die "curl が見つかりません"
command -v jq   >/dev/null 2>&1 || die "jq が必要です。brew install jq"

QUESTION=""; OUT_COPY=""
while [ $# -gt 0 ]; do
  case "$1" in
    -f|--file) [ -f "$2" ] || die "ファイルが見つかりません: $2"; QUESTION="$(cat "$2")"; shift 2 ;;
    -o|--out)  OUT_COPY="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) if [ -z "$QUESTION" ]; then QUESTION="$1"; else QUESTION="$QUESTION $1"; fi; shift ;;
  esac
done
[ -n "$QUESTION" ] || die "質問を渡してください"

STAMP="$(date '+%Y%m%d-%H%M%S')"
RUN_DIR="$RUNS_DIR/$STAMP"
mkdir -p "$RUN_DIR"
printf '%s\n' "$QUESTION" > "$RUN_DIR/question.md"

# OpenAI 互換のエンドポイントに投げる共通処理
# $1=ラベル $2=URL $3=認証ヘッダ $4=モデル $5=出力先
ask_openai_compatible() {
  jq -n --arg m "$4" --arg q "$QUESTION" \
     '{model:$m, messages:[{role:"user",content:$q}]}' \
  | curl -sS -m "$TIMEOUT" -X POST "$2" \
      -H 'Content-Type: application/json' -H "$3" --data-binary @- \
  | jq -r 'if (.choices[0].message.content // "") != "" then .choices[0].message.content
           else "【取得できませんでした】" + ((.error.message // .error // .) | tostring) end' > "$5"
}

SLOTS=""
PIDS=""
add() { SLOTS="$SLOTS$1|$2|$3
"; }

if [ -n "${OPENAI_API_KEY:-}" ]; then
  out="$RUN_DIR/01-openai.txt"; add "ChatGPT (OpenAI)" "$OPENAI_MODEL" "$out"
  ( s=$(date +%s)
    ask_openai_compatible "openai" "https://api.openai.com/v1/chat/completions" \
      "Authorization: Bearer $OPENAI_API_KEY" "$OPENAI_MODEL" "$out"
    printf '%s' "$(( $(date +%s) - s ))" > "$out.sec"; printf '  完了: ChatGPT\n' ) &
  PIDS="$PIDS $!"
fi

if [ -n "${GEMINI_API_KEY:-}" ]; then
  out="$RUN_DIR/02-gemini.txt"; add "Gemini (Google)" "$GEMINI_MODEL" "$out"
  ( s=$(date +%s)
    ask_openai_compatible "gemini" "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
      "Authorization: Bearer $GEMINI_API_KEY" "$GEMINI_MODEL" "$out"
    printf '%s' "$(( $(date +%s) - s ))" > "$out.sec"; printf '  完了: Gemini\n' ) &
  PIDS="$PIDS $!"
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  out="$RUN_DIR/03-github.txt"; add "GitHub Models" "$GITHUB_MODEL" "$out"
  ( s=$(date +%s)
    ask_openai_compatible "github" "https://models.github.ai/inference/chat/completions" \
      "Authorization: Bearer $GITHUB_TOKEN" "$GITHUB_MODEL" "$out"
    printf '%s' "$(( $(date +%s) - s ))" > "$out.sec"; printf '  完了: GitHub Models\n' ) &
  PIDS="$PIDS $!"
fi

if [ -z "$PIDS" ]; then
  die "APIキーが1つも設定されていません。OPENAI_API_KEY / GEMINI_API_KEY / GITHUB_TOKEN のいずれかを export してください"
fi

for p in $PIDS; do wait "$p"; done

COMBINED="$RUN_DIR/combined.md"
{
  printf '# 3社API 回答まとめ\n\n- 実行: %s\n\n## 質問\n\n%s\n\n---\n\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$QUESTION"
  while IFS='|' read -r label model out; do
    [ -z "$label" ] && continue
    printf '## %s\n\n`%s` / %s秒\n\n' "$label" "$model" "$(cat "$out.sec" 2>/dev/null || echo '?')"
    cat "$out" 2>/dev/null || printf '(出力なし)\n'
    printf '\n\n---\n\n'
  done <<EOF
$SLOTS
EOF
} > "$COMBINED"

[ -n "$OUT_COPY" ] && { mkdir -p "$(dirname "$OUT_COPY")"; cp "$COMBINED" "$OUT_COPY"; }
printf '\nまとめ: %s\n' "$COMBINED"
