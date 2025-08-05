# Local RAG - Agentic Knowledge Graph System 🤖

**One-command deployment of a complete RAG system** with intelligent document processing, knowledge graph integration, and streaming chat interface.

## 🚀 Quick Start

```bash
# Start the system (takes ~60 seconds)
make up

# Verify everything is working
make ready

# Open chat interface
open http://localhost:8002
```

That's it! Your RAG system is now running with 9 AI industry documents ready to query.

## 📋 System Overview

**Core Components:**
- **🤖 Agentic RAG Agent**: FastAPI backend with OpenAI-compatible endpoints
- **🌐 OpenWebUI**: Modern chat interface with streaming support
- **🧠 Knowledge Graph**: Neo4j for entity relationships and semantic search
- **🔍 Vector Database**: Qdrant for embedding-based retrieval
- **📊 Database**: PostgreSQL with document chunks and embeddings
- **🌐 Reverse Proxy**: Caddy for unified access

**Access Points:**
- **Chat Interface:** http://localhost:8002
- **Database UI:** http://localhost:8005  
- **Neo4j Browser:** http://localhost:8008
- **Agent API:** http://localhost:8009

## 🔧 Commands

### Basic Usage
```bash
make up          # Core system + database UI (recommended)
make up-minimal  # Core system only (minimal resources)
make up-full     # Everything including extra tools
make down        # Stop all services
```

### System Management  
```bash
make ready       # Health check + data validation
make status      # Service dashboard + resource usage
make build       # Rebuild agent container
make logs        # View all service logs
```

## 📊 Service Profiles

**Core Services (Always Running):**
- Agent, OpenWebUI, PostgreSQL, Neo4j, Qdrant, Caddy

**Database Profile** (`make up` includes):
- Supabase Studio, postgres-meta, analytics

**Extra Profile** (`make up-full` includes):
- Langfuse, N8N, Flowise, ClickHouse, Minio, etc.

**Search Profile** (`make up-full` includes):
- SearXNG web search

## 💾 Resource Usage

- **Minimal**: ~1.5GB RAM (6 services)
- **Default**: ~2.2GB RAM (core + database UI)  
- **Full**: ~4GB+ RAM (all services)

## 🧪 System Validation

The system includes automated health checks:

```bash
make ready
```

**Validates:**
- ✅ Agent API healthy
- ✅ OpenWebUI accessible  
- ✅ Models endpoint working
- ✅ Documents loaded (9 found)
- ✅ Chunks loaded (136 found)

## 📚 Sample Queries

Try these queries in the chat interface:

- "What documents do you have access to?"
- "What are Apple's main AI challenges?"  
- "Tell me about recent AI investments and funding trends"
- "What companies are mentioned in your knowledge base?"

## 🏗️ Architecture

**Data Flow:**
1. Documents → Chunking → Embeddings → PostgreSQL
2. Documents → Entity Extraction → Knowledge Graph → Neo4j  
3. User Query → Vector Search + Graph Search → LLM → Response

**API Compatibility:**
- OpenAI-compatible `/v1/chat/completions` endpoint
- Streaming and non-streaming responses
- Stateless mode (no conversation persistence by default)

## ⚙️ Configuration

**Environment Variables:**
- `OPENAI_API_KEY`: Required for LLM and embeddings
- `MEMORY_ENABLED=false`: Stateless mode (default)
- `STREAMING_ENABLED=true`: Enable response streaming

**Stateless Mode:**
- No database writes during chat
- Perfect for development and testing
- Enable memory by setting `MEMORY_ENABLED=true`

## 🔍 Troubleshooting

**Common Issues:**

1. **Services not starting:** Check `make status` and `docker-compose logs`
2. **OpenWebUI 502 error:** Wait for services to be healthy (`make ready`)
3. **No documents found:** Verify agent container built correctly (`make build`)
4. **High memory usage:** Use `make up-minimal` for lighter footprint

**Health Check Commands:**
```bash
curl http://localhost:8009/health        # Agent health
curl http://localhost:8009/v1/models     # Available models  
curl http://localhost:8002               # OpenWebUI status
```

## 🔄 Development Workflow

**Daily Usage:**
```bash
make up      # Start system
make ready   # Verify health
# ... work with system ...
make down    # Clean shutdown
```

**Debugging:**
```bash
make status  # See all service states
make logs    # Monitor all logs
docker-compose logs agent  # Agent-specific logs
```

## 📖 Documentation

- **[PLAN.md](PLAN.md)**: Complete implementation history
- **[TEST_PLAN.md](TEST_PLAN.md)**: Comprehensive testing strategy  
- **[SOP-DAILY-OPERATIONS.md](SOP-DAILY-OPERATIONS.md)**: Daily operations guide

## 🎯 Features

- ✅ **One-command deployment** with health validation
- ✅ **Docker profiles** for flexible resource management
- ✅ **Streaming chat responses** with OpenAI compatibility
- ✅ **Knowledge graph integration** for semantic relationships
- ✅ **Vector similarity search** for relevant document retrieval
- ✅ **Stateless operation** for development workflows
- ✅ **Comprehensive health monitoring** and diagnostics
- ✅ **Auto-configured reverse proxy** with unified access

---

**Phase 3.3 Complete**: Production-ready RAG system with reliable one-command deployment! 🎉