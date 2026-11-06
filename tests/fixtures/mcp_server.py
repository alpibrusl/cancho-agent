#!/usr/bin/env python3
# A fake MCP server over stdio, for tests only: written from the shapes of the specification as read (modern 2026-07-28, legacy 2025-11-25), not from a real server.
#   mcp_server.py modern|legacy|silent|crash
import json, sys
mode = sys.argv[1] if len(sys.argv) > 1 else "modern"
if mode == "crash":
    sys.stderr.write("crashing on purpose\n"); sys.exit(3)
if mode == "silent":
    sys.stdin.read(); sys.exit(0)
TOOLS1 = [{"name": "add", "title": "Add", "description": "Add two integers", "annotations": {"readOnlyHint": True}, "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}}]
TOOLS2 = [{"name": "echo", "description": "Say it back", "annotations": {"readOnlyHint": True}, "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}, {"name": "fail", "description": "Always fails", "inputSchema": {"type": "object", "additionalProperties": False}}, {"name": "write_thing", "description": "Changes something", "annotations": {"readOnlyHint": False}, "inputSchema": {"type": "object"}}]
def out(o): sys.stdout.write(json.dumps(o, separators=(",", ":")) + "\n"); sys.stdout.flush()
def err(i, code, message): out({"jsonrpc": "2.0", "id": i, "error": {"code": code, "message": message}})
initialized = False
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try: m = json.loads(line)
    except Exception: continue
    method = m.get("method"); i = m.get("id"); params = m.get("params") or {}
    sys.stderr.write("got %s\n" % method)
    if i is None: 
        if method == "notifications/initialized": initialized = True
        continue
    out({"jsonrpc": "2.0", "method": "notifications/message", "params": {"level": "info", "data": "hello"}})
    meta = params.get("_meta") or {}
    if mode == "modern":
        if method == "server/discover":
            out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "supportedVersions": ["2026-07-28"], "capabilities": {"tools": {}}, "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "fake", "version": "1"}}}}); continue
        if meta.get("io.modelcontextprotocol/protocolVersion") != "2026-07-28" or "io.modelcontextprotocol/clientCapabilities" not in meta:
            err(i, -32602, "missing protocol version or capabilities in _meta"); continue
    else:
        if method == "initialize":
            out({"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}, "serverInfo": {"name": "fake", "version": "1"}}}); continue
        if method == "server/discover": err(i, -32601, "Method not found"); continue
        if not initialized: err(i, -32002, "not initialized"); continue
    if method == "tools/list":
        if params.get("cursor") == "p2": out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "tools": TOOLS2}})
        else: out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "tools": TOOLS1, "nextCursor": "p2"}})
    elif method == "tools/call":
        name = params.get("name"); a = params.get("arguments") or {}
        if name == "add": out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "content": [{"type": "text", "text": str(a.get("a", 0) + a.get("b", 0))}], "isError": False}})
        elif name == "echo": out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "content": [{"type": "text", "text": a.get("text", "")}]}})
        elif name == "write_thing": out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "content": [{"type": "text", "text": "changed"}]}})
        elif name == "fail": out({"jsonrpc": "2.0", "id": i, "result": {"resultType": "complete", "content": [{"type": "text", "text": "it always fails"}], "isError": True}})
        else: err(i, -32602, "Unknown tool: %s" % name)
    else: err(i, -32601, "Method not found")
