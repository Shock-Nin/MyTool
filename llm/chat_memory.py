#!/usr/bin/env python3
"""
記憶付きローカルLLMチャット（Ollama / LM Studio 共通）

このフォルダの中だけで完結します（フォルダごと移動してもそのまま動きます）。
  data/llm_memory.json        記憶（プロフィール・/remember・会話の要約）
  profile/profile.json        プロフィールの原本 → profile/add_profile.py で記憶に反映
  profile/*.pdf, *.xlsx       置く・更新するとプロフィールを自動で作り直す（profile/update_profile.py）
  data/settings.json          前回のバックエンド・モデル等（自動保存）
  export/lmstudio_system_prompt.txt  LM Studio用（自動更新）
  export/Modelfile            Ollama用（自動更新）

使い方:
    python3 chat_memory.py                       # 前回と同じ設定で起動
        llmで起動(初回のみ)
        　　vi ~/.zshrc に alias llm="python3 ~/MyTool/llm/chat_memory.py"
    python3 chat_memory.py --backend lmstudio    # 指定した設定は次回も使われる
    python3 chat_memory.py --model qwen3:8b      # LM Studio名(qwen/qwen3-8b)でもOK

チャット終了時、記憶が変わっていれば  Ollamaモデルは自動で更新
    LM Studio プリセット更新用
    　　python3 export_to_apps.py --copy
"""
import argparse
import copy
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------- 設定 ----------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
EXPORT_DIR = HERE / "export"
MEMORY_FILE = DATA_DIR / "llm_memory.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
PROFILE_FILE = HERE / "profile" / "profile.json"
DEFAULT_MEMORY = MEMORY_FILE  # 旧版との互換用

BACKENDS = {
    "ollama": "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
}
MAX_SUMMARIES_IN_PROMPT = 5   # システムプロンプトに入れる直近の要約数
MAX_SUMMARIES_STORED = 50     # ファイルに残す要約の上限
BASE_PROMPT = "あなたは日本語で簡潔かつ正確に答えるアシスタントです。"

EMPTY_MEMORY = {"facts": [], "summaries": []}
DEFAULT_SETTINGS = {
    "backend": "ollama",
    "models": {},                  # バックエンドごとの前回モデル
    "ollama_base": None,           # Ollamaカスタムモデルの元モデル（例: qwen3:8b）
    "ollama_name": "my-assistant", # 作成するOllamaモデル名
}

HELP = """\
コマンド:
  /remember <内容>   記憶に追加（例: /remember 私はpandasをよく使う）
  /forget <番号>     記憶を削除（3 → 3番目の記憶、s2 → 2番目の要約。番号は /memory で確認）
  /memory            記憶の一覧を表示
  /backend <名前>    ollama / lmstudio を切り替え
  /model [名前]      モデル一覧を表示、または切り替え
  /sync              LM Studio用テキストとOllamaモデルを今すぐ更新
  /new               今の会話を要約して保存し、新しい会話を始める
  /exit              要約して保存し終了（/exit! で保存せず終了）
  /help              このヘルプ
"""


# ---------- JSONファイル共通 ----------
# 手で編集した内容を消さないよう、変更のたびにファイルを読み直してから保存する

def read_json(path: Path, default: dict) -> dict:
    path = Path(path)
    if not path.exists():
        return copy.deepcopy(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[エラー] JSONが壊れています: {path}\n{e}")
    for k, v in default.items():
        data.setdefault(k, copy.deepcopy(v))
    return data


def write_json(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def update_json(path: Path, default: dict, fn) -> dict:
    data = read_json(path, default)   # 直前に読み直す
    fn(data)
    write_json(path, data)
    return data


def load_memory(path: Path = MEMORY_FILE) -> dict:
    return read_json(path, EMPTY_MEMORY)


def update_memory(path: Path, fn) -> dict:
    return update_json(path, EMPTY_MEMORY, fn)


def load_settings() -> dict:
    return read_json(SETTINGS_FILE, DEFAULT_SETTINGS)


def update_settings(fn) -> dict:
    return update_json(SETTINGS_FILE, DEFAULT_SETTINGS, fn)


def build_system_prompt(mem: dict) -> str:
    parts = [BASE_PROMPT]
    if mem["facts"]:
        parts.append("\n# ユーザーについて覚えていること")
        parts += [f"- {f['text']}" for f in mem["facts"]]
    recent = mem["summaries"][-MAX_SUMMARIES_IN_PROMPT:]
    if recent:
        parts.append("\n# これまでの会話の要約（古い順）")
        parts += [f"[{s['date']}] {s['text']}" for s in recent]
    if len(parts) > 1:
        parts.append("\n上の情報は必要なときだけ自然に使い、毎回言及しないこと。")
    return "\n".join(parts)


# ---------- API ----------

def http_json(url: str, payload=None, stream=False, timeout=600):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError as e:
        raise ConnectionError(f"{url} に接続できません（アプリ／サーバーは起動していますか？）: {e.reason}")
    return resp if stream else json.loads(resp.read().decode("utf-8"))


def list_models(base: str) -> list[str]:
    return [m["id"] for m in http_json(f"{base}/models", timeout=10).get("data", [])]


def _norm(name: str) -> str:
    """qwen3:8b と qwen/qwen3-8b を同じものとして比較するための正規化"""
    return re.sub(r"[^a-z0-9]", "", name.lower().split("/")[-1])


def resolve_model(backend: str, requested: str | None) -> str:
    """指定 → 前回 → 先頭 の順でモデルを決める。名前の表記ゆれは自動で補正"""
    models = list_models(BACKENDS[backend])
    if not models:
        raise ConnectionError(f"{backend} にモデルがありません（LM Studioはモデルをダウンロード／ロードしてください）")
    want = requested or load_settings()["models"].get(backend)
    if not want:
        return models[0]
    if want in models:
        return want
    near = [m for m in models if _norm(want) in _norm(m) or _norm(m) in _norm(want)]
    if near:
        print(f"（「{want}」は {backend} では「{near[0]}」として使います）")
        return near[0]
    print(f"[注意] {backend} にモデル「{want}」がありません。利用可能: {', '.join(models)}")
    return models[0]


def remember_choice(backend: str, model: str) -> None:
    def fn(s):
        s["backend"] = backend
        s["models"][backend] = model
    update_settings(fn)


def chat_stream(base: str, model: str, messages: list):
    resp = http_json(f"{base}/chat/completions",
                     {"model": model, "messages": messages, "stream": True}, stream=True)
    for raw in resp:
        line = raw.decode("utf-8").strip()
        if not line.startswith("data:"):
            continue
        body = line[5:].strip()
        if body == "[DONE]":
            break
        try:
            delta = json.loads(body)["choices"][0].get("delta", {})
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
        if delta.get("content"):
            yield delta["content"]


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def summarize(base: str, model: str, history: list) -> str | None:
    convo = [m for m in history if m["role"] != "system"]
    if not any(m["role"] == "assistant" and m["content"] for m in convo):
        return None
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in convo)
    prompt = [
        {"role": "system", "content": "あなたは会話の要約係です。"},
        {"role": "user", "content":
            "次の会話から、今後の別の会話でも役立つ要点（ユーザーの状況・決めたこと・"
            "未解決の課題・好み）だけを、日本語で3〜5個の短い箇条書きにしてください。"
            "雑談・挨拶・一般知識の説明・あいまいで推測にすぎないことは省くこと。"
            "保存する価値のある内容がなければ「なし」とだけ答えること。\n\n" + transcript},
    ]
    res = http_json(f"{base}/chat/completions",
                    {"model": model, "messages": prompt, "stream": False})
    text = strip_think(res["choices"][0]["message"]["content"])
    return None if re.fullmatch(r"[「」\s]*なし[。.\s」]*", text) else text


# ---------- チャット ----------

class Session:
    def __init__(self, backend: str, model: str | None, mem_path: Path):
        self.mem_path = Path(mem_path)
        self.dirty = False   # 記憶が変わったら True（終了時にアプリ側へ同期）
        self.set_backend(backend, model)
        self.reset()

    def set_backend(self, backend: str, model: str | None = None):
        self.model = resolve_model(backend, model)
        self.backend, self.base = backend, BACKENDS[backend]
        remember_choice(self.backend, self.model)

    def reset(self):
        self.history = [{"role": "system", "content": build_system_prompt(load_memory(self.mem_path))}]

    def refresh_prompt(self):
        self.history[0]["content"] = build_system_prompt(load_memory(self.mem_path))
        self.dirty = True

    def save_summary(self):
        if not any(m["role"] == "assistant" for m in self.history):
            return
        print("（会話を要約して保存中…）")
        try:
            text = summarize(self.base, self.model, self.history)
        except Exception as e:
            print(f"[要約失敗] {e}")
            return
        if not text:
            print("（保存するほどの内容はありませんでした）")
            return
        entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": text}

        def add(mem):
            mem["summaries"].append(entry)
            mem["summaries"] = mem["summaries"][-MAX_SUMMARIES_STORED:]
        update_memory(self.mem_path, add)
        self.dirty = True
        print(f"保存しました:\n{text}")

    def sync_apps(self, force=False):
        if not (self.dirty or force):
            return
        if self.mem_path.resolve() != MEMORY_FILE.resolve():
            if force:
                print("（--memory で別ファイルを使っているため、アプリへの同期は行いません）")
            return
        from export_to_apps import sync   # 循環importを避けるためここで読み込む
        sync()
        self.dirty = False

    def forget(self, arg: str):
        is_summary = arg.lower().startswith("s")
        num = arg[1:] if is_summary else arg
        if not num.isdigit():
            print("番号を指定してください（例: /forget 3 、/forget s2）")
            return
        idx, key = int(num) - 1, ("summaries" if is_summary else "facts")
        removed = []

        def rm(mem):
            if 0 <= idx < len(mem[key]):
                removed.append(mem[key].pop(idx))
        update_memory(self.mem_path, rm)
        if removed:
            self.refresh_prompt()
            print(f"削除しました: {removed[0]['text'].splitlines()[0]}")
        else:
            print("その番号はありません。")

    def show_memory(self):
        mem = load_memory(self.mem_path)
        print(f"記憶ファイル: {self.mem_path}")
        print("■ 覚えていること")
        for i, f in enumerate(mem["facts"], 1):
            tag = "（profile）" if f.get("source") == "profile" else ""
            print(f"  {i}. {f['text']}{tag}")
        total = len(mem["summaries"])
        print(f"■ 会話の要約: {total}件（直近{MAX_SUMMARIES_IN_PROMPT}件を使用）")
        start = max(0, total - MAX_SUMMARIES_IN_PROMPT)
        for i, s in enumerate(mem["summaries"][start:], start + 1):
            print(f"  s{i}. [{s['date']}]\n      " + s["text"].replace("\n", "\n      "))

    def command(self, line: str) -> bool:
        """コマンドを処理。False を返したら終了。"""
        cmd, _, arg = line.partition(" ")
        arg = arg.strip()
        if cmd == "/help":
            print(HELP)
        elif cmd == "/remember" and arg:
            update_memory(self.mem_path, lambda m: m["facts"].append(
                {"text": arg, "date": datetime.now().strftime("%Y-%m-%d")}))
            self.refresh_prompt()
            print("覚えました。")
        elif cmd == "/forget" and arg:
            self.forget(arg)
        elif cmd == "/memory":
            self.show_memory()
        elif cmd == "/backend" and arg in BACKENDS:
            self.set_backend(arg)
            print(f"{arg} に切り替えました（モデル: {self.model}）")
        elif cmd == "/model":
            if arg:
                self.set_backend(self.backend, arg)
                print(f"モデル: {self.model}")
            else:
                for m in list_models(self.base):
                    print(("* " if m == self.model else "  ") + m)
        elif cmd == "/sync":
            self.sync_apps(force=True)
        elif cmd == "/new":
            self.save_summary()
            self.reset()
            print("新しい会話を始めます。")
        elif cmd == "/exit":
            self.save_summary()
            return False
        elif cmd == "/exit!":
            return False
        else:
            print("不明なコマンドです。/help を参照してください。")
        return True

    def run(self):
        print(f"[{self.backend}] モデル: {self.model}  （/help でコマンド一覧）")
        try:
            self.loop()
        finally:
            self.sync_apps()

    def loop(self):
        while True:
            try:
                line = input("\nあなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self.save_summary()
                return
            if not line:
                continue
            if line.startswith("/"):
                try:
                    if not self.command(line):
                        return
                except (ConnectionError, urllib.error.HTTPError) as e:
                    print(f"[エラー] {e}")
                continue

            self.history.append({"role": "user", "content": line})
            print("AI> ", end="", flush=True)
            reply = ""
            try:
                for piece in chat_stream(self.base, self.model, self.history):
                    print(piece, end="", flush=True)
                    reply += piece
                print()
            except (ConnectionError, urllib.error.HTTPError) as e:
                print(f"\n[エラー] {e}")
                self.history.pop()
                continue
            except KeyboardInterrupt:
                print("\n（中断）")
            self.history.append({"role": "assistant", "content": strip_think(reply)})


def check_profile_sources(backend, model):
    """profile フォルダの PDF / Excel が追加・更新されていれば、プロフィールを作り直す"""
    try:
        sys.path.insert(0, str(HERE / "profile"))
        from update_profile import check_and_update
        check_and_update(backend, model)
    except Exception as e:   # 失敗してもチャットは起動する
        print(f"[プロフィール] 資料のチェックをスキップしました: {e}")


def main():
    p = argparse.ArgumentParser(description="記憶付きローカルLLMチャット")
    p.add_argument("--backend", choices=BACKENDS, help="省略時は前回と同じ")
    p.add_argument("--model", help="省略時は前回と同じ（初回は最初に見つかったもの）")
    p.add_argument("--memory", type=Path, default=MEMORY_FILE, help="記憶ファイル（通常は指定不要）")
    a = p.parse_args()
    check_profile_sources(a.backend, a.model)
    try:
        Session(a.backend or load_settings()["backend"], a.model, a.memory).run()
    except ConnectionError as e:
        sys.exit(f"[エラー] {e}")


if __name__ == "__main__":
    main()
