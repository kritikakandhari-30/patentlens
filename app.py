import os, json, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))
MODEL = "claude-sonnet-4-20250514"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): print(f % a)
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()
    def do_GET(self):
        with open("index.html", "rb") as f: body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors(); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        if self.path != "/analyze":
            self._json({"error":"not found"},404); return
        try:
            n = int(self.headers.get("Content-Length",0))
            txt = json.loads(self.rfile.read(n)).get("text","").strip()
            if not txt: self._json({"error":"no text"},400); return
            p = json.dumps({"model":MODEL,"max_tokens":8000,"messages":[{"role":"user","content":"Analyze this invention and return ONLY valid JSON with keys: title, summary, keywords(term,category,definition,synonyms[5]), ipc(code,section,definition,relevance), cpc(code,section,definition,relevance). Min 20 keywords, 75 IPC, 75 CPC codes.\n\n"+txt}]}).encode()
            req = Request("https://api.anthropic.com/v1/messages",data=p,headers={"Content-Type":"application/json","x-api-key":API_KEY,"anthropic-version":"2023-06-01"},method="POST")
            with urlopen(req,context=ssl.create_default_context(),timeout=120) as r:
                res = json.loads(r.read())
            raw = "".join(b.get("text","") for b in res.get("content",[])).strip()
            if raw.startswith("```"): raw=raw.split("\n",1)[-1]
            if raw.endswith("```"): raw=raw.rsplit("```",1)[0]
            self._json(json.loads(raw.strip()))
        except HTTPError as e: self._json({"error":str(e)},502)
        except Exception as e: self._json({"error":str(e)},500)
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
    print(f"Starting on port {PORT}")
    HTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
