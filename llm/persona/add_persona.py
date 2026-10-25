#!/usr/bin/env python3
"""
persona.json（チャット由来の記憶の原本）を記憶 data/llm_memory.json に反映する

- persona.json は Claude のチャットで「persona 更新」と言ったときに、承認した行だけが書き込まれる
- profile.json（資料由来）とは別管理。add_profile.py / update_profile.py を実行しても消えない
- persona.json から消えた行は persona_backup.json に日時付きで追記して保管
- 何度実行しても重複しない
- 反映後、LM Studio用テキストと Ollamaモデルも自動で更新

使い方:
    python3 ~/MyTool/llm/persona/add_persona.py
    python3 ~/MyTool/llm/persona/add_persona.py --no-sync   # アプリ側への同期をしない
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PERSONA_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PERSONA_DIR.parent))   # llm フォルダの chat_memory.py を読み込む

from chat_memory import MEMORY_FILE, update_json, update_memory  # noqa: E402

PERSONA_FILE = PERSONA_DIR / "persona.json"
BACKUP_FILE = PERSONA_DIR / "persona_backup.json"
SOURCE = "persona"


def load_persona(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[エラー] persona の原本がありません: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[エラー] JSONが壊れています: {path}\n{e}")
    items = data.get("facts", []) if isinstance(data, dict) else data
    out, seen = [], set()
    for i in items:
        if isinstance(i, dict):
            text, date, cat = i.get("text", "").strip(), i.get("date"), i.get("category")
        else:
            text, date, cat = str(i).strip(), None, None
        if text and text not in seen:
            seen.add(text)
            out.append({"text": text, "date": date, "category": cat})
    return out


def apply_persona(path: Path = PERSONA_FILE, sync: bool = True) -> None:
    items = load_persona(path)
    texts = [i["text"] for i in items]
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    stats = {}

    def apply(mem):
        old = {f["text"]: f for f in mem["facts"] if f.get("source") == SOURCE}
        others = [f for f in mem["facts"] if f.get("source") != SOURCE and f["text"] not in texts]
        new = []
        for i in items:
            date = old[i["text"]]["date"] if i["text"] in old else (i["date"] or today)
            f = {"text": i["text"], "date": date, "source": SOURCE}
            if i["category"]:
                f["category"] = i["category"]
            new.append(f)
        mem["facts"] = others + new          # profile（資料由来）の後ろに並べる
        stats.update(added=[t for t in texts if t not in old],
                     removed=[old[t] for t in old if t not in texts],
                     kept=len(others))

    update_memory(MEMORY_FILE, apply)

    if stats["removed"]:
        def backup(data):
            data["history"].append({
                "archived_at": now.strftime("%Y-%m-%d %H:%M"),
                "reason": "persona.json から外れた行",
                "facts": stats["removed"],
            })
        update_json(BACKUP_FILE, {"history": []}, backup)

    print(f"persona {len(texts)}件を反映しました（記憶ファイル: {MEMORY_FILE}）")
    for t in stats["added"]:
        print(f"  + {t}")
    for f in stats["removed"]:
        print(f"  - {f['text']}（persona_backup.json に保管）")
    if not stats["added"] and not stats["removed"]:
        print("  （変更なし）")
    print(f"  その他の記憶 {stats['kept']}件はそのまま残しています")

    if sync:
        from export_to_apps import sync as sync_apps
        sync_apps()


def main():
    p = argparse.ArgumentParser(description="persona.json を記憶に反映")
    p.add_argument("--persona", type=Path, default=PERSONA_FILE)
    p.add_argument("--no-sync", action="store_true", help="アプリ側への同期をしない")
    a = p.parse_args()
    apply_persona(a.persona, sync=not a.no_sync)


if __name__ == "__main__":
    main()
