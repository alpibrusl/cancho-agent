#!/bin/sh
# Run every test: `scripts/test.sh`. CANCHO overrides the compiler path. The live checks (a real model, your key) are separate: scripts/live.sh.
cd "$(dirname "$0")/.." || exit 2
C="${CANCHO:-cancho}"
status=0
for t in tests/*_test.cho; do
    out=$("$C" test "$t" src/msg.cho src/openai.cho src/anthropic.cho src/agent.cho src/policy.cho src/mock.cho --std 2>&1 | grep -v "^ld:")
    echo "$out" | tail -1 | sed "s|^|$t: |"
    echo "$out" | grep -q "test result: ok" || { echo "$out"; status=1; }
done
exit $status
