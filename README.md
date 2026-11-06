# cancho-agent

A provider-neutral agent library for [cancho](../cancho): a conversation and tool model, adapters for the model APIs, and the decisions of the agent loop, all pure and tested without a model. Private, built first for `cancho-ota` (the group-trip service), and meant to be reused (`cancho-code` has its own copy of the transport it was taken from).

* `src/msg.cho` — the neutral conversation: a JSON array of `system`, `user`, `assistant` (with `calls`) and `tool` messages, kept as text so it can be stored and replayed; tool definitions; the helpers adapters share.
* `src/openai.cho` — OpenAI-compatible chat completions (llama.cpp's server, Ollama, vLLM, Mistral): a request from a conversation and tools, an answer read back.
* `src/anthropic.cho` — the Anthropic Messages API (system at the top, a turn's tool results together, `tool_use` blocks).
* `src/mock.cho` — a scripted model for tests (one assistant message per line, no network), `model.k_mock`.
* `src/agent.cho` — what the loop decides after each answer: done, run the tools, too many steps, out of tokens, cut off.
* `src/transport.cho` — one HTTP POST over TLS or plain TCP (from cancho-code's `provider`), for the caller to carry a request.
* `bin/live.cho`, `bin/live_tools.cho` — a question, and a tool round trip, against a real model (`scripts/live.sh`, opt-in, not in the normal tests).

`scripts/test.sh` runs the tests. Design and what is not built: `docs/design.md`.
