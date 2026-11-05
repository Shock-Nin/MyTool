#!/usr/bin/env python3
"""
体重・体脂肪率・体脂肪量を1つのグラフにする（Claudeのチャットにインライン表示する用のHTML断片を出力）
Claudeに「ヘルスケア」とだけ送ると、Claudeがこれを実行して出力をそのままグラフとして表示する

使い方: python3 ~/MyTool/llm/health/chart_widget.py [日数]   # 既定365日
"""
import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "health_log.csv"
days = int(sys.argv[1]) if len(sys.argv) > 1 else 365
rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))[-days:]
f = lambda c: [float(r[c]) if r[c] else None for r in rows]
D = json.dumps({"d": [r["date"][2:] for r in rows], "w": f("weight"), "p": f("body_fat_pct"), "m": f("fat_mass")},
               separators=(",", ":"))
span = f"{rows[0]['date']}〜{rows[-1]['date']}"

HTML = r'''<h2 class="sr-only">SPAN の体重、体脂肪率、体脂肪量の推移（7日移動平均と日々の値）</h2>
<div style="display:flex;flex-wrap:wrap;gap:16px;margin:0 0 8px;font-size:12px;color:var(--text-secondary);align-items:center">
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#2a78d6" stroke-width="2"/></svg>体重 kg <span id="lw"></span></span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#eb6834" stroke-width="2" stroke-dasharray="6 3"/></svg>体脂肪率 % <span id="lp"></span></span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#1baf7a" stroke-width="2" stroke-dasharray="2 3"/></svg>体脂肪量 kg <span id="lm"></span></span>
<label style="display:flex;align-items:center;gap:6px;margin-left:auto"><input type="checkbox" id="raw" checked>日々の値も表示</label>
</div>
<div style="position:relative;width:100%;height:360px"><canvas id="c1" role="img" aria-label="SPAN の体重、体脂肪率、体脂肪量の折れ線グラフ">体重・体脂肪率・体脂肪量の推移</canvas></div>
<p style="font-size:12px;color:var(--text-muted);margin:6px 0 0">SPAN　太線＝7日移動平均、薄い線＝毎朝の値。縦軸は kg と % の共通目盛り</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const D=DATA;
const ma=a=>a.map((_,i)=>{const s=a.slice(Math.max(0,i-6),i+1).filter(v=>v!=null);return s.length?+(s.reduce((x,y)=>x+y,0)/s.length).toFixed(2):null});
const dark=matchMedia('(prefers-color-scheme: dark)').matches||document.documentElement.dataset.mode==='dark';
const muted='#898781',grid=dark?'#2c2c2a':'#e1e0d9';
const S=[["体重","w","#2a78d6",[],"kg"],["体脂肪率","p","#eb6834",[6,3],"%"],["体脂肪量","m","#1baf7a",[2,3],"kg"]];
const sets=[];
S.forEach(([n,k,c,dash,u])=>{
 sets.push({label:n+"（7日平均）",data:ma(D[k]),borderColor:c,borderWidth:2,borderDash:dash,pointRadius:0,tension:.3,unit:u});
 sets.push({label:n,data:D[k],borderColor:c+"40",borderWidth:1,pointRadius:0,tension:0,unit:u,raw:true});
});
const last=k=>{const v=ma(D[k]).filter(x=>x!=null).at(-1);return v==null?'':v.toFixed(1)};
document.getElementById('lw').textContent=last('w');
document.getElementById('lp').textContent=last('p');
document.getElementById('lm').textContent=last('m');
const all=[...D.w,...D.p,...D.m].filter(v=>v!=null);
const ymin=Math.floor(Math.min(...all)/10)*10,ymax=Math.ceil(Math.max(...all)/10)*10;
const ch=new Chart(document.getElementById('c1'),{type:'line',data:{labels:D.d,datasets:sets},
options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
plugins:{legend:{display:false},tooltip:{filter:i=>!i.dataset.raw||document.getElementById('raw').checked,callbacks:{title:i=>'20'+i[0].label,label:i=>`${i.dataset.label}: ${i.parsed.y.toFixed(1)} ${i.dataset.unit}`}}},
scales:{x:{grid:{display:false},ticks:{color:muted,maxRotation:0,autoSkip:false,callback:function(v,i){const l=D.d[i];if(D.d.length<=62)return (i%7===0)?(+l.slice(3,5)+'/'+(+l.slice(6))):null;return l.endsWith('-01')?(l.slice(3,5)==='01'?'20'+l.slice(0,2)+'/1':+l.slice(3,5)+'月'):null}}},
y:{min:ymin,max:ymax,grid:{color:grid},ticks:{color:muted,stepSize:10},title:{display:true,text:'kg / %',color:muted}}}}});
document.getElementById('raw').addEventListener('change',e=>{ch.data.datasets.forEach(d=>{if(d.raw)d.hidden=!e.target.checked});ch.update()});
</script>'''
print(HTML.replace("DATA", D).replace("SPAN", span))
