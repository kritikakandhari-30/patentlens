import os, json, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))

PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PatentLens</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#F4F1EB;color:#1C1915;font-size:14px}
.hdr{background:#1C1915;display:flex;align-items:center;justify-content:space-between;padding:0 1.5rem;height:56px}
.hn{font-size:17px;color:#fff;font-weight:600}
.hb{padding:7px 14px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;border:none;background:#B86A08;color:#fff}
.hb:disabled{opacity:.4;cursor:not-allowed}
.wrap{display:flex;height:calc(100vh - 56px)}
.left{width:320px;background:#FDFBF8;border-right:1px solid #e0ddd6;display:flex;flex-direction:column;padding:1.5rem;gap:12px}
.lbl{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#8A837A}
.ta{width:100%;height:200px;padding:10px 12px;border:1.5px solid #d0cdc6;border-radius:8px;font-family:system-ui;font-size:13px;resize:vertical;background:#F4F1EB;color:#1C1915;line-height:1.5}
.ta:focus{outline:none;border-color:#2D5F3F}
.info{font-size:12px;color:#8A837A;min-height:18px}
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
.body{flex:1;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
thead{position:sticky;top:0}
th{padding:10px 16px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#8A837A;background:#EEEAE0;border-bottom:1px solid #d0cdc6;white-space:nowrap}
td{padding:12px 16px;border-bottom:1px solid #f0ede6;vertical-align:top;line-height:1.5}
tr:hover td{background:#f5f2eb}
.rn{font-family:monospace;font-size:11px;color:#aaa;width:36px;text-align:center}
.cd{font-family:monospace;font-size:12px;font-weight:700;color:#1B4F8A;white-space:nowrap}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;white-space:nowrap}
.b1{background:#F0FDF4;color:#14532D}.b2{background:#FEF3E2;color:#78350F}.b3{background:#E6F2EC;color:#1A3D27}.b4{background:#FEE2E2;color:#991B1B}.b5{background:#EDE9FE;color:#4C1D95}.bi{background:#E8F0FB;color:#1B4F8A}.bc{background:#ECFDF5;color:#065F46}
.syns{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.syn{background:#eee;color:#555;font-size:11px;padding:2px 7px;border-radius:5px}
.panel{display:none;flex-direction:column;flex:1;overflow:hidden}
.panel.on{display:flex}
.empty{flex:1;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:#8A837A;text-align:center}
.spinner{display:none;flex:1;align-items:center;justify-content:center;flex-direction:column;gap:12px}
.spinner.on{display:flex}
.spin{width:36px;height:36px;border:3px solid #e0ddd6;border-top-color:#2D5F3F;border-radius:50%;animation:s .8s linear infinite}
@keyframes s{to{transform:rotate(360deg)}}
.pf{padding:8px 1.5rem;border-top:1px solid #e0ddd6;background:#FDFBF8;font-size:12px;color:#8A837A}
.msg{position:fixed;bottom:20px;right:20px;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:500;color:#fff;transform:translateY(60px);opacity:0;transition:all .3s;z-index:999}
.msg.show{transform:translateY(0);opacity:1}
.msg.ok{background:#2D5F3F}
.msg.err{background:#DC2626}
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
    <textarea id="txt" class="ta" placeholder="Paste your invention disclosure text here..."></textarea>
    <div class="info" id="info">Paste text above then click Analyze</div>
    <button class="abtn" id="abtn" onclick="run()">Analyze Invention</button>
  </div>
  <div class="right">
    <div class="rh">
      <div class="rt" id="rt">Analysis Results</div>
      <div class="rs" id="rs">Paste your invention disclosure and click Analyze</div>
    </div>
    <div class="tabs">
      <div class="tab on" id="tab-kw" onclick="sw('kw')">Keywords <span class="tbg" id="bkw">0</span></div>
      <div class="tab" id="tab-ipc" onclick="sw('ipc')">IPC Classes <span class="tbg" id="bipc">0</span></div>
      <div class="tab" id="tab-cpc" onclick="sw('cpc')">CPC Classes <span class="tbg" id="bcpc">0</span></div>
    </div>
    <div class="spinner" id="spin">
      <div class="spin"></div>
      <div id="smt" style="font-size:14px;font-weight:500">Analyzing...</div>
      <div style="font-size:12px;color:#8A837A">Please wait 30-60 seconds</div>
    </div>
    <div class="empty" id="emp">
      <div style="font-size:16px;font-weight:600">No analysis yet</div>
      <div style="font-size:13px">Paste disclosure text and click Analyze Invention</div>
    </div>
    <div class="panel" id="p-kw">
      <div class="body"><table><thead><tr><th class="rn">#</th><th>Keyword</th><th>Category</th><th>Definition</th><th>Synonyms</th></tr></thead><tbody id="kwb"></tbody></table></div>
      <div class="pf" id="kwc"></div>
    </div>
    <div class="panel" id="p-ipc">
      <div class="body"><table><thead><tr><th class="rn">#</th><th>IPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="ipcb"></tbody></table></div>
      <div class="pf" id="ipcc"></div>
    </div>
    <div class="panel" id="p-cpc">
      <div class="body"><table><thead><tr><th class="rn">#</th><th>CPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead><tbody id="cpcb"></tbody></table></div>
      <div class="pf" id="cpcc"></div>
    </div>
  </div>
</div>
<div class="msg" id="msg"></div>

<script>
var D = {};

function sw(t) {
  ['kw','ipc','cpc'].forEach(function(x) {
    document.getElementById('tab-'+x).classList.toggle('on', x===t);
    document.getElementById('p-'+x).classList.toggle('on', x===t);
  });
}

function getTxt() {
  var el = document.getElementById('txt');
  // Try multiple ways to get the text
  var v = '';
  try { v = el.value; } catch(e) {}
  if (!v) try { v = el.textContent; } catch(e) {}
  if (!v) try { v = el.innerHTML; } catch(e) {}
  return (v || '').replace(/<[^>]*>/g, '').trim();
}

function run() {
  var txt = getTxt();
  document.getElementById('info').textContent = 'Characters detected: ' + txt.length;
  
  if (txt.length < 10) {
    showMsg('No text detected. Please click in the box, select all with Cmd+A, copy and paste again.', 'err');
    return;
  }
  
  document.getElementById('spin').classList.add('on');
  document.getElementById('emp').style.display = 'none';
  document.getElementById('abtn').disabled = true;
  document.getElementById('info').textContent = 'Sending ' + txt.length + ' characters to server...';
  
  var msgs = ['Analyzing invention...','Mapping IPC classes...','Finding CPC codes...','Building report...'];
  var mi = 0;
  var iv = setInterval(function() {
    document.getElementById('smt').textContent = msgs[++mi % msgs.length];
  }, 3000);
  
  fetch('/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: txt})
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    clearInterval(iv);
    if (d.error) throw new Error(d.error);
    D = d;
    render(d);
    document.getElementById('rt').textContent = d.title || 'Analysis Results';
    document.getElementById('rs').textContent = d.summary || 'Complete';
    document.getElementById('dlBtn').disabled = false;
    document.getElementById('bkw').textContent = (d.keywords||[]).length;
    document.getElementById('bipc').textContent = (d.ipc||[]).length;
    document.getElementById('bcpc').textContent = (d.cpc||[]).length;
    sw('kw');
    document.getElementById('info').textContent = 'Done! ' + (d.keywords||[]).length + ' keywords, ' + (d.ipc||[]).length + ' IPC, ' + (d.cpc||[]).length + ' CPC';
    showMsg('Analysis complete!', 'ok');
  })
  .catch(function(err) {
    clearInterval(iv);
    document.getElementById('emp').style.display = 'flex';
    document.getElementById('info').textContent = 'Error: ' + err.message;
    showMsg('Error: ' + err.message, 'err');
  })
  .finally(function() {
    document.getElementById('spin').classList.remove('on');
    document.getElementById('abtn').disabled = false;
  });
}

var CM = {'Core Invention':'b1','Material':'b2','Process':'b3','Application':'b4','Comparative':'b5'};

function render(d) {
  document.getElementById('kwb').innerHTML = (d.keywords||[]).map(function(k,i) {
    return '<tr><td class="rn">'+(i+1)+'</td><td><strong>'+h(k.term)+'</strong></td><td><span class="badge '+(CM[k.category]||'b1')+'">'+h(k.category)+'</span></td><td style="max-width:220px">'+h(k.definition)+'</td><td><div class="syns">'+(k.synonyms||[]).map(function(s){return '<span class="syn">'+h(s)+'</span>';}).join('')+'</div></td></tr>';
  }).join('');
  document.getElementById('kwc').textContent = (d.keywords||[]).length + ' keywords';
  
  document.getElementById('ipcb').innerHTML = (d.ipc||[]).map(function(c,i) {
    return '<tr><td class="rn">'+(i+1)+'</td><td class="cd">'+h(c.code)+'</td><td><span class="badge bi">'+h(c.section)+'</span></td><td style="max-width:220px">'+h(c.definition)+'</td><td style="max-width:200px;color:#555">'+h(c.relevance)+'</td></tr>';
  }).join('');
  document.getElementById('ipcc').textContent = (d.ipc||[]).length + ' IPC codes';
  
  document.getElementById('cpcb').innerHTML = (d.cpc||[]).map(function(c,i) {
    return '<tr><td class="rn">'+(i+1)+'</td><td class="cd">'+h(c.code)+'</td><td><span class="badge bc">'+h(c.section)+'</span></td><td style="max-width:220px">'+h(c.definition)+'</td><td style="max-width:200px;color:#555">'+h(c.relevance)+'</td></tr>';
  }).join('');
  document.getElementById('cpcc').textContent = (d.cpc||[]).length + ' CPC codes';
}

function dlCSV() {
  if (!D.keywords) return;
  var e = function(v) { return '"' + String(v||'').replace(/"/g,'""') + '"'; };
  var rows = [['PATENT CLASSIFICATION ANALYSIS'],['Invention:',D.title||''],['Summary:',D.summary||'],[]];\n  rows.push(['=== KEYWORDS ==='],['#','Keyword','Category','Definition','Syn1','Syn2','Syn3','Syn4','Syn5']);
  (D.keywords||[]).forEach(function(k,i){var s=k.synonyms||[];rows.push([i+1,k.term,k.category,k.definition,s[0]||'',s[1]||'',s[2]||'',s[3]||'',s[4]||'']);});
  rows.push([],['=== IPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (D.ipc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  rows.push([],['=== CPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (D.cpc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  var csv = rows.map(function(r){return r.map(e).join(',');}).join('\\n');
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8;'}));
  a.download = 'patent_classification.csv';
  a.click();
  showMsg('CSV downloaded!', 'ok');
}

function h(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function showMsg(m, t) { var el=document.getElementById('msg'); el.textContent=m; el.className='msg '+(t||'')+' show'; setTimeout(function(){el.classList.remove('show');},4000); }
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a):
        print(f % a)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        body = PAGE.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/analyze":
            self._json({"error": "not found"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            data = json.loads(body)
            txt = data.get("text", "").strip()
            if not txt:
                self._json({"error": "No text received. Please paste your invention disclosure."}, 400)
                return

            print("Received %d characters" % len(txt))

            prompt = """You are a patent classification expert. Analyze this invention disclosure carefully.

Return ONLY a valid JSON object. Start with { and end with }. No markdown, no explanation, no text before or after the JSON.

JSON structure:
{
  "title": "concise invention title",
  "summary": "one sentence technical summary",
  "keywords": [
    {"term": "keyword", "category": "Core Invention", "definition": "2 sentence definition", "synonyms": ["s1","s2","s3","s4","s5"]}
  ],
  "ipc": [
    {"code": "B27D 1/00", "section": "Plywood manufacture", "definition": "official definition", "relevance": "relevance to invention"}
  ],
  "cpc": [
    {"code": "B27D 1/00", "section": "Plywood manufacture", "definition": "official definition", "relevance": "relevance to invention"}
  ]
}

Requirements:
- 20 keywords with categories: Core Invention, Material, Process, Application, or Comparative
- Each keyword needs 5 synonyms
- 50 real valid IPC classification codes
- 50 real valid CPC classification codes

Invention disclosure text:
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
            
            # Extract JSON from response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]

            parsed = json.loads(raw)
            kw = len(parsed.get("keywords", []))
            ipc = len(parsed.get("ipc", []))
            cpc = len(parsed.get("cpc", []))
            print("Success! KW:%d IPC:%d CPC:%d" % (kw, ipc, cpc))
            self._json(parsed)

        except HTTPError as e:
            err = e.read().decode("utf-8", "ignore")[:200]
            print("API Error %d: %s" % (e.code, err))
            self._json({"error": "API error. Please try again."}, 502)
        except json.JSONDecodeError as e:
            print("JSON parse error: %s" % e)
            self._json({"error": "Response parsing failed. Please try again."}, 500)
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
