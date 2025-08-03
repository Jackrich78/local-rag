# 🔄 Daily Operations SOP - Agentic RAG Knowledge Graph System

*Last Updated: 2025-08-03*

---

## 📋 Quick Reference

| Action | Command | Time | Notes |
|--------|---------|------|-------|
| **Start System** | `make up` | ~60s | Wait for all services |
| **Stop System** | `make down` | ~15s | Graceful shutdown |
| **Check Status** | `make status` | ~2s | See all container health |
| **Chat with Agent** | See Chat Section | ~5s | Interactive terminal |
| **Emergency Stop** | `docker stop $(docker ps -aq)` | ~10s | Force stop all |

---

## 🌅 **STARTUP PROCEDURE (Morning/Session Start)**

### **Step 1: Verify Prerequisites**
```bash
# Navigate to project root
cd /Users/jack/Developer/local-RAG

# Verify Docker is running
docker ps
# Should show: CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES

# Check disk space (need ~5GB free)
df -h
```

### **Step 2: Start All Services**
```bash
# Start the complete stack
make up

# Expected output:
# 🟢 Starting Local RAG services...
# ⏱️  Services started! Access points:
#   🤖 Agent API:    http://localhost:8009
#   📊 Supabase:     http://localhost:8005
#   🕸️  Neo4j:       http://localhost:8008
#   📝 N8N:          http://localhost:8001
# ⚠️  Wait ~60s for all services to be ready
```

### **Step 3: Verify System Health (Wait 60 seconds)**
```bash
# Check all container status
make status

# Verify health endpoints
make health

# Expected: All services showing "Up" or "healthy"
# ✅ Agent Health: healthy
# ✅ Database connections working
```

### **Step 4: Quick System Test**
```bash
# Navigate to docker directory for manual testing
cd local-ai-packaged

# Test agent chat functionality
docker-compose exec agent curl -X POST http://localhost:8058/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Are you working?", "session_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Expected: JSON response with agent greeting
```

### **Step 5: Access Web Interfaces (Optional)**
```bash
# Open in browser:
open http://localhost:8005    # Supabase Studio
open http://localhost:8008    # Neo4j Browser
open http://localhost:8001    # N8N Workflow Manager
```

---

## 💬 **CHAT WITH AGENT (Primary Usage)**

### **Method 1: Direct API Call (Current)**
```bash
# Navigate to docker directory
cd /Users/jack/Developer/local-RAG/local-ai-packaged

# Interactive chat (replace message as needed)
docker-compose exec agent curl -X POST http://localhost:8058/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are Google'\''s AI initiatives?", "session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

### **Method 2: Health Check**
```bash
# Check if agent is responding
docker-compose exec agent curl -f http://localhost:8058/health
```

### **Method 3: View Agent Logs**
```bash
# Monitor agent activity
make agent-logs
# Press Ctrl+C to stop following logs
```

---

## 📊 **DATA OPERATIONS**

### **Document Ingestion**
```bash
# Navigate to docker directory
cd /Users/jack/Developer/local-RAG/local-ai-packaged

# Ingest test documents
docker-compose exec agent python -m ingestion.ingest -d test_docs --verbose

# Expected output:
# ✅ Documents processed: 2
# ✅ Total chunks created: 7  
# ✅ Total entities extracted: 46
# ✅ Total errors: 0
```

### **Database Inspection**
```bash
# Check Supabase database
open http://localhost:8005
# Login with: supabase / password (check .env file)

# Check Neo4j graph database
open http://localhost:8008
# Login with: neo4j / G?kZt?7[LC{Ym3tI}YKfEk (check .env file)
```

---

## 🌙 **SHUTDOWN PROCEDURE (Evening/Session End)**

### **Step 1: Save Work & Commit**
```bash
# Navigate to project root
cd /Users/jack/Developer/local-RAG

# Check git status
git status

# Add and commit any changes
git add .
git commit -m "Daily work: [describe what you accomplished]"

# Push to remote branch
git push origin [your-branch-name]
```

### **Step 2: Export Important Data (Optional)**
```bash
# Export recent agent conversations (if needed)
# Note: Currently stored in database, survives container restarts

# Export any custom documents you added
# (test_docs and big_tech_docs are already in git)
```

### **Step 3: Graceful Service Shutdown**
```bash
# Stop all services gracefully
make down

# Expected output:
# 🔴 Stopping Local RAG services...
# 🟢 Services stopped

# Verify all containers stopped
docker ps
# Should show: empty or unrelated containers only
```

### **Step 4: System Cleanup (Weekly)**
```bash
# Clean up Docker resources (run weekly)
docker system prune -f

# Remove unused volumes (run monthly)
docker volume prune -f
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: Agent Not Responding**
```bash
# Check agent container status
make status | grep agent

# If container restarting, check logs
make agent-logs

# Common fix: Restart just the agent
cd local-ai-packaged
docker-compose restart agent
sleep 30
make health
```

### **Problem: Database Connection Failed**
```bash
# Check database containers
make status | grep -E "(supabase-db|neo4j)"

# If databases unhealthy, restart them
cd local-ai-packaged
docker-compose restart supabase-db neo4j
sleep 60
make health
```

### **Problem: "No Configuration File" Error**
```bash
# Always run docker-compose from correct directory
cd /Users/jack/Developer/local-RAG/local-ai-packaged

# Or use Makefile from root
cd /Users/jack/Developer/local-RAG
make [command]
```

### **Problem: Port Conflicts**
```bash
# Check what's using ports
lsof -i :8005 -i :8008 -i :8009

# Kill conflicting processes if needed
sudo kill -9 [PID]
```

### **Emergency Reset**
```bash
# Nuclear option - stop everything and clean up
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker volume prune -f
make up
```

---

## 🔧 **CONFIGURATION FILES**

### **Critical Files You MUST NOT Lose:**
- `/Users/jack/Developer/local-RAG/local-ai-packaged/.env` (contains API keys)
- `/Users/jack/Developer/local-RAG/local-ai-packaged/docker-compose.yml`
- `/Users/jack/Developer/local-RAG/agentic-rag-knowledge-graph/` (entire directory)

### **Environment Variables Check:**
```bash
# Verify OpenAI API key is set
cd /Users/jack/Developer/local-RAG/local-ai-packaged
grep "OPENAI_API_KEY=" .env

# Should show: OPENAI_API_KEY=sk-proj-[your-key]
# If empty, add your key before starting
```

---

## 📈 **PERFORMANCE EXPECTATIONS**

### **Normal Startup Times:**
- System startup: ~60 seconds
- Agent first response: ~5-10 seconds  
- Database queries: ~1-3 seconds
- Document ingestion: ~1-2 minutes per document

### **Resource Usage:**
- RAM: ~8-12 GB total
- Disk: ~5 GB Docker volumes
- CPU: Moderate during ingestion, low during chat

### **Success Indicators:**
- ✅ All containers show "healthy" status
- ✅ Agent responds to chat within 10 seconds
- ✅ Health endpoint returns HTTP 200
- ✅ No error messages in logs

---

## 🎯 **DAILY WORKFLOW EXAMPLES**

### **Research Session:**
1. `make up` (wait 60s)
2. `make health` (verify ready)
3. Chat with agent about your research questions
4. Ingest new documents if needed
5. `git commit` any code changes
6. `make down` when done

### **Development Session:**
1. `make up` (wait 60s)  
2. Make code changes in `agentic-rag-knowledge-graph/`
3. `make build` (rebuild agent container)
4. `docker-compose restart agent` (test changes)
5. Test functionality
6. Commit and push changes
7. `make down` when done

---

## 📞 **SUPPORT & RECOVERY**

### **If System Won't Start:**
1. Check Docker Desktop is running
2. Check available disk space (need 5GB+)
3. Try `make clean` then `make up`
4. Check `.env` file has OpenAI API key
5. Restart Docker Desktop if needed

### **If Data Seems Lost:**
- **Documents**: Check `test_docs/` and `big_tech_docs/` folders
- **Conversations**: Stored in database, survives restarts
- **Configuration**: All in git, can be restored

### **Best Practices:**
- ✅ Always commit changes before shutdown
- ✅ Use `make down` instead of force-stopping
- ✅ Wait full 60s after `make up` before testing
- ✅ Check logs if something seems wrong
- ✅ Keep OpenAI API key secure and valid

---

*💡 **Pro Tip**: Bookmark this file and keep it open in a tab while working with the system!*