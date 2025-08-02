# PRD • Agentic RAG + Knowledge-Graph MVP (Sprint-0)

## 1 Background
We have two sibling repos in `~/Developer/local-RAG/`  

| Repo | Purpose |
|------|---------|
| **local-ai-packaged/** | Docker stack that starts Supabase (Postgres+Supavisor), Neo4j, n8n, Ollama, etc. using a single `docker-compose`. The stack is already running on the developer’s machine (`localhost`). |
| **agentic-rag-knowledge-graph/** | Python 3.11 codebase that will ingest docs, build embeddings, populate the Neo4j KG via Graphiti, and expose an API/CLI powered by Pydantic AI. |

Supabase Postgres is reachable at  
`postgres://postgres.{POOLER_TENANT_ID}:{POSTGRES_PASSWORD}@localhost:6543/postgres`  

Neo4j is reachable at  
`bolt://localhost:7687` (`neo4j/<password>`).

## 2 Goal (Sprint-0)
*Ingest → index → query* a small set of markdown docs via both:
1. **Vector search** (pgvector in Supabase Postgres)  
2. **Knowledge graph traversal** (Neo4j + Graphiti)

…and return correct answers through:
* **FastAPI endpoint** (`POST /chat` and `/chat/stream`)
* **CLI** with tool-usage visibility

## 3 Scope

| In-scope this sprint | Out-of-scope |
|----------------------|--------------|
| Semantic chunking, embedding, graph extraction | Advanced reranking or rerouter |
| Pydantic AI agent with three tools: `vector_search`, `graph_search`, `hybrid_search` | Web search, Supabase storage, n8n workflows |
| Supabase connection via SQL‐alchemy/asyncpg (through Supavisor port 6543) | Cloud deployment, HTTPS (Caddy), production SMTP |
| Unit & integration tests (pytest) | Load-test, CI/CD |
| `.env` templating & README updates | UI front-end |

## 4 Functional requirements
1. **Ingestion CLI**  
   * `python -m ingestion.ingest` reads `./documents` (or `big_tech_docs`)  
   * Creates embeddings (`text-embedding-3-small` unless overridden)  
   * Writes chunks to `public.chunks` (pgvector)  
   * Extracts entities/relations → writes to Neo4j via Graphiti
2. **Agent**  
   * Tool selection logic in `prompts.py`  
   * Must hit the right DB given the prompt pattern  
   * Returns JSON with `answer`, `sources`, `tools_used`
3. **API**  
   * FastAPI app at `:8058` with `/chat`, `/chat/stream`, `/health`
4. **CLI**  
   * Streams tokens, prints tool list each turn
5. **Config**  
   * Reads secrets from project-root `.env` (never committed)

## 5 Non-functional requirements
* **Async-first** DB & HTTP calls  
* Works on macOS Apple-silicon CPU profile (no GPU)  
* ≤ 90 seconds ingest for the provided 21 docs  
* 100 % pytest pass rate

## 6 Acceptance tests
| Test | Criteria |
|------|----------|
| **Ingestion smoke** | Running `ingestion.ingest --clean --verbose` exits `0`; `select count(*) from chunks` > 0; Neo4j has ≥ 1 `(:Entity)` node |
| **Vector query** | POST `/chat` with “What are Google’s AI initiatives?” returns answer & `tools_used=["vector_search"]` in < 5 s |
| **Graph query** | “How are Amazon and Anthropic related?” uses `graph_search` and cites the correct relationship |
| **Hybrid query** | “Compare Microsoft’s and Anthropic’s AI focus” uses both tools |
| **Unit tests** | `pytest -q` shows all green |

## 7 Assumptions / open questions
1. **Embedding dimension** – default 1536 (OpenAI text-embedding-3-small).  
   Can change in `sql/schema.sql` before ingest.  
2. **NUMBER_OF_DOCS** – limited to starter set; large corpora are future work.

