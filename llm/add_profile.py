#!/usr/bin/env python3
"""
profile.json（プロフィールの原本）を記憶 llm_memory.json に反映する

- profile.json を書き換えて実行すれば、記憶の中のプロフィールも差し替わる
  （/remember で追加した記憶や会話の要約はそのまま残る）
- 何度実行しても重複しない
- 反映後、LM Studio用テキストと Ollamaモデルも自動で更新

profile.json の書き方（どちらでもOK）:
    ["プロフィール1", "プロフィール2"]
    {"facts": [{"text": "プロフィール1"}, ...]}

使い方:
    python3 add_profile.py
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from chat_memory import MEMORY_FILE, PROFILE_FILE, update_memory


def load_profile(path: Path) -> list[str]:
    if not path.exists():
        sys.exit(f"[エラー] プロフィールの原本がありません: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[エラー] JSONが壊れています: {path}\n{e}")
    items = data.get("facts", []) if isinstance(data, dict) else data
    texts = [(i.get("text", "") if isinstance(i, dict) else str(i)).strip() for i in items]
    return list(dict.fromkeys(t for t in texts if t))   # 空行・重複を除く


def main():
    p = argparse.ArgumentParser(description="profile.json を記憶に反映")
    p.add_argument("--profile", type=Path, default=PROFILE_FILE)
    p.add_argument("--no-sync", action="store_true", help="アプリ側への同期をしない")
    a = p.parse_args()

    texts = load_profile(a.profile)
    today = datetime.now().strftime("%Y-%m-%d")
    stats = {}

    def apply(mem):
        is_profile = lambda f: f.get("source") == "profile" or f["text"] in texts
        old = {f["text"]: f for f in mem["facts"] if is_profile(f)}
        others = [f for f in mem["facts"] if not is_profile(f)]
        new = [{"text": t, "date": old[t]["date"] if t in old else today, "source": "profile"}
               for t in texts]
        mem["facts"] = new + others
        stats.update(added=[t for t in texts if t not in old],
                     removed=[t for t in old if t not in texts],
                     kept=len(others))

    update_memory(MEMORY_FILE, apply)
    print(f"プロフィール {len(texts)}件を反映しました（記憶ファイル: {MEMORY_FILE}）")
    for t in stats["added"]:
        print(f"  + {t}")
    for t in stats["removed"]:
        print(f"  - {t}")
    if not stats["added"] and not stats["removed"]:
        print("  （変更なし）")
    print(f"  その他の記憶 {stats['kept']}件はそのまま残しています")

    if not a.no_sync:
        from export_to_apps import sync
        sync()


if __name__ == "__main__":
    main()
