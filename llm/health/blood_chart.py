#!/usr/bin/env python3
"""
献血の検査結果のグラフ（Claudeのチャットにインライン表示する用のHTML断片を出力）
データは blood_log.csv（ラブラッドの「献血記録の確認」から取り込んだもの）
項目を選ぶと、その項目の献血ごとの推移を表示。点の色＝献血の種類（全血・血漿・血小板）
破線＝基準値（ラブラッドの表示）、基準値から外れた回は点を赤い輪で囲む

使い方: python3 ~/MyTool/llm/health/blood_chart.py [回数] [項目]   # 既定＝全件・コレステロール
  例: python3 blood_chart.py 30 alt
"""
import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "blood_log.csv"
ITEMS = [  # (列名, 表示名, 単位, 基準値下限, 基準値上限)  基準値＝ラブラッドの表示（男性）。血圧・脈拍は基準値なし
    ("chol", "コレステロール CHOL", "mg/dL", 140, 259), ("ga", "グリコアルブミン GA", "%", None, 16.5),
    ("alt", "ALT（GPT）", "IU/L", 8, 49), ("ggt", "γ-GTP", "IU/L", 9, 68),
    ("tp", "総蛋白 TP", "g/dL", 6.6, 8.2), ("alb", "アルブミン ALB", "g/dL", 4.0, 5.1), ("ag", "A/G比", "", 1.3, 2.1),
    ("rbc", "赤血球数 RBC", "万/μL", 418, 560), ("hb", "ヘモグロビン Hb", "g/dL", 12.7, 17.0),
    ("ht", "ヘマトクリット Ht", "%", 38.8, 50.0),
    ("mcv", "MCV", "fL", 83.0, 99.5), ("mch", "MCH", "pg", 26.8, 33.5), ("mchc", "MCHC", "%", 31.7, 35.2),
    ("wbc", "白血球数 WBC", "百/μL", 38, 89), ("plt", "血小板数 PLT", "万/μL", 17.0, 36.5),
    ("bp_sys", "血圧（最高）", "mmHg", None, None), ("bp_dia", "血圧（最低）", "mmHg", None, None),
    ("pulse", "脈拍", "回/分", None, None),
]
args = sys.argv[1:]
n = int(args[0]) if args and args[0].isdigit() else 0
first = next((a for a in args if a in {it[0] for it in ITEMS}), "chol")
rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
if n:
    rows = rows[-n:]
kind = lambda t: "全血" if "全血" in t else "血小板" if "血小板" in t else "血漿"
D = json.dumps({"d": [r["date"] for r in rows], "k": [kind(r["type"]) for r in rows],
                "v": {it[0]: [float(r[it[0]]) if r[it[0]] else None for r in rows] for it in ITEMS},
                "items": [list(it) for it in ITEMS], "first": first},
               ensure_ascii=False, separators=(",", ":"))
span = f"{rows[0]['date']}〜{rows[-1]['date']}（{len(rows)}回分）"

HTML = r'''<h2 class="sr-only">SPAN の献血検査結果の推移</h2>
<div style="display:flex;flex-wrap:wrap;gap:14px;margin:0 0 8px;font-size:12px;color:var(--text-secondary);align-items:center">
<select id="it" style="font-size:13px;padding:2px 4px"></select>
<span id="lv" style="font-size:13px;color:var(--text-primary)"></span>
<span style="display:flex;align-items:center;gap:5px"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="#c2412d"/></svg>全血</span>
<span style="display:flex;align-items:center;gap:5px"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="#d9a21b"/></svg>血漿</span>
<span style="display:flex;align-items:center;gap:5px"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="#2a78d6"/></svg>血小板</span>
<span style="display:flex;align-items:center;gap:5px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#1baf7a" stroke-width="2" stroke-dasharray="5 3"/></svg><span id="lr">基準値</span></span>
<span style="display:flex;align-items:center;gap:5px"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="none" stroke="#e34948" stroke-width="2"/></svg>基準値外 <span id="lo"></span></span>
</div>
<div style="position:relative;width:100%;height:300px"><canvas id="c" role="img" aria-label="SPAN の献血検査結果の折れ線グラフ">献血検査結果の推移</canvas></div>
<p style="font-size:12px;color:var(--text-muted);margin:6px 0 0">SPAN　細線＝各回の値、太線＝直近5回の平均、緑の破線＝基準値（ラブラッドの表示）。点の色＝献血の種類、赤い輪＝基準値外</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const D=DATA;
const C={"全血":"#c2412d","血漿":"#d9a21b","血小板":"#2a78d6"};
const dark=matchMedia('(prefers-color-scheme: dark)').matches||document.documentElement.dataset.mode==='dark';
const muted='#898781',grid=dark?'#2c2c2a':'#e1e0d9',line=dark?'#c9c7bf':'#5f5e5a';
const ma=a=>a.map((_,i)=>{const s=a.slice(Math.max(0,i-4),i+1).filter(v=>v!=null);return s.length?+(s.reduce((x,y)=>x+y,0)/s.length).toFixed(2):null});
const sel=document.getElementById('it');
D.items.forEach(([k,l])=>{const o=document.createElement('option');o.value=k;o.textContent=l;sel.appendChild(o)});
sel.value=D.first;
const xt={grid:{display:false},ticks:{color:muted,maxRotation:0,autoSkip:false,callback:function(v,i){const y=D.d[i].slice(0,4);return (i===0||D.d[i-1].slice(0,4)!==y)?y:null}}};
const ch=new Chart(document.getElementById('c'),{type:'line',data:{labels:D.d,datasets:[]},
 options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
  plugins:{legend:{display:false},tooltip:{filter:i=>i.datasetIndex<2,callbacks:{label:i=>i.datasetIndex===0?`${D.k[i.dataIndex]}: ${i.parsed.y}`:`直近5回平均: ${i.parsed.y.toFixed(1)}`}}},
  scales:{x:xt,y:{grid:{color:grid},ticks:{color:muted},title:{display:true,text:'',color:muted}}}}});
function draw(){const [k,l,u,lo,hi]=D.items.find(x=>x[0]===sel.value);const v=D.v[k];
 const out=v.map(x=>x!=null&&((lo!=null&&x<lo)||(hi!=null&&x>hi)));
 const ref=r=>({data:v.map(()=>r),borderColor:'#1baf7a',borderWidth:1.5,borderDash:[5,3],pointRadius:0,pointHitRadius:0,tension:0});
 ch.data.datasets=[{data:v,borderColor:line+'55',borderWidth:1,pointRadius:out.map(o=>o?4:3),pointHoverRadius:5,pointBackgroundColor:D.k.map(x=>C[x]),pointBorderColor:'#e34948',pointBorderWidth:out.map(o=>o?2:0),tension:0},
  {data:ma(v),borderColor:line,borderWidth:2,pointRadius:0,tension:.3}];
 if(lo!=null)ch.data.datasets.push(ref(lo));if(hi!=null)ch.data.datasets.push(ref(hi));
 ch.options.scales.y.title.text=u;const last=v.filter(x=>x!=null).at(-1);
 document.getElementById('lr').textContent=lo==null&&hi==null?'基準値なし':lo==null?`基準値 ${hi}未満`:`基準値 ${lo}〜${hi}`;
 document.getElementById('lo').textContent=`${out.filter(Boolean).length}回`;
 document.getElementById('lv').textContent=`最新 ${last}${u?' '+u:''}（${D.d.at(-1)}）`;ch.update()}
sel.addEventListener('change',draw);draw();
</script>'''
print(HTML.replace("DATA", D).replace("SPAN", span))
