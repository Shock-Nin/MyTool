# multi-llm — 同じ質問を3者に投げて突き合わせる

ひとつの質問を複数のLLMに同時に投げ、回答を1枚のMarkdownにまとめる。
ルートが3本あり、用途が違う。

| | 答えるのは | 自動化 | 所要 | 費用 |
|---|---|---|---|---|
| ① `ask3.sh` | Ollama / LM Studio のローカルモデル | 完全自動 | 数十秒 | 無料 |
| ② デスクトップアプリ操作 | 本家 ChatGPT / Gemini / Copilot | 半自動（Claudeが画面操作） | 1問 数分 | 契約内 |
| ③ `ask3-api.sh` | 本家 OpenAI / Google / GitHub Models | 完全自動 | 数十秒 | 従量課金 |

本家3社を自動で回したいなら③。無料で回し続けたいなら①。②は「本家の画面でしか出ない結果」が要るときだけ。

---

## ① ローカルLLM版 — ask3.sh

事前準備:

    brew install jq            # まだなら
    ollama serve               # 別タブで常駐
    # LM Studio は Developer タブで Start Server を押し、モデルを1つロードしておく

実行:

    ./ask3.sh "業務自動化にローカルLLMとクラウドAPIのどちらを使うべきか"
    ./ask3.sh -f question.md -o ~/Desktop/answer.md
    MODELS="ollama:qwen2.5:7b,lmstudio:openai/gpt-oss-20b" ./ask3.sh "質問"

Ollama (11434) と LM Studio (1234) で動いているモデルを自動検出し、両方から交互に
3体ぶん拾って並列で投げる。結果は `runs/<日時>/combined.md`。

環境変数: `OLLAMA_URL` `LMSTUDIO_URL` `NUM_MODELS` `TIMEOUT` `RUNS_DIR`

### Claudeから直接投げたいとき — watch.sh

    ./watch.sh

`queue/*.txt` を5秒ごとに見て、見つけたら ask3.sh を回し `answers/<名前>.md` に書く。
これを常駐させておけば、Claude が `queue/` に質問ファイルを置くだけで3体に投げられる。
（ClaudeのMac側シェルは Linux コンテナで、Macの localhost には届かない。
  この queue 経由なら、ファイルのやりとりだけで成立する。）

---

## ② デスクトップアプリ操作

Claude が ChatGPT・Gemini・Copilot の画面を直接クリック／入力して回答を回収する。
2026-10-23 に3アプリすべてで実際に動作を確認済み。

分かったこと:

- **Gemini** がいちばん素直。アクセシビリティが効いていて、入力欄も送信ボタンも要素として掴める。
- **ChatGPT** (Electron) は送信ボタンの AXPress が背面では効かない。
  `app_type` を `overwrite_existing: true` で打ち直してから Return キーを送ると通る。
- **Copilot** は `app_type` を `target: "focused"` で打ち、Return キーで送信。
  送信ボタンのクリックは背面では効かない。
- クリップボード読み取りは許可されていないため、回答の回収はスクリーンショット経由。
  長い回答はスクロールしながら複数枚読む必要があり、ここがいちばん重い。

所要は1問あたり数分。毎回の質問に使うのは現実的でない。

---

## ③ クラウドAPI版 — ask3-api.sh

APIキーの取得（本人が実施。Claudeは代行しない）:

| サービス | 取得先 | メモ |
|---|---|---|
| OpenAI | https://platform.openai.com/api-keys | 支払い方法の登録が必要。従量課金 |
| Google Gemini | https://aistudio.google.com/apikey | 無料枠あり。レート制限はきつめ |
| GitHub Models | https://github.com/settings/personal-access-tokens | fine-grained PAT に **Models: read** を付与 |

GitHub Copilot のチャットそのものを叩くAPIは個人向けに公開されていない。
③の3本目は GitHub Models（OpenAI互換エンドポイントで各社モデルを呼べる）で代替している。

キーの置き場所（Claudeは値を見ない）:

    # ~/.zshrc
    export OPENAI_API_KEY="sk-..."
    export GEMINI_API_KEY="..."
    export GITHUB_TOKEN="github_pat_..."

実行:

    ./ask3-api.sh "質問文"
    ./ask3-api.sh -f question.md -o ~/Desktop/answer.md

設定済みのキーの分だけ並列で投げる。1つしかなくても動く。
モデル差し替え: `OPENAI_MODEL` `GEMINI_MODEL` `GITHUB_MODEL`

---

## 向き不向き

3者に投げて効くのは、視点が割れる問い。

- 効く: 設計判断、技術選定、文章の評価、リスクの洗い出し、見落としの発見
- 効かない: 事実確認、計算、仕様の参照、短い質問
  → 同じ答えが3回返るだけで、待ち時間とコストが増える

全部の質問を機械的に3者に流すより、割れそうな問いだけ回すほうが効く。
