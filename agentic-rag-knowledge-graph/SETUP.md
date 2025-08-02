# Agentic RAG + Knowledge Graph - Complete Setup Guide

## System Overview

This is a complete agentic RAG (Retrieval Augmented Generation) system that combines vector search with knowledge graph capabilities. The system consists of two repositories:

1. **`local-ai-packaged`** - Docker infrastructure (Supabase, Neo4j, n8n, etc.)
2. **`agentic-rag-knowledge-graph`** - Python application with agent and ingestion pipeline

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│                 Docker Infrastructure                    │
│  ┌─────────────────┐        ┌────────────────────┐     │
│  │   Supabase      │        │      Neo4j         │     │
│  │   PostgreSQL    │        │   Knowledge Graph  │     │
│  │   + pgvector    │        │                    │     │
│  └─────────────────┘        └────────────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  Python Application                     │
│  ┌─────────────────┐        ┌────────────────────┐     │
│  │  Pydantic AI    │        │   Ingestion        │     │
│  │    Agent        │        │   Pipeline         │     │
│  └─────────────────┘        └────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Software
- **Docker & Docker Compose** - For infrastructure services
- **Python 3.12+** - Critical requirement (3.10 has numpy compatibility issues)
- **Git** - For cloning repositories
- **OpenAI API Key** - For LLM and embedding services

### System Requirements
- **8GB+ RAM** - For running Docker services + Python application
- **Available Ports**: 7687 (Neo4j), 6543 (PostgreSQL), 3000 (Supabase), 8058 (FastAPI)

## Complete Setup Instructions

### 1. Clone and Setup Docker Infrastructure

```bash
# Navigate to your development directory
cd /path/to/your/dev/directory

# Clone the Docker infrastructure repository
git clone [local-ai-packaged-repo-url] local-ai-packaged
cd local-ai-packaged

# Copy and configure environment file
cp .env.example .env
# Edit .env file with your specific configurations
```

### 2. Start Docker Infrastructure

```bash
# From local-ai-packaged directory
docker-compose up -d

# Verify services are running
docker-compose ps

# Check service logs if needed
docker-compose logs [service-name]
```

**Services Started:**
- Supabase (PostgreSQL + pgvector + admin interface)
- Neo4j (Knowledge graph database)
- n8n (Workflow automation - optional)
- Other supporting services

### 3. Setup Python Application

```bash
# Navigate to parent directory and clone Python app
cd ..
git clone [agentic-rag-knowledge-graph-repo-url] agentic-rag-knowledge-graph
cd agentic-rag-knowledge-graph

# Verify Python version (CRITICAL: Must be 3.12+)
python3 --version
# If you don't have Python 3.12+, install it:
# brew install python  # macOS
# Or use your system's package manager

# Create virtual environment with Python 3.12+
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file in the `agentic-rag-knowledge-graph` directory:

```bash
# Copy template and edit
cp .env.template .env
```

**Key Configuration (edit .env file):**

```bash
############
# Database Configuration (Supabase via Docker)
############
DATABASE_URL=postgresql://postgres.58c98044-7168-488d-9a35-73561194789c:61ead4d7b6d2ca90e598796468484b61@localhost:6543/postgres

############
# Neo4j Configuration (Docker instance)
############
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=G?kZt?7[LC{Ym3tI}YKfEk

############
# LLM Provider Configuration (OpenAI API)
############
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key-here
LLM_CHOICE=gpt-4o-mini

############
# Embedding Configuration (OpenAI API)
############
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=your-openai-api-key-here
EMBEDDING_MODEL=text-embedding-3-small

############
# Application Configuration
############
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8058
```

**⚠️ IMPORTANT:** Replace `your-openai-api-key-here` with your actual OpenAI API key.

### 5. Initialize Database Schema

```bash
# Apply PostgreSQL schema (includes pgvector setup)
# Connect to Supabase and run sql/schema.sql
# Or use your preferred PostgreSQL client
```

## Testing the System

### Test Document Ingestion

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run complete ingestion test (vector + knowledge graph)
OPENAI_API_KEY="your-api-key" python -m ingestion.ingest --documents test_docs --clean --verbose

# Expected output:
# Documents processed: 2
# Total chunks created: 7
# Total entities extracted: 46
# Total graph episodes: 6
# Total errors: 0-1 (minor errors acceptable)
```

### Test Vector-Only Pipeline (Faster)

```bash
# Test just vector processing (skips knowledge graph)
OPENAI_API_KEY="your-api-key" python -m ingestion.ingest --documents test_docs --clean --fast --verbose
```

### Test Agent Interface

**Terminal 1: Start FastAPI Server**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Start the FastAPI server (runs continuously)
python -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8058 (Press CTRL+C to quit)
# INFO: Application startup complete.
```

**Terminal 2: Run CLI Interface**
```bash
# Open a NEW terminal window/tab
cd /Users/jack/Developer/local-RAG/agentic-rag-knowledge-graph
source venv/bin/activate

# Run CLI client (connects to FastAPI server)
python cli.py

# Expected output:
# 🤖 Agentic RAG with Knowledge Graph CLI
# Connected to: http://localhost:8058
```

**Validate Setup:**
```bash
# Check FastAPI is running (in browser or terminal)
curl http://localhost:8058/health
# Or visit: http://localhost:8058/docs
```

## Critical Configuration Discoveries

### 1. PostgreSQL Connection Fix
**Issue:** pgbouncer connection pooling conflicts with asyncpg prepared statements.

**Solution:** Added `statement_cache_size=0` to asyncpg connection in `agent/db_utils.py`:
```python
self.pool = await asyncpg.create_pool(
    self.database_url,
    min_size=5,
    max_size=20,
    statement_cache_size=0  # Disable prepared statements for pgbouncer
)
```

### 2. Vector Dimensions Configuration
**Issue:** OpenAI embeddings use 1536 dimensions, not 768.

**Solution:** Updated `sql/schema.sql`:
```sql
embedding vector(1536),  -- Changed from vector(768)
```

### 3. Python Version Requirement
**Issue:** Python 3.10 incompatible with numpy 2.3.1 and other dependencies.

**Solution:** Use Python 3.12+ and recreate virtual environment:
```bash
deactivate
rm -rf venv
python3 -m venv venv  # Using Python 3.12+
source venv/bin/activate
pip install -r requirements.txt
```

## Operational Commands

### Startup Sequence
```bash
# 1. Start Docker infrastructure
cd local-ai-packaged
docker-compose up -d

# 2. Activate Python environment
cd ../agentic-rag-knowledge-graph
source venv/bin/activate

# 3. Verify services
python test_connections.py
```

### Shutdown Sequence
```bash
# 1. Deactivate Python environment
deactivate

# 2. Stop Docker services
cd ../local-ai-packaged
docker-compose down
```

### Status Checking
```bash
# Check Docker services
docker-compose ps

# Check Python environment
source venv/bin/activate
python --version
pip list | grep -E "(graphiti|pydantic|fastapi)"

# Test database connections
python test_connections.py
```

## Maintenance Procedures

### Adding New Documents
```bash
# 1. Place markdown files in test_docs/ or create new folder
# 2. Run ingestion
OPENAI_API_KEY="your-key" python -m ingestion.ingest --documents your_folder --clean --verbose
```

### Database Management
```bash
# Clean all data (DESTRUCTIVE)
OPENAI_API_KEY="your-key" python -m ingestion.ingest --documents test_docs --clean

# View Supabase admin
# Navigate to http://localhost:3000

# View Neo4j browser
# Navigate to http://localhost:7474
```

### Updating Dependencies
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Troubleshooting Guide

### Common Issues

#### 1. "Connection refused" to Neo4j
**Symptoms:** Neo4j connection errors in logs
**Solution:**
```bash
cd local-ai-packaged
docker-compose restart neo4j
# Wait 30 seconds for startup
docker-compose logs neo4j
```

#### 2. "prepared statement already exists"
**Symptoms:** PostgreSQL errors during ingestion
**Solution:** Already fixed in db_utils.py with `statement_cache_size=0`

#### 3. "numpy version not found"
**Symptoms:** pip install failures
**Solution:** Recreate virtual environment with Python 3.12+

#### 4. OpenAI API errors
**Symptoms:** Authentication or rate limit errors
**Solution:**
- Verify API key in .env file
- Check OpenAI account credits
- Reduce batch sizes in ingestion

#### 5. Port conflicts
**Symptoms:** "Port already in use" errors
**Solution:**
```bash
# Find process using port
lsof -i :7687  # or other port
# Kill process or change port in docker-compose.yml
```

### Debug Commands
```bash
# Check all processes
docker-compose ps

# View logs for specific service
docker-compose logs neo4j
docker-compose logs supabase-db

# Test database connections
python test_connections.py

# Verbose ingestion with full logging
OPENAI_API_KEY="your-key" python -m ingestion.ingest --documents test_docs --verbose
```

## Performance Notes

### System Resources
- **RAM Usage:** 4-6GB for Docker services
- **Processing Time:** ~50-100 seconds per document (including knowledge graph)
- **Storage:** ~100MB for sample documents

### Optimization Options
- Use `--fast` flag to skip knowledge graph building
- Reduce chunk sizes in ingestion config
- Batch process large document sets

## Security Considerations

### Environment Variables
- Never commit `.env` files
- Use different passwords for production
- Rotate OpenAI API keys regularly

### Network Security
- Docker services bind to localhost only
- No external access by default
- Use proper authentication in production

## Success Metrics

When properly configured, you should see:
✅ Docker services running (docker-compose ps)
✅ Python 3.12+ virtual environment
✅ All dependencies installed without errors
✅ Database connections successful
✅ Document ingestion completing with minimal errors
✅ Vector and graph data populated

**Test Success Output:**
```
==================================================
INGESTION SUMMARY
==================================================
Documents processed: 2
Total chunks created: 7
Total entities extracted: 46
Total graph episodes: 6
Total errors: 0-1
Total processing time: ~100 seconds
```

## Next Steps

1. **Test the Agent:** Run `python cli.py` to interact with the system
2. **Add More Documents:** Expand the knowledge base
3. **Customize Prompts:** Modify agent behavior in `agent/prompts.py`
4. **Scale Infrastructure:** Adjust Docker resource limits as needed

## Support

For issues or questions:
1. Check this troubleshooting guide first
2. Review logs: `docker-compose logs [service]`
3. Verify environment configuration
4. Test individual components separately

---

**Last Updated:** [Current Date]
**System Version:** Sprint-0 MVP
**Tested Configuration:** macOS with Python 3.13, Docker Desktop