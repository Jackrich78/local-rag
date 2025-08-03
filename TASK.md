🚧 Phase 3.2 To Do - OpenWebUI Integration & Chat Memory

## Phase 1: OpenAI API Compatibility (Critical Path) ✅
- [x] **P32-1.1** Add `/v1/models` endpoint to agent/api.py
  - ✅ Return: `{"data":[{"id":"agent-model","object":"model"}]}`
  - ✅ Test: `curl localhost:8009/v1/models`

- [x] **P32-1.2** Add `/v1/chat/completions` endpoint with OpenAI schema
  - ✅ Accept: `{"model":"agent-model","messages":[...],"stream":true}`
  - ✅ Convert to internal `ChatRequest` format
  - ✅ Reuse existing `execute_agent()` logic

- [x] **P32-1.3** Implement OpenAI-compatible SSE streaming
  - ✅ Format: `data: {"choices":[{"delta":{"content":"text"}}]}\n\n`
  - ✅ Add termination: `data: [DONE]\n\n`
  - ✅ Preserve session persistence

## Phase 2: Kong Removal & Direct Access (High Impact) ✅
- [x] **P32-2.1** Remove Kong from Supabase docker-compose
  - ✅ Edit: `supabase/docker/docker-compose.yml`
  - ✅ Remove: kong service completely
  - ✅ Keep: supabase-studio, supabase-db, supabase-auth

- [x] **P32-2.2** Update Caddy for direct Studio access
  - ✅ Edit: `Caddyfile`
  - ✅ Change: `{$SUPABASE_HOSTNAME} { reverse_proxy supabase-studio:3000 }`
  - ✅ Test: Studio accessible at localhost:8005 without Kong

## Phase 3: OpenWebUI Integration Validation (Medium Priority) ✅  
- [x] **P32-3.1** Verify model discovery in OpenWebUI
  - ✅ Test: "agent-model" configured in WebUI
  - ✅ Verify: `OPENAI_API_BASE_URL=http://agent:8058/v1`

- [x] **P32-3.2** Add SSE optimization to Caddy
  - ✅ Add: `flush_interval 1s` to agent reverse_proxy
  - ✅ Test: Token streaming latency optimized

## Phase 4: Session Memory Enhancement (Medium Priority) ✅
- [x] **P32-4.1** OpenAI session extraction
  - ✅ Parse conversation from OpenAI messages array
  - ✅ Generate session_id from message history hash
  - ✅ Maintain conversation continuity across WebUI refreshes

- [x] **P32-4.2** Message persistence validation  
  - ✅ Ensure user/assistant pairs save to Supabase
  - ✅ Test: Session management working with OpenAI format

## Phase 5: Automated Testing (Quality Assurance) ✅
- [x] **P32-5.1** Add acceptance criteria tests
  - ✅ T1: `GET /v1/models` returns agent-model
  - ✅ T2: SSE first token < 1s on "ping" message
  - ✅ T3: Session persistence across 2+ messages
  - ✅ T4: Zero Kong containers running
  - ✅ T5: Health endpoint returns 200 OK
  - ✅ Created: `test_phase32.py` comprehensive test suite

- [x] **P32-5.2** Update Makefile health checks
  - ✅ Add Phase 3.2 validation targets: `make validate-phase32`
  - ✅ Test WebUI model availability
  - ✅ Verify streaming performance

## Success Metrics - Status Update
- ⚠️ OpenWebUI loads but has UUID validation errors in chat
- ❌ Chat responses fail with "invalid UUID" error (12 chars vs 32-36 required)
- ❌ Multiple models showing ("agent-model" + "arena-model") - should be one clear model
- ✅ Conversations should persist after page refresh (≥10 turns) - blocked by UUID issue
- ✅ Zero Kong containers: `docker compose ps | grep kong` empty
- ✅ All URLs functional: localhost:8002, 8005, 8009
- ✅ Zero configuration required after `make up`

---

## 🐛 Phase 3.2 Debugging & Resolution Tasks

### **Critical Issues (Blocking OpenWebUI Chat)**
- [ ] **DEBUG-1** Fix UUID validation error in session ID generation
  - Problem: `'oai-1da3b2bf'` (12 chars) vs required 32-36 chars for PostgreSQL UUID
  - Location: `extract_session_id_from_messages()` in agent/api.py:166-170
  - Test: Send chat message in OpenWebUI without UUID error

- [ ] **DEBUG-2** Investigate multiple models in OpenWebUI
  - Problem: Shows "agent-model" AND "arena-model" (unexpected)
  - Check: OpenWebUI container logs, configuration, model discovery
  - Expected: Only "agent-model" should appear

### **Enhancement Issues (UX Improvements)**
- [ ] **DEBUG-3** Update model name to reflect actual LLM
  - Current: "agent-model" 
  - Target: Dynamic name based on LLM_CHOICE env var (e.g., "GPT-4o Mini")
  - Location: `/v1/models` endpoint in agent/api.py

- [ ] **DEBUG-4** Install missing test dependencies
  - Problem: `ModuleNotFoundError: No module named 'aiohttp'`
  - Solution: Add aiohttp to requirements or install locally
  - Test: `make test-phase32` runs without errors

### **Documentation Issues**
- [ ] **DEBUG-5** Document port changes
  - Update: Supabase changed from 8000 → 8005 (due to Kong removal)
  - Files: README.md, PLANNING.md, Makefile help text
  - Ensure: All documentation reflects new direct Studio access

### **Validation & Testing**
- [ ] **DEBUG-6** Test complete OpenWebUI chat workflow
  - Test 1: Send "Hello" message and get response without errors
  - Test 2: Send follow-up message and verify session persistence
  - Test 3: Refresh page and verify conversation history
  - Test 4: Verify streaming works in real-time

### **Root Cause Analysis Needed**
- [ ] **DEBUG-7** Investigate OpenWebUI model discovery mechanism
  - Check: How OpenWebUI detects models from `/v1/models`
  - Check: Why "arena-model" appears (not in our endpoint)
  - Check: OpenWebUI container logs for errors

## Debugging Strategy

### **Step 1: Fix UUID Issue (Critical Path)**
1. Examine current session ID generation logic
2. Update to generate proper UUID format (32-36 chars)
3. Test with simple curl request to `/v1/chat/completions`
4. Verify no UUID errors in agent logs

### **Step 2: Clean Model Discovery**
1. Check OpenWebUI logs: `docker logs open-webui`
2. Verify `/v1/models` endpoint only returns one model
3. Clear OpenWebUI data if needed: `docker volume rm open-webui`
4. Restart OpenWebUI and verify single model

### **Step 3: End-to-End Validation**
1. Test basic chat: "What is 2+2?"
2. Test session persistence: Multiple messages + page refresh
3. Test streaming: Verify real-time token delivery
4. Run acceptance tests: `make test-phase32`

### **Success Criteria**
- ✅ OpenWebUI chat works without UUID errors
- ✅ Only one model shows with clear naming
- ✅ Session persistence works across page refreshes
- ✅ Streaming responses work in real-time
- ✅ All acceptance tests pass

---

## ✅ Phase 3.1 Completed

- T1 ✅ Create Dockerfile for agentic-rag-knowledge-graph  
- T2 ✅ Add agent service to existing docker-compose.yml  
- T3 ✅ Configure container networking (agent ↔ supabase ↔ neo4j)  
- T4 ✅ Set up proper environment variable passing to agent container  
- T5 ✅ Add basic health check endpoint to FastAPI (/health)  
- T6 ✅ Test full containerized stack: docker-compose up -d  
- T7 ✅ Verify agent can connect to databases from inside container  
- T8 ✅ Test ingestion pipeline from containerized agent  
- T9 ✅ Test CLI/API access to containerized agent  
- T10 ✅ Create simple make up target for easy startup

✅ Foundation Complete

- Local Python application working  
- Docker infrastructure (Supabase, Neo4j) working  
- Vector + Knowledge graph functionality working
- Agent containerized and accessible via localhost:8009
- OpenWebUI container running (needs Phase 3.2 integration)
- Neo4j accessible via localhost:8008
- Supabase Studio blocked by Kong (resolved in Phase 3.2)

No Repository Restructuring

- Keep everything where it is
- Just add Dockerfile and update docker-compose.yml  
- Focus on getting containers talking to each other
- Save CI/CD and complex restructuring for later phases

Success Metric

docker-compose up -d starts everything and the agent can answer: "What are Google's AI 
initiatives?" using both vector search and knowledge graph data.
