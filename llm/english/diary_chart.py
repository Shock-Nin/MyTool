#!/usr/bin/env python3
"""
英語日記のスコアのグラフ（Claudeのチャットにインライン表示する用のHTML断片を出力）
Claudeに「英語」とだけ送ると、Claudeがこれを実行して出力をそのままグラフとして表示する
上段＝総合点（100点。最終版・初回・7回移動平均）、下段＝内訳（文法/40・語彙/30・自然さ/30 を満点比の%で）

使い方: python3 ~/MyTool/llm/english/diary_chart.py [日数]   # 既定365日
"""
import datetime as dt
import json
import sys
from pathlib import Path

DIARY = Path(__file__).resolve().parent / "diary.json"
days = int(sys.argv[1]) if len(sys.argv) > 1 else 365
entries = json.loads(DIARY.read_text(encoding="utf-8")).get("entries", [])
entries = sorted((e for e in entries if (e.get("scores") or {}).get("total_100") is not None), key=lambda e: e["date"])
if entries:
    since = (dt.date.fromisoformat(entries[-1]["date"]) - dt.timedelta(days=days - 1)).isoformat()
    entries = [e for e in entries if e["date"] >= since]
if not entries:
    sys.exit("採点済みの英語日記がありません")

def first_total(e):
    h = e.get("score_history") or []
    return h[0]["scores"].get("total_100") if h else e["scores"]["total_100"]

D = json.dumps({
    "d": [e["date"][2:] for e in entries],
    "t": [e["scores"]["total_100"] for e in entries],
    "f": [first_total(e) for e in entries],
    "r": [e.get("revision", 1) for e in entries],
    "g": [e["scores"].get("grammar_40") for e in entries],
    "v": [e["scores"].get("vocabulary_30") for e in entries],
    "n": [e["scores"].get("naturalness_30") for e in entries],
    "c": [e.get("cefr", "") for e in entries],
}, ensure_ascii=False, separators=(",", ":"))
span = f"{entries[0]['date']}〜{entries[-1]['date']}（{len(entries)}日分）"

HTML = r'''<h2 class="sr-only">SPAN の英語日記の総合点（上段）と内訳（下段）の推移</h2>
<div style="display:flex;flex-wrap:wrap;gap:16px;margin:0 0 8px;font-size:12px;color:var(--text-secondary);align-items:center">
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#2a78d6" stroke-width="2"/></svg>総合点（最終版） <span id="lt"></span></span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#2a78d6" stroke-opacity=".35" stroke-width="1.5" stroke-dasharray="3 3"/></svg>初回の点</span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#898781" stroke-width="2"/></svg>7回平均 <span id="la"></span></span>
</div>
<div style="display:flex;flex-wrap:wrap;gap:16px;margin:0 0 8px;font-size:12px;color:var(--text-secondary)">
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#eb6834" stroke-width="2"/></svg>文法 /40</span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#1baf7a" stroke-width="2" stroke-dasharray="6 3"/></svg>語彙 /30</span>
<span style="display:flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#9b59d0" stroke-width="2" stroke-dasharray="2 3"/></svg>自然さ /30</span>
</div>
<div style="position:relative;width:100%;height:190px"><canvas id="c1" role="img" aria-label="SPAN の英語日記の総合点の折れ線グラフ">英語日記の総合点の推移</canvas></div>
<div style="position:relative;width:100%;height:210px;margin-top:4px"><canvas id="c2" role="img" aria-label="SPAN の英語日記の文法・語彙・自然さの得点率の折れ線グラフ">英語日記の内訳の推移</canvas></div>
<p style="font-size:12px;color:var(--text-muted);margin:6px 0 0">SPAN　上段＝総合点（100点満点）、下段＝内訳を満点に対する割合（%）で表示。点の上にカーソルを合わせると実際の点数と修正回数</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const D=DATA;
const ma=a=>a.map((_,i)=>{const s=a.slice(Math.max(0,i-6),i+1).filter(v=>v!=null);return s.length?+(s.reduce((x,y)=>x+y,0)/s.length).toFixed(1):null});
const dark=matchMedia('(prefers-color-scheme: dark)').matches||document.documentElement.dataset.mode==='dark';
const muted='#898781',grid=dark?'#2c2c2a':'#e1e0d9';
const lbl=D.d.map(l=>(+l.slice(3,5))+'/'+(+l.slice(6)));
const avg=ma(D.t);
document.getElementById('lt').textContent=D.t.at(-1);
document.getElementById('la').textContent=avg.at(-1);
const pct=(a,m)=>a.map(v=>v==null?null:+(v/m*100).toFixed(1));
const all=[...D.t,...D.f].filter(v=>v!=null);
const y0=Math.max(0,Math.floor((Math.min(...all)-5)/10)*10);
const xt=show=>({grid:{display:false},ticks:{display:show,color:muted,maxRotation:0,autoSkip:true,maxTicksLimit:12}});
const base=(r,title,showX,cb)=>({responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
 plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>'20'+D.d[i[0].dataIndex],label:cb}}},
 scales:{x:xt(showX),y:{min:r[0],max:r[1],afterFit:s=>{s.width=48},grid:{color:grid},ticks:{color:muted,stepSize:10},title:{display:true,text:title,color:muted}}}});
const c1=new Chart(document.getElementById('c1'),{type:'line',data:{labels:lbl,datasets:[
 {label:'総合点（最終版）',data:D.t,borderColor:'#2a78d6',backgroundColor:'#2a78d6',borderWidth:2,pointRadius:3,tension:0},
 {label:'初回の点',data:D.f,borderColor:'#2a78d659',backgroundColor:'#2a78d659',borderWidth:1.5,borderDash:[3,3],pointRadius:2,tension:0},
 {label:'7回平均',data:avg,borderColor:'#898781',borderWidth:2,pointRadius:0,tension:.3}]},
 options:base([y0,100],'点',false,i=>{const k=i.dataIndex;if(i.datasetIndex===0)return `総合点: ${D.t[k]}点（修正${D.r[k]-1}回）`;if(i.datasetIndex===1)return `初回: ${D.f[k]}点`;return `7回平均: ${i.parsed.y}点`})});
const M={g:40,v:30,n:30};
const c2=new Chart(document.getElementById('c2'),{type:'line',data:{labels:lbl,datasets:[
 {label:'文法',k:'g',data:pct(D.g,40),borderColor:'#eb6834',backgroundColor:'#eb6834',borderWidth:2,pointRadius:3,tension:0},
 {label:'語彙',k:'v',data:pct(D.v,30),borderColor:'#1baf7a',backgroundColor:'#1baf7a',borderWidth:2,borderDash:[6,3],pointRadius:3,pointStyle:'rect',tension:0},
 {label:'自然さ',k:'n',data:pct(D.n,30),borderColor:'#9b59d0',backgroundColor:'#9b59d0',borderWidth:2,borderDash:[2,3],pointRadius:3,pointStyle:'triangle',tension:0}]},
 options:base([Math.max(0,Math.floor(Math.min(...[...pct(D.g,40),...pct(D.v,30),...pct(D.n,30)].filter(v=>v!=null))/10)*10-10),100],'%',true,
  i=>{const d=i.dataset;return `${d.label}: ${D[d.k][i.dataIndex]}/${M[d.k]}（${i.parsed.y}%）`})});
const sync=(src,dst)=>src.canvas.addEventListener('mousemove',e=>{const p=src.getElementsAtEventForMode(e,'index',{intersect:false},false);if(!p.length)return;const i=p[0].index;const act=dst.data.datasets.map((d,j)=>({datasetIndex:j,index:i}));dst.setActiveElements(act);dst.tooltip.setActiveElements(act,{x:dst.scales.x.getPixelForValue(i),y:dst.chartArea.top+20});dst.update('none')});
sync(c1,c2);sync(c2,c1);
[c1,c2].forEach(c=>c.canvas.addEventListener('mouseleave',()=>[c1,c2].forEach(x=>{x.setActiveElements([]);x.tooltip.setActiveElements([],{x:0,y:0});x.update('none')})));
</script>'''
print(HTML.replace("DATA", D).replace("SPAN", span))
