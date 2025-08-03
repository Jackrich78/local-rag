Product Requirement Document — Phase 3.2 Open WebUI Integration & Chat Memory
Revision date: 2025-08-03

1 Summary / Introduction
Expose the existing agentic RAG backend through Open WebUI so developers and non-technical users can chat in the browser with full session memory stored in Supabase. Eliminate the unused Kong proxy and keep Supabase Studio for DB introspection. No login/SSO required.

2 Goals & Success Metrics
Goal	Metric	Target
Browser chat works out-of-the-box	“agent-model” selectable in WebUI & returns answers	100 % of fresh installs
Session memory persists	Messages retrieved after page refresh	≥ 10 turns survive reload
Remove Kong complexity	Kong container absent & Caddy routes deleted	0 Kong services
Streaming response latency	Time to first token on “ping”	≤ 1 s
Zero extra configuration	Steps after make up	0

3 Scope
In Scope (must-haves)
Open WebUI → Agent wiring

WebUI environment: OPENAI_API_HOST=http://agent:8058, OPENAI_API_KEY=dev-local.

Agent exposes OpenAI-compatible endpoints:

GET /v1/models

POST /v1/chat/completions (SSE stream).

Supabase-backed memory

Use existing sessions and messages tables.

On each user/assistant turn the agent upserts both tables.

Streaming protocol

Server-Sent Events (data: {json}\n\n) identical to OpenAI API.

Docker changes

Delete Kong service & related Caddy host rule.

Keep Caddy for hostname multiplexing; ensure routes:

localhost:8002 → open-webui:8080

localhost:8009 → agent:8058

localhost:8005 → supabase-studio:3000

Stub model list

/v1/models returns {"data":[{"id":"agent-model","object":"model"}]}.

Automated tests (see §9).

Out of Scope (non-goals)
User authentication (SSO, JWT).

Multiple model orchestration or remote Ollama.

UI theming or brand customisation.

4 User Personas & Use Cases
Persona	Use Case
Developer	Runs make up, opens localhost:8002, chats with agent, refreshes page, conversation persists.
Analyst	Pastes product docs into WebUI, receives citations, later revisits entire thread.
DB Admin	Opens Supabase Studio at localhost:8005 to inspect messages table.

5 Functional Requirements
As a user of WebUI, I see a model named “agent-model” immediately after page load.

As a user, when I send a message, WebUI streams tokens in ≤ 1 s and shows final answer with citations.

As a user, when I reload the page, my previous messages and the agent’s replies re-appear.

As a developer, docker compose ps | grep kong returns empty.

6 Edge Cases & Error Handling
Scenario	Handling
Agent returns 500	WebUI shows banner “Agent unavailable (500)” and disables send button.
Supabase down	Agent returns 503 with JSON {"error":"supabase-unavailable"}; WebUI shows toast, still streams but without memory.
/v1/models empty	WebUI falls back to “No model available” screen.
Streaming interrupt	WebUI reconnects once; if second failure, shows truncated answer with notice.

7 Non-Functional Requirements
Performance: first SSE chunk ≤ 1 s; full answer ≤ 5 s for 100-token reply.

Security: secrets only via Docker secrets; no tokens in container env.

Compliance: no personal data stored; Supabase tables contain only chat text.

8 Technical Design & Constraints
Item	Specification
Language	Python 3.11 in agent container
Framework	FastAPI + Uvicorn
Streaming	Server-Sent Events (text/event-stream)
Compose network	Internal service names (agent:8058, open-webui:8080)
Database	Supabase (PostgreSQL 15) for sessions & messages
Graph	Neo4j Bolt remains on bolt://neo4j:7687
Front-end	Use upstream open-webui Docker image ghcr.io/open-webui/open-webui:main
Reverse proxy	Caddy 2-alpine; Kong removed

9 Testing & Acceptance Criteria
Automated (CI) – Given/When/Then
ID	Scenario	Given	When	Then
T1	Model discovery	WebUI service healthy	WebUI calls GET /v1/models	Response JSON includes agent-model
T2	First token latency	Agent and WebUI running	Post "ping" to /v1/chat/completions?stream=true	First data: line arrives < 1 s
T3	Session persistence	Row count sessions=0	Send two messages via API	sessions = 1 and messages = 2
T4	No Kong container	Stack running	List services	kong absent
T5	Health route	All services up	curl localhost:8009/healthz	200 OK, body {"status":"ok"}

Manual Validation Steps
make up

Visit http://localhost:8002 – choose agent-model.

Ask “2 + 2”; expect stream, final answer “4”.

Refresh page → history visible.

Open http://localhost:8005 (Supabase Studio) → verify messages table row count ≥ 2.

Run docker compose exec neo4j cypher-shell -u neo4j -p $NEO4J_PWD "MATCH (n) RETURN count(n)" – count > 0.

10 Risks & Mitigations
Risk	Mitigation
WebUI changes its expected OpenAI schema	Pin image tag ghcr.io/open-webui/open-webui:v0.2.13 and upgrade only with tests.
Supabase latency slows chat	Cache last 10 messages in memory; async write-behind.
SSE buffering via Caddy	Enable flush_interval 1s; in Caddy reverse-proxy directive.

11 Assumptions & Dependencies
Assumption: Agent’s internal /chat/stream can be adapted to OpenAI SSE without major refactor.

Dependency: Supabase sessions & messages tables exist with UUID primary keys (see current schema).

Assumption: No other service currently depends on Kong endpoints.

Dependency: Caddy remains single reverse-proxy; its global email setting is valid for Let’s Encrypt, though HTTPS is optional in local dev.

12 Open Questions
Should we expose agent’s /docs through Caddy or access directly on port 8009?

Do we require per-user separation in sessions table (multi-user local demo)?

Is in-memory cache for messages necessary or premature optimisation?

13 Future Improvements (out of scope)
Add optional OAuth login to WebUI, wiring to Supabase Auth.

Support multiple models (OpenAI, Ollama) via WebUI’s provider selector.

Replace Caddy with Traefik once moving to Kubernetes (Phase 4).

Known Facts vs. Assumptions (for Claude’s awareness)
Type	Item
Known	Agent container listens on 8058/tcp (internal only).
Known	Caddy maps localhost:8009 → agent:8058, localhost:8002 → open-webui:8080.
Known	Supabase schema already contains sessions & messages tables (UUID PK).
Assumption	Agent can be extended to serve /v1/models and /v1/chat/completions quickly.
Assumption	WebUI honours OPENAI_API_HOST and OPENAI_API_KEY env vars at startup.
Assumption	Dropping Kong does not break any current REST/Auth call paths.