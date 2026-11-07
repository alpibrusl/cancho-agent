#!/usr/bin/env python3
# A fake MCP server over HTTP, for tests only: written from the Streamable HTTP transport as read on 2026-11-07 (modern 2026-07-28 and legacy 2025-11-25), not from a real server.
#   mcp_http_server.py <port> modern-json|modern-sse|legacy-json|legacy-sse|auth|silent
# It checks what the spec says a client must send and answers 400 when it is wrong; MCP_LOG (a file) gets one line per request: method, the Mcp-Name and session headers.
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer as HTTPServer
port = int(sys.argv[1]); mode = sys.argv[2]
modern = mode.startswith("modern") or mode == "auth"
sse = mode.endswith("sse") or mode == "auth"
SID = "bad id" if mode == "badsid" else "sess-abc123"
TOOLS1 = [{"name": "add", "description": "Add two integers", "annotations": {"readOnlyHint": True}, "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}}]
TOOLS2 = [{"name": "echo", "description": "Say it back", "annotations": {"readOnlyHint": True}, "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}, {"name": "fail", "description": "Always fails", "inputSchema": {"type": "object"}}, {"name": "write_thing", "description": "Changes something", "annotations": {"readOnlyHint": False}, "inputSchema": {"type": "object"}}]
live_sessions = set(); started = set()
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def reply(self, status, body=b"", ctype="application/json", headers=()):
        self.send_response(status); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        for k, v in headers: self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)
    def rpc(self, i, result=None, error=None):
        o = {"jsonrpc": "2.0", "id": i}
        if error: o["error"] = error
        else: o["result"] = result
        return o
    def answer(self, o, headers=()):
        if not sse:
            # a pretty-printed body on purpose: a client must not depend on one line
            return self.reply(200, json.dumps(o, indent=2).encode(), "application/json", headers)
        ev = b"id: 0\r\ndata:\r\n\r\n" + b"event: message\r\nid: 1\r\ndata: " + json.dumps({"jsonrpc": "2.0", "method": "notifications/message", "params": {"level": "info", "data": "hello"}}).encode() + b"\r\n\r\n" + b"event: message\r\nid: 2\r\ndata: " + json.dumps(o).encode() + b"\r\n\r\n"
        self.reply(200, ev, "text/event-stream", headers)
    def do_GET(self): self.reply(405)
    def do_DELETE(self): self.reply(405)
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path != "/mcp": return self.reply(404)
        if mode == "silent": return self.reply(200, b"")
        if mode == "auth" and self.headers.get("Authorization") != "Bearer tok": return self.reply(401, b'{"error":"no"}')
        acc = self.headers.get("Accept", "")
        if "application/json" not in acc or "text/event-stream" not in acc: return self.reply(400, b"Accept must list both")
        try: m = json.loads(raw)
        except Exception: return self.reply(400, b"not json")
        method = m.get("method"); i = m.get("id"); params = m.get("params") or {}
        ver = self.headers.get("MCP-Protocol-Version"); sid = self.headers.get("Mcp-Session-Id")
        name = self.headers.get("Mcp-Name")
        if os.environ.get("MCP_LOG"):
            open(os.environ["MCP_LOG"], "a").write("%s name=%s sid=%s ver=%s mm=%s\n" % (method, name, sid, ver, self.headers.get("Mcp-Method")))
        if modern:
            meta = params.get("_meta") or {}
            if ver != "2026-07-28" or meta.get("io.modelcontextprotocol/protocolVersion") != ver: return self.reply(400, json.dumps(self.rpc(i, error={"code": -32020, "message": "HeaderMismatch"})).encode())
            if self.headers.get("Mcp-Method") != method: return self.reply(400, json.dumps(self.rpc(i, error={"code": -32020, "message": "HeaderMismatch"})).encode())
            if method == "tools/call" and name != params.get("name"): return self.reply(400, json.dumps(self.rpc(i, error={"code": -32020, "message": "HeaderMismatch"})).encode())
            if method == "server/discover": return self.answer(self.rpc(i, {"supportedVersions": ["2026-07-28"], "capabilities": {"tools": {}}}))
        else:
            if method == "initialize":
                live_sessions.add(SID)
                return self.answer(self.rpc(i, {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}, "serverInfo": {"name": "fake", "version": "1"}}), [("Mcp-Session-Id", SID)])
            if method == "server/discover":
                if mode == "legacy-sse": return self.reply(400, b"")
                return self.answer(self.rpc(i, error={"code": -32601, "message": "Method not found"}))
            if sid not in live_sessions: return self.reply(404 if sid else 400, b"")
            if ver != "2025-11-25": return self.reply(400, b"bad version")
            if method == "notifications/initialized": started.add(sid); return self.reply(202)
            if sid not in started: return self.answer(self.rpc(i, error={"code": -32002, "message": "not initialized"}))
        if i is None: return self.reply(202)
        if method == "tools/list":
            if params.get("cursor") == "p2": return self.answer(self.rpc(i, {"resultType": "complete", "tools": TOOLS2}))
            return self.answer(self.rpc(i, {"resultType": "complete", "tools": TOOLS1, "nextCursor": "p2"}))
        if method == "tools/call":
            n = params.get("name"); a = params.get("arguments") or {}
            def text(t, err=False): return self.answer(self.rpc(i, {"resultType": "complete", "content": [{"type": "text", "text": t}], "isError": err}))
            if n == "add": return text(str(a.get("a", 0) + a.get("b", 0)))
            if n == "echo": return text(a.get("text", ""))
            if n == "fail": return text("it always fails", True)
            return self.answer(self.rpc(i, error={"code": -32602, "message": "Unknown tool: %s" % n}))
        return self.answer(self.rpc(i, error={"code": -32601, "message": "Method not found"}))
HTTPServer(("127.0.0.1", port), H).serve_forever()
