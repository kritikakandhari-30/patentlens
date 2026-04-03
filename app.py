import os, json, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))

HTML = b"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PatentLens</title><style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#F4F1EB;color:#1C1915;font-size:13px;display:flex;flex-direction:column;height:100vh;overflow:hidden}.hdr{background:#1C1915;display:flex;align-items:center;justify-content:space-between;padding:0 1.25rem;height:52px;flex-shrink:0}.ln{font-size:16px;color:#fff;font-weight:600}.btn{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:500;cursor:pointer;border:none}.ag{background:rgba(255,255,255,.1);color:rgba(255,255,255,.8)}.am{background:#B86A08;color:#fff}.am:disabled{opacity:.4;cursor:not-allowed}.page{display:flex;flex:1;overflow:hidden}.sb{width:290px;background:#FDFBF8;border-right:1px solid rgba(0,0,0,.09);display:flex;flex-direction:column}.sbb{flex:1;overflow-y:auto;padding:1.25rem}.lbl{font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8A837A;margin-bottom:8px;margin-top:12px}.ta{width:100%;background:#F4F1EB;border:1px solid rgba(0,0,0,.09);border-radius:8px;padding:9px 11px;font-family:system-ui;font-size:12px;color:#1C1915;resize:vertical;min-height:200px;line-height:1.6;margin-bottom:4px}.ta:focus{outline:none;border-color:#2D5F3F}.ta::placeholder{color:#8A837A}.cc{font-size:10px;color:#8A837A;text-align:right;margin-bottom:12px}.rbtn{width:100%;padding:10px;font-size:13px;border-radius:8px;background:#2D5F3F;color:#fff;border:none;cursor:pointer;font-family:system-ui;font-weight:500;margin-top:4px}.rbtn:hover{background:#1A3D27}.rbtn:disabled{opacity:.45;cursor:not-allowed}.sbf{padding:9px 1.25rem;border-top:1px solid rgba(0,0,0,.09);display:flex;align-items:center;gap:7px;font-size:11px;color:#8A837A}.sd{width:6px;height:6px;border-radius:50%;background:#8A837A;flex-shrink:0}.sd.go{background:#2D5F3F;animation:blink 1.4s infinite}.sd.ok{background:#2D5F3F}.sd.err{background:#DC2626}@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}.main{flex:1;overflow:hidden;display:flex;flex-direction:column}.mh{padding:1rem 1.5rem;border-bottom:1px solid rgba(0,0,0,.09);background:#FDFBF8;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;flex-shrink:0}.mt{font-size:18px;font-weight:600}.ms{font-size:11px;color:#8A837A;margin-top:1px}.sr{padding:6px 11px;border:1px solid rgba(0,0,0,.09);border-radius:8px;font-size:12px;background:#F4F1EB;color:#1C1915;width:180px}.tabs{display:flex;padding:0 1.5rem;background:#FDFBF8;border-bottom:1px solid rgba(0,0,0,.09);flex-shrink:0}.tab{padding:9px 16px;font-size:12px;font-weight:500;color:#8A837A;cursor:pointer;border-bottom:2px solid transparent;display:flex;align-items:center;gap:6px}.tab.on{color:#2D5F3F;border-bottom-color:#2D5F3F}.tbg{background:#EEEAE0;color:#8A837A;font-size:9.5px;font-weight:700;padding:1px 5px;border-radius:9px}.tab.on .tbg{background:#E6F2EC;color:#2D5F3F}.stats{display:flex;border-bottom:1px solid rgba(0,0,0,.09);background:#FDFBF8;padding:0 1.5rem;flex-shrink:0}.stat{padding:9px 18px 9px 0;white-space:nowrap}.stat+.stat{border-left:1px solid rgba(0,0,0,.09);padding-left:18px}.sn{font-size:20px;font-weight:600;line-height:1}.sl{font-size:10px;color:#8A837A}.cnt{flex:1;overflow:hidden;position:relative;display:flex;flex-direction:column}.ldr{display:none;position:absolute;inset:0;background:rgba(244,241,235,.92);z-index:40;flex-direction:column;align-items:center;justify-content:center;gap:12px}.ldr.on{display:flex}.spin{width:32px;height:32px;border:2.5px solid rgba(0,0,0,.09);border-top-color:#2D5F3F;border-radius:50%;animation:spin .75s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.lt{font-size:13px;font-weight:500}.ls2{font-size:11px;color:#8A837A}.emp{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem}.et{font-size:18px;font-weight:600;margin-bottom:6px}.es{font-size:12px;color:#8A837A;max-width:300px;line-height:1.6}.panel{display:none;flex-direction:column;flex:1;overflow:hidden}.panel.on{display:flex}.tw{flex:1;overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}thead{position:sticky;top:0;z-index:10}th{padding:10px 14px;text-align:left;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#8A837A;background:#EEEAE0;border-bottom:1px solid rgba(0,0,0,.09);white-space:nowrap}td{padding:11px 14px;border-bottom:1px solid rgba(0,0,0,.05);vertical-align:top;line-height:1.55}tbody tr:hover td{background:#EEEAE0}.rn{font-family:monospace;font-size:10px;color:#8A837A;width:36px;text-align:center}.code{font-family:monospace;font-size:11.5px;font-weight:600;color:#1B4F8A;white-space:nowrap}.badge{display:inline-block;padding:2px 7px;border-radius:9px;font-size:10.5px;font-weight:500;white-space:nowrap}.b1{background:#F0FDF4;color:#14532D}.b2{background:#FEF3E2;color:#78350F}.b3{background:#E6F2EC;color:#1A3D27}.b4{background:#FEE2E2;color:#991B1B}.b5{background:#EDE9FE;color:#4C1D95}.bi{background:#E8F0FB;color:#1B4F8A}.bc{background:#ECFDF5;color:#065F46}.syns{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}.syn{background:#EEEAE0;color:#4A4540;font-size:10px;padding:2px 6px;border-radius:5px}.pf{padding:8px 1.5rem;border-top:1px solid rgba(0,0,0,.09);background:#FDFBF8;font-size:11px;color:#8A837A}.toast{position:fixed;bottom:20px;right:20px;background:#1C1915;color:#fff;padding:9px 14px;border-radius:9px;font-size:12px;font-weight:500;transform:translateY(70px);opacity:0;transition:all .3s;z-index:200}.toast.show{transform:translateY(0);opacity:1}.toast.ok{background:#2D5F3F}.toast.err{background:#DC2626}</style></head><body>
<header class="hdr"><span class="ln">PatentLens &mdash; IP Classification Analyzer</span><div style="display:flex;gap:8px"><button class="btn ag" onclick="clearAll()">Clear</button><button class="btn am" id="dlBtn" onclick="dlCSV()" disabled>Download CSV</button></div></header>
<div class="page">
<aside class="sb"><div class="sbb">
<p class="lbl">Invention Disclosure</p>
<textarea class="ta" id="txt" placeholder="Paste your invention disclosure text here..." oninput="ucc()"></textarea>
<div class="cc" id="cc">0 characters</div>
<button class="rbtn" id="rb" onclick="analyze()">Analyze Invention</button>
</div><div class="sbf"><div class="sd" id="sd"></div><span id="st">Paste disclosure and click Analyze</span></div></aside>
<main class="main">
<div class="mh"><div><div class="mt" id="mt">Analysis Results</div><div class="ms" id="ms">Paste invention disclosure and click Analyze</div></div><input class="sr" type="text" placeholder="Search..." oninput="doSearch(this.value)"></div>
<div class="tabs"><div class="tab on" onclick="gt('kw',this)">Keywords <span class="tbg" id="bkw">0</span></div><div class="tab" onclick="gt('ipc',this)">IPC Classes <span class="tbg" id="bipc">0</span></div><div class="tab" onclick="gt('cpc',this)">CPC Classes <span class="tbg" id="bcpc">0</span></div></div>
<div class="stats" id="sr" style="display:none"><div class="stat"><div class="sn" id="skw">0</div><div class="sl">Keywords</div></div><div class="stat"><div class="sn" id="sipc">0</div><div class="sl">IPC codes</div></div><div class="stat"><div class="sn" id="scpc">0</div><div class="sl">CPC codes</div></div><div class="stat"><div class="sn" id="ssyn">0</div><div class="sl">Synonyms</div></div></div>
<div class="cnt">
<div class="ldr" id="ldr"><div class="spin"></div><div class="lt" id="lt">Analyzing...</div><div class="ls2">Please wait 30-60 seconds</div></div>
<div class="emp" id="emp"><div class="et">No analysis yet</div><div class="es">Paste your invention disclosure on the left and click Analyze Invention.</div></div>
<div class="panel" id="p-kw"><div class="tw"><table><thead><tr><th class="rn">#</th><th>Keyword</th><th>Category</th><th>Definition</th><th>Synonyms</th></tr></thead><tbody id="kwb"></tbody></table></div><div class="pf" id="kwc">-</div></div>
<div class="panel" id="p-ipc"><div class="tw"><table><thead><tr><th class="rn">#</th><th>IPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="ipcb"></tbody></table></div><div class="pf" id="ipcc">-</div></div>
<div class="panel" id="p-cpc"><div class="tw"><table><thead><tr><th class="rn">#</th><th>CPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="cpcb"></tbody></table></div><div class="pf" id="cpcc">-</div></div>
</div></main></div>
<div class="toast" id="toast"></div>
<script>
let data={};
function ucc(){document.getElementById('cc').textContent=document.getElementById('txt').value.length.toLocaleString()+' characters'}
function gt(t,el){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));el.classList.add('on');document.getElementById('p-'+t).classList.add('on');doSearch(document.querySelector('.sr').value)}
function doSearch(q){q=q.toLowerCase().trim();['kw','ipc','cpc'].forEach(t=>{const b=document.getElementById(t+'b');if(!b)return;let v=0;b.querySelectorAll('tr').forEach(r=>{const m=!q||r.textContent.toLowerCase().includes(q);r.style.display=m?'':'none';if(m)v++});document.getElementById(t+'c').textContent=v+' result'+(v!==1?'s':'')})}
async function analyze(){
  const txt=document.getElementById('txt').value.trim();
  if(!txt){toast('Please paste your invention disclosure text','err');return}
  setSt('go','Analyzing...');
  document.getElementById('ldr').classList.add('on');
  document.getElementById('emp').style.display='none';
  document.getElementById('rb').disabled=true;
  const msgs=['Analyzing invention disclosure...','Mapping IPC classifications...','Identifying CPC subgroups...','Generating synonyms...','Almost done...'];
  let mi=0;const iv=setInterval(()=>{document.getElementById('lt').textContent=msgs[++mi%msgs.length]},3000);
  try{
    const res=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})});
    clearInterval(iv);
    const d=await res.json();
    if(d.error)throw new Error(d.error);
    data=d;render(d);
    document.getElementById('mt').textContent=d.title||'Analysis Results';
    document.getElementById('ms').textContent=d.summary||'Complete';
    document.getElementById('dlBtn').disabled=false;
    document.getElementById('sr').style.display='flex';
    const ts=(d.keywords||[]).reduce((a,k)=>a+(k.synonyms||[]).length,0);
    document.getElementById('bkw').textContent=(d.keywords||[]).length;
    document.getElementById('bipc').textContent=(d.ipc||[]).length;
    document.getElementById('bcpc').textContent=(d.cpc||[]).length;
    document.getElementById('skw').textContent=(d.keywords||[]).length;
    document.getElementById('sipc').textContent=(d.ipc||[]).length;
    document.getElementById('scpc').textContent=(d.cpc||[]).length;
    document.getElementById('ssyn').textContent=ts;
    gt('kw',document.querySelector('.tab'));
    setSt('ok','Done - '+(d.keywords||[]).length+' keywords, '+(d.ipc||[]).length+' IPC, '+(d.cpc||[]).length+' CPC');
    toast('Analysis complete!','ok');
  }catch(err){
    clearInterval(iv);setSt('err','Error: '+err.message);toast('Error: '+err.message,'err');document.getElementById('emp').style.display='flex';
  }finally{document.getElementById('ldr').classList.remove('on');document.getElementById('rb').disabled=false}
}
const cm={'Core Invention':'b1','Material':'b2','Process':'b3','Application':'b4','Comparative':'b5'};
function render(d){
  document.getElementById('kwb').innerHTML=(d.keywords||[]).map((k,i)=>`<tr><td class="rn">${i+1}</td><td><strong>${h(k.term)}</strong></td><td><span class="badge ${cm[k.category]||'b1'}">${h(k.category)}</span></td><td style="max-width:220px">${h(k.definition)}</td><td><div class="syns">${(k.synonyms||[]).map(s=>`<span class="syn">${h(s)}</span>`).join('')}</div></td></tr>`).join('');
  document.getElementById('kwc').textContent=(d.keywords||[]).length+' results';
  document.getElementById('ipcb').innerHTML=(d.ipc||[]).map((c,i)=>`<tr><td class="rn">${i+1}</td><td class="code">${h(c.code)}</td><td><span class="badge bi">${h(c.section)}</span></td><td style="max-width:220px">${h(c.definition)}</td><td style="max-width:200px;color:#4A4540">${h(c.relevance)}</td></tr>`).join('');
  document.getElementById('ipcc').textContent=(d.ipc||[]).length+' results';
  document.getElementById('cpcb').innerHTML=(d.cpc||[]).map((c,i)=>`<tr><td class="rn">${i+1}</td><td class="code">${h(c.code)}</td><td><span class="badge bc">${h(c.section)}</span></td><td style="max-width:220px">${h(c.definition)}</td><td style="max-width:200px;color:#4A4540">${h(c.relevance)}</td></tr>`).join('');
  document.getElementById('cpcc').textContent=(d.cpc||[]).length+' results';
}
function dlCSV(){
  if(!data.keywords){toast('No data','err');return}
  const e=v=>'"'+String(v||'').replace(/"/g,'""')+'"';
  const rows=[['PATENT CLASSIFICATION ANALYSIS'],['Invention:',data.title||''],['Summary:',data.summary||''],[]];
  rows.push(['=== KEYWORDS ==='],['#','Keyword','Category','Definition','Syn1','Syn2','Syn3','Syn4','Syn5']);
  (data.keywords||[]).forEach((k,i)=>{const s=k.synonyms||[];rows.push([i+1,k.term,k.category,k.definition,s[0]||'',s[1]||'',s[2]||'',s[3]||'',s[4]||''])});
  rows.push([],['=== IPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.ipc||[]).forEach((c,i)=>rows.push([i+1,c.code,c.section,c.definition,c.relevance]));
  rows.push([],['=== CPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (data.cpc||[]).forEach((c,i)=>rows.push([i+1,c.code,c.section,c.definition,c.relevance]));
  const csv=rows.map(r=>r.map(e).join(',')).join('\n');
  const a=Object.assign(document.createElement('a'),{href:URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8;'})),download:'patent_classification.csv'});
  a.click();toast('CSV downloaded!','ok');
}
function h(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function setSt(s,t){document.getElementById('sd').className='sd '+s;document.getElementById('st').textContent=t}
function toast(msg,type=''){const t=document.getElementById('toast');t.textContent=msg;t.className='toast '+type+' show';setTimeout(()=>t.classList.remove('show'),4000)}
function clearAll(){data={};['kw','ipc','cpc'].forEach(t=>{const b=document.getElementById(t+'b');if(b)b.innerHTML='';document.getElementById(t+'c').textContent='-';document.getElementById('b'+t).textContent='0'});document.getElementById('txt').value='';document.getElementById('emp').style.display='flex';document.getElementById('sr').style.display='none';document.getElementById('dlBtn').disabled=true;document.getElementById('mt').textContent='Analysis Results';document.getElementById('ms').textContent='Paste invention disclosure and click Analyze';ucc();setSt('','Paste disclosure and click Analyze')}
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): print(f % a)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(HTML)))
        self._cors()
        self.end_headers()
        self.wfile.write(HTML)

    def do_POST(self):
        if self.path != "/analyze":
            self._json({"error": "not found"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            txt = json.loads(body).get("text", "").strip()
            if not txt:
                self._json({"error": "No text provided"}, 400)
                return

            print("Analyzing...")
            prompt = """Analyze this invention disclosure. Return ONLY a raw JSON object, no markdown, no explanation.

Required JSON structure:
{"title":"short title","summary":"one sentence","keywords":[{"term":"keyword","category":"Core Invention","definition":"2 sentence definition","synonyms":["s1","s2","s3","s4","s5"]}],"ipc":[{"code":"B27D 1/00","section":"short name","definition":"official definition","relevance":"relevance"}],"cpc":[{"code":"B27D 1/00","section":"short name","definition":"official definition","relevance":"relevance"}]}

Requirements:
- 20 keywords with category (Core Invention/Material/Process/Application/Comparative) and 5 synonyms each
- 50 real valid IPC codes
- 50 real valid CPC codes
- Return ONLY the JSON object, nothing else

Invention disclosure:
""" + txt[:2000]

            payload = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )

            ctx = ssl.create_default_context()
            with urlopen(req, context=ctx, timeout=55) as r:
                result = json.loads(r.read())

            raw = "".join(b.get("text", "") for b in result.get("content", [])).strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            parsed = json.loads(raw)
            print("Done! KW:%d IPC:%d CPC:%d" % (
                len(parsed.get("keywords", [])),
                len(parsed.get("ipc", [])),
                len(parsed.get("cpc", []))
            ))
            self._json(parsed)

        except HTTPError as e:
            err = e.read().decode("utf-8", "ignore")[:300]
            print("API Error %d: %s" % (e.code, err))
            self._json({"error": "API error. Please try again."}, 502)
        except json.JSONDecodeError as e:
            print("JSON error: %s" % e)
            self._json({"error": "Please try again - response was cut off."}, 500)
        except Exception as e:
            print("Error: %s" % e)
            self._json({"error": str(e)}, 500)

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
    print("PatentLens starting on port %d" % PORT)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
