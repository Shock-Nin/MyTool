#!/usr/bin/env python3
"""
英語日記の1日分を diary.json に記録する（同じ日付は上書き）

- 同じ日に複数回送った日記は「指摘を受けての修正」として扱い、最後のものを正式な記録にする
- 上書きのたびに revision を1つ増やす（何回目の修正で確定したかが分かる）
- 採点（scores・cefr）は上書きせず、score_history に修正回ごとに追記して履歴を残す
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


def migrate_history(hist) -> list:
    """旧形式（合計点の数値だけのリスト）を辞書形式に変換する"""
    out = []
    for i, h in enumerate(hist or [], 1):
        if isinstance(h, dict):
            out.append(h)
        else:
            out.append({"revision": i, "recorded_at": None, "scores": {"total_100": h}, "cefr": None})
    return out


def score_snapshot(entry: dict, revision: int) -> dict:
    return {
        "revision": revision,
        "recorded_at": entry["updated_at"],
        "scores": entry.get("scores"),
        "cefr": entry.get("cefr"),
    }


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
        history = migrate_history(old.get("score_history")) if old else []
        if entry.get("scores") is not None:
            history.append(score_snapshot(entry, entry["revision"]))
        entry["score_history"] = history
        data["entries"] = [e for e in data["entries"] if e["date"] != entry["date"]] + [entry]
        data["entries"].sort(key=lambda e: e["date"])
        result.update(replaced=bool(old), revision=entry["revision"], total=len(data["entries"]))

    update_json(DIARY_FILE, {"entries": []}, upsert)
    act = "上書き" if result["replaced"] else "追加"
    hist = "→".join(str((h.get("scores") or {}).get("total_100", "?")) for h in entry["score_history"])
    print(f"{entry['date']} を{act}しました（修正{result['revision']}回目／全{result['total']}日分）")
    if hist:
        print(f"採点の履歴: {hist}")
    return result


def main():
    p = argparse.ArgumentParser(description="英語日記を diary.json に記録")
    p.add_argument("--file", type=Path)
    a = p.parse_args()
    raw = a.file.read_text(encoding="utf-8") if a.file else sys.stdin.read()
    add_entry(json.loads(raw))


if __name__ == "__main__":
    main()
