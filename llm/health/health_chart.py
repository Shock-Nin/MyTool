#!/usr/bin/env python3
"""
体重・体脂肪率・体脂肪量のグラフ（Claudeのチャットにインライン表示する用のHTML断片を出力）
Claudeに「ヘルスケア」とだけ送ると、Claudeがこれを実行して出力をそのままグラフとして表示する
上段＝体重(kg)、下段＝体脂肪率(%)・体脂肪量(kg)。横軸は共通で、カーソルを合わせると上下とも同じ日を表示

使い方: python3 ~/MyTool/llm/health/health_chart.py [日数]   # 既定365日
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

HTML = r'''<h2 class="sr-only">SPAN の体重（上段）と、体脂肪率・体脂肪量（下段）の推移（7日移動平均と日々の値）</h2>
<div style="display:flex;flex-wrap:wrap;gap:16px;margin:0 0 8px;font-size:12px;color:var(--text-secondary);align-items:center">
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#2a78d6" stroke-width="2"/></svg>体重 kg <span id="lw"></span></span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#eb6834" stroke-width="2" stroke-dasharray="6 3"/></svg>体脂肪率 % <span id="lp"></span></span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#1baf7a" stroke-width="2" stroke-dasharray="2 3"/></svg>体脂肪量 kg <span id="lm"></span></span>
<label style="display:flex;align-items:center;gap:6px;margin-left:auto"><input type="checkbox" id="raw" checked>日々の値も表示</label>
</div>
<div style="position:relative;width:100%;height:170px"><canvas id="c1" role="img" aria-label="SPAN の体重の折れ線グラフ">体重の推移</canvas></div>
<div style="position:relative;width:100%;height:230px;margin-top:4px"><canvas id="c2" role="img" aria-label="SPAN の体脂肪率と体脂肪量の折れ線グラフ">体脂肪率・体脂肪量の推移</canvas></div>
<p style="font-size:12px;color:var(--text-muted);margin:6px 0 0">SPAN　太線＝7日移動平均、薄い線＝毎朝の値。上段＝体重、下段＝体脂肪率と体脂肪量（kg と % の共通目盛り）</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const D=DATA;
const ma=a=>a.map((_,i)=>{const s=a.slice(Math.max(0,i-6),i+1).filter(v=>v!=null);return s.length?+(s.reduce((x,y)=>x+y,0)/s.length).toFixed(2):null});
const dark=matchMedia('(prefers-color-scheme: dark)').matches||document.documentElement.dataset.mode==='dark';
const muted='#898781',grid=dark?'#2c2c2a':'#e1e0d9';
const mk=(n,k,c,dash,u)=>[{label:n+"（7日平均）",data:ma(D[k]),borderColor:c,borderWidth:2,borderDash:dash,pointRadius:0,tension:.3,unit:u},
 {label:n,data:D[k],borderColor:c+"40",borderWidth:1,pointRadius:0,tension:0,unit:u,raw:true}];
const last=k=>{const v=ma(D[k]).filter(x=>x!=null).at(-1);return v==null?'':v.toFixed(1)};
document.getElementById('lw').textContent=last('w');
document.getElementById('lp').textContent=last('p');
document.getElementById('lm').textContent=last('m');
const rng=(keys,step)=>{const a=keys.flatMap(k=>D[k]).filter(v=>v!=null);return [Math.floor(Math.min(...a)/step)*step,Math.ceil(Math.max(...a)/step)*step]};
const xt=(show)=>({grid:{display:false},ticks:{display:show,color:muted,maxRotation:0,autoSkip:false,callback:function(v,i){const l=D.d[i];if(D.d.length<=62)return (i%7===0)?(+l.slice(3,5)+'/'+(+l.slice(6))):null;return l.endsWith('-01')?(l.slice(3,5)==='01'?'20'+l.slice(0,2)+'/1':+l.slice(3,5)+'月'):null}}});
const opt=(r,step,title,showX)=>({responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},layout:{padding:{left:0}},
 plugins:{legend:{display:false},tooltip:{filter:i=>!i.dataset.raw||document.getElementById('raw').checked,callbacks:{title:i=>'20'+i[0].label,label:i=>`${i.dataset.label}: ${i.parsed.y.toFixed(1)} ${i.dataset.unit}`}}},
 scales:{x:xt(showX),y:{min:r[0],max:r[1],afterFit:s=>{s.width=48},grid:{color:grid},ticks:{color:muted,stepSize:step},title:{display:true,text:title,color:muted}}}});
const [w0,w1]=rng(['w'],2),[f0,f1]=rng(['p','m'],5);
const c1=new Chart(document.getElementById('c1'),{type:'line',data:{labels:D.d,datasets:mk("体重","w","#2a78d6",[],"kg")},options:opt([w0,w1],2,'kg',false)});
const c2=new Chart(document.getElementById('c2'),{type:'line',data:{labels:D.d,datasets:[...mk("体脂肪率","p","#eb6834",[6,3],"%"),...mk("体脂肪量","m","#1baf7a",[2,3],"kg")]},options:opt([f0,f1],5,'% / kg',true)});
const sync=(src,dst)=>src.canvas.addEventListener('mousemove',e=>{const p=src.getElementsAtEventForMode(e,'index',{intersect:false},false);if(!p.length)return;const i=p[0].index;const act=dst.data.datasets.map((d,j)=>({datasetIndex:j,index:i})).filter(a=>!dst.data.datasets[a.datasetIndex].hidden);dst.setActiveElements(act);dst.tooltip.setActiveElements(act,{x:dst.scales.x.getPixelForValue(i),y:dst.chartArea.top+20});dst.update('none')});
sync(c1,c2);sync(c2,c1);
[c1,c2].forEach(c=>c.canvas.addEventListener('mouseleave',()=>[c1,c2].forEach(x=>{x.setActiveElements([]);x.tooltip.setActiveElements([],{x:0,y:0});x.update('none')})));
document.getElementById('raw').addEventListener('change',e=>{[c1,c2].forEach(ch=>{ch.data.datasets.forEach(d=>{if(d.raw)d.hidden=!e.target.checked});ch.update()})});
</script>'''
print(HTML.replace("DATA", D).replace("SPAN", span))
