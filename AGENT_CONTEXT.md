# Agent Context - Local RAG System Quick Reference

**5-Minute System Orientation for Coding Agents**

## What This System Is

**Local RAG with Agentic Knowledge Graph** - A comprehensive AI research platform that combines:
- **RAG (Retrieval-Augmented Generation)** using vector embeddings
- **Knowledge Graph** for entity relationships  
- **Agentic AI** that can use tools and reason
- **Multi-modal interfaces** (chat, API, workflows)

**Not just "chat with documents" - this is a complete AI research and knowledge management platform with 36+ distinct features.**

## Core Architecture (5 Key Components)

```
User Request → OpenWebUI → Agent (FastAPI) → {Supabase + Neo4j} → OpenAI → Response
     ↓              ↓            ↓              ↓                    ↓         ↓
  Port 8009    Port 8080    Port 8058     Vector DB          LLM API   Streaming
                                         Graph DB                      Response
```

1. **OpenWebUI** (`open-webui:8080`) - Chat interface accessible at `localhost:8009` via Caddy
2. **Agent Service** (`agent:8058`) - Core FastAPI application with OpenAI-compatible API
3. **Supabase** (`db:5432`) - PostgreSQL + vector storage for RAG
4. **Neo4j** (`neo4j:7687`) - Knowledge graph for entity relationships
5. **Caddy** (`caddy:80/443`) - Reverse proxy routing all services

## Data Flow Pattern

```
Documents → Ingestion Pipeline → Dual Storage → Agent Queries → LLM Integration → User
             (chunks + entities)   (vectors +   (hybrid search)  (OpenAI API)
                                   graph)
```

**Key Insight**: Every query triggers hybrid search across both vector similarity and graph relationships.

## Essential File Locations

### **Core Application**
- `agentic-rag-knowledge-graph/agent/api.py` - Main FastAPI server (582 lines)
- `agentic-rag-knowledge-graph/agent/agent.py` - Core agent logic with Pydantic AI
- `agentic-rag-knowledge-graph/agent/tools.py` - RAG search tools

### **Infrastructure**
- `local-ai-packaged/docker-compose.yml` - Service orchestration (534 lines)
- `local-ai-packaged/Caddyfile` - Reverse proxy configuration
- `Makefile` - System management commands

### **Configuration**
- `agentic-rag-knowledge-graph/.env` - Agent service config
- `local-ai-packaged/.env` - Infrastructure config
- `.env.test` - Test configuration overrides

### **Documentation**
- `docs/project/MASTERPLAN.md` - System phases and architecture decisions
- `docs/operations/TEST_PLAN.md` - Complete test infrastructure (31 tests)
- `TREE.md` - File structure overview

## System Modes & Features

### **Deployment Profiles** (Docker Compose)
- **Minimal** (`make up-minimal`) - Core RAG only
- **Database** (`make up`) - Core + database UI (Supabase Studio)  
- **Extra** (`make up-full`) - Everything + n8n, Flowise, Langfuse
- **Search** - Adds SearXNG web search

### **Agent Modes**
- **Stateless** (`MEMORY_ENABLED=false`) - No conversation persistence
- **Memory Enabled** (`MEMORY_ENABLED=true`) - Full session management
- **Streaming** (`STREAMING_ENABLED=true`) - Real-time response streaming

## Common Development Tasks

### **System Operations**
```bash
make up                    # Start core system
make ready                 # Health check all services
make status               # Resource usage dashboard
make logs                 # All service logs
make agent-logs           # Agent service only
```

### **Testing**
```bash
python tests/test_master_validation.py    # All 31 tests
python tests/test_api_streaming.py        # API/streaming tests
python tests/test_system_health.py        # Infrastructure tests
```

### **Development**
```bash
make shell-agent          # Shell into agent container
make shell-db             # PostgreSQL shell
make shell-neo4j          # Neo4j Cypher shell
make ingest              # Run document ingestion
```

## API Endpoints (Agent Service)

### **OpenAI Compatible**
- `GET /v1/models` - Available models
- `POST /v1/chat/completions` - Chat (streaming & non-streaming)

### **Native Agent API**
- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Server-sent events streaming  
- `POST /search/vector` - Direct vector search
- `POST /search/graph` - Direct graph search
- `POST /search/hybrid` - Combined search
- `GET /documents` - List ingested documents
- `GET /health` - System health check

### **API Documentation**
- **Interactive Docs**: `http://localhost:8009/docs` (FastAPI auto-generated)
- **OpenAPI Spec**: `http://localhost:8009/openapi.json` (always up-to-date)

## Key Development Patterns

### **Agent Tool Integration**
- Tools defined in `agent/tools.py` using Pydantic AI patterns
- Agent automatically selects tools based on query context
- Supports vector_search, graph_search, hybrid_search, list_documents

### **Configuration Management**
- Environment variables cascade: system → .env → docker-compose
- Feature flags control major behaviors (memory, streaming)
- Auto-detection patterns for models and services

### **Error Handling**
- OpenAI quota limits handled gracefully
- Service degradation when components unavailable
- Comprehensive health checks across all services

## Performance Characteristics

- **Startup Time**: ~45-60 seconds for full system
- **First Response**: ~2-5 seconds (within target)
- **Streaming Latency**: ~0.5-1.5 seconds first token
- **Resource Usage**: ~4GB RAM for full deployment

## Critical Architecture Decisions

1. **OpenAI Compatibility Layer** - Enables drop-in replacement for OpenAI API clients
2. **Hybrid RAG Strategy** - Vector similarity + knowledge graph relationships  
3. **Stateless-First Design** - Can run without persistence for demos
4. **Multi-Profile Deployment** - Flexible resource usage based on needs
5. **Real-time Streaming** - Server-sent events for responsive UX

## When Things Go Wrong

**Most Common Issues:**
1. **Port conflicts** - Check `make status` for service health
2. **Model unavailable** - Verify OpenAI API key in environment
3. **Database connection** - Ensure Supabase services healthy
4. **Memory issues** - Use `make up-minimal` for lower resource usage

**Debug Workflow:**
1. `make ready` - Check system health
2. `make agent-logs` - Check agent service errors  
3. `curl http://localhost:8009/health` - Verify API availability
4. Check test suite: `python tests/test_master_validation.py`

---

**This system is a sophisticated AI research platform, not a simple chatbot. Approach it as you would a complex distributed system with multiple data stores, streaming capabilities, and extensive integration possibilities.**