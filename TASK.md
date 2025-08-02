# TASK BOARD – Sprint-0

## 🚧 To Do
- [ ] **T1** Create `.env.template` in repo with required keys & sample values  
- [ ] **T2** DB utils: async Postgres pool (reads DATABASE_URL)  
- [ ] **T3** Graph utils: Graphiti client (reads NEO4J_* env)  
- [ ] **T4** Adjust `sql/schema.sql` vector dimensions (1536)  
- [ ] **T5** Implement `ingestion/chunker.py` (semantic split)  
- [ ] **T6** Implement `ingestion/embedder.py` (OpenAI embeddings)  
- [ ] **T7** Implement `ingestion/graph_builder.py` (entity → graph)  
- [ ] **T8** Write `ingestion/ingest.py` CLI (`--clean`, `--verbose`)  
- [ ] **T9** Write `agent/tools.py` (`vector_search`, `graph_search`, `hybrid_search`)  
- [ ] **T10** Draft `prompts.py` with tool-selection rules  
- [ ] **T11** Build `agent/agent.py` (Pydantic AI)  
- [ ] **T12** Build `agent/api.py` (FastAPI, SSE)  
- [ ] **T13** Create `cli.py` (streams, colors)  
- [ ] **T14** Unit tests for utils + tools (`pytest`)  
- [ ] **T15** Integration test: ingestion + simple query  
- [ ] **T16** Update `README.md` quick-start & .env instructions

## ✅ Done
<!-- Claude will tick tasks and move them here -->
