#!/bin/bash
# The HTTP MCP client against a fake server on 127.0.0.1 in each of its shapes (JSON or event-stream answers, both eras, bearer, silent, absent). CANCHO is the compiler; PK the packages.
cd "$(dirname "$0")/.." || exit 2
C="${CANCHO:-cancho}"; PK="${CANCHO_PACKAGES:-../cancho/packages}"
mkdir -p build
"$C" build tests/mcp_http_check.cho src/msg.cho src/mcp.cho src/transport.cho src/mcp_http.cho vendor/fetch_io.cho "$PK"/http-client/*.cho "$PK"/tls/*.cho "$PK"/x509/*.cho --std -o build/mcp_http_check 2>&1 | grep -v "^ld:\|^warning"
[ -x build/mcp_http_check ] || { echo "could not build"; exit 2; }
fails=0
pick() { python3 -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1])"; }
for kind in modern-json modern-sse legacy-json legacy-sse auth silent badsid; do
    port=$(pick); log=build/mcp_http_$kind.log; rm -f "$log"
    MCP_LOG="$log" python3 tests/fixtures/mcp_http_server.py "$port" "$kind" & srv=$!
    for _ in $(seq 50); do python3 -c "import socket;socket.create_connection(('127.0.0.1',$port),0.1)" 2>/dev/null && break; sleep 0.1; done
    echo "== a $kind server"
    build/mcp_http_check "$port" "$kind"; fails=$((fails + $?))
    kill $srv 2>/dev/null; wait $srv 2>/dev/null
    case "$kind" in
      modern-*) grep -q "^tools/call name=add .* ver=2026-07-28 mm=tools/call" "$log" && echo "ok   the request carried Mcp-Name, Mcp-Method and the version" || { echo "FAIL the modern headers were not sent"; fails=$((fails + 1)); } ;;
      legacy-*) grep -q "^tools/call name=None sid=sess-abc123 ver=2025-11-25" "$log" && echo "ok   the request carried the session id and the version" || { echo "FAIL the session was not carried"; fails=$((fails + 1)); } ;;
    esac
done
echo "== a server that is not there"
build/mcp_http_check 1 down; fails=$((fails + $?))
[ $fails -eq 0 ] && echo "all passed" || echo "FAILED"
exit $fails
