#!/bin/bash
# The stdio MCP client against a fake server in each of its eras, and against one that says nothing and one that crashes. CANCHO is the compiler. python3 runs the fake server.
cd "$(dirname "$0")/.." || exit 2
C="${CANCHO:-cancho}"
mkdir -p build
"$C" build tests/mcp_check.cho src/msg.cho src/mcp.cho src/shell.cho src/mcp_stdio.cho --std -o build/mcp_check 2>&1 | grep -v "^ld:\|^warning"
[ -x build/mcp_check ] || { echo "could not build"; exit 2; }
fails=0
for kind in modern legacy silent crash; do
    echo "== a $kind server"
    build/mcp_check "python3 tests/fixtures/mcp_server.py $kind" "$kind"; fails=$((fails + $?))
done
[ $fails -eq 0 ] && echo "all passed" || echo "FAILED"
exit $fails
