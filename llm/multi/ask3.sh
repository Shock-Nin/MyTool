#!/usr/bin/env bash
# ask3.sh - 同じ質問をローカルLLM複数体に並列で投げ、回答を1枚にまとめる
#
#   ./ask3.sh "質問文"
#   ./ask3.sh -f question.md
#   ./ask3.sh -o ~/Desktop/answer.md "質問文"
#   ./ask3.sh -H "最近の体重の傾向は？"     # 健康ログ（直近14日）を質問の前に付ける。-H 30 で30日
#   MODELS="ollama:qwen2.5:7b,lmstudio:openai/gpt-oss-20b" ./ask3.sh "質問文"
#
# 既定では Ollama と LM Studio で動いているモデルを自動検出し、先頭から NUM_MODELS 体
# (既定3体) に同じ質問を同時に投げる。結果は runs/<日時>/ に保存し、
# combined.md に全回答を1枚でまとめる。
#
# 環境変数: OLLAMA_URL LMSTUDIO_URL NUM_MODELS TIMEOUT RUNS_DIR
#
# macOS 標準の bash 3.2 でも動くように書いてある (mapfile/連想配列は使わない)。

set -o pipefail

OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
LMSTUDIO_URL="${LMSTUDIO_URL:-http://127.0.0.1:1234}"
TIMEOUT="${TIMEOUT:-600}"
NUM_MODELS="${NUM_MODELS:-3}"

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNS_DIR="${RUNS_DIR:-$BASE_DIR/runs}"

die() { printf 'エラー: %s\n' "$1" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || die "curl が見つかりません"
command -v jq   >/dev/null 2>&1 || die "jq が必要です。brew install jq を実行してください"

# ---------- 引数 ----------
QUESTION=""
OUT_COPY=""
HEALTH_DAYS=""
while [ $# -gt 0 ]; do
  case "$1" in
    -f|--file)
      [ -n "$2" ] || die "-f のあとにファイル名が必要です"
      [ -f "$2" ] || die "ファイルが見つかりません: $2"
      QUESTION="$(cat "$2")"; shift 2 ;;
    -o|--out)
      [ -n "$2" ] || die "-o のあとに出力先が必要です"
      OUT_COPY="$2"; shift 2 ;;
    -n|--num)
      NUM_MODELS="$2"; shift 2 ;;
    -H|--health)
      case "$2" in
        ''|*[!0-9]*) HEALTH_DAYS=14; shift ;;
        *) HEALTH_DAYS="$2"; shift 2 ;;
      esac ;;
    -h|--help)
      sed -n '2,16p' "$0"; exit 0 ;;
    *)
      if [ -z "$QUESTION" ]; then QUESTION="$1"; else QUESTION="$QUESTION $1"; fi
      shift ;;
  esac
done

case "$QUESTION" in
  "" ) die "質問を渡してください。例: ./ask3.sh \"質問文\"" ;;
esac

if [ -n "$HEALTH_DAYS" ]; then
  HEALTH_TEXT="$(python3 "$BASE_DIR/../health/health.py" "$HEALTH_DAYS")" || die "健康ログを読めません"
  QUESTION="$HEALTH_TEXT

$QUESTION"
fi

# ---------- 稼働中モデルの検出 ----------
list_ollama() {
  curl -sS -m 10 "$OLLAMA_URL/api/tags" 2>/dev/null | jq -r '.models[]?.name' 2>/dev/null
}
list_lmstudio() {
  curl -sS -m 10 "$LMSTUDIO_URL/v1/models" 2>/dev/null | jq -r '.data[]?.id' 2>/dev/null
}

OL_LIST=""; LM_LIST=""
while IFS= read -r m; do [ -n "$m" ] && OL_LIST="$OL_LIST$m
"; done <<EOF
$(list_ollama)
EOF
while IFS= read -r m; do [ -n "$m" ] && LM_LIST="$LM_LIST$m
"; done <<EOF
$(list_lmstudio)
EOF

TARGETS=""
if [ -n "${MODELS:-}" ]; then
  # 明示指定。カンマ区切りを改行に変える
  TARGETS="$(printf '%s' "$MODELS" | tr ',' '\n' | sed '/^[[:space:]]*$/d')"
else
  # Ollama と LM Studio を交互に拾って、同じ系統で3体埋まるのを避ける
  i=1
  while [ "$(printf '%s' "$TARGETS" | grep -c . )" -lt "$NUM_MODELS" ]; do
    o="$(printf '%s' "$OL_LIST" | sed -n "${i}p")"
    l="$(printf '%s' "$LM_LIST" | sed -n "${i}p")"
    [ -z "$o" ] && [ -z "$l" ] && break
    [ -n "$o" ] && TARGETS="$TARGETS
ollama:$o"
    [ "$(printf '%s' "$TARGETS" | grep -c . )" -ge "$NUM_MODELS" ] && break
    [ -n "$l" ] && TARGETS="$TARGETS
lmstudio:$l"
    i=$((i+1))
  done
  TARGETS="$(printf '%s' "$TARGETS" | sed '/^[[:space:]]*$/d' | head -n "$NUM_MODELS")"
fi

COUNT="$(printf '%s' "$TARGETS" | grep -c . )"
if [ "$COUNT" -eq 0 ]; then
  cat >&2 <<'MSG'
エラー: 応答するモデルが1つも見つかりませんでした。

  - Ollama:    ollama serve が動いているか / ollama list にモデルがあるか
  - LM Studio: アプリの Developer タブで "Start Server" を押し、
               モデルを1つロードしてあるか (既定 http://127.0.0.1:1234)

MODELS 環境変数で明示指定もできます。
  MODELS="ollama:qwen2.5:7b,lmstudio:openai/gpt-oss-20b" ./ask3.sh "質問"
MSG
  exit 1
fi

# ---------- 実行 ----------
STAMP="$(date '+%Y%m%d-%H%M%S')"
RUN_DIR="$RUNS_DIR/$STAMP"
mkdir -p "$RUN_DIR"
printf '%s\n' "$QUESTION" > "$RUN_DIR/question.md"

printf '質問を %s 体に投げます:\n' "$COUNT"
printf '%s\n' "$TARGETS" | sed 's/^/  - /'
printf '\n'

ask_ollama() {   # $1=model $2=outfile
  jq -n --arg m "$1" --arg q "$QUESTION" \
     '{model:$m, stream:false, messages:[{role:"user",content:$q}]}' \
  | curl -sS -m "$TIMEOUT" -X POST "$OLLAMA_URL/api/chat" \
      -H 'Content-Type: application/json' --data-binary @- \
  | jq -r 'if (.message.content // "") != "" then .message.content
           else "【応答を取得できませんでした】" + ((.error // .) | tostring) end' > "$2"
}

ask_lmstudio() { # $1=model $2=outfile
  jq -n --arg m "$1" --arg q "$QUESTION" \
     '{model:$m, stream:false, messages:[{role:"user",content:$q}]}' \
  | curl -sS -m "$TIMEOUT" -X POST "$LMSTUDIO_URL/v1/chat/completions" \
      -H 'Content-Type: application/json' --data-binary @- \
  | jq -r 'if (.choices[0].message.content // "") != "" then .choices[0].message.content
           else "【応答を取得できませんでした】" + ((.error // .) | tostring) end' > "$2"
}

idx=0
PIDS=""
SLOTS=""
while IFS= read -r t; do
  [ -z "$t" ] && continue
  idx=$((idx+1))
  backend="${t%%:*}"
  model="${t#*:}"
  slug="$(printf '%02d-%s' "$idx" "$(printf '%s' "$model" | tr '/:' '--' | tr -cd '[:alnum:]._-')")"
  out="$RUN_DIR/$slug.txt"
  SLOTS="$SLOTS$backend|$model|$out
"
  (
    start=$(date +%s)
    case "$backend" in
      ollama)   ask_ollama   "$model" "$out" ;;
      lmstudio) ask_lmstudio "$model" "$out" ;;
      *) printf '【未対応のバックエンド: %s】\n' "$backend" > "$out" ;;
    esac
    printf '%s' "$(( $(date +%s) - start ))" > "$out.sec"
    printf '  完了: %s (%s秒)\n' "$model" "$(cat "$out.sec")"
  ) &
  PIDS="$PIDS $!"
done <<EOF
$TARGETS
EOF

for p in $PIDS; do wait "$p"; done

# ---------- まとめ ----------
COMBINED="$RUN_DIR/combined.md"
{
  printf '# 3者回答まとめ\n\n'
  printf -- '- 実行: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  printf -- '- 回答数: %s\n\n' "$COUNT"
  printf '## 質問\n\n%s\n\n' "$QUESTION"
  printf -- '---\n\n'
  n=0
  while IFS='|' read -r backend model out; do
    [ -z "$backend" ] && continue
    n=$((n+1))
    sec="$(cat "$out.sec" 2>/dev/null || echo '?')"
    printf '## 回答%s: %s\n\n' "$n" "$model"
    printf -- '`%s` / %s秒\n\n' "$backend" "$sec"
    cat "$out" 2>/dev/null || printf '(出力なし)\n'
    printf '\n\n---\n\n'
  done <<EOF
$SLOTS
EOF
} > "$COMBINED"

if [ -n "$OUT_COPY" ]; then
  mkdir -p "$(dirname "$OUT_COPY")"
  cp "$COMBINED" "$OUT_COPY"
fi

printf '\nまとめ: %s\n' "$COMBINED"
[ -n "$OUT_COPY" ] && printf 'コピー: %s\n' "$OUT_COPY"
exit 0
