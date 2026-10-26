#!/usr/bin/env python3
"""
健康ログ（iPhoneヘルスケア → ショートカットで毎朝前日分を記録）を読み出す

- 原本: このフォルダの health_log.csv（iPhoneのショートカットがSSHで --add を実行して追記）
- 記憶には入れない。必要なときだけ呼び出す（chat_memory.py の /health、ask3.sh -H、Claude経由で三者へ）
- 同じ日付が再送されたら最後の内容で上書き（＝確定値の差し替え）

使い方:
    python3 ~/MyTool/llm/health/health.py          # 直近14日
    python3 ~/MyTool/llm/health/health.py 30       # 直近30日
    python3 ~/MyTool/llm/health/health.py --add 2026-10-25 "10,432" 61.6 18.3 "" 118 76 64
"""
import argparse
import csv
import re
from pathlib import Path
from statistics import mean

CSV_PATH = Path(__file__).resolve().parent / "health_log.csv"
HEADER = "date,steps,weight_kg,body_fat_pct,lean_mass_kg,bp_sys,bp_dia,pulse"

COLUMNS = [  # (CSV列名, 表示名, 単位, 小数桁)
    ("steps", "歩数", "歩", 0),
    ("weight_kg", "体重", "kg", 1),
    ("body_fat_pct", "体脂肪率", "%", 1),
    ("lean_mass_kg", "除脂肪体重", "kg", 1),
    ("bp_sys", "最高血圧", "mmHg", 0),
    ("bp_dia", "最低血圧", "mmHg", 0),
    ("pulse", "脈拍", "bpm", 0),
]
KEYWORDS = ["体重", "体脂肪", "筋肉", "除脂肪", "歩数", "血圧", "脈拍", "心拍", "健康ログ", "体組成"]


def _num(s):
    try:
        return float(str(s).replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def load(path: Path = CSV_PATH) -> list[dict]:
    """日付順の記録（同じ日付は最後の行を採用）"""
    if not path.exists():
        return []
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            d = (r.get("date") or "").strip()
            if not d:
                continue
            rec = {"date": d}
            for key, *_ in COLUMNS:
                rec[key] = _num(r.get(key, ""))
            bf = rec.get("body_fat_pct")
            if bf is not None and bf < 1:      # ヘルスケアが 0.182 の形で出した場合
                rec["body_fat_pct"] = bf * 100
            rows[d] = rec
    return [rows[d] for d in sorted(rows)]


def _fmt(v, digits):
    return "-" if v is None else (f"{v:,.0f}" if digits == 0 else f"{v:.{digits}f}")


def context_text(days: int = 14, path: Path = CSV_PATH) -> str:
    recs = load(path)
    if not recs:
        return f"（健康ログがまだありません: {path}）"
    recs = recs[-days:]
    cols = [c for c in COLUMNS if any(r[c[0]] is not None for r in recs)]
    lines = [f"【健康ログ】iPhoneヘルスケアの前日確定値（直近{len(recs)}日、{recs[0]['date']}〜{recs[-1]['date']}）"]
    lines.append("日付 | " + " | ".join(f"{n}({u})" for _, n, u, _ in cols))
    for r in recs:
        lines.append(r["date"] + " | " + " | ".join(_fmt(r[k], d) for k, _, _, d in cols))
    last7, prev7 = recs[-7:], recs[-14:-7]
    avg = []
    for k, n, u, d in cols:
        a = [r[k] for r in last7 if r[k] is not None]
        b = [r[k] for r in prev7 if r[k] is not None]
        if a:
            s = f"{n} {_fmt(mean(a), d)}{u}"
            if b:
                diff = mean(a) - mean(b)
                s += f"（前週比 {'+' if diff >= 0 else ''}{_fmt(diff, d)}）"
            avg.append(s)
    if avg:
        lines.append("直近7日平均: " + "、".join(avg))
    return "\n".join(lines)


def _clean(c: str) -> str:
    """「10,432」「61.6 kg」「18.3%」などから数値だけ取り出す。値がなければ空欄"""
    m = re.search(r"-?\d+(?:\.\d+)?", c.replace(",", ""))
    return m.group(0) if m else ""


def add_row(values: list[str], path: Path = CSV_PATH) -> str:
    """1日分を追記。同じ日付の行は置き換える（ファイルは毎回読み直してから保存）
    values: 8個の値（日付,歩数,体重,体脂肪率,除脂肪体重,最高,最低,脈拍）、または ; か , 区切りの1行"""
    if len(values) == 1:
        line = values[0].strip()
        sep = ";" if ";" in line else ("|" if "|" in line else ",")   # ; 区切りなら歩数の「10,432」も壊れない
        cells = [c.strip() for c in line.split(sep)]
    else:
        cells = [c.strip() for c in values]
    n = len(HEADER.split(","))
    if len(cells) != n:
        raise SystemExit(f"[エラー] 列数が {len(cells)} です（{n} 列必要: {HEADER}）")
    m = re.search(r"(\d{4})\D(\d{1,2})\D(\d{1,2})", cells[0])   # 2026/10/26 0:00 や 2026年10月26日 も可
    date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else cells[0]
    cells[0] = date
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise SystemExit(f"[エラー] 日付の形式が違います: {date}（yyyy-MM-dd）")
    cells[1:] = [_clean(c) for c in cells[1:]]
    if cells[3] and float(cells[3]) < 1:          # 体脂肪率が 0.183 の形なら % に直す
        cells[3] = f"{float(cells[3]) * 100:.1f}"
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    body = [l for l in lines[1:] if l.strip() and not l.startswith(date + ",")]
    body.append(",".join(cells))
    body.sort(key=lambda l: l.split(",", 1)[0])
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join([HEADER] + body) + "\n", encoding="utf-8")
    tmp.replace(path)
    return ",".join(cells)


def is_health_topic(text: str) -> bool:
    return any(k in text for k in KEYWORDS)


def main():
    p = argparse.ArgumentParser(description="健康ログを表示")
    p.add_argument("days", nargs="?", type=int, default=14)
    p.add_argument("--csv", type=Path, default=CSV_PATH)
    p.add_argument("--add", nargs="+", metavar="値", help="1日分を記録（8個の値、またはカンマ区切り1行）")
    import sys
    # iPhoneのスマート句読点で「--add」が「—add」「–add」に化けても受け付ける
    argv = ["--add" if x in ("—add", "–add", "−−add", "––add") else x for x in sys.argv[1:]]
    a = p.parse_args(argv)
    if a.add:
        print("記録しました: " + add_row(a.add, a.csv))
        return
    print(context_text(a.days, a.csv))


if __name__ == "__main__":
    main()
