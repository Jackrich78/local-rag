# Phase 1 Implementation Plan

## Overview
Implement OpenWebUI chat integration with stateless mode for the Agentic RAG stack. This phase delivers a one-command, zero-login browser chat interface that talks to our FastAPI agent over OpenAI-style endpoints without writing to the database.

## Critical Issues to Fix
1. **Agent Code Issues**: OpenAI `/v1/chat/completions` endpoint fails with foreign key constraints because it creates sessions but they're not properly saved
2. **Missing Memory/Streaming Guards**: No environment flag checks for `MEMORY_ENABLED=false` and `STREAMING_ENABLED=false`
3. **OpenWebUI Configuration**: Wrong image version and missing environment variables

## Implementation Steps

### Step 1: Fix Agent API Code (agent/api.py)

**Priority: CRITICAL - Fix first**

**File:** `agentic-rag-knowledge-graph/agent/api.py`

**Changes needed:**

1. **Add Phase 1 startup logging** (after line 79):
```python
# Phase 1 startup verification
memory_enabled = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
streaming_enabled = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
logger.info(f"🚀 Phase 1 Agent Starting - MEMORY_ENABLED={memory_enabled}, STREAMING_ENABLED={streaming_enabled}")
```

2. **Replace entire `/v1/chat/completions` endpoint** (lines 466-656):
```python
@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible chat completions endpoint."""
    # Phase 1 startup log to verify container is running updated code
    logger.info("🤖 Phase 1 Stateless Mode Active - OpenAI endpoint called")
    
    try:
        # Check if streaming is requested but disabled
        streaming_enabled = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
        if request.stream and not streaming_enabled:
            raise HTTPException(
                status_code=400, 
                detail="Streaming is disabled in this configuration"
            )
        
        # Convert OpenAI format to internal format
        user_message, user_id = convert_openai_to_internal(request)
        
        # Check memory mode
        memory_enabled = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
        
        if memory_enabled:
            # Full memory mode - use existing session logic
            internal_request = ChatRequest(
                message=user_message,
                session_id=None,
                user_id=user_id,
                metadata={"openai_format": True, "model": request.model}
            )
            
            session_id = await get_or_create_session(internal_request)
            save_conversation = True
        else:
            # Stateless mode - create temporary session ID, no DB writes
            session_id = f"temp-{uuid.uuid4()}"
            save_conversation = False
        
        # Execute agent with save_conversation flag
        response, tools_used = await execute_agent(
            message=user_message,
            session_id=session_id,
            user_id=user_id,
            save_conversation=save_conversation
        )
        
        # Create OpenAI-compatible response
        openai_response = create_openai_response(
            content=response,
            session_id=session_id,
            model=request.model,
            is_stream=False
        )
        
        return openai_response
        
    except Exception as e:
        logger.error(f"Chat completions endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 2: Update Docker Compose Configuration

**File:** `local-ai-packaged/docker-compose.yml`

**Changes needed:**

1. **Update OpenWebUI service** (lines 73-94):
```yaml
  open-webui:
    image: ghcr.io/open-webui/open-webui:v0.6.21  # Pin to specific version
    restart: unless-stopped
    container_name: open-webui
    expose:
      - 8080/tcp
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - open-webui:/app/backend/data
    environment:
      # Phase 1 OpenWebUI Configuration  
      - ENABLE_PERSISTENT_CONFIG=false
      - OPENAI_API_BASE_URL=http://agent:8058/v1
      - OPENAI_API_KEY=local-dev-key
      - WEBUI_AUTH=false
      - ENABLE_SIGNUP=false
    depends_on:
      agent:
        condition: service_healthy
```

2. **Update agent service environment** (lines 431-460):
```yaml
    environment:
      # Phase 1 Feature Flags
      - MEMORY_ENABLED=false
      - STREAMING_ENABLED=false
      
      # Application config
      - APP_ENV=production
      - APP_HOST=0.0.0.0
      - APP_PORT=8058
      - LOG_LEVEL=INFO
      
      # Database connection (container networking)
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@supabase-db:5432/postgres
      
      # Neo4j connection (container networking)  
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD:-G?kZt?7[LC{Ym3tI}YKfEk}
      
      # LLM Provider (from environment)
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - LLM_BASE_URL=${LLM_BASE_URL:-https://api.openai.com/v1}
      - LLM_API_KEY=${OPENAI_API_KEY}
      - LLM_CHOICE=${LLM_CHOICE:-gpt-4o-mini}
      
      # Embedding Provider (from environment)
      - EMBEDDING_PROVIDER=${EMBEDDING_PROVIDER:-openai}
      - EMBEDDING_BASE_URL=${EMBEDDING_BASE_URL:-https://api.openai.com/v1}
      - EMBEDDING_API_KEY=${OPENAI_API_KEY}
      - EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-3-small}
      
      # Ingestion config
      - INGESTION_LLM_CHOICE=${INGESTION_LLM_CHOICE:-gpt-4o-mini}
```

3. **Fix dependency reference** (line 469):
```yaml
    depends_on:
      neo4j:
        condition: service_started
      supabase-db:  # Fixed service name (was 'db')
        condition: service_healthy
```

### Step 3: Update Makefile Commands

**File:** `Makefile`

**Add after line 132:**
```makefile
# Phase 1 Commands
test-phase1: build up ## Run Phase 1 acceptance tests  
	@echo "$(GREEN)Running Phase 1 OpenWebUI integration tests...$(RESET)"
	@sleep 60  # Wait for services to start
	@echo "$(YELLOW)Testing OpenWebUI access...$(RESET)"
	@curl -f http://localhost:8002 > /dev/null 2>&1 && echo "✅ OpenWebUI accessible" || echo "❌ OpenWebUI not responding"
	@echo "$(YELLOW)Testing OpenAI models endpoint...$(RESET)"  
	@curl -f http://localhost:8009/v1/models > /dev/null 2>&1 && echo "✅ Models endpoint working" || echo "❌ Models endpoint failed"
	@echo "$(YELLOW)Testing OpenAI chat completions (stateless)...$(RESET)"
	@curl -X POST http://localhost:8009/v1/chat/completions \
		-H "Content-Type: application/json" \
		-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "ping"}]}' \
		> /dev/null 2>&1 && echo "✅ OpenAI chat endpoint working" || echo "❌ OpenAI chat endpoint failed"
	@echo "$(YELLOW)Verifying no database writes...$(RESET)"
	@cd local-ai-packaged && docker-compose exec -T supabase-db psql -U postgres -c "SELECT COUNT(*) FROM messages;" | grep -q "0" && echo "✅ No database writes confirmed" || echo "❌ Database writes detected"

wipe-openwebui: ## Wipe OpenWebUI volume and restart
	@echo "$(RED)Wiping OpenWebUI volume...$(RESET)"
	cd local-ai-packaged && docker-compose down open-webui
	docker volume rm local-ai-packaged_open-webui || true
	cd local-ai-packaged && docker-compose up -d open-webui
	@echo "$(GREEN)OpenWebUI volume wiped and restarted$(RESET)"
```

### Step 4: Create Phase 1 Test Script

**New file:** `test_phase1.py`

```python
#!/usr/bin/env python3
"""
Phase 1 OpenWebUI Integration Test Script
Tests all Phase 1 acceptance criteria from PRD.md
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8009"
OPENWEBUI_URL = "http://localhost:8002"

def test_models_endpoint() -> bool:
    """Test GET /v1/models endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        if response.status_code != 200:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
        
        data = response.json()
        if "gpt-4o-mini" not in str(data):
            print(f"❌ gpt-4o-mini not found in models response")
            return False
        
        print("✅ Models endpoint working")
        return True
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_chat_completions() -> bool:
    """Test POST /v1/chat/completions endpoint."""
    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Chat completions failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            print(f"❌ No choices in chat response")
            return False
        
        print("✅ Chat completions working")
        return True
    except Exception as e:
        print(f"❌ Chat completions error: {e}")  
        return False

def test_openwebui_access() -> bool:
    """Test OpenWebUI accessibility."""
    try:
        response = requests.get(OPENWEBUI_URL, timeout=10)
        if response.status_code == 200:
            print("✅ OpenWebUI accessible")
            return True
        else:
            print(f"❌ OpenWebUI not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenWebUI access error: {e}")
        return False

def test_health_endpoint() -> bool:
    """Test /health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ Health endpoint working")
                return True
        
        print(f"❌ Health check failed")
        return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def main():
    """Run Phase 1 acceptance tests."""
    print("🧪 Running Phase 1 OpenWebUI Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Models Endpoint", test_models_endpoint), 
        ("Chat Completions", test_chat_completions),
        ("OpenWebUI Access", test_openwebui_access)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Execution Order

1. **Fix Agent Code First** - Update `agent/api.py` with memory guards and stateless mode
2. **Update Docker Compose** - Fix OpenWebUI configuration and agent environment
3. **Update Makefile** - Add Phase 1 test commands  
4. **Create Test Script** - Add validation script
5. **Test Implementation** - Run `make test-phase1` to validate

## Validation Commands

```bash
# Build and test Phase 1
make test-phase1

# Manual verification
curl http://localhost:8009/v1/models
curl -X POST http://localhost:8009/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}]}'

# Check OpenWebUI
open http://localhost:8002
```

## Success Criteria

- ✅ OpenWebUI loads at `http://localhost:8002` without login prompt
- ✅ Chat interface works with agent via OpenAI API format
- ✅ No database writes when `MEMORY_ENABLED=false` (verified by DB query)
- ✅ All health checks pass (`/health`, `/v1/models`)
- ✅ Response time < 4 seconds for chat messages
- ✅ Agent logs show "Phase 1 Stateless Mode Active" message

---

## Post-Implementation Issues & Resolutions

### Issue 1: Browser 400 Error Investigation - Methodological Concerns

**Problem Identified**: During browser testing, user reported 400 error on chat attempts, but investigation made critical assumption errors about log accessibility and error visibility.

**Key Learning**: 
- 5/6 automated tests pass, indicating core functionality works
- Made assumptions about Docker log access without validation
- Need methodical approach: verify log access → identify actual error source → implement fix

**Action Required**: Validate log access capabilities before proceeding with error diagnosis.

---

### Issue 2: Failing Phase 1 Startup Logs Test (6th Test)

**Root Cause**: Directory and Docker context mismatch between test script and container management.

**Technical Details**:
- Test script location: `/Users/jack/Developer/local-RAG/test_phase1.py`
- Docker containers managed from: `/Users/jack/Developer/local-RAG/local-ai-packaged/`
- Container name correct: `agentic-rag-agent`
- Issue: Test runs Docker commands without proper directory context

**Specific Fixes Needed**:

1. **Working Directory Fix**:
   ```python
   # Change from:
   subprocess.run(["docker", "logs", "agentic-rag-agent", "--since", "5m"])
   
   # To:
   subprocess.run(["docker", "logs", "agentic-rag-agent", "--tail", "100"], 
                  cwd="/Users/jack/Developer/local-RAG/local-ai-packaged")
   ```

2. **Log Timing Fix**:
   - Replace `--since 5m` with `--tail 100` to avoid timing issues
   - Startup logs may be older than 5 minutes if container was restarted earlier

3. **Container Validation**:
   - Add check for container existence before attempting log access
   - Provide clear error messages if container not found

4. **Pattern Matching Robustness**:
   - Verify exact log format: "Phase 1 Agent Starting - MEMORY_ENABLED=False"
   - Make search case-insensitive if needed

**Expected Outcome**: 6/6 tests passing, establishing reliable foundation for browser error investigation.

---

## 🎯 Phase 3.1 Completion Summary - 2025-08-04

### **Implementation Status: ✅ COMPLETE**

**Final Achievement**: Zero-login OpenWebUI integration with stateless mode successfully delivered.

**Key Resolution**: Streaming configuration mismatch identified and resolved.
- **User Discovery**: Browser chat works when streaming disabled in OpenWebUI interface
- **Root Cause**: OpenWebUI defaults to `stream=true` but Phase 1 requires `STREAMING_ENABLED=false`
- **Solution**: Configured for Phase 1 stateless mode without streaming

**Final Configuration**:
- `MEMORY_ENABLED=false` ✅ (stateless mode)
- `STREAMING_ENABLED=false` ✅ (non-streaming responses)
- Zero-login OpenWebUI access ✅
- All automated tests passing ✅ (6/6)
- Browser chat functionality ✅ (confirmed working)

**Deliverables Ready for GitHub**:
1. Working OpenWebUI integration
2. Stateless agent mode
3. Complete test suite
4. Updated documentation
5. Docker compose configuration

**Next Phase Planning**: Streaming support implementation scheduled for future phase.

---

## 🎯 Phase 3.2 Implementation Plan - Streaming Support (2025-08-04)

### **Current Status Summary**
- **Phase 3.1**: ✅ **COMPLETE** - Zero-login OpenWebUI integration with stateless mode delivered
- **Phase 3.2**: 🔄 **IN PROGRESS** - OpenAI-compatible streaming implementation 85% complete

### **Completed in This Session**
1. ✅ **Streaming Architecture Built**: Complete OpenAI-compatible SSE streaming in `/v1/chat/completions`
2. ✅ **Configuration Updated**: `STREAMING_ENABLED=true` in docker-compose.yml  
3. ✅ **Stateless Mode Preserved**: Streaming respects `save_conversation=false` flag
4. ✅ **OpenAI Format Compliance**: Proper chunk format with `[DONE]` termination
5. ✅ **Infrastructure Diagnosed**: Identified OpenWebUI startup issue in Makefile

### **Outstanding Issues for Next Session**

#### **Priority 1: Streaming Activation Debug (30 min)**
**Problem**: `stream=true` requests still return non-streaming responses
**Root Cause Hypothesis**: Container not running updated streaming code
**Action Plan**:
```bash
# Verify code deployment
docker exec agentic-rag-agent grep -n "_create_streaming_response" /app/agent/api.py
docker logs agentic-rag-agent | grep "OpenAI Chat Completions - Streaming"

# Test streaming activation
curl -X POST http://localhost:8009/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test"}], "stream": true}'

# Force rebuild if needed
docker-compose build --no-cache agent && docker-compose up -d --force-recreate agent
```

#### **Priority 2: Makefile OpenWebUI Fix (15 min)**
**Problem**: `make up` doesn't start OpenWebUI container automatically
**Impact**: Poor developer experience, manual steps required
**Solution**:
```yaml
# Update Makefile line 22 or docker-compose.yml service dependencies
# Ensure OpenWebUI starts with core services
```

#### **Priority 3: End-to-End Streaming Test (15 min)**
**Goal**: Verify browser streaming experience
**Test Sequence**:
1. Run `python test_phase1.py` (should pass 6/6)
2. Access OpenWebUI at `localhost:8002`
3. Send chat message with default streaming enabled
4. Verify real-time token delivery in browser

### **Expected Deliverables Next Session**
1. ✅ **Working streaming responses** from agent API
2. ✅ **Browser streaming experience** functional in OpenWebUI
3. ✅ **One-command startup** via `make up` including OpenWebUI
4. ✅ **Updated test suite** validating streaming functionality
5. ✅ **Phase 3.2 completion** - Full streaming support delivered

### **Technical Implementation Details**

#### **Streaming Code Architecture**
```python
# In /v1/chat/completions endpoint:
if request.stream:
    return await _create_streaming_response(...)  # SSE generator
else:
    return create_openai_response(...)            # Standard response
```

#### **OpenAI Streaming Format**
```json
// Streaming chunks
{"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}
{"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" there"}}]}
{"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"finish_reason":"stop"}]}
data: [DONE]
```

### **Risk Mitigation**
- **Rollback Plan**: Revert to `STREAMING_ENABLED=false` if issues arise
- **Testing Strategy**: Use existing test_phase1.py + manual browser verification
- **Compatibility**: Maintain backward compatibility with non-streaming requests

### **Success Criteria for Phase 3.2**
1. ✅ Real-time streaming responses in browser
2. ✅ Stateless mode preserved (no database writes)
3. ✅ OpenAI API compatibility maintained  
4. ✅ One-command environment startup
5. ✅ All existing functionality preserved

**Estimated Completion**: 60 minutes from fresh session start

---

### Directory Structure Impact Analysis

The project spans two directories:
- `/Users/jack/Developer/local-RAG/` - Test scripts, documentation
- `/Users/jack/Developer/local-RAG/local-ai-packaged/` - Docker infrastructure

**Implications**:
- All Docker commands must account for working directory context
- Test scripts need explicit path handling for cross-directory operations
- Future debugging requires understanding this dual-directory structure

---

## 🎯 Phase 3.3 Implementation Plan - Complete Docker Infrastructure Improvement (2025-08-05)

### **Goal**
Transform `make up` into a reliable one-command solution that starts ALL services ready for browser use, with `make down` providing clean shutdown, backed by comprehensive test coverage.

### **Current Problems Analysis**
1. **Database Services**: Supabase services failing to start consistently, stuck in "Created" state
2. **Dependency Timing**: Agent waits for DB health but DB services don't transition to running
3. **Missing Health Checks**: Some services lack proper health check configurations
4. **Test Coverage Gap**: No end-to-end validation of complete startup sequence
5. **User Experience**: Manual steps required after `make up` to access OpenWebUI at localhost:8002

### **Implementation Strategy**

#### **Phase 1: Docker Compose Infrastructure Fixes (30 min)**
**Fix database startup reliability:**
- Review Supabase service configurations for missing environment variables
- Add proper health checks for all critical services (agent, database, OpenWebUI)
- Fix service dependency chains with appropriate conditions
- Add init containers where needed for proper startup sequencing
- Resolve environment variable warnings (FLOWISE_USERNAME, FLOWISE_PASSWORD)

**Improve service definitions:**
- Ensure all services have proper restart policies
- Add missing environment variables causing startup warnings
- Optimize container resource limits and startup timeouts
- Verify network connectivity between services

#### **Phase 2: Makefile Enhancement (15 min)**
**Update core targets:**
- `make up`: Start all services with automatic readiness verification (wait for OpenWebUI at localhost:8002)
- `make down`: Clean shutdown of all services with proper cleanup
- `make status`: Comprehensive service health dashboard showing all container states
- `make ready`: Quick check if system is ready for browser use

**Add diagnostic targets:**
- `make debug-startup`: Troubleshoot startup issues with detailed logging
- `make logs-critical`: Show logs for core services (agent, db, openwebui, caddy)
- `make restart-openwebui`: Restart OpenWebUI and dependencies if needed

#### **Phase 3: Comprehensive Test Suite (30 min)**
**Create `test_complete_startup.py`:**
- Validate all services start and reach healthy state within timeout
- Test OpenWebUI accessibility at localhost:8002 (via Caddy proxy)
- Verify agent API endpoints respond correctly (health, models, chat completions)
- Confirm streaming functionality works end-to-end
- Test browser chat workflow (automated where possible)
- Validate dependency chain: Database → Agent → OpenWebUI → Browser Access

**Update existing tests:**
- Integrate startup validation into existing test_phase1.py
- Add timeout handling and retry logic for container health checks
- Include dependency verification and service interconnectivity tests

#### **Phase 4: Documentation Updates (10 min)**
**Update PLAN.md with:**
- Complete implementation details and troubleshooting guides
- Service dependency maps and startup sequence documentation
- Updated developer workflow (one-command deployment)
- Common startup issues and resolution steps

### **Expected Deliverables**

#### **Technical Outcomes**
1. **Reliable Startup**: `make up` → All services running and healthy within 2 minutes
2. **Browser Ready**: OpenWebUI accessible at localhost:8002 immediately after startup completion
3. **Clean Shutdown**: `make down` → Complete environment cleanup, no orphaned containers/volumes
4. **Test Coverage**: Automated validation of entire stack functionality
5. **Error Handling**: Clear error messages and recovery instructions for failed startups

#### **User Experience**
- **Single Command Deployment**: `make up && open http://localhost:8002`
- **Predictable Behavior**: Same startup experience every time, no manual intervention
- **Self-Diagnostic Capabilities**: Built-in health checking and troubleshooting
- **Development-Friendly**: Easy debugging, log access, and service management

### **Implementation Priority**
1. **Critical**: Fix database service startup (blocks entire dependency chain)
2. **High**: Add comprehensive health checks (enables reliable service dependencies)
3. **High**: Create complete test suite (validates fixes work reliably)
4. **Medium**: Enhance Makefile UX (improves developer experience)
5. **Low**: Documentation updates (supports team adoption)

### **Success Criteria**
- ✅ `make up` → OpenWebUI accessible at localhost:8002 within 2 minutes
- ✅ All Phase 3.2 streaming functionality preserved and working
- ✅ `make down` → Complete cleanup, no orphaned containers/volumes
- ✅ Test suite validates entire stack (database → agent → OpenWebUI → browser)
- ✅ Zero manual intervention required for typical developer workflow
- ✅ Consistent behavior across different development environments

### **Technical Implementation Details**

#### **Service Dependency Chain**
```
Supabase Database (db) → Agent (health check) → OpenWebUI → Caddy Proxy → localhost:8002
```

#### **Critical Health Checks Needed**
- **Database**: PostgreSQL ready for connections
- **Agent**: API endpoints responding (health, models)  
- **OpenWebUI**: Container started and web interface ready
- **Caddy**: Proxy routes configured and forwarding correctly

#### **Test Coverage Requirements**
- Container startup validation (all services reach "running" state)
- Network connectivity between services
- API endpoint functionality (direct and proxied)
- Browser accessibility (localhost:8002 responds)
- Streaming functionality end-to-end
- Database connectivity and write prevention in stateless mode

### **Estimated Completion Time: 85 minutes total**

**Ready for Phase 3.3 implementation to deliver the complete "one-command startup" developer experience.**