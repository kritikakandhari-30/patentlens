import os, json, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))

HTML = b"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PatentLens</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#F4F1EB;color:#1C1915;font-size:14px}
.hdr{background:#1C1915;display:flex;align-items:center;justify-content:space-between;padding:0 1.5rem;height:56px}
.hn{font-size:17px;color:#fff;font-weight:600}
.hb{padding:7px 14px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;border:none;background:#B86A08;color:#fff}
.hb:disabled{opacity:.4}
.wrap{display:flex;height:calc(100vh - 56px)}
.left{width:320px;background:#FDFBF8;border-right:1px solid #e0ddd6;display:flex;flex-direction:column;padding:1.5rem;gap:1rem}
.lbl{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#8A837A}
textarea{width:100%;height:220px;padding:10px 12px;border:1.5px solid #d0cdc6;border-radius:8px;font-family:system-ui;font-size:13px;resize:vertical;background:#F4F1EB;color:#1C1915}
textarea:focus{outline:none;border-color:#2D5F3F}
.abtn{width:100%;padding:12px;background:#2D5F3F;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;font-family:system-ui}
.abtn:hover{background:#1A3D27}
.right{flex:1;overflow:hidden;display:flex;flex-direction:column}
.rh{padding:1rem 1.5rem;border-bottom:1px solid #e0ddd6;background:#FDFBF8}
.rt{font-size:18px;font-weight:600}
.rs{font-size:12px;color:#8A837A;margin-top:2px}
.tabs{display:flex;padding:0 1.5rem;background:#FDFBF8;border-bottom:1px solid #e0ddd6}
.tab{padding:10px 18px;font-size:13px;font-weight:500;color:#8A837A;cursor:pointer;border-bottom:2px solid transparent;display:flex;align-items:center;gap:6px}
.tab.on{color:#2D5F3F;border-bottom-color:#2D5F3F}
.tbg{background:#eee;color:#666;font-size:10px;font-weight:700;padding:1px 6px;border-radius:8px}
.tab.on .tbg{background:#E6F2EC;color:#2D5F3F}
.tc{flex:1;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
thead{position:sticky;top:0}
th{padding:10px 16px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#8A837A;background:#EEEAE0;border-bottom:1px solid #d0cdc6;white-space:nowrap}
td{padding:12px 16px;border-bottom:1px solid #f0ede6;vertical-align:top;line-height:1.5}
tr:hover td{background:#f5f2eb}
.rn{font-family:monospace;font-size:11px;color:#aaa;width:36px;text-align:center}
.code{font-family:monospace;font-size:12px;font-weight:700;color:#1B4F8A;white-space:nowrap}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;white-space:nowrap}
.b1{background:#F0FDF4;color:#14532D}.b2{background:#FEF3E2;color:#78350F}.b3{background:#E6F2EC;color:#1A3D27}.b4{background:#FEE2E2;color:#991B1B}.b5{background:#EDE9FE;color:#4C1D95}.bi{background:#E8F0FB;color:#1B4F8A}.bc{background:#ECFDF5;color:#065F46}
.syns{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.syn{background:#eee;color:#555;font-size:11px;padding:2px 7px;border-radius:5px}
.panel{display:none;flex-direction:column;flex:1;overflow:hidden}
.panel.on{display:flex}
.empty{flex:1;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:#8A837A}
.loader{display:none;flex:1;align-items:center;justify-content:center;flex-direction:column;gap:12px}
.loader.on{display:flex}
.spin{width:36px;height:36px;border:3px solid #e0ddd6;border-top-color:#2D5F3F;border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.lt{font-size:14px;font-weight:500;color:#333}
.st{font-size:12px;color:#8A837A}
.pf{padding:8px 1.5rem;border-top:1px solid #e0ddd6;background:#FDFBF8;font-size:12px;color:#8A837A}
.toast{position:fixed;bottom:20px;right:20px;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:500;color:#fff;transform:translateY(60px);opacity:0;transition:all .3s;z-index:999}
.toast.show{transform:translateY(0);opacity:1}
.toast.ok{background:#2D5F3F}
.toast.err{background:#DC2626}
#status{font-size:12px;color:#8A837A;margin-top:4px}
</style>
</head>
<body>
<div class="hdr">
  <span class="hn">PatentLens &mdash; IP Classification Analyzer</span>
  <button class="hb" id="dlBtn" onclick="dlCSV()" disabled>Download CSV</button>
</div>
<div class="wrap">
  <div class="left">
    <div class="lbl">Invention Disclosure</div>
    <textarea id="txt" placeholder="Paste your invention disclosure text here..."></textarea>
    <div id="status">Ready</div>
    <button class="abtn" onclick="analyze()">Analyze Invention</button>
  </div>
  <div class="right">
    <div class="rh"><div class="rt" id="rt">Analysis Results</div><div class="rs" id="rs">Paste your invention disclosure and click Analyze</div></div>
    <div class="tabs">
      <div class="tab on" onclick="gt('kw',this)">Keywords <span class="tbg" id="bkw">0</span></div>
      <div class="tab" onclick="gt('ipc',this)">IPC Classes <span class="tbg" id="bipc">0</span></div>
      <div class="tab" onclick="gt('cpc',this)">CPC Classes <span class="tbg" id="bcpc">0</span></div>
    </div>
    <div class="loader" id="ldr"><div class="spin"></div><div class="lt" id="lt">Analyzing...</div><div class="st">Please wait 30-60 seconds</div></div>
    <div class="empty" id="emp"><div>No analysis yet</div><div style="font-size:13px">Paste disclosure text and click Analyze Invention</div></div>
    <div class="panel" id="p-kw"><div class="tc"><table><thead><tr><th class="rn">#</th><th>Keyword</th><th>Category</th><th>Definition</th><th>Synonyms</th></tr></thead><tbody id="kwb"></tbody></table></div><div class="pf" id="kwc"></div></div>
    <div class="panel" id="p-ipc"><div class="tc"><table><thead><tr><th class="rn">#</th><th>IPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="ipcb"></tbody></table></div><div class="pf" id="ipcc"></div></div>
    <div class="panel" id="p-cpc"><div class="tc"><table><thead><tr><th class="rn">#</th><th>CPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="cpcb"></tbody></table></div><div class="pf" id="cpcc"></div></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
let data={};
function gt(t,el){
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
  el.classList.add('on');
  document.getElementById('p-'+t).classList.add('on');
}
async function analyze(){
  var el=document.getElementById('txt');
  var txt=el.value||el.textContent||el.innerHTML||'';
  txt=txt.trim();
  document.getElementById('status').textContent='Sending... ('+txt.length+' chars)';
  if(txt.length<3){
    txt=document.querySelector('#txt').value;
    if(txt.length<3){toast('Please type or paste text first','err');return;}
  }
  document.getElementById('ldr').classList.add('on');
  document.getElementById('emp').style.display='none';
  document.getElementById('status').textContent='Sending to server...';
  var msgs=['Analyzing invention...','Mapping IPC classes...','Finding CPC codes...','Building report...'];
  var mi=0;
  var iv=setInterval(function(){document.getElementById('lt').textContent=msgs[++mi%msgs.length];},3000);
  try{
    var res=await fetch('/analyze',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:txt})
    });
    clearInterval(iv);
    var d=await res.json();
    if(d.error)throw new Error(d.error);
    data=d;
    render(d);
    document.getElementById('rt').textContent=d.title||'Analysis Results';
    document.getElementById('rs').textContent=d.summary||'Complete';
    document.getElementById('dlBtn').disabled=false;
    document.getElementById('bkw').textContent=(d.keywords||[]).length;
    document.getElementById('bipc').textContent=(d.ipc||[]).length;
    document.getElementById('bcpc').textContent=(d.cpc||[]).length;
    gt('kw',document.querySelector('.tab'));
    document.getElementById('status').textContent='Done!';
    toast('Analysis complete!','ok');
  }catch(err){
    clearInterval(iv);
    document.getElementById('emp').style.display='flex';
    document.getElementById('status').textContent='Error: '+err.message;
    toast('Error: '+err.message,'err');
  }finally{
    document.getElementById('ldr').classList.remove('on');
  }
}
var cm={'Core Invention':'b1','Material':'b2','Process':'b3','Application':'b4','Comparative':'b5'};
function render(d){
  document.getElementById('kwb').innerHTML=(d.keywords||[]).map(function(k,i){
    return '<tr><td class="rn">'+(i+1)+'</td><td><strong>'+h(k.term)+'</strong></td><td><span class="badge '+(cm[k.category]||'b1')+'">'+h(k.category)+'</span></td><td style="max-width:220px">'+h(k.definition)+'</td><td><div class="syns">'+(k.synonyms||[]).map(function(s){return '<span class="syn">'+h(s)+'</span>';}).join('')+'</div></td></tr>';
  }).join('');
  document.getElementById('kwc').textContent=(d.keywords||[]).length+' keywords';
  document.getElementById('ipcb').innerHTML=(d.ipc||[]).map(function(c,i){
    return '<tr><td class="rn">'+(i+1)+'</td><td class="code">'+h(c.code)+'</td><td><span class="badge bi">'+h(c.section)+'</span></td><td style="max-width:220px">'+h(c.definition)+'</td><td style="max-width:200px;color:#555">'+h(c.relevance)+'</td></tr>';
  }).join('');
  document.getElementById('ipcc').textContent=(d.ipc||[]).length+' IPC codes';
  document.getElementById('cpcb').innerHTML=(d.cpc||[]).map(function(c,i){
    return '<tr><td class="rn">'+(i+1)+'</td><td class="code">'+h(c.code)+'</td><td><span class="badge bc">'+h(c.section)+'</span></td><td style="max-width:220px">'+h(c.definition)+'</td><td style="max-width:200px;color:#555">'+h(c.relevance)+'</td></tr>';
  }).join('');
  document.getElementById('cpcc').textContent=(d.cpc||[]).length+' CPC codes';
}
function dlCSV(){
  if(!data.keywords)return;
  var e=function(v){return '"'+String(v||'').replace(/"/g,'""')+'"';};
  var rows=[['PATENT CLASSIFICATION ANALYSIS'],['Invention:',data.title||''],['Summary:',data.summary||''],[]];
  rows.push(['=== KEYWORDS ==='],['#','Keyword','Category','Definition','Syn1','Syn2','Syn3','Syn4','Syn5']);
  (data.keywords||[]).forEach(function(k,i){var s=k.synonyms||[];rows.push([i+1,k.term,k.category,k.definition,s[0]||'',s[1]||'',s[2]||'',s[3]||'',s[4]||'']);});
  rows.push([],['=== IPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.ipc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  rows.push([],['=== CPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.cpc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  var csv=rows.map(function(r){return r.map(e).join(',');}).join('\n');
  var a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob(['\N{BOM}'+csv],{type:'text/csv;charset=utf-8;'}));
  a.download='patent_classification.csv';
  a.click();
  toast('CSV downloaded!','ok');
}
function h(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function toast(msg,type){var t=document.getElementById('toast');t.textContent=msg;t.className='toast '+(type||'')+' show';setTimeout(function(){t.classList.remove('show');},4000);}
</script>
</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): print(f % a)
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(HTML)))
        self._cors(); self.end_headers(); self.wfile.write(HTML)
    def do_POST(self):
        if self.path != "/analyze":
            self._json({"error":"not found"},404); return
        try:
            n=int(self.headers.get("Content-Length",0))
            body=self.rfile.read(n)
            txt=json.loads(body).get("text","").strip()
            if not txt:
                self._json({"error":"No text received"},400); return
            print("Analyzing: %d chars" % len(txt))
            prompt="""Analyze this invention disclosure. Return ONLY a raw JSON object, absolutely no markdown or explanation before or after.

The JSON must have these exact keys:
{
  "title": "short invention title",
  "summary": "one sentence summary",
  "keywords": [{"term":"","category":"Core Invention","definition":"","synonyms":["","","","",""]}],
  "ipc": [{"code":"","section":"","definition":"","relevance":""}],
  "cpc": [{"code":"","section":"","definition":"","relevance":""}]
}

Produce exactly 20 keywords (categories: Core Invention/Material/Process/Application/Comparative), 50 IPC codes, 50 CPC codes.
Start your response with { and end with }

Invention:
"""+txt[:2000]
            payload=json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":4000,"messages":[{"role":"user","content":prompt}]}).encode()
            req=Request("https://api.anthropic.com/v1/messages",data=payload,headers={"Content-Type":"application/json","x-api-key":API_KEY,"anthropic-version":"2023-06-01"},method="POST")
            with urlopen(req,context=ssl.create_default_context(),timeout=55) as r:
                result=json.loads(r.read())
            raw="".join(b.get("text","") for b in result.get("content",[])).strip()
            # find the JSON object
            start=raw.find("{")
            end=raw.rfind("}")+1
            if start>=0 and end>start:
                raw=raw[start:end]
            parsed=json.loads(raw)
            print("Done KW:%d IPC:%d CPC:%d"%(len(parsed.get("keywords",[])),len(parsed.get("ipc",[])),len(parsed.get("cpc",[]))))
            self._json(parsed)
        except HTTPError as e:
            err=e.read().decode("utf-8","ignore")[:200]
            print("API Error %d: %s"%(e.code,err))
            self._json({"error":"API error. Try again."},502)
        except json.JSONDecodeError as e:
            print("JSON error: %s"%e)
            self._json({"error":"Please try again."},500)
        except Exception as e:
            print("Error: %s"%e)
            self._json({"error":str(e)},500)
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
    def _json(self,data,status=200):
        body=json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self._cors(); self.end_headers(); self.wfile.write(body)

if __name__=="__main__":
    print("PatentLens on port %d"%PORT)
    HTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
