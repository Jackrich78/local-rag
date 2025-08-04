<!-- Header -->

# PRODUCT REQUIREMENT DOCUMENT

**Project:** OpenWebUI Chat MVP for Local RAG

**Version:** 0.3.0

**Owner:** @backend-architect • **Tech-Lead:** @tldr_engineer

**Status:** *Final*

**Last Edited:** 2025-08-04

---

## 1 Summary

> “Ship a one-command, zero-login browser chat for the Agentic RAG stack running on a Mac M2, talking to our FastAPI agent over OpenAI-style endpoints, never writes to the database, and replies in ≤ 4 s.”
> 

---

## 2 Goals & Success Metrics

| Goal | Metric | Target | Owner |
| --- | --- | --- | --- |
| Instant install | Steps clone→first reply | **1** (`make up`) | DevRel |
| Responsive chat | p95 time-to-first token | **≤ 4 s** | Eng |
| No accidental memory | Rows in `messages` table | **0** | QA |
| Auth frictionless | Login prompts shown | **0** | UX |
| Safe cost ceiling | OpenAI spend/day | **≤ $2** | PM |

---

## 3 Scope

### 3.1 In-Scope (Phase 1)

- **OpenWebUI**
    - Given the docker container is up and running. When I go to the OpenWebUI local host. Then I am able to see a chatgpt model name and receive messages from the agentic-rag-knowledge-graph.
    - Image: `ghcr.io/open-webui/open-webui:v0.6.21`
    - Env:
        - `ENABLE_PERSISTENT_CONFIG=false`
        - `OPENAI_API_BASE_URL=http://agent:8058/v1`
        - `OPENAI_API_KEY=local-dev-key` (any non-empty string; ignored by agent)
    - One-time volume wipe:
        
        ```bash
        bash
        CopyEdit
        docker volume rm local-ai-packaged_open-webui
        docker compose up -d open-webui
        
        ```
        
- **Agent (FastAPI)**
    - Env flags:
        - `MEMORY_ENABLED=false`
        - `STREAMING_ENABLED=false`
    - Endpoints:
        - `POST /v1/chat/completions` → full JSON, no DB writes
        - `GET /v1/models` → `["gpt-4o-mini"]`
        - `GET /health` → `{status:"ok"}`
    - Logs: STDOUT → `docker compose logs -f agent`
    - Rebuild workflow (Option B):
        
        ```bash
        bash
        CopyEdit
        make build               # rebuilds agent image
        docker compose up -d agent
        
        ```
        
- **Compose fix**:
    - `agent.depends_on.supabase-db: { condition: service_healthy }`
- **Database URL** (verified in container):
    
    ```
    bash
    CopyEdit
    postgresql://postgres:61ead4d7b6d2ca90e598796468484b61@supabase-db:5432/postgres
    
    ```
    
- **Model cap**:
    - `max_tokens` capped at **8000** (OpenAI default)

### 3.2 Out-of-Scope

- Token streaming
- Conversation memory
- JWT auth/validation
- External HTTPS (HTTP via Caddy only)

### 3.3 Future Phases

| Phase | Feature |
| --- | --- |
| **2** | SSE token streaming (`STREAMING_ENABLED=true`) |
| **3** | Supabase-backed memory (`MEMORY_ENABLED=true`), sidebar sessions |

---

## 4 Personas & Use Cases

| Persona | Job-to-be-Done |
| --- | --- |
| Solo Founder | Chat against competitive-analysis docs locally |
| Data Scientist | Ask natural language questions of vector search |
| Tech-Lead | Demo full stack offline without cloud |

---

## 5 Functional Requirements

> As a <persona>, when I <action>, the system does <behaviour>.
> 
1. **Chat completion** — user types prompt in UI → agent returns assistant reply within 4 s.
2. **Model listing** — UI fetches `/v1/models` → sees `gpt-4o-mini`.
3. **Stateless guard** — with `MEMORY_ENABLED=false`, no inserts into `sessions` or `messages`.
4. **Zero-login UX** — loading `http://localhost:8002` shows chat immediately, no signup.
5. **Health check** — `/health` returns HTTP 200 and `{status:"ok"}`.

---

## 6 Prompt Controls

| Param | Default | Range | Notes |
| --- | --- | --- | --- |
| model | `gpt-4o-mini` | IU from `/v1/models` | MVP single-model |
| stream | `false` | `true`/`false` | Phase 2 only |
| temperature | `0.2` | 0–1 | Low randomness |
| max_tokens | `8000` | ≤ 8192 | Default window |

---

## 7 Edge Cases & Error Handling

| Event | Handler |
| --- | --- |
| Database down | 503 `"DB unavailable"` |
| Unknown model | 400 `{error:"model_not_found"}` |
| `stream=true` sent | 400 `"streaming disabled"` |
| WebUI mis-configured | Browser console error, guide to wipe volume |
| First model pull slow | Health check allows up to 10 min on initial startup |

---

## 8 Non-Functional Requirements

- **Performance:** p95 ≤ 4 s
- **Resource:** ≤ 16 GB RAM (macOS-ARM)
- **Security:** All traffic in Docker network
- **Reliability:** ≥ 99 % agent uptime
- **Cost:** ≤ $2 OpenAI spend/day (manual check)

---

## 9 Technical Design & Constraints

| Layer | Choice |
| --- | --- |
| UI | OpenWebUI v0.6.21 (auth disabled) |
| API | FastAPI on port 8058 |
| Env flags | `MEMORY_ENABLED`, `STREAMING_ENABLED` |
| DB | Supabase Postgres (`supabase-db`) — *read-only* |
| Proxy | Caddy routes 8002→8080, 8009→8058 |
| Dummy API key | `local-dev-key` |
| Vector cleanup | Cron (Phase 2) purges vectors > 30 days |

**Reference:** OpenWebUI docs – OpenAPI Servers / Open WebUI:

https://docs.openwebui.com/openapi-servers/open-webui

---

## 10 Acceptance Criteria

### Automated

| ID | Scenario | Given | When | Then |
| --- | --- | --- | --- | --- |
| **AC-1** | Chat works | Stack healthy | `curl /v1/chat/completions` | HTTP 200 + valid JSON |
| **AC-2** | No writes | `MEMORY_ENABLED=false` | 5 chats | `SELECT COUNT(*) FROM messages` = 0 |
| **AC-3** | No login | Fresh UI volume | Load UI | Chat input visible |
| **AC-4** | Model list | Agent up | GET `/v1/models` | Contains `gpt-4o-mini` |

### Manual

1. `make clean && make up` → “ping” reply < 4 s.
2. Wipe UI volume → restart OpenWebUI → no login.

---

## 11 Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| Auth flag bug | Pin v0.6.21 + `ENABLE_PERSISTENT_CONFIG=false` |
| DB schema mismatch | Verify `DATABASE_URL` inside container vs. host |
| Initial model pull | Allow extended health-check timeout |
| Disk bloat | Phase 2 cleanup cron |

---

## 12 Rollback & Observability

- Disable UI: remove `open-webui` service or set `CHAT_ENABLED=false`.
- Logs: `docker compose logs agent open-webui`.
- Rollback: `git checkout <previous-tag> && make up`.

---

## 13 Assumptions & Dependencies

- Docker Desktop ≥ 28.3 on macOS-ARM64
- OpenAI key for `gpt-4o-mini` quota
- Ports 8002 & 8009 free
- Supabase schema loaded with `01-agent-schema.sql`

---

## 14 Glossary

| Term | Meaning |
| --- | --- |
| OpenWebUI | OSS ChatGPT-style front-end |
| Dummy API key | Non-empty string required by UI |
| Stateless mode | Phase 1 guard to skip DB writes |
| SSE | Server-Sent Events (Phase 2) |

---

## 15 Changelog

| Date | Ver | Change |
| --- | --- | --- |
| 2025-08-04 | 0.3.0 | Added dummy key, rebuild workflow, DB URL, logs, test script, 8k token cap |
| 2025-08-03 | 0.2.0 | Final draft v0.2.0 |
| 2025-08-03 | 0.1.0 | Initial draft |

<!-- END -->