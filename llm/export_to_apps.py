#!/usr/bin/env python3
"""
記憶を Ollama / LM Studio のアプリ画面でも使えるように書き出す

- Ollama   : 記憶入りのカスタムモデル（既定名 my-assistant）を作成・更新
- LM Studio: プリセット（既定 profile）のシステムプロンプトを直接書き換え、
             export/lmstudio_system_prompt.txt も更新（--copy でクリップボードにも入る）

chat_memory.py の起動時（記憶がアプリ側より新しいとき）・終了時と、add_profile.py / add_persona.py の
実行後に自動で呼ばれるので、普段は手で実行する必要はありません。

使い方:
    python3 export_to_apps.py --base qwen3:8b    # 初回だけ元モデルを指定（次回から記憶される）
    python3 export_to_apps.py                    # 手動で同期
    python3 export_to_apps.py --copy             # LM Studio用テキストをクリップボードへ
    python3 export_to_apps.py --name work-ai     # Ollamaモデル名を変える（記憶される）
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from chat_memory import (EXPORT_DIR, MEMORY_FILE, build_system_prompt, load_memory,
                         load_settings, update_settings)

LM_FILE = EXPORT_DIR / "lmstudio_system_prompt.txt"
MODELFILE = EXPORT_DIR / "Modelfile"
SYNC_STATE = EXPORT_DIR / ".ollama_synced"   # 最後に Ollama へ反映した Modelfile のハッシュ
LMSTUDIO_PRESET_DIR = Path(os.environ.get("LMSTUDIO_PRESET_DIR",
                                          Path.home() / ".lmstudio" / "config-presets"))
PROMPT_KEY = "llm.prediction.systemPrompt"


def _write_if_changed(path, text) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _modelfile_text(base: str, prompt: str) -> str:
    escaped = prompt.replace('"""', '\\"\\"\\"')
    return f'FROM {base}\nSYSTEM """\n{escaped}\n"""\n'


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ollama_synced(text: str) -> bool:
    return SYNC_STATE.exists() and SYNC_STATE.read_text(encoding="utf-8").strip() == _hash(text)


def _preset_path() -> Path:
    return LMSTUDIO_PRESET_DIR / f"{load_settings().get('lmstudio_preset', 'profile')}.preset.json"


def _preset_prompt(path: Path) -> Optional[str]:
    try:
        fields = json.loads(path.read_text(encoding="utf-8")).get("operation", {}).get("fields", [])
    except (OSError, json.JSONDecodeError):
        return None
    return next((f.get("value") for f in fields if f.get("key") == PROMPT_KEY), None)


def update_lmstudio_preset(prompt: str) -> str:
    """LM Studio のプリセットファイルのシステムプロンプトを書き換える（他の設定はそのまま）"""
    path = _preset_path()
    if not path.exists():
        return f"プリセットが見つかりません（{path}）"
    data = json.loads(path.read_text(encoding="utf-8"))   # 書き込み直前に読み直す
    fields = data.setdefault("operation", {}).setdefault("fields", [])
    field = next((f for f in fields if f.get("key") == PROMPT_KEY), None)
    if field and field.get("value") == prompt:
        return "変更なし"
    if field:
        field["value"] = prompt
    else:
        fields.append({"key": PROMPT_KEY, "value": prompt})
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return "更新しました"


def needs_sync() -> bool:
    """記憶の内容が LM Studio用テキスト・Ollamaモデルにまだ反映されていなければ True"""
    prompt = build_system_prompt(load_memory(MEMORY_FILE))
    if not LM_FILE.exists() or LM_FILE.read_text(encoding="utf-8") != prompt:
        return True
    if _preset_path().exists() and _preset_prompt(_preset_path()) != prompt:
        return True
    base = load_settings().get("ollama_base")
    return bool(base) and not _ollama_synced(_modelfile_text(base, prompt))


def _ollama_has(name: str) -> bool:
    r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    return r.returncode == 0 and any(
        line.split()[0] in (name, f"{name}:latest") for line in r.stdout.splitlines()[1:] if line.strip())


def sync(base: Optional[str] = None, name: Optional[str] = None, copy: bool = False) -> None:
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
    preset_msg = update_lmstudio_preset(prompt)
    print(f"[同期] LM Studioプリセット「{settings.get('lmstudio_preset', 'profile')}」: {preset_msg}")
    if preset_msg == "更新しました":
        print("        → LM Studio を開いている場合は、一度終了して開き直すと反映されます")

    # Ollama
    base, name = settings["ollama_base"], settings["ollama_name"]
    if not base:
        print("[同期] Ollama: 元モデルが未設定です。一度だけ `python3 export_to_apps.py --base qwen3:8b` を実行してください")
        return
    text = _modelfile_text(base, prompt)
    changed = _write_if_changed(MODELFILE, text)
    if not shutil.which("ollama"):
        print(f"[同期] Ollama: コマンドが見つかりません。手動で `ollama create {name} -f \"{MODELFILE}\"`")
        return
    if not changed and _ollama_synced(text) and _ollama_has(name):
        print(f"[同期] Ollamaモデル「{name}」: 変更なし")
        return
    r = subprocess.run(["ollama", "create", name, "-f", str(MODELFILE)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        SYNC_STATE.write_text(_hash(text), encoding="utf-8")
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
        sys.exit(f"[エラー] 記憶が空です: {MEMORY_FILE}\n先に profile/add_profile.py を実行してください。")
    sync(a.base, a.name, a.copy)


if __name__ == "__main__":
    main()
