#!/usr/bin/env python3
"""
英語日記の1日分を diary.json に記録する（同じ日付は上書き）

- 同じ日に複数回送った日記は「指摘を受けての修正」として扱い、最後のものを正式な記録にする
- 上書きのたびに revision を1つ増やす（何回目の修正で確定したかが分かる）
- 入力は JSON（標準入力 or --file）。必須項目は date と original

使い方:
    python3 ~/MyTool/llm/persona/add_diary.py --file entry.json
    echo '{"date":"2026/10/26","original":"..."}' | python3 ~/MyTool/llm/persona/add_diary.py
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent))
from chat_memory import update_json  # noqa: E402

DIARY_FILE = DIR / "diary.json"


def norm_date(s: str) -> str:
    s = s.strip().split()[0].replace("/", "-").replace(".", "-")
    return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")


def add_entry(entry: dict) -> dict:
    if not entry.get("date") or not entry.get("original"):
        sys.exit("[エラー] date と original は必須です")
    entry = dict(entry)
    entry["date"] = norm_date(entry["date"])
    entry["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = {}

    def upsert(data):
        old = next((e for e in data["entries"] if e["date"] == entry["date"]), None)
        entry["revision"] = (old.get("revision", 1) + 1) if old else 1
        data["entries"] = [e for e in data["entries"] if e["date"] != entry["date"]] + [entry]
        data["entries"].sort(key=lambda e: e["date"])
        result.update(replaced=bool(old), revision=entry["revision"], total=len(data["entries"]))

    update_json(DIARY_FILE, {"entries": []}, upsert)
    act = "上書き" if result["replaced"] else "追加"
    print(f"{entry['date']} を{act}しました（修正{result['revision']}回目／全{result['total']}日分）")
    return result


def main():
    p = argparse.ArgumentParser(description="英語日記を diary.json に記録")
    p.add_argument("--file", type=Path)
    a = p.parse_args()
    raw = a.file.read_text(encoding="utf-8") if a.file else sys.stdin.read()
    add_entry(json.loads(raw))


if __name__ == "__main__":
    main()
