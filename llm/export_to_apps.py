#!/usr/bin/env python3
"""
記憶を Ollama・Bionic でも使えるように書き出す

- Ollama   : 記憶入りのカスタムモデル（既定名 my-assistant）を作成・更新
             settings.json の ollama_remotes にある端末（Windows VM・VPS）にも
             Tailscale 経由で同じモデルを作る（つながらない端末は飛ばして次回に再挑戦）
             同期のあと・自動実行のたびに、VM・VPS の記憶が Mac と違えば警告する
             （ターミナル表示と Mac の通知。check_remotes）
- Bionic   : export/lmstudio_system_prompt.txt を更新（Bionic の my-profile スキルが読む。
             --copy でクリップボードにも入る）。LM Studio アプリは 2026-11-22 に削除したため、
             プリセットの書き換えは settings.json の lmstudio_preset が null のあいだは行わない

chat_memory.py の起動時（記憶がアプリ側より新しいとき）・終了時と、add_profile.py / add_persona.py の
実行後に自動で呼ばれるほか、install_auto_sync.command で登録した自動実行
（記憶が変わったとき・ログイン時、--if-needed 付き）でも動くので、普段は手で実行する必要はありません。

使い方:
    python3 export_to_apps.py --base qwen3:8b    # 初回だけ元モデルを指定（次回から記憶される）
    python3 export_to_apps.py                    # 手動で同期
    python3 export_to_apps.py --copy             # LM Studio用テキストをクリップボードへ
    python3 export_to_apps.py --name work-ai     # Ollamaモデル名を変える（記憶される）
    python3 export_to_apps.py --if-needed        # 反映が必要なときだけ同期（自動実行用）
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

from chat_memory import (EXPORT_DIR, MEMORY_FILE, build_system_prompt, load_memory,
                         load_settings, update_settings)

LM_FILE = EXPORT_DIR / "lmstudio_system_prompt.txt"
MODELFILE = EXPORT_DIR / "Modelfile"
SYNC_STATE = EXPORT_DIR / ".ollama_synced"   # 最後に Ollama へ反映した Modelfile のハッシュ
REMOTE_STATE = EXPORT_DIR / ".ollama_remote_synced.json"   # ほかの端末ごとの同じハッシュ
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


def _remotes() -> dict:
    """{"表示名": "http://<TailscaleのIP>:11434"} … settings.json の ollama_remotes"""
    return load_settings().get("ollama_remotes") or {}


def _remote_state() -> dict:
    try:
        return json.loads(REMOTE_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _remote_synced(host: str, text: str) -> bool:
    return _remote_state().get(host) == _hash(text)


def _save_remote_state(host: str, text: str) -> None:
    state = _remote_state()   # 書き込み直前に読み直す
    state[host] = _hash(text)
    REMOTE_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _reachable(host: str) -> bool:
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/version", timeout=3):
            return True
    except Exception:
        return False


LOCAL_OLLAMA = "http://localhost:11434"


def _ensure_local_ollama() -> None:
    """Mac の Ollama が止まっていれば画面を出さずに起動し、応答するまで最大30秒待つ"""
    if _reachable(LOCAL_OLLAMA) or sys.platform != "darwin":
        return
    subprocess.run(["open", "-g", "-j", "-a", "Ollama"], capture_output=True)
    for _ in range(30):
        time.sleep(1)
        if _reachable(LOCAL_OLLAMA):
            return


def _remote_system(host: str, name: str) -> Optional[str]:
    """ほかの端末の Ollama モデルに入っている記憶（SYSTEM）。モデルが無ければ None"""
    req = urllib.request.Request(host.rstrip("/") + "/api/show",
                                 data=json.dumps({"model": name}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8")).get("system") or ""
    except Exception:
        return None


def _norm(text: str) -> str:
    return " ".join(text.split())


def _notify(message: str) -> None:
    if sys.platform != "darwin":
        return
    msg = message.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "ローカルLLMの記憶" sound name "Basso"'],
                   capture_output=True)


def check_remotes() -> list:
    """VM・VPS の記憶が Mac と違えば警告する（違う端末の一覧を返す）"""
    settings = load_settings()
    base, name = settings.get("ollama_base"), settings.get("ollama_name", "my-assistant")
    if not base or not _remotes():
        return []
    prompt = build_system_prompt(load_memory(MEMORY_FILE))
    text = _modelfile_text(base, prompt)
    problems = []
    for label, host in _remotes().items():
        if not _reachable(host):
            if not _remote_synced(host, text):
                problems.append(f"{label}: つながらず、最新の記憶がまだ反映されていません")
            continue
        remote = _remote_system(host, name)
        if remote is None:
            problems.append(f"{label}: Ollamaモデル「{name}」がありません")
        elif _norm(remote) != _norm(prompt):
            problems.append(f"{label}: 記憶が Mac と異なります")
    if problems:
        print("⚠️ [警告] VM・VPS の記憶が Mac と一致していません")
        for line in problems:
            print(f"        - {line}")
        print("        → 端末を起動して Tailscale につないでから update_llm.command を実行してください")
        _notify(" / ".join(problems))
    return problems


def _ollama_env(host: Optional[str]) -> Optional[dict]:
    if not host:
        return None   # この端末：環境変数はそのまま
    return {**os.environ, "OLLAMA_HOST": host}


def _preset_path() -> Optional[Path]:
    name = load_settings().get("lmstudio_preset", "profile")
    return LMSTUDIO_PRESET_DIR / f"{name}.preset.json" if name else None


def _preset_prompt(path: Path) -> Optional[str]:
    try:
        fields = json.loads(path.read_text(encoding="utf-8")).get("operation", {}).get("fields", [])
    except (OSError, json.JSONDecodeError):
        return None
    return next((f.get("value") for f in fields if f.get("key") == PROMPT_KEY), None)


def update_lmstudio_preset(prompt: str) -> str:
    """LM Studio のプリセットファイルのシステムプロンプトを書き換える（他の設定はそのまま）"""
    path = _preset_path()
    if path is None:
        return "使わない設定"
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
    preset = _preset_path()
    if preset and preset.exists() and _preset_prompt(preset) != prompt:
        return True
    base = load_settings().get("ollama_base")
    if not base:
        return False
    text = _modelfile_text(base, prompt)
    return not _ollama_synced(text) or any(not _remote_synced(h, text) for h in _remotes().values())


def _ollama_has(name: str, host: Optional[str] = None) -> bool:
    r = subprocess.run(["ollama", "list"], capture_output=True, text=True, env=_ollama_env(host))
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
    print(f"[同期] Bionic用テキスト（lmstudio_system_prompt.txt）: {msg}")
    if _preset_path():
        preset_msg = update_lmstudio_preset(prompt)
        print(f"[同期] LM Studioプリセット「{settings.get('lmstudio_preset')}」: {preset_msg}")
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
    # 反映済みなら、Ollama が止まっていてもわざわざ起動しない
    if not changed and _ollama_synced(text) and (not _reachable(LOCAL_OLLAMA) or _ollama_has(name)):
        print(f"[同期] Ollamaモデル「{name}」: 変更なし")
    else:
        _ensure_local_ollama()
        r = _ollama_create(name)
        if r.returncode == 0:
            SYNC_STATE.write_text(_hash(text), encoding="utf-8")
            print(f"[同期] Ollamaモデル「{name}」を更新しました（元: {base}）")
        else:
            print(f"[同期] Ollamaモデルの作成に失敗: {(r.stderr or r.stdout).strip()[-300:]}")
            print("        元モデル名が正しいか `ollama list` で確認してください")

    # ほかの端末（Windows VM・VPS）の Ollama にも同じモデルを作る（Tailscale 経由・SSH 不要）
    for label, host in _remotes().items():
        if not _reachable(host):
            print(f"[同期] {label}（{host}）: つながらないため飛ばしました（次回の同期で再挑戦）")
            continue
        if _remote_synced(host, text) and _ollama_has(name, host):
            print(f"[同期] {label} のOllamaモデル「{name}」: 変更なし")
            continue
        r = _ollama_create(name, host)
        if r.returncode == 0:
            _save_remote_state(host, text)
            print(f"[同期] {label} のOllamaモデル「{name}」を更新しました")
        else:
            print(f"[同期] {label} のOllamaモデルの作成に失敗: {(r.stderr or r.stdout).strip()[-300:]}")
            print(f"        {label} に元モデル {base} があるか確認してください")

    check_remotes()


def _ollama_create(name: str, host: Optional[str] = None):
    return subprocess.run(["ollama", "create", name, "-f", str(MODELFILE)],
                          capture_output=True, text=True, env=_ollama_env(host))


def main():
    p = argparse.ArgumentParser(description="記憶を Ollama / LM Studio に書き出す")
    p.add_argument("--base", help="Ollamaの元モデル（例: qwen3:8b）。一度指定すれば記憶される")
    p.add_argument("--name", help="作成するOllamaモデル名（既定: my-assistant）")
    p.add_argument("--copy", action="store_true", help="LM Studio用テキストをクリップボードへコピー")
    p.add_argument("--if-needed", action="store_true", help="反映が必要なときだけ同期する（自動実行用）")
    a = p.parse_args()
    if a.if_needed:
        if not needs_sync():
            check_remotes()   # 反映済みでも、VM・VPS 側が変わっていないか確かめる
            return
        print(f"--- {datetime.now():%Y-%m-%d %H:%M:%S} 自動同期 ---")
    mem = load_memory(MEMORY_FILE)
    if not mem["facts"] and not mem["summaries"]:
        sys.exit(f"[エラー] 記憶が空です: {MEMORY_FILE}\n先に profile/add_profile.py を実行してください。")
    sync(a.base, a.name, a.copy)


if __name__ == "__main__":
    main()
