# Product Requirement Document — **Phase 3.1 Stabilisation & Test Automation**

*Revision date:  2025‑08‑03*

---

## 1 Summary

Phase 3 delivered basic Dockerisation & secrets management but surfaced reliability gaps (crashing agent, missing tests, unclear repo layout). **Phase 3.1** closes those gaps by:

1. relocating the **Docker Compose file to monorepo root** for clearer ownership,
2. packaging the agent (API **and** CLI) as a first‑class Python package inside the monorepo,
3. adding an **automated and manual test plan** that developers can run locally and CI can run on every PR, and
4. documenting an opinionated repo structure for future phases.

Success is a green CI pipeline plus a single‑command local spin‑up that passes the same checks.

---

## 2 Goals & Success Metrics

| Goal | Metric | Target |
| --- | --- | --- |
| One‑command spin‑up | `make up` exits healthy | ≤ 60 s cold start |
| Secrets outside Git | `.env` contains **no** OpenAI or Neo4j creds | 100 % |
| Health visibility | `/healthz` returns 200 in < 300 ms | pass |
| **Automated test suite** | `make test` returns 0 | 100 % pass |
| **Agent CLI works** | `agent-cli "1+1"` returns `2` | pass |
| Native build | Agent image builds `arm64` locally on M‑series | pass |

---

## 3 Scope

### Must‑have

- **Repository layout** moves to:
    
    ```
    /docker-compose.yaml                # root‑level, canonical stack orchestrator
    
    /local-ai-packaged/                 # helper scripts & third‑party services (Supabase, Neo4j, Flowise…)
    
    /agentic-rag-knowledge-graph/       # FastAPI + CLI package plus data & Dockerfile
    
    ├─ agent/                         # ← api.py, cli.py, etc.
    
    ├─ ingestion/
    
    ├─ documents_test/
    
    ├─ big_tech_docs/
    
    └─ Dockerfile                     # multi‑stage build for agent image
    
    /scripts/start_services.py          # invoked by make targets; points to root compose
    
    /secrets/*                          # ignored in Git
    ```
    
- **Agent package** (`agentic-rag-knowledge-graph/agent/`):
    - `api.py` — FastAPI app (unchanged)
    - `cli.py` — Click‑based CLI with entry‑point `agent-cli`.
    - `pyproject.toml` with `[project.scripts] agent-cli = "agent.cli:main"`.
- **Test harness** (`tests/`):
    1. `test_health.py` → spins `docker compose up -d --profile core` then asserts 200 status.
    2. `test_cli.py` → mounts secrets, runs `docker compose run agent agent-cli "2+2"`.
    3. `test_rotation.py` → rewrites `secrets/openai_key`, `docker compose up -d --force-recreate agent`, asserts new key accepted.
- **CI workflow** (`.github/workflows/ci.yml`): matrix `{ arm64 }`, jobs: lint → build → test.
- **Make targets**: `make up`, `make down`, `make test`, `make build`.
- **FastAPI validation:** `pydantic`‑based env parsing; app fails fast with clear 40x if secrets missing.
- **Agentic RAG Knowledge Graph integration**: ensure the entire `agentic-rag-knowledge-graph/` package—including data loaders, embedding pipelines, and example corpora—is shipped in the agent image or mounted at runtime. Build context must include its `pyproject.toml` so both API and CLI resolve the package correctly.
- **Data seeding scripts**: provide `scripts/seed_supabase.py` (creates tables, inserts metadata) and `scripts/ingest_documents.py` (chunks & stores sample docs). `make seed` runs both and CI asserts Supabase contains ≥ 1 document and ≥ 1 000 chunks while Neo4j holds corresponding nodes.
- **Compose override for knowledge‑graph**: optional `docker-compose.arkg.yml` inside the package for focused development; root‑level `docker-compose.yaml` remains the canonical entry point. CI merges both files (`docker compose -f ...`) and must stay green.
- **Cleanup phase**: purge temporary or placeholder test artifacts generated during development; a CI step (`make hygiene`) ensures `git status --porcelain` is empty after the full test suite. Final repository remains tidy and free of dead files.

---

## 4 Technical Design

### 4.1 Repository layout rationale

Keeping Compose at the **root** avoids duplicating infra per package and matches mono‑repo conventions (single root stack). Service code stays in `/services/*` to preserve modular boundaries.

### 4.2 Compose file changes

**Root‑level `docker-compose.yaml` is the *single source of truth* that orchestrates the entire stack across local development, CI, and any future preview environments.**

- `x-secrets:` extension defines common secret mounts shared by every service.
- Profiles: `core` (supabase, neo4j, agent) / `extra` (flowise, searxng, etc.).
- `env_file:` still supported for non‑secret config.
- Optional package overrides (e.g. `docker-compose.arkg.yml`) may be merged with `f` flags for focused inner‑loop development, **but CI and `make up` always rely on the root file.**

### 4.3 Agent Dockerfile

Unchanged multi‑stage image now lives in `agentic-rag-knowledge-graph/Dockerfile`. Build context remains the repo root so the Docker build can COPY both the `agent/` code and the data directories (`ingestion/`, `documents_test/`, `big_tech_docs/`).

### 4.4 start\_services.py

Refactor to compute paths relative to script location so it works regardless of current working dir.

---

## 5 User Stories

1. **As a dev**, I run `make up` and get a URL to `http://localhost:8058/docs`.
2. **As a dev**, I execute `agent-cli "capital of Spain"` and receive `Madrid`.
3. **As CI**, I run `make test` on every pull request and block merges on failure.
4. **As a security auditor**, I search the image & container env for `sk-` and find nothing.

---

## 6 Security & Secrets (unchanged)

| Secret | Path | Mount | Notes |
| --- | --- | --- | --- |
| OpenAI key | `./secrets/openai_key` | `/run/secrets/openai_key` | read‑only |
| Neo4j auth | `./secrets/neo4j_auth` | `/run/secrets/neo4j_auth` | read‑only |

Add **pre‑commit hook**: blocks commits containing `sk-` or `neo4j/` patterns.

---

## 7 Testing & Acceptance

### 7.1 Automated (CI)

| ID | Test | Pass Condition |
| --- | --- | --- |
| A1 | `docker compose ps` → all services report `healthy` | ✅ |
| A2 | `curl /healthz` responds < 0.30 s | ✅ |
| A3 | `agent-cli "1+1"` returns `2` | ✅ |
| A4 | Secret‑rotation: overwrite `secrets/openai_key`; `docker compose up -d --force-recreate agent`; health stays green | ✅ |
| A5 | `make seed` → Supabase contains ≥ 1 document row and ≥ 1 000 chunk rows | ✅ |
| A6 | Neo4j node count ≥ 100 and edge count ≥ 100 after seeding (queried via Bolt) | ✅ |
| A7 | Retrieval: `agent-cli "capital of France"` returns `"Paris"` with ≥ 1 citation | ✅ |
| A8 | In‑container run: `docker compose run --rm agent agent-cli "Who founded Apple?"` returns `"Steve Jobs"` | ✅ |
| A9 | Failure path: stop Neo4j (`docker compose stop neo4j`); `/healthz` returns non‑200 within 10 s | ✅ |
| A10 | Hygiene: after `make test`, `git status --porcelain` is empty | ✅ |

### 7.2 Manual

1. `make up` → all containers green.
2. Run `make seed`; confirm log shows "Ingestion completed".
3. Open `http://localhost:8058/docs` and execute `GET /query?question=capital%20of%20Germany`, expect `Berlin`.
4. Tail agent logs (`docker logs -f agent`) while issuing CLI queries; verify embeddings cache hits.
5. Stop & restart agent only; repeat query to ensure state persists.
6. Inspect Supabase dashboard: verify `documents`, `chunks` tables populated.
7. Open Neo4j Browser at `bolt://localhost:7687`; run `MATCH (d:Document)-[:MENTIONS]->(:Entity) RETURN count(d)` returns > 0.
8. Search container env for secrets leakage (`docker exec agent env | grep -E "sk-|neo4j"` returns nothing). Manual
9. `make up` → green containers.
10. Browser to `/docs` shows Swagger.
11. Stop & restart agent only; stack recovers.
12. `docker inspect` shows **no** secrets in env.

### 9 Risks & Mitigations (updated)

---

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Missing tests allow regressions | High | CI gate with `make test` |
| Compose at root spills infra concerns into non‑docker projects | Low | Use `services/` sub‑dirs & profiles to bound scope |
| Secrets still leak via logs | Med | Scrub secrets in logging config |

---

## 10 Open Questions & Proposed Resolutions

| # | Question | Proposed Resolution |
| --- | --- | --- |
| 1 | Keep compose at root? | **Yes**, mono‑repo norm; revisit if repo bloats |
| 2 | Which test framework? | `pytest` + `pytest‑docker` |
| 3 | How to snapshot secrets rotation in CI without real keys? | Use dummy keys & assert file change timestamp > container start |
| 4 | Do we need a dedicated compose file inside `agentic-rag-knowledge-graph`? | Provide optional override `docker-compose.arkg.yml`; keep root compose as single source of truth |

---

# Product Requirement Document — **Phase 3.2 User Experience & CLI Enhancement**

*Revision date: 2025‑08‑03*

---

## 1 Summary
Phase 3.1 delivered basic CLI functionality focused on testing and infrastructure. **Phase 3.2** elevates the CLI to a first-class user interface by creating an interactive, developer-friendly experience that makes the agentic RAG system as easy to use as familiar tools like `git`, `docker`, or `kubectl`.

Success is measured by developer adoption and reduced friction between thought and AI assistance.

## 2 Goals & Success Metrics
| Goal | Metric | Target |
| --- | --- | --- |
| Interactive conversation | `agent chat` maintains context | ≥ 10 turns |
| Command discoverability | `agent --help` shows all features | 100% coverage |
| Response formatting | Pretty output with sources/tools | readable |
| Session persistence | Conversation survives restarts | 100% |
| Zero-configuration | Works immediately after `make up` | 0 setup steps |

## 3 User Experience Philosophy

### Interaction Paradigms
1. **API-First**: HTTP endpoints for integration (Phase 3.1 ✅)
2. **CLI-Native**: Terminal-based for developers (Phase 3.2 🎯)
3. **Container-Integrated**: Direct access to agent capabilities

### CLI Design Principles
- **Zero-configuration**: Works immediately after `make up`
- **Context-aware**: Maintains conversation history
- **Multi-modal**: Both interactive and single-command modes
- **Transparent**: Shows sources, tools used, and reasoning
- **Familiar**: Follows conventions from `git`, `docker`, `kubectl`

## 4 Command Structure

### Base Commands
```bash
agent chat                    # Interactive conversation mode
agent ask "question"          # Single query mode
agent ingest /path/to/docs    # Batch document ingestion
agent status                  # System health and statistics
agent history                 # Show recent conversations
agent --help                  # Command discovery
```

### Interactive Mode Features
```bash
agent chat
> Hello! What can you do?
🤖 I can help you with...

Sources: [doc1.pdf, knowledge_graph]
Tools: [vector_search, graph_search]

> What are Google's AI initiatives?
🤖 Google has several key AI initiatives...

> /sources     # Show last response sources
> /tools       # Show tools used
> /history     # Conversation history
> /clear       # Clear context
> /quit        # Exit gracefully
```

## 5 Technical Implementation

### 5.1 CLI Module Structure
```
agentic-rag-knowledge-graph/agent/
├── cli/
│   ├── __init__.py
│   ├── main.py          # Entry point, command routing
│   ├── chat.py          # Interactive conversation handler
│   ├── commands.py      # Single-command handlers
│   ├── session.py       # Session management
│   ├── formatting.py    # Pretty output, colors, tables
│   └── config.py        # CLI-specific configuration
```

### 5.2 Session Management
- **Local storage**: `~/.agent/sessions/` for conversation history
- **Auto-resume**: Detect interrupted sessions
- **Export capability**: Save conversations as markdown

### 5.3 Output Formatting
- **Rich text**: Colors, bold, tables using `rich` library
- **Streaming**: Real-time response display for long queries
- **Source attribution**: Clear citation formatting
- **Tool transparency**: Show which tools were used and why

## 6 Integration with Existing Infrastructure

### 6.1 Container Integration
```bash
# From host (via Make targets)
make chat                    # Launch interactive session
make ask "question"          # Single query

# Direct container access
docker-compose exec agent agent chat
docker-compose exec agent agent ask "question"
```

### 6.2 API Reuse
- CLI calls existing FastAPI endpoints internally
- No duplicate business logic
- Consistent behavior between API and CLI
- Leverages existing authentication and session management

## 7 Developer Workflow Integration

### 7.1 Context Switching
- **Quick answers**: `agent ask "what is RAG?"` without leaving terminal
- **Deep research**: `agent chat` for exploratory conversations
- **Documentation**: `agent ask "how do I deploy this?"` for project-specific help

### 7.2 Automation Friendly
```bash
# Scriptable single commands
result=$(agent ask "summarize recent AI developments")
echo "$result" | mail -s "AI Update" team@company.com

# Batch processing
find ./docs -name "*.pdf" | xargs -I {} agent ingest {}
```

## 8 Testing & Acceptance

### 8.1 Automated Tests (extends Phase 3.1)
| ID | Test | Pass Condition |
| --- | --- | --- |
| B1 | Interactive mode lifecycle | `agent chat` starts/stops cleanly |
| B2 | Context preservation | Multi-turn conversation maintains context |
| B3 | Output formatting | Rich formatting displays correctly |
| B4 | Session persistence | History survives container restarts |
| B5 | Error handling | Graceful degradation with helpful messages |

### 8.2 User Experience Tests
1. **First-time user**: Can discover commands via `--help`
2. **Power user**: Can maintain 20+ turn conversations
3. **Developer**: Can integrate with shell scripts and aliases
4. **Researcher**: Can export conversation as shareable markdown

## 9 Future Considerations (Phase 4+)

### 9.1 Advanced Features
- **Auto-completion**: Tab completion for commands and context
- **Syntax highlighting**: Code examples and query formatting
- **Plugin system**: Extensible command architecture
- **Multi-session**: Parallel conversation contexts

### 9.2 Integration Opportunities
- **IDE plugins**: VS Code extension calling CLI backend
- **Shell integration**: Bash/Zsh aliases and functions
- **Workflow tools**: GitHub Actions, CI/CD integration

---