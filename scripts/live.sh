#!/bin/sh
# Opt-in live check: one question and one tool round trip against a real model. NOT part of scripts/test.sh and never run in CI: it spends tokens and calls a hosted API.
#   scripts/live.sh anthropic <key-file> [model]      scripts/live.sh mistral <key-file> [model]      ROOTS=/etc/ssl/cert.pem
cd "$(dirname "$0")/.." || exit 2
C="${CANCHO:-cancho}"; PK="${CANCHO_PACKAGES:-../cancho/packages}"; ROOTS="${ROOTS:-/etc/ssl/cert.pem}"
kind="$1"; key="$2"
case "$kind" in
  anthropic) host=api.anthropic.com; model="${3:-claude-haiku-5-5}";;
  mistral) host=api.mistral.ai; model="${3:-mistral-small-latest}";;
  *) echo "usage: live.sh anthropic|mistral <key-file> [model]"; exit 2;;
esac
ip=$(python3 -c "import socket,sys;print(socket.gethostbyname(sys.argv[1]))" "$host") || exit 2
mkdir -p build
for b in live live_tools; do
  "$C" build "bin/$b.cho" src/msg.cho src/openai.cho src/anthropic.cho src/agent.cho src/transport.cho vendor/fetch_io.cho "$PK"/http-client/*.cho "$PK"/tls/*.cho "$PK"/x509/*.cho --std -o "build/$b" 2>&1 | grep -v "^ld:"
done
build/live "$kind" "$key" "$ROOTS" "$host" "$ip" "$model" "What is the capital of Portugal?" || exit 1
build/live_tools "$kind" "$key" "$ROOTS" "$host" "$ip" "$model" "What is 1234 plus 4321? Use the tool." || exit 1
