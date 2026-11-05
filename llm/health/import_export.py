#!/usr/bin/env python3
"""
iPhoneヘルスケアの「すべてのヘルスケアデータを書き出す」で作った zip（または中の xml）から、
過去分を health_log.csv に取り込む。毎朝のショートカットと同じルールで1日1行にまとめる。

- 歩数: その日の合計（iPhoneとApple Watchなど複数の記録元があるときは、二重計上を避けて合計が最大の記録元を採用）
- 体重・体脂肪率: その日最初（朝）の測定。既存の記録に合わせる（朝晩測っている日は朝の値）／体脂肪量: 体重×体脂肪率
- 血圧: その日の最初の測定／脈拍: 血圧と同じ記録元（A&D）のその日最初の値。血圧がない日はその日最初の心拍数
- 既にある日付はそのまま残す（--overwrite で書き出しの値に置き換え）。今日の分は未確定なので取り込まない
- 書き込む前に health_log.csv のバックアップを作る

使い方:
    python3 ~/MyTool/llm/health/import_export.py ~/Downloads/書き出したデータ.zip --dry-run   # 件数の確認だけ
    python3 ~/MyTool/llm/health/import_export.py ~/Downloads/書き出したデータ.zip             # 取り込み
"""
import argparse
import datetime as dt
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from health import CSV_PATH, HEADER  # noqa: E402

P = "HKQuantityTypeIdentifier"
TYPES = {P + "StepCount", P + "BodyMass", P + "BodyFatPercentage",
         P + "BloodPressureSystolic", P + "BloodPressureDiastolic", P + "HeartRate"}


def open_xml(path: Path):
    if path.suffix.lower() == ".zip":
        z = zipfile.ZipFile(path)
        xmls = [i for i in z.infolist()
                if i.filename.lower().endswith(".xml") and "cda" not in i.filename.lower()]
        if not xmls:
            raise SystemExit(f"[エラー] zipの中にヘルスケアのxmlが見つかりません: {path}")
        return z.open(max(xmls, key=lambda i: i.file_size))   # 本体（一番大きいxml）
    return path.open("rb")


def parse(path: Path):
    steps = defaultdict(lambda: defaultdict(float))   # 日付 -> 記録元 -> 合計
    last = {}                                          # (種類, 日付) -> (時刻, 値)  体重・体脂肪率はその日最初（朝）の値
    first = {}                                         # (種類, 日付) -> (時刻, 値, 記録元)  最初の値
    hr = defaultdict(list)                             # 日付 -> [(時刻, 値, 記録元)]
    with open_xml(path) as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != "Record":
                if el.tag in ("Correlation", "Workout", "ActivitySummary"):
                    el.clear()
                continue
            t = el.get("type")
            if t in TYPES:
                start = el.get("startDate", "")        # 例: 2026-10-25 07:12:00 +0900（記録時の端末の時刻）
                day, src = start[:10], el.get("sourceName", "")
                try:
                    v = float(el.get("value", ""))
                except ValueError:
                    v = None
                if v is not None and len(day) == 10:
                    if t == P + "StepCount":
                        steps[day][src] += v
                    elif t == P + "BodyMass":
                        unit = (el.get("unit") or "kg").lower()
                        v = v * 0.45359237 if unit == "lb" else (v / 1000 if unit == "g" else v)
                        if (t, day) not in last or start < last[(t, day)][0]:
                            last[(t, day)] = (start, v)
                    elif t == P + "BodyFatPercentage":
                        v = v * 100 if v < 1 else v
                        if (t, day) not in last or start < last[(t, day)][0]:
                            last[(t, day)] = (start, v)
                    elif t == P + "HeartRate":
                        hr[day].append((start, v, src))
                    else:
                        if (t, day) not in first or start < first[(t, day)][0]:
                            first[(t, day)] = (start, v, src)
            el.clear()
    days = set(steps) | {d for _, d in last} | {d for _, d in first} | set(hr)
    rows = {}
    for d in sorted(days):
        st = round(max(steps[d].values())) if d in steps else None
        w = last.get((P + "BodyMass", d), (None, None))[1]
        bf = last.get((P + "BodyFatPercentage", d), (None, None))[1]
        sys_ = first.get((P + "BloodPressureSystolic", d))
        dia = first.get((P + "BloodPressureDiastolic", d))
        pulse = None
        if hr[d]:
            cand = [h for h in hr[d] if sys_ and h[2] == sys_[2]] or hr[d]
            pulse = min(cand)[1]
        cells = [
            d,
            "" if st is None else str(st),
            "" if w is None else f"{w:.2f}",
            "" if bf is None else f"{bf:.2f}",
            f"{w * bf / 100:.2f}" if w is not None and bf is not None else "",
            "" if sys_ is None else f"{sys_[1]:.0f}",
            "" if dia is None else f"{dia[1]:.0f}",
            "" if pulse is None else f"{pulse:.0f}",
        ]
        if any(cells[1:]):
            rows[d] = ",".join(cells)
    return rows


def main():
    ap = argparse.ArgumentParser(description="ヘルスケアの書き出しから過去分を取り込む")
    ap.add_argument("export", type=Path, help="書き出した zip（または中の xml）")
    ap.add_argument("--csv", type=Path, default=CSV_PATH)
    ap.add_argument("--since", help="この日付以降だけ取り込む（yyyy-MM-dd）")
    ap.add_argument("--overwrite", action="store_true", help="既にある日付も書き出しの値で置き換える")
    ap.add_argument("--dry-run", action="store_true", help="書き込まずに件数だけ表示")
    a = ap.parse_args()

    new = parse(a.export.expanduser())
    today = dt.datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()   # 今日（日本時間）は未確定なので除く
    new = {d: r for d, r in new.items() if d < today and (not a.since or d >= a.since)}

    lines = a.csv.read_text(encoding="utf-8-sig").splitlines() if a.csv.exists() else []
    existing = {l.split(",", 1)[0]: l for l in lines[1:] if l.strip()}   # 書き込む直前に読み直す
    merged = dict(existing)
    added = replaced = 0
    for d, r in new.items():
        if d not in existing:
            merged[d] = r
            added += 1
        elif a.overwrite and existing[d] != r:
            merged[d] = r
            replaced += 1
    span = f"{min(new)}〜{max(new)}" if new else "なし"
    print(f"書き出しの期間: {span}（{len(new)}日分）")
    print(f"追加: {added}日 / 置き換え: {replaced}日 / 既存のまま: {len(existing) - replaced}日")
    if a.dry_run or not (added or replaced):
        return
    if a.csv.exists():
        bak = a.csv.with_name(f"{a.csv.stem}.bak-{dt.datetime.now(ZoneInfo('Asia/Tokyo')):%Y%m%d-%H%M%S}.csv")
        shutil.copy2(a.csv, bak)
        print(f"バックアップ: {bak.name}")
    tmp = a.csv.with_suffix(".tmp")
    tmp.write_text("\n".join([HEADER] + [merged[d] for d in sorted(merged)]) + "\n", encoding="utf-8")
    tmp.replace(a.csv)
    print(f"取り込みました: {a.csv}")


if __name__ == "__main__":
    main()
