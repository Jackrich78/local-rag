# System Architecture - Local RAG with Agentic Knowledge Graph

**Comprehensive Technical Foundation and Mental Models**

## Executive Summary

The Local RAG system is a **distributed AI research platform** implementing hybrid retrieval-augmented generation through dual-path knowledge storage (vector + graph) with agentic reasoning capabilities. Built as a microservices architecture using Docker orchestration, it provides OpenAI-compatible APIs while maintaining local-first principles.

**Key Architectural Patterns:**
- **Hybrid RAG**: Vector similarity + knowledge graph relationships
- **Agent-Centric Design**: Tools and reasoning, not just Q&A
- **Stateless-First**: Can operate without persistence for demos
- **Progressive Enhancement**: Multiple deployment profiles for different use cases
- **API Compatibility**: Drop-in OpenAI replacement

## 1. Overall System Architecture

### 1.1 High-Level Component Architecture

```
                           ┌─────────────────┐
                           │  External APIs  │
                           │   (OpenAI)      │
                           └─────────┬───────┘
                                     │
┌─────────────┐    ┌─────────────┐  │  ┌─────────────────┐
│   Users     │◄──►│    Caddy    │  │  │  Agent Service  │
│(Browser/API)│    │(Port 80/443)│  │  │   (FastAPI)     │
└─────────────┘    └─────┬───────┘  │  │   Port 8058     │
                         │          │  └─────────┬───────┘
                 ┌───────▼────┐     │            │
                 │ OpenWebUI   │     │      ┌─────▼─────┐
                 │  Port 8080  │◄────┼──────┤   Tools   │
                 └─────────────┘     │      │& Reasoning│
                                     │      └─────┬─────┘
         ┌───────────────────────────┼────────────┘
         │                           │
    ┌────▼────┐              ┌──────▼──────┐
    │Supabase │              │    Neo4j    │
    │Database │              │    Graph    │
    │(Vectors)│              │  Database   │
    │Port 5432│              │  Port 7687  │
    └─────────┘              └─────────────┘
```

### 1.2 Service Interaction Patterns

**Request Flow (Synchronous):**
1. User → Caddy → OpenWebUI → Agent API
2. Agent → Tool Selection → Database Queries
3. Agent → LLM Integration → Response Assembly
4. Response → OpenWebUI → User

**Streaming Flow (Async):**
1. WebSocket/SSE connection established
2. Agent streams tokens via Server-Sent Events
3. Real-time updates to user interface
4. Background conversation persistence

**Data Ingestion Flow (Batch):**
1. Documents → Ingestion Pipeline → Chunking
2. Parallel Processing → Vector Embeddings + Entity Extraction  
3. Dual Storage → Supabase (vectors) + Neo4j (graph)
4. Index Updates → Search Optimization

## 2. Data Architecture

### 2.1 Dual-Path Knowledge Storage

```
Documents
    │
    ▼
┌─────────────────┐
│ Ingestion       │
│ Pipeline        │
│ (Python)        │
└─────┬───────────┘
      │
      ├─────────────────────┬─────────────────────┐
      │                     │                     │
      ▼                     ▼                     ▼
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│Chunking  │      │  Embedding   │      │   Entity     │
│Strategy  │      │  Generation  │      │ Extraction   │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘
     │                   │                     │
     ▼                   ▼                     ▼
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│Document  │      │    Vector    │      │ Knowledge    │
│Metadata  │      │   Storage    │      │   Graph      │
│(Supabase)│      │  (Supabase)  │      │   (Neo4j)    │
└──────────┘      └──────────────┘      └──────────────┘
```

### 2.2 Database Schema Design

**Supabase (PostgreSQL + pgvector):**
- `documents` - Source document metadata
- `chunks` - Text chunks with vector embeddings  
- `sessions` - Conversation persistence
- `messages` - Chat history with metadata
- Vector indexes for similarity search

**Neo4j (Graph Database):**
- `Entity` nodes - Companies, people, concepts
- `Document` nodes - Source materials
- `Relationship` edges - Semantic connections
- Temporal validity tracking

**Key Design Decisions:**
- **Eventual Consistency** - Vector and graph updates may lag slightly
- **Immutable Documents** - Source docs never modified, only versioned
- **Soft Deletes** - Preserve audit trail and rollback capability

### 2.3 Data Flow Patterns

**Query Processing:**
```
User Query → Intent Analysis → Multi-path Search
    │               │                    │
    │               ▼                    ├─ Vector Search (similarity)
    │         Tool Selection             ├─ Graph Search (relationships)  
    │               │                    └─ Hybrid Ranking
    │               ▼
    └─── Context Assembly ◄─────────── Search Results
                    │
                    ▼
            LLM Integration → Response Generation
```

**Performance Characteristics:**
- Vector search: ~50-200ms (depending on corpus size)
- Graph queries: ~10-100ms (depending on relationship depth)
- LLM calls: ~1-3 seconds (first token), streaming thereafter
- Total response time: ~2-5 seconds typical

## 3. Service Architecture

### 3.1 Agent Service (Core Intelligence)

**Technology Stack:**
- **FastAPI** - High-performance async API framework
- **Pydantic AI** - Agent framework with tool integration
- **Uvicorn** - ASGI server with hot reload support

**Key Components:**
- `api.py` - HTTP endpoints and OpenAI compatibility
- `agent.py` - Core reasoning engine and tool orchestration  
- `tools.py` - RAG search implementations
- `models.py` - Data validation and serialization

**Design Patterns:**
- **Dependency Injection** - AgentDependencies for session/user context
- **Tool-Based Architecture** - Agent selects tools based on query analysis
- **Streaming-First** - All responses can stream via SSE
- **Error Isolation** - Graceful degradation when services unavailable

### 3.2 Infrastructure Services

**Caddy (Reverse Proxy):**
- **TLS Termination** - Automatic HTTPS with Let's Encrypt
- **Load Balancing** - Future horizontal scaling support
- **Request Routing** - Path-based routing to services
- **SSE Optimization** - Streaming configuration for real-time responses

**Docker Orchestration:**
- **Service Profiles** - Flexible deployment configurations
- **Health Checks** - Container-level and application-level monitoring
- **Volume Management** - Persistent data across container restarts
- **Network Isolation** - Internal communication + exposed endpoints

### 3.3 Database Services

**Supabase Ecosystem:**
- **PostgreSQL** - Primary data storage with ACID compliance
- **pgvector** - Vector similarity search extensions
- **Studio** - Database administration interface
- **Auth** - User authentication (currently disabled for demos)
- **Analytics** - Query performance monitoring

**Neo4j Graph Database:**
- **APOC Procedures** - Advanced graph algorithms
- **Browser Interface** - Visual graph exploration
- **Cypher Queries** - Declarative graph query language
- **Clustering Support** - Future distributed graph capabilities

## 4. State Management Architecture

### 4.1 Stateless vs Stateful Modes

**Stateless Mode (`MEMORY_ENABLED=false`):**
```
Request → Processing → Response
   │                      ▲
   └── Temporary Context ──┘
   (No database writes)
```

**Stateful Mode (`MEMORY_ENABLED=true`):**
```
Request → Session Management → Processing → Response
   │            │                             ▲
   │            ▼                             │
   └── Persistent Context ◄──── Database ─────┘
       (Full conversation history)
```

**Key Architectural Decisions:**
- **Stateless-First Design** - System works without persistence
- **Progressive Enhancement** - Add memory for production use
- **Session Isolation** - User sessions completely independent
- **Context Windows** - Sliding window for conversation context

### 4.2 Configuration Management

**Environment Variable Cascade:**
1. **System Defaults** - Hardcoded fallbacks in code
2. **Container Environment** - Docker-compose environment
3. **File Overrides** - .env files for customization
4. **Runtime Detection** - Auto-detection of available services

**Feature Flag Architecture:**
- `MEMORY_ENABLED` - Persistence on/off
- `STREAMING_ENABLED` - Real-time responses  
- `AUTO_DETECT_MODELS` - Model discovery vs fixed configuration
- Profile-based feature sets (minimal/database/extra/search)

## 5. Integration Architecture

### 5.1 OpenAI API Compatibility

**Compatibility Layer Implementation:**
- **Endpoint Mapping** - `/v1/models`, `/v1/chat/completions`
- **Request Translation** - OpenAI format → internal format
- **Response Adaptation** - Internal format → OpenAI format
- **Streaming Protocol** - Server-Sent Events with proper formatting
- **Error Code Mapping** - HTTP status codes and error formats

**Benefits:**
- Drop-in replacement for existing OpenAI clients
- Gradual migration path from cloud to local
- Standard tooling compatibility (SDKs, frameworks)

### 5.2 External Service Integration

**LLM Provider Integration:**
- **Primary**: OpenAI API (gpt-4o-mini default)
- **Extensible**: Plugin architecture for other providers
- **Fallback Strategies**: Multiple model support with graceful degradation

**Tool Integration Patterns:**
- **Search Tools**: Vector, graph, hybrid search implementations
- **Document Tools**: List, retrieve, analyze document collections
- **Future Extensions**: Web search (SearXNG), workflows (n8n)

## 6. Performance Architecture

### 6.1 Performance Characteristics

**Latency Targets:**
- Health checks: < 1s
- Model discovery: < 2s  
- First message: < 5s
- Subsequent messages: < 3s
- First streaming token: < 2s

**Throughput Capabilities:**
- Concurrent users: ~10-50 (depending on hardware)
- Requests per second: ~5-20 (LLM-bound)
- Document ingestion: ~100-1000 docs/hour

**Resource Requirements:**
- **Minimal Deployment**: 2GB RAM, 2 CPU cores
- **Standard Deployment**: 4GB RAM, 4 CPU cores
- **Full Deployment**: 6-8GB RAM, 6+ CPU cores

### 6.2 Scaling Architecture

**Vertical Scaling (Current):**
- Increase container resource limits
- Optimize database queries and indexes
- Implement caching strategies

**Horizontal Scaling (Future):**
- Load balancer configuration ready (Caddy)
- Stateless agent design enables replication
- Database clustering supported (PostgreSQL + Neo4j)

**Bottleneck Analysis:**
1. **LLM API calls** - Rate limits and latency from OpenAI
2. **Vector search** - Query complexity and corpus size
3. **Memory usage** - Large document collections and embeddings

## 7. Security Architecture

### 7.1 Security Boundaries

```
Internet ─── Caddy (TLS) ─── Internal Network ─── Services
   │            │                    │               │
   │            ▼                    │               ▼
   │      Rate Limiting              │         Database
   │      Request Filtering          │         Access Control
   │                                 │
   └─── Authentication (future) ─────┘
```

**Current Security Model:**
- **Network Isolation** - Internal Docker networking
- **TLS Termination** - HTTPS at proxy layer
- **API Key Protection** - OpenAI keys in environment variables
- **No Authentication** - Demo mode only (Phase 1 requirement)

**Production Security Roadmap:**
- User authentication and session management
- Role-based access control (RBAC)
- API rate limiting and quota management
- Audit logging and compliance features

### 7.2 Data Security

**Sensitive Data Handling:**
- **API Keys** - Environment variables, not in code
- **User Data** - Local storage, no external transmission
- **Conversation History** - Encrypted at rest (future)
- **Document Content** - Access-controlled retrieval

## 8. Reliability & Resilience Architecture

### 8.1 Failure Domains

**Service Independence:**
- Agent service can operate with degraded search
- OpenWebUI falls back to basic functionality
- Database failures don't crash the system
- External API failures handled gracefully

**Recovery Patterns:**
- **Health Checks** - Container-level monitoring
- **Graceful Degradation** - Reduced functionality vs total failure
- **Circuit Breakers** - Prevent cascade failures
- **Retry Logic** - Transient failure recovery

### 8.2 Data Consistency

**Consistency Models:**
- **Strong Consistency** - Within PostgreSQL transactions
- **Eventual Consistency** - Between vector and graph storage
- **Session Consistency** - Within user sessions

**Backup & Recovery:**
- **Database Backups** - Automated PostgreSQL dumps
- **Volume Persistence** - Docker volume backups
- **Configuration Backups** - Environment and setup reproducibility

## 9. Development Architecture

### 9.1 Code Organization

**Modular Design:**
- **Agent Package** - Core intelligence and API
- **Ingestion Package** - Document processing pipeline
- **Tools Package** - Search and retrieval implementations
- **Infrastructure** - Docker, networking, deployment

**Testing Strategy:**
- **Unit Tests** - Individual component testing
- **Integration Tests** - Service interaction testing
- **System Tests** - End-to-end workflow validation
- **Performance Tests** - Load and stress testing

### 9.2 Development Workflows

**Local Development:**
- **Hot Reload** - FastAPI development server
- **Container Development** - Docker-compose for full system
- **Database Access** - Direct SQL and graph query tools
- **Debug Modes** - Verbose logging and error reporting

## 10. Architecture Evolution (Temporal)

### 10.1 Phase Evolution

**Phase 1 (Completed)** - Stateless OpenWebUI integration
**Phase 2 (Completed)** - CLI agent with RAG capabilities  
**Phase 3 (Completed)** - Dockerization and streaming
**Phase 4 (Completed)** - Test infrastructure
**Phase 5 (Completed)** - Test reality alignment and configuration system

**Phase 6 (Next)** - Multi-agent orchestration with MCP
**Phase 7 (Future)** - Memory-enabled with conversation persistence
**Phase 8 (Future)** - Cloud deployment options

### 10.2 Technical Debt & Refactoring

**Current Technical Debt:**
- Port mapping inconsistencies in documentation
- Hardcoded model references in tests (resolved via configuration system)
- Manual service discovery vs automatic registration

**Refactoring Priorities:**
1. **Service Discovery** - Automatic service registration and health monitoring
2. **Configuration Management** - Centralized configuration with validation
3. **Observability** - Structured logging and metrics collection
4. **Error Handling** - Consistent error propagation and user messaging

## 11. Architecture Decision Records

### 11.1 Key Design Decisions

**Hybrid RAG Architecture**
- **Decision**: Combine vector similarity with knowledge graph relationships
- **Rationale**: Better context understanding and factual grounding
- **Trade-offs**: Increased complexity, dual storage overhead

**OpenAI Compatibility Layer**  
- **Decision**: Implement OpenAI-compatible API endpoints
- **Rationale**: Enable existing tools and gradual migration
- **Trade-offs**: Additional translation overhead, API design constraints

**Stateless-First Design**
- **Decision**: System works without database persistence
- **Rationale**: Demo-friendly, easier deployment, reduced complexity
- **Trade-offs**: Limited conversation continuity in stateless mode

**Docker-Based Deployment**
- **Decision**: Container orchestration with profiles
- **Rationale**: Consistent environments, scalable deployment, service isolation
- **Trade-offs**: Container overhead, complexity for simple deployments

---

**This architecture enables a sophisticated AI research platform that combines the best of retrieval-augmented generation with agentic reasoning, while maintaining flexibility for different deployment scenarios and future evolution.**