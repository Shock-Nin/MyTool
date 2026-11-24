#!/usr/bin/env bash
# ask9.sh - ローカルLLM 3モデル × 3性格 = 9人に同じ質問を投げ、回答を1枚にまとめる
#
#   ./ask9.sh "質問文"
#   ./ask9.sh -f question.txt -o ~/Desktop/answer.md
#
# 割り振り（3台×3性格で、同じ「モデル×性格」が重ならない）:
#           楽観派         思いつき派      慎重派
#   Mac     qwen3.8:27b    gemma4:31b      mistral-small3.2:24b
#   VM      gemma4:31b     mistral-small3.2:24b  qwen3.8:27b
#   VPS     mistral-small3.2:24b  qwen3.8:27b    gemma4:31b
# モデルはすべて Mac の Ollama で動くため、実行は Mac で行う（台の名前は表示用）。
# モデルごとに1本の流れで3性格を順に処理し、3モデルは並列に動かす。
#
# 環境変数: OLLAMA_URL TIMEOUT RUNS_DIR QWEN GEMMA MISTRAL
# macOS 標準の bash 3.2 でも動くように書いてある。

set -o pipefail

OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
TIMEOUT="${TIMEOUT:-900}"
QWEN="${QWEN:-qwen3.8:27b}"
GEMMA="${GEMMA:-gemma4:31b}"
MISTRAL="${MISTRAL:-mistral-small3.2:24b}"

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNS_DIR="${RUNS_DIR:-$BASE_DIR/runs9}"

die() { printf 'エラー: %s\n' "$1" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || die "curl が見つかりません"
command -v jq   >/dev/null 2>&1 || die "jq が必要です。brew install jq を実行してください"

QUESTION=""; OUT_COPY=""
while [ $# -gt 0 ]; do
  case "$1" in
    -f|--file) [ -f "$2" ] || die "ファイルが見つかりません: $2"; QUESTION="$(cat "$2")"; shift 2 ;;
    -o|--out)  OUT_COPY="$2"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) if [ -z "$QUESTION" ]; then QUESTION="$1"; else QUESTION="$QUESTION $1"; fi; shift ;;
  esac
done
[ -n "$QUESTION" ] || die "質問を渡してください。例: ./ask9.sh \"質問文\""

persona_prompt() {  # $1=性格キー
  case "$1" in
    optimist) echo "あなたは「楽観派」です。うまくいった場合の可能性とメリットを最大限に見て答えてください。" ;;
    impulse)  echo "あなたは「思いつき派」です。深く考えず直感で、今すぐ試せる意外な一手を出してください。" ;;
    cautious) echo "あなたは「慎重派」です。リスク・落とし穴・反対意見を遠慮なく挙げてください。" ;;
  esac
}
persona_name() {
  case "$1" in optimist) echo "楽観派";; impulse) echo "思いつき派";; cautious) echo "慎重派";; esac
}
FORMAT="必ず日本語で、前置きなしに次の形式だけで答えてください。
【結論】賛成／反対／条件付き のどれか1つ（1行）
【理由】3行以内
口調だけでなく、結論そのものがほかの人と違ってかまいません。"

# 割り振り表: 台|性格|モデル
ASSIGN="Mac|optimist|$QWEN
Mac|impulse|$GEMMA
Mac|cautious|$MISTRAL
VM|optimist|$GEMMA
VM|impulse|$MISTRAL
VM|cautious|$QWEN
VPS|optimist|$MISTRAL
VPS|impulse|$QWEN
VPS|cautious|$GEMMA"

STAMP="$(date '+%Y%m%d-%H%M%S')"
RUN_DIR="$RUNS_DIR/$STAMP"
mkdir -p "$RUN_DIR"
printf '%s\n' "$QUESTION" > "$RUN_DIR/question.md"

ask_one() {  # $1=台 $2=性格 $3=モデル
  out="$RUN_DIR/$1-$2.txt"
  sys="$(persona_prompt "$2")

$FORMAT"
  # thinking 対応モデルは思考を切って速くする（非対応モデルに付けるとエラーになるため付けない）
  case "$3" in qwen3*|gemma4*) think='false' ;; *) think='null' ;; esac
  start=$(date +%s)
  jq -n --arg m "$3" --arg s "$sys" --arg q "$QUESTION" --argjson t "$think" \
     '{model:$m, stream:false, keep_alive:"30m",
       messages:[{role:"system",content:$s},{role:"user",content:$q}]}
      + (if $t == null then {} else {think:$t} end)' \
  | curl -sS -m "$TIMEOUT" -X POST "$OLLAMA_URL/api/chat" \
      -H 'Content-Type: application/json' --data-binary @- \
  | jq -r 'if (.message.content // "") != "" then .message.content
           else "【応答を取得できませんでした】" + ((.error // .) | tostring) end' > "$out"
  printf '%s' "$(( $(date +%s) - start ))" > "$out.sec"
  printf '  完了: %s %s (%s / %s秒)\n' "$1" "$(persona_name "$2")" "$3" "$(cat "$out.sec")"
}

printf '9人に質問します（3モデル並列）\n'
PIDS=""
for model in "$QWEN" "$GEMMA" "$MISTRAL"; do
  (
    printf '%s\n' "$ASSIGN" | while IFS='|' read -r host key m; do
      [ "$m" = "$model" ] && ask_one "$host" "$key" "$m"
    done
  ) &
  PIDS="$PIDS $!"
done
for p in $PIDS; do wait "$p"; done

conclusion() {  # 回答から【結論】の行を1行抜き出す
  grep -m1 '【結論】' "$1" 2>/dev/null | sed 's/.*【結論】[：: ]*//' | cut -c1-60
}

COMBINED="$RUN_DIR/combined.md"
{
  printf '# ローカルLLM 9人の回答\n\n'
  printf -- '- 実行: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  printf '## 質問\n\n%s\n\n' "$QUESTION"
  printf '## 結論の一覧\n\n| 台 | 楽観派 | 思いつき派 | 慎重派 |\n|---|---|---|---|\n'
  for host in Mac VM VPS; do
    row="| $host"
    for key in optimist impulse cautious; do
      m="$(printf '%s\n' "$ASSIGN" | awk -F'|' -v h="$host" -v k="$key" '$1==h && $2==k {print $3}')"
      row="$row | $(conclusion "$RUN_DIR/$host-$key.txt")（${m}）"
    done
    printf '%s |\n' "$row"
  done
  printf '\n---\n\n'
  printf '%s\n' "$ASSIGN" | while IFS='|' read -r host key m; do
    f="$RUN_DIR/$host-$key.txt"
    printf '## %s・%s（%s / %s秒）\n\n' "$host" "$(persona_name "$key")" "$m" "$(cat "$f.sec" 2>/dev/null || echo '?')"
    cat "$f" 2>/dev/null || printf '(出力なし)\n'
    printf '\n\n'
  done
} > "$COMBINED"

[ -n "$OUT_COPY" ] && cp "$COMBINED" "$OUT_COPY"
printf '\nまとめ: %s\n' "$COMBINED"
[ -n "$OUT_COPY" ] && printf 'コピー: %s\n' "$OUT_COPY"
exit 0
