# Master Plan – Agentic Knowledge Base System

## 0. Context

Build a local-first, agent-driven knowledge base that combines vector RAG and Neo4j knowledge‑graph reasoning.  Primary use‑case: query a scraped Notion corpus (~100 pages) through a terminal chat agent.  Hardware: MacBook Pro M2 Max.  All services run in Docker Compose except the Python agent for v0 (venv, later containerised).

---

## 1. Guiding Principles

1. **Single Walking Skeleton first.** One data source, one agent, one UI.
2. **Local services over cloud** except for OpenAI models.
3. **Stateless containers, stateful volumes.** Data lives in mounted volumes, secrets in Docker secrets or `.env` (to be migrated).
4. **Fail fast.** Each phase ends with an executable demo and minimal test.

---

## 2. Roadmap & Milestones

| Phase | Goal | Key Deliverables | Target Date |
| --- | --- | --- | --- |
| **0** | Environment ready & KG bug fixed | ✔ Neo4j and Graphiti reachable, ✔ `MATCH (n) RETURN count(n)` > 0 | D+1 |
| **1** | Ingest Notion JSON → Supabase + Neo4j | ✔ CLI `ingest --clean --verbose` succeeds, ✔ 100 % docs vectorised & graphed, ✔ sample Cypher query returns expected triples | D+2 |
| **2** | CLI Question‑Answer agent | ✔ `python cli.py` interactive REPL, ✔ answers 8/10 gold questions correctly, ✔ < 10 s latency, ✔ citations (vector + graph) | D+3 |
| **3** | Dockerisation of agent | ✔ `docker-compose -f full-stack.yml up` brings **all** services including agent API, ✔ health‑check endpoints | D+5 |
| **4** | Context‑7 MCP tool | ✔ MCP microservice container, ✔ agent tool hook, ✔ internal docs answerable | +1 week |
| **5** | Multi‑agent orchestrator & Web UI | ✔ Orchestrator agent container, ✔ Open WebUI chat wired, ✔ user can select knowledge‑base | TBD |

> D = start of implementation (today)
> 

---

## 3. Architecture (Target after Phase 3)

```
                 ┌────────────┐           ┌─────────────┐
        chat →   │  CLI / UI  │  HTTP     │  Agent API  │
                 └────────────┘  ↖︎tool    └─────────────┘
                       │             ↙︎              ↘︎
                       │            ↙︎                 ↘︎
                Postgres (Supabase)      Neo4j + Graphiti
                 vectors, chunks          knowledge‑graph
                       │                        │
                       └──────→ OpenAI (embeddings & chat)

```

*Docker Compose services*: `supabase`, `supavisor`, `neo4j`, `graphiti`, `agent`, `open-webui` (optional), `mcps` (future).

---

## 4. Phase Breakdown

### Phase 0 – Env & Bug‑fix

- Reproduce KG ingestion error; capture stack‑trace.
- Verify `graphiti-core` import patch works.
- Add Makefile targets: `make up`, `make logs`, `make db-shell`.

### Phase 1 – Ingestion Pipeline

- **Input**: Notion JSON directory.
- **Steps**: clean → chunk (existing rules) → vectorise w/ OpenAI → graph build (Graphiti).
- **Tables used**: `documents`, `chunks`.
- **Graph schema** (initial):
    - Nodes: `Page {id, title, url}`, `Heading {text}`, `Entity {name}`.
    - Rels: `PAGE_CONTAINS_HEADING`, `MENTIONS` (Page→Entity).
- **Tests**: pytest fixture with 2 pages.

### Phase 2 – CLI Agent

- **LLM**: gpt‑4o (chat), `text-embedding-3-small`.
- **Prompt structure**: system + memory + retrieved (k = 4) + user.
- **Memory**: insert every turn into `messages` (session table).
- **Eval**: simple JSON file with 10 Q/A pairs; script counts correct matches.

### Phase 3

[Phase 3 – Dockerisation & Secrets](https://www.notion.so/Phase-3-Dockerisation-Secrets-2432b7314780800c919adbe18bcf3a7f?pvs=21)

- Build `agent` image (Python 3.10‑slim).
- Use `docker compose --env-file .env.prod`.
- Move credentials to **Docker secrets** (OpenAI, Neo4j).
- Implement health check endpoints for Supabase, Neo4j, Agent.
- To start just core services: `docker compose --profile core up -d`

### Phase 4 – Context‑7 MCP Tool

[PHASE 4-A - Context7 for Claude](https://www.notion.so/PHASE-4-A-Context7-for-Claude-2432b7314780803c9b4ec3388b287fde?pvs=21)

[PHASE 4-b MCPs for agentic-rag](https://www.notion.so/PHASE-4-b-MCPs-for-agentic-rag-2432b7314780800c8eb9f8b4e4dbd5cf?pvs=21)

- Container `mcp-context7` exposing HTTP search endpoint.
- Agent tool schema: `{query:string} → {answer:string, sources:list}`.
- Extend ingestion pipeline to index Context‑7 docs.
- https://www.youtube.com/watch?v=MBaTuJfICP4
    
    Supabase MCP
    
    Crawl4AI MCP
    
    Context7 MCP
    
    Brave MCP
    
    n8n
    
    Notion
    

### Phase 5 – Orchestrator & Web UI

- Adopt LangGraph or CrewAI for multi‑agent flows.
- Open WebUI talks to Orchestrator via REST.
- Role‑based routing: `researcher`, `planner`, `executor`.

---

## 5. Acceptance Criteria (v0 = Phases 0‑2)

1. Dev can run `make demo` and ask a question; answer returns within 10 s.
2. Answer text cites either vector doc id or graph entity id.
3. All tests pass (`pytest -q`).
4. Code lint‑clean (`ruff`, `mypy --strict`).

- Future
    - [planning] Better PRD template builder

---

## 6. Decisions

1. **Retention** – keep messages 30 days, then auto‑purge.
2. **Graph schema** – initial minimal schema (Page, Heading, Entity) is acceptable; existing ingest schema may override as needed.
3. **Python version lock** – 3.10.
4. **Secrets** – migrate Neo4j & OpenAI credentials to **Docker secrets** in Phase 3.
5. **Licensing** – no current restrictions; use well‑supported open‑source libraries and prompt human review before adopting new paid services.