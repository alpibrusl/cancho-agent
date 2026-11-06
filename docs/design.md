# cancho-agent design

## 1. What it is for
An agent in a backend (cancho-ota's assistant first) needs four things that are not about any one product: talk to a model whatever its API, let it use tools, keep the loop bounded, and speak the standard agent protocols. This library is those, and nothing about trips.

## 2. The neutral conversation (`msg`)
A conversation is JSON text: `[{"role":"system","text":..},{"role":"user","text":..},{"role":"assistant","text":..,"calls":[{"id","name","args"}]},{"role":"tool","id","name","text"}]`. The arguments of a call and the schema of a tool are **JSON kept as a string**: the providers disagree on how to write them (OpenAI wants a string, Anthropic an object), and the library's JSON tape has no byte range for an object, so a string is the one form every adapter can read and write exactly. Tool results are data: they are never put in a system or user message.

## 3. Adapters and the loop
`openai.request/reply` and `anthropic.request/reply` are pure: a body out, a body in. `reply` gives (ok, an assistant message, why it stopped, tokens in, tokens out), so a refusal, an error body or garbage is `ok = false`, never a crash. The loop is the caller's (it is I/O), `agent.decide` says what to do after each answer: a spent token budget stops everything, a cut-off answer is not an answer, tools are run only if a step is left to use their results.

## 4. Transport and policy
`transport` is native HTTPS (cancho's `http-client` and `tls`), taken from cancho-code. It takes the host and the address as arguments: resolving, and which hosts are allowed, is the caller's policy (an agent that must make no external call refuses any address that is not private). Keys are read by the caller and live only in a header line.

## 5. Checked
Pure tests by hand-written expected JSON for every adapter case (a conversation with a tool turn, several tool results in one turn, a nested argument that must be written out again, a cut answer, an error body, garbage) and for every decision. **Live**, opt-in: Claude Haiku 5.5 and Mistral Small each answered a question and ran a tool (an `add` tool the model called in step 1 and used in its step 2 answer).

## 6. Not built yet
* **Protocols.** MCP client (use any MCP server's tools), A2A (an agent card, tasks over JSON-RPC and server-sent events), AG-UI (the event stream a front end reads from an agent) and A2UI (declarative UI messages an agent sends). They are JSON over HTTP, so they fit this library as modules beside the adapters; none is written, and none will be written from memory: each needs its current specification read first.
* A server-sent events reader (streaming answers), a streaming reply parser, retries with backoff in the loop, a host policy module, and a tool table helper (name to function).
