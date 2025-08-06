# Agentic‑RAG Knowledge Graph – Consolidated Plan (v6)

## 0 · Purpose

Provide a single, up‑to‑date blueprint for the coding agent.  **Phase 5 – Test Reality Alignment** is the active work‑stream; Phases 0‑4 are finished and kept only for context.

---

## 0.1 · Guiding Principles

1. **Single Walking Skeleton first** – start with one data source, one agent, one UI.
2. **Local‑first** – prefer local services over cloud (OpenAI models are the exception).
3. **Stateless containers, stateful volumes** – persist data in volumes; keep containers ephemeral.
4. **Fail fast** – finish every phase with a runnable demo and minimal test suite.

These principles originate from the original Master Plan and remain non‑negotiable for all future phases. fileciteturn2file0

---

## 1 · Current Architecture (post‑Phase 4)

```
┌───────────────┐  http  ┌────────────┐
│ Open WebUI    │ ─────▶ │  Orchestrator* │
└───────────────┘        │    (agent)   │
        ▲                 └──────┬─────┘
        │ REST                ↙︎     ↘︎
        │               Supabase    Neo4j
        │              (vectors)   (graph)
        │                        ↘︎
        │                     OpenAI API
```

*The Orchestrator container subsumes the previous “agent” API: it listens on ****8058**** inside the container and is published on ****8059**** to the host network.*

Key runtime flags (all in `docker‑compose.yml`):

| Var                 | Default                  | Meaning                         |
| ------------------- | ------------------------ | ------------------------------- |
| `MEMORY_ENABLED`    | `false`                  | Skip DB writes (stateless mode) |
| `STREAMING_ENABLED` | `true` (Phase 3.2+)      | Enable SSE chunking             |
| `LLM_CHOICE`        | `gpt‑4o‑mini`            | Primary model used everywhere   |
| `EMBEDDING_MODEL`   | `text‑embedding‑3‑small` | Vector store embeddings         |

Docker profiles: **core** (agent, UI, DB, Neo4j, Qdrant, Caddy) · **database** (Supabase Studio etc.) · **extra** (MCPs, Langfuse, n8n, Flowise) · **search** (SearXNG).

## 1.1 · Port Map — *source of truth 2025‑08‑06*

\| Host Port | Route | Container\:Port | Notes |
|## 2 · Phase 5 — *Test Reality Alignment*  🔄  · Phase 5 — *Test Reality Alignment*  🔄 

### Goal

Update the automated test‑suite so it reflects the working system, eliminating false negatives (especially in `tests/test_api_streaming.py`).

### Deliverables

1. **Fixed expectations** — model list recognises `gpt‑4o‑mini`; latency threshold raised to < 2 s; network checks reuse health helper.
2. **Async hygiene** — proper `aiohttp` context managers, no `await` on sync fns, sessions closed correctly.
3. **Streaming validator** — confirms correct SSE chunk format `delta.content`, `[DONE]` terminator.
4. **Pass gate** — CI passes 31/31 automated tests + master orchestration.

### Success criteria

| Metric                             | Target                     |
| ---------------------------------- | -------------------------- |
| API streaming tests                | **11/11 pass**             |
| `python test_master_validation.py` | exits 0 every run          |
| Browser chat                       | unaffected (manual sanity) |

### Work‑list

1. **Align assertions** → `tests/test_api_streaming.py` lines 33‑71.
2. **Refactor latency benchmark** → helper `first_token_latency(target=2.0)`.
3. **Fix session closed errors** → wrap each HTTP call inside `async with`.
4. **Kong stub removal** → delete obsolete Kong container check.
5. **Run full matrix**: `make up‑minimal`, `make up`, `make up‑full`, `make up --profile search` → all green.

---

## 2.1 · Global Acceptance Criteria

| # | Criterion                                                                      |
| - | ------------------------------------------------------------------------------ |
| 1 | `make demo` (or `make up && make ready`) responds to a question in **≤ 10 s**  |
| 2 | Responses include citations to either vector **doc id** or graph **entity id** |
| 3 | **All automated tests pass** (`pytest -q`)                                     |
| 4 | Codebase is **lint‑clean** (`ruff`) and **type‑safe** (`mypy --strict`)        |

### Key Product Decisions

* **Retention**: keep chat messages **30 days**, then auto‑purge fileciteturn4file3.
* **Graph schema**: minimal (`Page`, `Heading`, `Entity`) is sufficient for now fileciteturn4file3.
* **Python version**: locked to **3.13**.
* **Secrets**: sensitive creds moved to **Docker secrets** in Phase 3.
* **Licensing**: prefer permissive OSS; human review before adopting paid services.

---

## 3 · Historical Phases (compressed)

> Completed; do **not** modify unless rolling back.

### Phase 4 — Test Infrastructure Enhancement ✅ *(2025‑08‑05)*

* Expanded test coverage from 18 → **31** automated cases
* Added **master orchestration runner** `test_master_validation.py`
* Human validation checklist (23 items) documented in `TEST_PLAN.md`
* Profiles validation ensures every compose combination boots & passes health

### Phase 3 — Dockerisation & Streaming ✅ *(2025‑08‑03 → 08‑05)*

| Sub‑phase | Outcome                                                                                 |
| --------- | --------------------------------------------------------------------------------------- |
| **3.1**   | Moved compose to repo root, packaged agent & CLI, green CI on arm64                     |
| **3.2**   | Enabled SSE streaming (`STREAMING_ENABLED=true`), browser real‑time tokens              |
| **3.3**   | Introduced Docker **profiles**, `make up` reliable in ≤ 60 s, health‑check optimisation |

### Phase 2 — CLI Question‑Answer Agent ✅ *(2025‑08‑02)*

* `agent-cli` interactive REPL answers 8/10 gold questions in < 10 s
* Prompt template: system + memory + retrieved **k=4** + user
* Uses Supabase vectors + Neo4j entities for citations

### Phase 1 — OpenWebUI Stateless MVP ✅ *(2025‑08‑01 → 08‑04)*

* Zero‑login **OpenWebUI** (`WEBUI_AUTH=false`, `ENABLE_SIGNUP=false`)
* Agent stateless guard (`MEMORY_ENABLED=false`) — **no** DB writes
* Endpoints: `/v1/chat/completions`, `/v1/models`, `/health`
* Test script `test_phase1.py` (6 checks) – all now pass

### Phase 0 — Environment & KG bug‑fix ✅ *(2025‑07‑31)*

* Fixed Graphiti import path; Neo4j returns node counts > 0
* Added Make targets: `make up`, `make logs`, `make db‑shell`

---

## 4 · Open Questions / Potential Clashes

| Topic                              | Observation                                                                           | Action                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **Phase numbering**                | Master Plan uses 0‑5; some docs label streaming as *Phase 3.2* vs original *Phase 2*. | **Keep table above as source of truth** (0‑5 linear). |
| **`open-webui`**\*\* image tag\*\* | Compose tracks `latest` (v0.7 series).                                                | Decision: stay on `latest`; pin if CI breaks.         |
| **Streaming latency target**       | Browser p95 ≈ 1.4 s                                                                   | **Target < 2 s** (tests enforce)                      |

---

## 5 · Next Steps After Phase 5

1. **Phase 6 — Multi‑Agent Orchestrator**

   * graduate MCP containers (Brave, Crawl4AI) from `profiles:extra` to default
   * adopt LangGraph or CrewAI for role‑based routing (researcher/planner/executor)
2. **Phase 7 — Memory On**

   * flip `MEMORY_ENABLED=true`, implement session save & recall
   * add privacy‑driven retention purge (30 d cron)
3. **Phase 8 — Cloud Remote Option**

   * optional AWS‑Fargate deployment with SSM tunnelling; CI publishes `arm64`/`amd64` images

---

## 6 · Command Reference (cheat‑sheet)

```bash
# bring up default stack (core + database UI)
make up
# minimal core (fast)
make up‑minimal
# everything including MCPs etc.
make up‑full
# validate full health & tests
python tests/test_master_validation.py
# run Phase‑5 suite only
pytest tests/test_api_streaming.py -v
```

---

## 7 · Glossary

| Term        | Definition                                                  |
| ----------- | ----------------------------------------------------------- |
| **MCP**     | *Model Context Protocol* micro‑service (e.g., Brave Search) |
| **SSE**     | Server‑Sent Events (token streaming)                        |
| **Profile** | Docker Compose grouping to toggle service sets              |

---

*Document version 6 generated 2025‑08‑06.*
