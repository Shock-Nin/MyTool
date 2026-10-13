#!/usr/bin/env python3
"""
記憶を Ollama / LM Studio のアプリ画面でも使えるように書き出す

- Ollama   : 記憶入りのカスタムモデル（既定名 my-assistant）を作成・更新
- LM Studio: lmstudio_system_prompt.txt を更新（--copy でクリップボードにも入る）

chat_memory.py の終了時と add_profile.py の実行後に自動で呼ばれるので、
普段は手で実行する必要はありません。

使い方:
    python3 export_to_apps.py --base qwen3:8b    # 初回だけ元モデルを指定（次回から記憶される）
    python3 export_to_apps.py                    # 手動で同期
    python3 export_to_apps.py --copy             # LM Studio用テキストをクリップボードへ
    python3 export_to_apps.py --name work-ai     # Ollamaモデル名を変える（記憶される）
"""
import argparse
import shutil
import subprocess
import sys

from chat_memory import (HERE, MEMORY_FILE, build_system_prompt, load_memory,
                         load_settings, update_settings)

LM_FILE = HERE / "lmstudio_system_prompt.txt"
MODELFILE = HERE / "Modelfile"


def _write_if_changed(path, text) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _ollama_has(name: str) -> bool:
    r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    return r.returncode == 0 and any(
        line.split()[0] in (name, f"{name}:latest") for line in r.stdout.splitlines()[1:] if line.strip())


def sync(base: str | None = None, name: str | None = None, copy: bool = False) -> None:
    if base or name:
        update_settings(lambda s: s.update({k: v for k, v in
                                            (("ollama_base", base), ("ollama_name", name)) if v}))
    settings = load_settings()
    prompt = build_system_prompt(load_memory(MEMORY_FILE))

    # LM Studio
    changed = _write_if_changed(LM_FILE, prompt)
    msg = "更新しました" if changed else "変更なし"
    if copy:
        if shutil.which("pbcopy"):
            subprocess.run(["pbcopy"], input=prompt.encode("utf-8"))
            msg += "・クリップボードにコピーしました"
        else:
            msg += "（pbcopy が無いためコピーできません）"
    print(f"[同期] LM Studio用テキスト: {msg}")
    if changed:
        print("        → LM Studio のプリセットに貼り直して上書き保存してください（--copy で楽にできます）")

    # Ollama
    base, name = settings["ollama_base"], settings["ollama_name"]
    if not base:
        print("[同期] Ollama: 元モデルが未設定です。一度だけ `python3 export_to_apps.py --base qwen3:8b` を実行してください")
        return
    escaped = prompt.replace('"""', '\\"\\"\\"')
    changed = _write_if_changed(MODELFILE, f'FROM {base}\nSYSTEM """\n{escaped}\n"""\n')
    if not shutil.which("ollama"):
        print(f"[同期] Ollama: コマンドが見つかりません。手動で `ollama create {name} -f \"{MODELFILE}\"`")
        return
    if not changed and _ollama_has(name):
        print(f"[同期] Ollamaモデル「{name}」: 変更なし")
        return
    r = subprocess.run(["ollama", "create", name, "-f", str(MODELFILE)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"[同期] Ollamaモデル「{name}」を更新しました（元: {base}）")
    else:
        print(f"[同期] Ollamaモデルの作成に失敗: {(r.stderr or r.stdout).strip()[-300:]}")
        print("        元モデル名が正しいか `ollama list` で確認してください")


def main():
    p = argparse.ArgumentParser(description="記憶を Ollama / LM Studio に書き出す")
    p.add_argument("--base", help="Ollamaの元モデル（例: qwen3:8b）。一度指定すれば記憶される")
    p.add_argument("--name", help="作成するOllamaモデル名（既定: my-assistant）")
    p.add_argument("--copy", action="store_true", help="LM Studio用テキストをクリップボードへコピー")
    a = p.parse_args()
    mem = load_memory(MEMORY_FILE)
    if not mem["facts"] and not mem["summaries"]:
        sys.exit(f"[エラー] 記憶が空です: {MEMORY_FILE}\n先に add_profile.py を実行してください。")
    sync(a.base, a.name, a.copy)


if __name__ == "__main__":
    main()
