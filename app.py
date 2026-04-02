import os
import json
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))
MODEL = "claude-sonnet-4-20250514"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PatentLens — IP Classification Analyzer</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');
:root{--bg:#F4F1EB;--surface:#FDFBF8;--surface2:#EEEAE0;--ink:#1C1915;--ink2:#4A4540;--ink3:#8A837A;--accent:#2D5F3F;--accent2:#1A3D27;--accent-light:#E6F2EC;--amber:#B86A08;--amber-light:#FEF3E2;--blue:#1B4F8A;--blue-light:#E8F0FB;--red-light:#FEE2E2;--purple-light:#EDE9FE;--green-light:#F0FDF4;--border:rgba(28,25,21,0.09);--border2:rgba(28,25,21,0.05);--r:10px;}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;overflow:hidden;}
body{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--ink);font-size:13px;display:flex;flex-direction:column;}
.hdr{background:var(--ink);display:flex;align-items:center;justify-content:space-between;padding:0 1.25rem;height:52px;flex-shrink:0;}
.hdr-logo{display:flex;align-items:center;gap:9px;}
.hdr-mark{width:28px;height:28px;background:var(--accent);border-radius:6px;display:grid;grid-template-columns:1fr 1fr;gap:2px;padding:5px;}
.hdr-mark span{background:#fff;border-radius:1px;opacity:.85;}
.hdr-mark span:nth-child(2),.hdr-mark span:nth-child(3){opacity:.5;}
.hdr-mark span:nth-child(4){opacity:.25;}
.hdr-name{font-family:'DM Serif Display',serif;font-size:17px;color:#fff;letter-spacing:-.2px;}
.hdr-sub{font-size:10px;color:rgba(255,255,255,.38);margin-left:2px;}
.hdr-right{display:flex;gap:8px;align-items:center;}
.btn{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;border-radius:8px;font-size:12px;font-family:'Outfit',sans-serif;font-weight:500;cursor:pointer;border:none;transition:all .15s;white-space:nowrap;}
.btn-ghost{background:rgba(255,255,255,.07);color:rgba(255,255,255,.65);border:1px solid rgba(255,255,255,.12);}
.btn-ghost:hover{background:rgba(255,255,255,.12);color:#fff;}
.btn-green{background:var(--accent);color:#fff;}
.btn-green:hover{background:var(--accent2);}
.btn-green:disabled{opacity:.45;cursor:not-allowed;}
.btn-amber{background:var(--amber);color:#fff;}
.btn-amber:hover{background:#955508;}
.btn-amber:disabled{opacity:.4;cursor:not-allowed;}
.page{display:flex;flex:1;overflow:hidden;}
.sidebar{width:300px;min-width:280px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;}
.sb-body{flex:1;overflow-y:auto;padding:1.25rem;}
.sb-body::-webkit-scrollbar{width:3px;}
.sb-body::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
.lbl{font-size:9.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;}
.drop-zone{border:1.5px dashed var(--border);border-radius:var(--r);padding:1.25rem;text-align:center;cursor:pointer;transition:all .2s;margin-bottom:1rem;background:var(--bg);}
.drop-zone:hover,.drop-zone.over{border-color:var(--accent);background:var(--accent-light);}
.drop-icon{width:32px;height:32px;background:var(--surface2);border-radius:7px;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;}
.drop-icon svg{width:16px;height:16px;color:var(--ink3);}
.drop-t{font-size:12px;font-weight:500;color:var(--ink);margin-bottom:2px;}
.drop-s{font-size:10.5px;color:var(--ink3);}
.file-chip{display:flex;align-items:center;gap:7px;background:var(--accent-light);border:1px solid rgba(45,95,63,.18);border-radius:8px;padding:7px 10px;margin-bottom:1rem;font-size:11px;color:var(--accent2);font-weight:500;}
.file-chip svg{width:13px;height:13px;flex-shrink:0;}
.file-chip-x{margin-left:auto;cursor:pointer;opacity:.5;font-size:16px;line-height:1;}
.file-chip-x:hover{opacity:1;}
.textarea{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:9px 11px;font-family:'Outfit',sans-serif;font-size:12px;color:var(--ink);resize:vertical;min-height:180px;line-height:1.6;margin-bottom:3px;transition:border-color .15s;}
.textarea:focus{outline:none;border-color:var(--accent);}
.textarea::placeholder{color:var(--ink3);}
.char-ct{font-size:10px;color:var(--ink3);text-align:right;margin-bottom:.9rem;}
.checks{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:1rem;}
.chk{display:flex;align-items:center;gap:5px;padding:6px 9px;border:1px solid var(--border);border-radius:7px;font-size:11.5px;color:var(--ink2);cursor:pointer;transition:all .15s;background:var(--bg);user-select:none;}
.chk input{display:none;}
.chk.on{border-color:var(--accent);background:var(--accent-light);color:var(--accent2);font-weight:500;}
.dot{width:13px;height:13px;border-radius:50%;border:1.5px solid var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;}
.chk.on .dot{background:var(--accent);border-color:var(--accent);}
.dot-i{width:4px;height:4px;border-radius:50%;background:#fff;display:none;}
.chk.on .dot-i{display:block;}
.run-btn{width:100%;justify-content:center;padding:10px;font-size:13px;border-radius:var(--r);}
.sb-foot{padding:9px 1.25rem;border-top:1px solid var(--border);display:flex;align-items:center;gap:7px;font-size:11px;color:var(--ink3);background:var(--surface);}
.sdot{width:6px;height:6px;border-radius:50%;background:var(--ink3);flex-shrink:0;}
.sdot.go{background:var(--accent);animation:blink 1.4s infinite;}
.sdot.ok{background:var(--accent);}
.sdot.err{background:#DC2626;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
.main{flex:1;overflow:hidden;display:flex;flex-direction:column;}
.main-hdr{padding:1rem 1.5rem;border-bottom:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;flex-shrink:0;}
.main-title{font-family:'DM Serif Display',serif;font-size:18px;color:var(--ink);letter-spacing:-.2px;}
.main-sub{font-size:11px;color:var(--ink3);margin-top:1px;}
.toolbar{display:flex;align-items:center;gap:7px;flex-shrink:0;}
.srch{padding:6px 11px;border:1px solid var(--border);border-radius:8px;font-size:12px;font-family:'Outfit',sans-serif;background:var(--bg);color:var(--ink);width:180px;transition:all .15s;}
.srch:focus{outline:none;border-color:var(--accent);width:210px;}
.tabs{display:flex;padding:0 1.5rem;background:var(--surface);border-bottom:1px solid var(--border);flex-shrink:0;}
.tab{padding:9px 16px;font-size:12px;font-weight:500;color:var(--ink3);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;white-space:nowrap;display:flex;align-items:center;gap:6px;}
.tab:hover{color:var(--ink);}
.tab.on{color:var(--accent);border-bottom-color:var(--accent);}
.tbadge{background:var(--surface2);color:var(--ink3);font-size:9.5px;font-weight:600;padding:1px 5px;border-radius:9px;}
.tab.on .tbadge{background:var(--accent-light);color:var(--accent);}
.stats{display:flex;border-bottom:1px solid var(--border);background:var(--surface);padding:0 1.5rem;overflow-x:auto;flex-shrink:0;}
.stat{padding:9px 18px 9px 0;white-space:nowrap;}
.stat+.stat{border-left:1px solid var(--border);padding-left:18px;}
.stat-n{font-family:'DM Serif Display',serif;font-size:20px;color:var(--ink);line-height:1;}
.stat-l{font-size:10px;color:var(--ink3);line-height:1.4;}
.content{flex:1;overflow:hidden;position:relative;display:flex;flex-direction:column;}
.loader{display:none;position:absolute;inset:0;background:rgba(244,241,235,.9);backdrop-filter:blur(3px);z-index:40;flex-direction:column;align-items:center;justify-content:center;gap:12px;}
.loader.on{display:flex;}
.spin{width:32px;height:32px;border:2.5px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .75s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
.load-t{font-size:13px;color:var(--ink2);font-weight:500;}
.load-s{font-size:11px;color:var(--ink3);}
.empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2.5rem;text-align:center;}
.empty-ic{width:56px;height:56px;background:var(--surface2);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;}
.empty-ic svg{width:24px;height:24px;color:var(--ink3);}
.empty-t{font-family:'DM Serif Display',serif;font-size:18px;color:var(--ink);margin-bottom:6px;}
.empty-s{font-size:12px;color:var(--ink3);max-width:300px;line-height:1.6;}
.panel{display:none;flex-direction:column;flex:1;overflow:hidden;}
.panel.on{display:flex;}
.tbl-wrap{flex:1;overflow:auto;}
.tbl-wrap::-webkit-scrollbar{width:5px;height:5px;}
.tbl-wrap::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
table{width:100%;border-collapse:collapse;font-size:12px;}
thead{position:sticky;top:0;z-index:10;}
th{padding:10px 14px;text-align:left;font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);background:var(--surface2);border-bottom:1px solid var(--border);white-space:nowrap;}
td{padding:11px 14px;border-bottom:1px solid var(--border2);vertical-align:top;color:var(--ink);line-height:1.55;}
tbody tr:hover td{background:var(--surface2);}
.rn{font-family:'DM Mono',monospace;font-size:10px;color:var(--ink3);width:36px;text-align:center;}
.code{font-family:'DM Mono',monospace;font-size:11.5px;font-weight:500;color:var(--blue);white-space:nowrap;}
.badge{display:inline-block;padding:2px 7px;border-radius:9px;font-size:10.5px;font-weight:500;white-space:nowrap;}
.b-core{background:var(--green-light);color:#14532D;}
.b-mat{background:var(--amber-light);color:#78350F;}
.b-proc{background:var(--accent-light);color:var(--accent2);}
.b-app{background:var(--red-light);color:#991B1B;}
.b-comp{background:var(--purple-light);color:#4C1D95;}
.b-ipc{background:var(--blue-light);color:var(--blue);}
.b-cpc{background:#ECFDF5;color:#065F46;}
.syns{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px;}
.syn{background:var(--surface2);color:var(--ink2);font-size:10px;padding:2px 6px;border-radius:5px;border:1px solid var(--border);}
.panel-foot{padding:8px 1.5rem;border-top:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:space-between;font-size:11px;color:var(--ink3);}
.toast{position:fixed;bottom:20px;right:20px;background:var(--ink);color:#fff;padding:9px 14px;border-radius:9px;font-size:12px;font-weight:500;transform:translateY(70px);opacity:0;transition:all .3s;z-index:200;max-width:340px;}
.toast.show{transform:translateY(0);opacity:1;}
.toast.ok{background:var(--accent);}
.toast.err{background:#DC2626;}
input[type=file]{display:none;}
</style>
</head>
<body>
<header class="hdr">
  <div class="hdr-logo">
    <div class="hdr-mark"><span></span><span></span><span></span><span></span></div>
    <span class="hdr-name">PatentLens</span>
    <span class="hdr-sub">IP Classification Analyzer</span>
  </div>
  <div class="hdr-right">
    <button class="btn btn-ghost" onclick="clearAll()">Clear</button>
    <button class="btn btn-amber" id="dlBtn" onclick="dlCSV()" disabled>Download CSV</button>
  </div>
</header>
<div class="page">
  <aside class="sidebar">
    <div class="sb-body">
      <p class="lbl">Invention Disclosure</p>
      <div class="drop-zone" id="dz" onclick="document.getElementById('fi').click()" ondragover="dzOver(event)" ondragleave="dzOut()" ondrop="dzDrop(event)">
        <div class="drop-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="12" x2="12" y2="18"/><polyline points="9 15 12 12 15 15"/></svg></div>
        <div class="drop-t">Upload .txt file</div>
        <div class="drop-s">Drag and drop or click to browse</div>
      </div>
      <input type="file" id="fi" accept=".txt" onchange="loadFile(event)">
      <div id="fp" class="file-chip" style="display:none">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span id="fn">file.txt</span><span class="file-chip-x" onclick="rmFile()">x</span>
      </div>
      <p class="lbl" style="margin-top:4px">Or paste text</p>
      <textarea class="textarea" id="txt" placeholder="Paste your invention disclosure text here..." oninput="updCC()"></textarea>
      <div class="char-ct" id="cc">0 characters</div>
      <p class="lbl">Output Sections</p>
      <div class="checks">
        <label class="chk on" id="ck-kw"><div class="dot"><div class="dot-i"></div></div><input type="checkbox" checked onchange="togChk(this,'ck-kw')"> Keywords</label>
        <label class="chk on" id="ck-ipc"><div class="dot"><div class="dot-i"></div></div><input type="checkbox" checked onchange="togChk(this,'ck-ipc')"> IPC Classes</label>
        <label class="chk on" id="ck-cpc"><div class="dot"><div class="dot-i"></div></div><input type="checkbox" checked onchange="togChk(this,'ck-cpc')"> CPC Classes</label>
        <label class="chk on" id="ck-syn"><div class="dot"><div class="dot-i"></div></div><input type="checkbox" checked onchange="togChk(this,'ck-syn')"> Synonyms</label>
      </div>
      <button class="btn btn-green run-btn" id="runBtn" onclick="analyze()">Analyze Invention</button>
    </div>
    <div class="sb-foot"><div class="sdot" id="sdot"></div><span id="stxt">Paste your invention disclosure and click Analyze</span></div>
  </aside>
  <main class="main">
    <div class="main-hdr">
      <div><div class="main-title" id="mtitle">Analysis Results</div><div class="main-sub" id="msub">Paste your invention disclosure text and click Analyze Invention</div></div>
      <div class="toolbar"><input class="srch" type="text" placeholder="Search results..." oninput="doSearch(this.value)" id="srch"></div>
    </div>
    <div class="tabs">
      <div class="tab on" onclick="goTab('kw',this)">Keywords <span class="tbadge" id="bkw">0</span></div>
      <div class="tab" onclick="goTab('ipc',this)">IPC Classes <span class="tbadge" id="bipc">0</span></div>
      <div class="tab" onclick="goTab('cpc',this)">CPC Classes <span class="tbadge" id="bcpc">0</span></div>
    </div>
    <div class="stats" id="statsRow" style="display:none">
      <div class="stat"><div class="stat-n" id="skw">0</div><div class="stat-l">Keywords<br>extracted</div></div>
      <div class="stat"><div class="stat-n" id="sipc">0</div><div class="stat-l">IPC<br>classes</div></div>
      <div class="stat"><div class="stat-n" id="scpc">0</div><div class="stat-l">CPC<br>classes</div></div>
      <div class="stat"><div class="stat-n" id="ssyn">0</div><div class="stat-l">Synonyms<br>mapped</div></div>
    </div>
    <div class="content">
      <div class="loader" id="ldr"><div class="spin"></div><div class="load-t" id="lt">Analyzing invention disclosure...</div><div class="load-s">This takes 30-60 seconds</div></div>
      <div class="empty" id="emp">
        <div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></div>
        <div class="empty-t">No analysis yet</div>
        <div class="empty-s">Paste your invention disclosure text on the left and click Analyze Invention to begin.</div>
      </div>
      <div class="panel" id="p-kw"><div class="tbl-wrap"><table><thead><tr><th class="rn">#</th><th style="min-width:150px">Keyword</th><th style="min-width:100px">Category</th><th style="min-width:220px">Definition</th><th style="min-width:200px">Synonyms</th></tr></thead><tbody id="kwb"></tbody></table></div><div class="panel-foot"><span id="kwc">-</span></div></div>
      <div class="panel" id="p-ipc"><div class="tbl-wrap"><table><thead><tr><th class="rn">#</th><th style="min-width:100px">IPC Code</th><th style="min-width:120px">Section</th><th style="min-width:240px">Official Definition</th><th style="min-width:210px">Relevance</th></tr></thead><tbody id="ipcb"></tbody></table></div><div class="panel-foot"><span id="ipcc">-</span></div></div>
      <div class="panel" id="p-cpc"><div class="tbl-wrap"><table><thead><tr><th class="rn">#</th><th style="min-width:100px">CPC Code</th><th style="min-width:120px">Section</th><th style="min-width:240px">Official Definition</th><th style="min-width:210px">Relevance</th></tr></thead><tbody id="cpcb"></tbody></table></div><div class="panel-foot"><span id="cpcc">-</span></div></div>
    </div>
  </main>
</div>
<div class="toast" id="toast"></div>
<script>
let data={};
function dzOver(e){e.preventDefault();document.getElementById('dz').classList.add('over');}
function dzOut(){document.getElementById('dz').classList.remove('over');}
function dzDrop(e){e.preventDefault();dzOut();const f=e.dataTransfer.files[0];if(f)readFile(f);}
function loadFile(e){const f=e.target.files[0];if(f)readFile(f);}
function readFile(f){const r=new FileReader();r.onload=ev=>{document.getElementById('txt').value=ev.target.result;updCC();};r.readAsText(f);document.getElementById('fn').textContent=f.name;document.getElementById('fp').style.display='flex';document.getElementById('dz').style.display='none';toast('File loaded: '+f.name,'ok');}
function rmFile(){document.getElementById('fp').style.display='none';document.getElementById('dz').style.display='block';document.getElementById('fi').value='';}
function updCC(){document.getElementById('cc').textContent=document.getElementById('txt').value.length.toLocaleString()+' characters';}
function togChk(inp,id){document.getElementById(id).classList.toggle('on',inp.checked);}
function goTab(t,el){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));el.classList.add('on');document.getElementById('p-'+t).classList.add('on');doSearch(document.getElementById('srch').value);}
function doSearch(q){q=q.toLowerCase().trim();['kw','ipc','cpc'].forEach(t=>{const b=document.getElementById(t+'b');if(!b)return;let v=0;b.querySelectorAll('tr').forEach(r=>{const m=!q||r.textContent.toLowerCase().includes(q);r.style.display=m?'':'none';if(m)v++;});document.getElementById(t+'c').textContent=v+' result'+(v!==1?'s':'');});}
async function analyze(){
  const txt=document.getElementById('txt').value.trim();
  if(!txt){toast('Please paste your invention disclosure text','err');return;}
  setSt('go','Analyzing...');document.getElementById('ldr').classList.add('on');document.getElementById('emp').style.display='none';document.getElementById('runBtn').disabled=true;
  const msgs=['Analyzing invention disclosure...','Mapping IPC classification hierarchy...','Identifying CPC subgroups...','Generating synonyms and variants...','Building classification report...'];
  let mi=0;const iv=setInterval(()=>{document.getElementById('lt').textContent=msgs[++mi%msgs.length];},2800);
  try{
    const res=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})});
    clearInterval(iv);
    const d=await res.json();
    if(!res.ok||d.error)throw new Error(d.error||'Server error');
    data=d;render(d);
    document.getElementById('mtitle').textContent=d.title||'Analysis Results';
    document.getElementById('msub').textContent=d.summary||'Patent classification analysis complete';
    document.getElementById('dlBtn').disabled=false;document.getElementById('statsRow').style.display='flex';
    const ts=(d.keywords||[]).reduce((a,k)=>a+(k.synonyms||[]).length,0);
    document.getElementById('skw').textContent=(d.keywords||[]).length;
    document.getElementById('sipc').textContent=(d.ipc||[]).length;
    document.getElementById('scpc').textContent=(d.cpc||[]).length;
    document.getElementById('ssyn').textContent=ts;
    document.getElementById('bkw').textContent=(d.keywords||[]).length;
    document.getElementById('bipc').textContent=(d.ipc||[]).length;
    document.getElementById('bcpc').textContent=(d.cpc||[]).length;
    goTab('kw',document.querySelector('.tab'));
    setSt('ok','Done - '+(d.keywords||[]).length+' keywords, '+(d.ipc||[]).length+' IPC, '+(d.cpc||[]).length+' CPC');
    toast('Analysis complete!','ok');
  }catch(err){clearInterval(iv);setSt('err','Error: '+err.message);toast('Error: '+err.message,'err');document.getElementById('emp').style.display='flex';}
  finally{document.getElementById('ldr').classList.remove('on');document.getElementById('runBtn').disabled=false;}
}
const catMap={'Core Invention':'b-core','Material':'b-mat','Process':'b-proc','Application':'b-app','Comparative':'b-comp'};
function render(d){
  document.getElementById('kwb').innerHTML=(d.keywords||[]).map((k,i)=>`<tr><td class="rn">${i+1}</td><td><strong style="font-weight:500">${h(k.term)}</strong></td><td><span class="badge ${catMap[k.category]||'b-core'}">${h(k.category)}</span></td><td style="max-width:240px">${h(k.definition)}</td><td><div class="syns">${(k.synonyms||[]).map(s=>`<span class="syn">${h(s)}</span>`).join('')}</div></td></tr>`).join('');
  document.getElementById('kwc').textContent=(d.keywords||[]).length+' results';
  document.getElementById('ipcb').innerHTML=(d.ipc||[]).map((c,i)=>`<tr><td class="rn">${i+1}</td><td class="code">${h(c.code)}</td><td><span class="badge b-ipc">${h(c.section)}</span></td><td style="max-width:240px">${h(c.definition)}</td><td style="max-width:210px;color:var(--ink2)">${h(c.relevance)}</td></tr>`).join('');
  document.getElementById('ipcc').textContent=(d.ipc||[]).length+' results';
  document.getElementById('cpcb').innerHTML=(d.cpc||[]).map((c,i)=>`<tr><td class="rn">${i+1}</td><td class="code">${h(c.code)}</td><td><span class="badge b-cpc">${h(c.section)}</span></td><td style="max-width:240px">${h(c.definition)}</td><td style="max-width:210px;color:var(--ink2)">${h(c.relevance)}</td></tr>`).join('');
  document.getElementById('cpcc').textContent=(d.cpc||[]).length+' results';
}
function dlCSV(){
  if(!data.keywords){toast('No data','err');return;}
  const e=v=>'"'+String(v||'').replace(/"/g,'""')+'"';
  const rows=[['PATENT CLASSIFICATION ANALYSIS'],['Invention:',data.title||''],['Summary:',data.summary||''],[]];
  rows.push(['=== KEYWORDS ==='],['#','Keyword','Category','Definition','Syn1','Syn2','Syn3','Syn4','Syn5']);
  (data.keywords||[]).forEach((k,i)=>{const s=k.synonyms||[];rows.push([i+1,k.term,k.category,k.definition,s[0]||'',s[1]||'',s[2]||'',s[3]||'',s[4]||'']);});
  rows.push([],['=== IPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.ipc||[]).forEach((c,i)=>rows.push([i+1,c.code,c.section,c.definition,c.relevance]));
  rows.push([],['=== CPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.cpc||[]).forEach((c,i)=>rows.push([i+1,c.code,c.section,c.definition,c.relevance]));
  const csv=rows.map(r=>r.map(e).join(',')).join('\\n');
  const a=Object.assign(document.createElement('a'),{href:URL.createObjectURL(new Blob(['\\uFEFF'+csv],{type:'text/csv;charset=utf-8;'})),download:'patent_classification.csv'});
  a.click();toast('CSV downloaded','ok');
}
function h(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function setSt(s,t){document.getElementById('sdot').className='sdot '+s;document.getElementById('stxt').textContent=t;}
function toast(msg,type=''){const t=document.getElementById('toast');t.textContent=msg;t.className='toast '+type+' show';setTimeout(()=>t.classList.remove('show'),4000);}
function clearAll(){data={};['kw','ipc','cpc'].forEach(t=>{const b=document.getElementById(t+'b');if(b)b.innerHTML='';document.getElementById(t+'c').textContent='-';document.getElementById('b'+t).textContent='0';});document.getElementById('txt').value='';document.getElementById('emp').style.display='flex';document.getElementById('statsRow').style.display='none';document.getElementById('dlBtn').disabled=true;document.getElementById('mtitle').textContent='Analysis Results';document.getElementById('msub').textContent='Paste your invention disclosure text and click Analyze Invention';rmFile();updCC();setSt('','Paste your invention disclosure and click Analyze');}
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print("[%s] %s" % (self.address_string(), format % args))

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/analyze":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                text = body.get("text", "").strip()
                if not text:
                    self._json({"error": "No text provided"}, 400)
                    return
                print("Calling Claude API...")
                prompt = """You are a senior patent classification expert. Analyze the invention disclosure and return ONLY a valid JSON object. No markdown, no explanation.

Invention Disclosure:
\"\"\"
%s
\"\"\"

Return exactly this structure:
{
  "title": "concise invention title max 10 words",
  "summary": "one clear technical sentence",
  "keywords": [{"term":"","category":"Core Invention|Material|Process|Application|Comparative","definition":"2-3 sentences","synonyms":["","","","",""]}],
  "ipc": [{"code":"","section":"3-5 words","definition":"official definition","relevance":"1-2 sentences"}],
  "cpc": [{"code":"","section":"3-5 words","definition":"official definition","relevance":"1-2 sentences"}]
}

REQUIREMENTS: Minimum 20 keywords with 5 synonyms each. Minimum 75 real valid IPC codes. Minimum 75 real valid CPC codes. Return ONLY raw JSON.""" % text

                payload = json.dumps({"model": MODEL, "max_tokens": 8000, "messages": [{"role": "user", "content": prompt}]}).encode()
                req = Request("https://api.anthropic.com/v1/messages", data=payload,
                    headers={"Content-Type": "application/json", "x-api-key": API_KEY, "anthropic-version": "2023-06-01"}, method="POST")
                ctx = ssl.create_default_context()
                with urlopen(req, context=ctx, timeout=120) as r:
                    result = json.loads(r.read())
                raw = "".join(b.get("text", "") for b in result.get("content", [])).strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw.rsplit("```", 1)[0]
                parsed = json.loads(raw.strip())
                print("Done! Keywords: %d, IPC: %d, CPC: %d" % (len(parsed.get("keywords",[])), len(parsed.get("ipc",[])), len(parsed.get("cpc",[]))))
                self._json(parsed)
            except HTTPError as e:
                msg = e.read().decode("utf-8", "ignore")[:300]
                print("API Error %d: %s" % (e.code, msg))
                self._json({"error": "API error %d: %s" % (e.code, msg)}, 502)
            except Exception as e:
                print("Error: %s" % e)
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "Not found"}, 404)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print("PatentLens server starting on port %d" % PORT)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
