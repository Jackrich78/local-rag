# Services Registry - Complete Service Catalog

**Definitive service catalog with resolved port conflicts and accurate deployment information**

## Service Overview

The Local RAG system consists of **15+ services** across multiple Docker Compose profiles. Services are organized by function and deployment requirements.

## Core Services (Always Running)

### 1. **Agent Service** - Core Intelligence
**Container**: `agentic-rag-agent`  
**Image**: Built from `../agentic-rag-knowledge-graph/Dockerfile`  
**Internal Port**: `8058/tcp`  
**External Access**: `http://localhost:8009` (via Caddy)  
**Purpose**: Core FastAPI application providing OpenAI-compatible API and agentic RAG capabilities

**Key Endpoints**:
- `GET /health` - System health check
- `GET /v1/models` - OpenAI-compatible model list
- `POST /v1/chat/completions` - OpenAI-compatible chat API
- `POST /chat` - Native chat endpoint
- `POST /chat/stream` - Server-sent events streaming
- `POST /search/*` - Direct search APIs

**Dependencies**: `neo4j`, `db` (Supabase)  
**Health Check**: `curl -f http://localhost:8058/health`

### 2. **OpenWebUI** - Chat Interface  
**Container**: `open-webui`  
**Image**: `ghcr.io/open-webui/open-webui:latest`  
**Internal Port**: `8080/tcp`  
**External Access**: `http://localhost:8009` (via Caddy) ⚠️ **Note: MASTERPLAN.md incorrectly shows this as unused**  
**Purpose**: Web-based chat interface for user interactions

**Configuration**:
- `WEBUI_AUTH=false` - No authentication required
- `ENABLE_SIGNUP=false` - Registration disabled  
- `OPENAI_API_BASE_URL=http://agent:8058/v1` - Routes to agent service

**Dependencies**: `agent` (service_healthy condition)

### 3. **Neo4j Graph Database**
**Container**: `local-ai-packaged-neo4j-1`  
**Image**: `neo4j:latest`  
**Internal Ports**: `7474/tcp` (HTTP), `7687/tcp` (Bolt), `7473/tcp`  
**External Access**: 
- `http://localhost:7474` - Neo4j Browser (direct)
- `http://localhost:8008` - Neo4j Browser (via Caddy)  
**Purpose**: Knowledge graph storage for entity relationships

**Authentication**: `NEO4J_AUTH=${NEO4J_AUTH:-"neo4j/your_password"}`  
**Volumes**: `./neo4j/{logs,config,data,plugins}`

### 4. **Supabase Database** (from included compose)
**Container**: `supabase-db` (actual container name from included compose)  
**Image**: `postgres:${POSTGRES_VERSION:-latest}`  
**Internal Port**: `5432/tcp`  
**External Access**: Internal only  
**Purpose**: PostgreSQL with pgvector for document storage and vector search

**Referenced as**: `db` in agent service dependencies  
**Health Check**: `pg_isready -U postgres`

### 5. **Qdrant Vector Database**
**Container**: `qdrant`  
**Image**: `qdrant/qdrant`  
**Internal Ports**: `6333/tcp`, `6334/tcp`  
**External Access**: Internal only  
**Purpose**: Vector storage and similarity search

### 6. **Caddy Reverse Proxy**
**Container**: `caddy`  
**Image**: `caddy:2-alpine`  
**Internal Ports**: `80/tcp`, `443/tcp`, `2019/tcp` (admin)  
**External Ports**: 
- `80:80` - HTTP
- `443:443` - HTTPS  
- `8001:8001` - N8N
- `8002:8002` - WebUI ⚠️ **Appears unused based on Caddyfile**
- `8003:8003` - Flowise
- `8005:8005` - Supabase Studio
- `8007:8007` - Langfuse
- `8008:8008` - Neo4j Browser
- `8009:8009` - Agent API

**Purpose**: Reverse proxy, TLS termination, service routing

**Route Configuration** (from Caddyfile):
- `{$AGENT_HOSTNAME}` → `agent:8058` (default :8009)
- `{$WEBUI_HOSTNAME}` → `open-webui:8080` (default :8002) ⚠️ **Currently unused**
- `{$NEO4J_HOSTNAME}` → `local-ai-packaged-neo4j-1:7474` (default :8008)
- `{$SUPABASE_HOSTNAME}` → `supabase-studio:3000` (default :8005)

## Database Profile Services

**Activated with**: `make up` or `docker-compose --profile database up`

### 7. **Supabase Studio** - Database Administration
**Container**: `supabase-studio`  
**Image**: `supabase/studio:2025.06.30-sha-6f5982d`  
**Internal Port**: `3000/tcp`  
**External Access**: 
- `http://localhost:3000` (direct)
- `http://localhost:8005` (via Caddy)  
**Purpose**: Database administration and analytics interface

**Dependencies**: `analytics` (service_healthy)

### 8. **Supabase Analytics**
**Container**: Analytics service from Supabase compose  
**Internal Port**: `4000/tcp`  
**External Access**: `http://localhost:4000` (direct)  
**Purpose**: Database analytics and monitoring

## Extra Profile Services

**Activated with**: `make up-full` or `docker-compose --profile extra up`

### 9. **N8N Workflow Automation**
**Container**: `n8n`  
**Image**: `n8nio/n8n:latest`  
**Internal Port**: `5678/tcp`  
**External Access**: `http://localhost:8001` (via Caddy)  
**Purpose**: Workflow automation and integration platform

**Database**: Uses same PostgreSQL as Supabase  
**Dependencies**: `n8n-import` (service_completed_successfully)

### 10. **Flowise** - No-Code AI Workflows
**Container**: `flowise`  
**Image**: `flowiseai/flowise`  
**Internal Port**: `3001/tcp`  
**External Access**: `http://localhost:8003` (via Caddy)  
**Purpose**: Visual AI workflow builder and automation

### 11. **Langfuse** - LLM Observability
**Containers**: `langfuse-web`, `langfuse-worker`  
**Image**: `langfuse/langfuse:3`, `langfuse/langfuse-worker:3`  
**Internal Port**: `3000/tcp` (web), `3030/tcp` (worker)  
**External Access**: `http://localhost:8007` (via Caddy)  
**Purpose**: LLM performance monitoring and observability

**Dependencies**: `postgres`, `minio`, `redis`, `clickhouse` (all service_healthy)

### 12. **Supporting Infrastructure (Extra Profile)**

**PostgreSQL** (separate from Supabase)  
**Container**: `postgres`  
**Purpose**: Database for Langfuse and N8N  

**Redis/Valkey**  
**Container**: `redis`  
**Image**: `valkey/valkey:8-alpine`  
**Purpose**: Caching and session storage

**ClickHouse**  
**Container**: `clickhouse`  
**Image**: `clickhouse/clickhouse-server`  
**Purpose**: Analytics database for Langfuse

**MinIO**  
**Container**: `minio`  
**Image**: `minio/minio`  
**Purpose**: S3-compatible object storage

## Search Profile Services

**Activated with**: `docker-compose --profile search up`

### 13. **SearXNG** - Web Search
**Container**: `searxng`  
**Image**: `searxng/searxng:latest`  
**Internal Port**: `8080/tcp`  
**External Access**: `http://localhost:8006` (via Caddy) ⚠️ **Currently commented out in Caddyfile**  
**Purpose**: Privacy-focused web search aggregator

## Optional Services (CPU/GPU Profiles)

### 14. **Ollama** (Local LLM)
**Containers**: `ollama-cpu`, `ollama-gpu`, `ollama-gpu-amd`  
**Profiles**: `cpu`, `gpu-nvidia`, `gpu-amd`  
**Image**: `ollama/ollama:latest` (or `:rocm` for AMD)  
**Internal Port**: `11434/tcp`  
**Purpose**: Local LLM inference (alternative to OpenAI)

**Note**: Currently commented out in Caddyfile, not actively routed

## Service Dependencies

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Users    │───▶│    Caddy    │───▶│ OpenWebUI   │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Neo4j     │◄───┤    Agent    │
                   └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  Supabase   │
                                      │ (Database)  │
                                      └─────────────┘
```

**Startup Order**:
1. **Infrastructure**: Caddy, databases (PostgreSQL, Neo4j, Qdrant)
2. **Core Services**: Agent service  
3. **UI Services**: OpenWebUI
4. **Optional Services**: Supabase Studio, N8N, Flowise, etc.

## Network Topology

**Docker Networks**:
- Default bridge network for service communication
- All services communicate via container names
- External access only through Caddy proxy

**Internal Communication**:
- `agent` → `neo4j:7687` (Bolt protocol)
- `agent` → `db:5432` (PostgreSQL)  
- `open-webui` → `agent:8058` (HTTP API)
- `supabase-studio` → `db:5432` (Database access)

## Health Check Endpoints

| Service | Health Check Command | Endpoint |
|---------|---------------------|----------|
| Agent | `curl -f http://localhost:8058/health` | `/health` |
| Neo4j | Browser accessibility | `http://localhost:7474` |
| Supabase | `pg_isready -U postgres` | N/A |
| Caddy | Port accessibility | `http://localhost:80` |
| OpenWebUI | HTTP response | `http://localhost:8080` |
| Qdrant | Internal health check | N/A |

## Port Resolution Summary

**✅ Resolved Port Conflicts:**

| Service | MASTERPLAN.md Says | Actual Implementation | Resolution |
|---------|-------------------|---------------------|------------|
| Agent API | Port 8059 | Port 8009 (via Caddy) | **Use 8009** - Makefile and Caddy confirm this |
| OpenWebUI | "Currently unused" | Active at port 8009 | **OpenWebUI IS active** - MASTERPLAN outdated |
| MCP Services | Ports 8007, 8008 | Not implemented | **MCP services not yet implemented** |

**⚠️ Documentation Updates Needed:**
- MASTERPLAN.md port mappings need updates to reflect actual implementation
- MCP service references should be marked as "planned" not "active"
- OpenWebUI status should be corrected from "unused" to "active"

## Docker Profile Matrix

| Service | minimal | database | extra | search |
|---------|---------|----------|-------|--------|
| Agent | ✅ | ✅ | ✅ | ✅ |
| OpenWebUI | ✅ | ✅ | ✅ | ✅ |
| Neo4j | ✅ | ✅ | ✅ | ✅ |  
| Supabase DB | ✅ | ✅ | ✅ | ✅ |
| Qdrant | ✅ | ✅ | ✅ | ✅ |
| Caddy | ✅ | ✅ | ✅ | ✅ |
| Supabase Studio | ❌ | ✅ | ✅ | ✅ |
| N8N | ❌ | ❌ | ✅ | ✅ |
| Flowise | ❌ | ❌ | ✅ | ✅ |
| Langfuse | ❌ | ❌ | ✅ | ✅ |
| SearXNG | ❌ | ❌ | ❌ | ✅ |

**Profile Commands**:
- `make up-minimal` - Core services only (~2GB RAM)
- `make up` - Core + database UI (~4GB RAM)  
- `make up-full` - Everything except search (~6-8GB RAM)
- `docker-compose --profile search up` - Add SearXNG

## Service Status Monitoring

**Quick Health Check**:
```bash
make ready                    # Complete system health check
make status                   # Resource usage dashboard
curl http://localhost:8009/health  # Agent service health
```

**Detailed Monitoring**:
```bash
docker-compose ps             # Container status
docker stats --no-stream     # Resource usage
make logs                     # All service logs
make agent-logs               # Agent-specific logs
```

---

**This registry provides the definitive service catalog with accurate port mappings and resolved documentation conflicts. Use this as the authoritative source for system architecture and deployment planning.**