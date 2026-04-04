import os, json, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))

HTML = b"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>PatentLens</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f5f5f5}
.header{background:#1a1a1a;color:white;padding:15px 20px;font-size:20px;font-weight:bold}
.container{display:flex;height:calc(100vh - 54px)}
.left{width:350px;background:white;padding:20px;border-right:1px solid #ddd;display:flex;flex-direction:column;gap:10px}
.right{flex:1;padding:20px;overflow:auto}
label{font-size:12px;font-weight:bold;color:#666;text-transform:uppercase}
textarea{width:100%;height:250px;padding:10px;border:1px solid #ccc;border-radius:5px;font-size:13px;resize:vertical;font-family:Arial}
#status{color:#666;font-size:13px;padding:5px 0}
button{width:100%;padding:12px;background:#2d5f3f;color:white;border:none;border-radius:5px;font-size:15px;font-weight:bold;cursor:pointer}
button:hover{background:#1a3d27}
button:disabled{background:#999;cursor:not-allowed}
.tabs{display:flex;border-bottom:2px solid #ddd;margin-bottom:15px}
.tab{padding:10px 20px;cursor:pointer;font-weight:bold;color:#666;border-bottom:3px solid transparent;margin-bottom:-2px}
.tab.active{color:#2d5f3f;border-bottom-color:#2d5f3f}
.panel{display:none}.panel.active{display:block}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f0f0f0;padding:10px;text-align:left;font-size:11px;text-transform:uppercase;color:#666;border-bottom:2px solid #ddd}
td{padding:10px;border-bottom:1px solid #eee;vertical-align:top}
tr:hover{background:#fafafa}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold}
.b1{background:#d4edda;color:#155724}
.b2{background:#fff3cd;color:#856404}
.b3{background:#d1ecf1;color:#0c5460}
.b4{background:#f8d7da;color:#721c24}
.b5{background:#e2d9f3;color:#432874}
.bi{background:#cce5ff;color:#004085}
.bc{background:#d4edda;color:#155724}
.syns{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px}
.syn{background:#eee;padding:2px 6px;border-radius:3px;font-size:11px}
.spinner{display:none;text-align:center;padding:40px;color:#666}
.spinner.on{display:block}
#dlbtn{background:#b86a08;margin-top:0}
#dlbtn:hover{background:#955508}
</style>
</head>
<body>
<div class="header">PatentLens &mdash; IP Classification Analyzer</div>
<div class="container">
<div class="left">
  <label>Invention Disclosure Text</label>
  <textarea id="txt" placeholder="Paste your invention disclosure text here..."></textarea>
  <div id="status">Ready — paste text and click Analyze</div>
  <button onclick="doAnalyze()">Analyze Invention</button>
  <button id="dlbtn" onclick="doDownload()" disabled>Download CSV</button>
</div>
<div class="right">
  <div class="tabs">
    <div class="tab active" onclick="showTab('kw',this)">Keywords (<span id="nkw">0</span>)</div>
    <div class="tab" onclick="showTab('ipc',this)">IPC Classes (<span id="nipc">0</span>)</div>
    <div class="tab" onclick="showTab('cpc',this)">CPC Classes (<span id="ncpc">0</span>)</div>
  </div>
  <div class="spinner" id="spin">Analyzing your invention disclosure...<br><br>Please wait 30-60 seconds.</div>
  <div id="empty" style="text-align:center;padding:60px;color:#999">
    <h3>No analysis yet</h3>
    <p>Paste your invention disclosure text on the left and click Analyze Invention</p>
  </div>
  <div class="panel active" id="p-kw">
    <table><thead><tr><th>#</th><th>Keyword</th><th>Category</th><th>Definition</th><th>Synonyms</th></tr></thead>
    <tbody id="kwb"></tbody></table>
  </div>
  <div class="panel" id="p-ipc">
    <table><thead><tr><th>#</th><th>IPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead>
    <tbody id="ipcb"></tbody></table>
  </div>
  <div class="panel" id="p-cpc">
    <table><thead><tr><th>#</th><th>CPC Code</th><th>Section</th><th>Definition</th><th>Relevance</th></tr></thead>
    <tbody id="cpcb"></tbody></table>
  </div>
</div>
</div>
<script>
var RES = null;

function showTab(t, el) {
  document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('active')});
  document.querySelectorAll('.panel').forEach(function(x){x.classList.remove('active')});
  el.classList.add('active');
  document.getElementById('p-'+t).classList.add('active');
}

function doAnalyze() {
  var txt = document.getElementById('txt').value;
  document.getElementById('status').textContent = 'Reading text: ' + txt.length + ' characters';
  
  if (txt.length < 5) {
    alert('Please paste your invention disclosure text first!');
    return;
  }
  
  document.getElementById('status').textContent = 'Sending to server...';
  document.getElementById('spin').classList.add('on');
  document.getElementById('empty').style.display = 'none';
  document.getElementById('kwb').innerHTML = '';
  document.getElementById('ipcb').innerHTML = '';
  document.getElementById('cpcb').innerHTML = '';

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/analyze', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.timeout = 90000;
  
  xhr.onload = function() {
    document.getElementById('spin').classList.remove('on');
    try {
      var d = JSON.parse(xhr.responseText);
      if (d.error) {
        document.getElementById('status').textContent = 'Error: ' + d.error;
        document.getElementById('empty').style.display = 'block';
        return;
      }
      RES = d;
      renderResults(d);
      document.getElementById('status').textContent = 'Done! ' + (d.keywords||[]).length + ' keywords, ' + (d.ipc||[]).length + ' IPC, ' + (d.cpc||[]).length + ' CPC';
      document.getElementById('dlbtn').disabled = false;
    } catch(e) {
      document.getElementById('status').textContent = 'Parse error. Please try again.';
      document.getElementById('empty').style.display = 'block';
    }
  };
  
  xhr.onerror = function() {
    document.getElementById('spin').classList.remove('on');
    document.getElementById('status').textContent = 'Network error. Please try again.';
    document.getElementById('empty').style.display = 'block';
  };
  
  xhr.ontimeout = function() {
    document.getElementById('spin').classList.remove('on');
    document.getElementById('status').textContent = 'Timeout. Please try again.';
    document.getElementById('empty').style.display = 'block';
  };
  
  xhr.send(JSON.stringify({text: txt}));
}

var CM = {'Core Invention':'b1','Material':'b2','Process':'b3','Application':'b4','Comparative':'b5'};

function renderResults(d) {
  var kw = d.keywords || [];
  var ipc = d.ipc || [];
  var cpc = d.cpc || [];
  
  document.getElementById('nkw').textContent = kw.length;
  document.getElementById('nipc').textContent = ipc.length;
  document.getElementById('ncpc').textContent = cpc.length;
  
  document.getElementById('kwb').innerHTML = kw.map(function(k,i) {
    var syns = (k.synonyms||[]).map(function(s){return '<span class="syn">'+s+'</span>';}).join('');
    return '<tr><td>'+(i+1)+'</td><td><b>'+k.term+'</b></td><td><span class="badge '+(CM[k.category]||'b1')+'">'+k.category+'</span></td><td>'+k.definition+'</td><td><div class="syns">'+syns+'</div></td></tr>';
  }).join('');
  
  document.getElementById('ipcb').innerHTML = ipc.map(function(c,i) {
    return '<tr><td>'+(i+1)+'</td><td><b style="color:#1B4F8A;font-family:monospace">'+c.code+'</b></td><td><span class="badge bi">'+c.section+'</span></td><td>'+c.definition+'</td><td style="color:#555">'+c.relevance+'</td></tr>';
  }).join('');
  
  document.getElementById('cpcb').innerHTML = cpc.map(function(c,i) {
    return '<tr><td>'+(i+1)+'</td><td><b style="color:#1B4F8A;font-family:monospace">'+c.code+'</b></td><td><span class="badge bc">'+c.section+'</span></td><td>'+c.definition+'</td><td style="color:#555">'+c.relevance+'</td></tr>';
  }).join('');
}

function doDownload() {
  if (!RES) return;
  var rows = [['PATENT CLASSIFICATION ANALYSIS'],['Title:',RES.title||''],['Summary:',RES.summary||''],[]];
  rows.push(['=== KEYWORDS ==='],['#','Keyword','Category','Definition','Syn1','Syn2','Syn3','Syn4','Syn5']);
  (RES.keywords||[]).forEach(function(k,i){
    var s=k.synonyms||[];
    rows.push([i+1,k.term,k.category,k.definition,s[0]||'',s[1]||'',s[2]||'',s[3]||'',s[4]||'']);
  });
  rows.push([],['=== IPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (RES.ipc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  rows.push([],['=== CPC CODES ==='],['#','Code','Section','Definition','Relevance']);
  (RES.cpc||[]).forEach(function(c,i){rows.push([i+1,c.code,c.section,c.definition,c.relevance]);});
  var csv = rows.map(function(r){return r.map(function(v){return '"'+String(v||'').replace(/"/g,'""')+'"';}).join(',');}).join('\n');
  var a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURIComponent(csv);
  a.download = 'patent_classification.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
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
            print("Analyzing %d chars" % len(txt))
            prompt = """Analyze this invention disclosure. Return ONLY a raw JSON object starting with { and ending with }. No markdown, no explanation.

JSON structure:
{"title":"short title","summary":"one sentence","keywords":[{"term":"","category":"Core Invention","definition":"","synonyms":["","","","",""]}],"ipc":[{"code":"","section":"","definition":"","relevance":""}],"cpc":[{"code":"","section":"","definition":"","relevance":""}]}

Rules:
- 20 keywords, categories must be one of: Core Invention, Material, Process, Application, Comparative
- 5 synonyms per keyword
- 50 real IPC codes
- 50 real CPC codes
- Start response with { immediately

Invention:
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
            s = raw.find("{")
            e = raw.rfind("}") + 1
            if s >= 0 and e > s:
                raw = raw[s:e]
            parsed = json.loads(raw)
            print("OK KW:%d IPC:%d CPC:%d" % (len(parsed.get("keywords",[])), len(parsed.get("ipc",[])), len(parsed.get("cpc",[]))))
            self._json(parsed)

        except HTTPError as e:
            msg = e.read().decode("utf-8","ignore")[:200]
            print("HTTPError %d: %s" % (e.code, msg))
            self._json({"error": "API error. Try again."}, 502)
        except json.JSONDecodeError as ex:
            print("JSONError: %s" % ex)
            self._json({"error": "Try again - response incomplete."}, 500)
        except Exception as ex:
            print("Error: %s" % ex)
            self._json({"error": str(ex)}, 500)

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
    print("PatentLens on port %d" % PORT)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
