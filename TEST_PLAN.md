# Pre-Migration Test Plan
## Protecting Functionality During Makefile Infrastructure Improvements

### **Executive Summary**

This test plan ensures that Makefile improvements for reliable one-command startup don't break existing functionality. The focus is on **practical protection against migration risks** rather than comprehensive system testing.

**Current Challenge**: Services aren't running consistently after `make up`, requiring manual intervention to access OpenWebUI at localhost:8002.

**Migration Goal**: Reliable `make up` → all services running → OpenWebUI accessible at localhost:8002 without manual steps.

---

## **Migration Risk Analysis**

### **High Risk Areas** (Must Test)
1. **Service Dependencies**: `depends_on` conditions and health checks
2. **Startup Timing**: Services starting too fast/slow causing failures  
3. **Port Mappings**: Changes affecting localhost:8002 accessibility
4. **Environment Variables**: New configurations breaking existing behavior
5. **Volume Mounts**: Development overrides not working
6. **Container Networking**: Inter-service communication failing

### **Low Risk Areas** (Don't Over-Test)
- RAG pipeline internals (not affected by Makefile changes)
- Database schemas (not changed by container startup)  
- AI model integrations (not affected by service orchestration)
- Advanced streaming features (work if basic API connectivity works)

---

## **Test Enhancement Strategy**

### **Approach: Enhance Existing Tests Minimally**
- Build on existing `test_phase1.py`, `test_phase32.py`, `test_openwebui_config.py`
- Add only tests that protect against Makefile migration risks
- Maintain existing test patterns and structure
- Total new tests: ~12 (focused and practical)

---

## **Phase 1: Establish Current Baseline (30 min)**

### **Step 1.1: Start Current System**
```bash
cd /Users/jack/Developer/local-RAG
make up
# Wait for services to stabilize (~2 minutes)
docker-compose ps  # Document which services start vs fail
```

### **Step 1.2: Run Existing Test Suite**
```bash
python test_phase1.py          # Document: X/6 tests passing
python test_phase32.py         # Document: X/7 tests passing  
python test_openwebui_config.py # Document: X/5 tests passing
```

### **Step 1.3: Manual Validation Checklist**
- [ ] OpenWebUI loads at localhost:8002 (no manual container start needed)
- [ ] Chat message sends and receives response
- [ ] Streaming toggle works (if implemented)
- [ ] Agent API responds at localhost:8009
- [ ] All expected containers in "running" state

### **Result: Baseline Functionality Inventory**
Document exactly what works/fails before any changes.

---

## **Phase 2: Test Enhancement Implementation (45 min)**

### **Enhanced test_phase1.py (15 min)**
**Risk Focus**: Service startup dependencies and timing

**Add 3 New Tests**:
1. `test_all_containers_running()`:
   - Verify all expected containers reach "running" state
   - Check: agent, open-webui, caddy, supabase-db, neo4j, etc.
   - Timeout: 120 seconds maximum
   
2. `test_startup_timing()`:
   - Measure time from `docker-compose up -d` to all services healthy
   - Success criteria: < 2 minutes for full stack
   - Detect timing-related startup failures
   
3. `test_port_accessibility()`:
   - Verify all expected ports respond: 8002, 8009, 7474, 8005
   - Test both direct container ports and proxy routes
   - Ensure no port conflicts or binding issues

**Keep**: All existing 6 tests (health, models, chat, OpenWebUI, database writes, logs)

### **Enhanced test_phase32.py (15 min)**
**Risk Focus**: Advanced features breaking due to service communication

**Add 2 New Tests**:
1. `test_service_communication()`:
   - Verify OpenWebUI → Agent → Database communication chain
   - Test container networking (not localhost networking)
   - Validate service discovery and DNS resolution
   
2. `test_proxy_routing()`:
   - Ensure localhost:8002 → Caddy → OpenWebUI routing works
   - Test WebSocket connections for streaming
   - Validate SSL/TLS if configured

**Keep**: All existing 7 tests (model discovery, latency, session persistence, etc.)

### **Enhanced test_openwebui_config.py (15 min)**
**Risk Focus**: OpenWebUI not starting automatically

**Add 2 New Tests**:
1. `test_openwebui_auto_start()`:
   - Verify OpenWebUI starts without manual `docker-compose up open-webui`
   - Check container startup order and dependencies
   - Validate health check conditions are met
   
2. `test_caddy_proxy_health()`:
   - Ensure localhost:8002 responds immediately after startup completion
   - Test proxy configuration and routing rules
   - Validate no 502/503 errors during startup sequence

**Keep**: All existing 5 tests (accessibility, models endpoint, chat completions, etc.)

---

## **Phase 3: Master Validation Script (15 min)**

### **Create test_migration_validation.py**
**Purpose**: Before/after comparison and reporting

```python
#!/usr/bin/env python3
"""
Pre/Post Migration Validation Script
Compares test results before and after Makefile changes
"""

def run_all_test_suites():
    """Execute all enhanced test suites and collect results"""
    # Run: test_phase1.py, test_phase32.py, test_openwebui_config.py
    # Return: structured results with pass/fail/timing data

def save_baseline(results):
    """Save pre-migration results as baseline.json"""

def compare_against_baseline(current_results):
    """Compare current results vs saved baseline"""
    # Report: newly passing, newly failing, unchanged tests
    
def generate_migration_report():
    """Create human-readable before/after report"""
```

---

## **Phase 4: Documentation (15 min)**

### **Complete this TEST_PLAN.md**
- Document baseline results
- Add troubleshooting section
- Define success criteria
- Create rollback procedures

---

## **Validation Workflow**

### **Pre-Migration Validation**
1. Start current system: `make up`
2. Run enhanced test suite: `python test_migration_validation.py --baseline`
3. Document results: "X/17 tests passing" (6+7+5 existing + 7 new)
4. Save baseline for comparison

### **Post-Migration Validation**  
1. Start new system: `make up` (with improved Makefile)
2. Run same test suite: `python test_migration_validation.py --compare`
3. Review comparison report
4. All previously passing tests must still pass

### **Success Criteria**
- ✅ **No Regression**: All baseline passing tests still pass
- ✅ **Improved Reliability**: Fewer manual steps required
- ✅ **Service Startup**: All containers reach "running" state within 2 minutes
- ✅ **OpenWebUI Access**: localhost:8002 accessible without manual intervention
- ✅ **Complete Functionality**: Chat, streaming, and all APIs work as before

### **Rollback Criteria**
- ❌ Any previously passing test now fails
- ❌ Manual intervention required that wasn't needed before
- ❌ Services don't start within reasonable time
- ❌ Core functionality broken (chat, API access, streaming)

---

## **Troubleshooting Guide**

### **Common Post-Migration Issues**

#### **Services Not Starting**
```bash
# Check service status
docker-compose ps

# Check logs for startup errors  
docker-compose logs agent
docker-compose logs open-webui
docker-compose logs caddy
```

#### **Port Accessibility Issues**
```bash
# Verify port bindings
docker-compose ps --format "table {{.Names}}\t{{.Ports}}"

# Test direct port access
curl -I http://localhost:8002
curl -I http://localhost:8009/health
```

#### **Service Communication Failures**
```bash
# Test inter-container networking
docker exec open-webui ping agent
docker exec agent ping supabase-db

# Check DNS resolution
docker exec open-webui nslookup agent
```

---

## **Implementation Timeline**

- **Phase 1**: 30 minutes - Establish baseline
- **Phase 2**: 45 minutes - Enhance existing tests
- **Phase 3**: 15 minutes - Master validation script  
- **Phase 4**: 15 minutes - Documentation completion
- **Total**: 105 minutes

---

## **Test Matrix Summary**

| Test Suite | Existing Tests | New Tests | Migration Risk Focus |
|------------|----------------|-----------|---------------------|
| test_phase1.py | 6 | 3 | Service startup, timing, ports |
| test_phase32.py | 7 | 2 | Service communication, proxy |
| test_openwebui_config.py | 5 | 2 | Auto-start, Caddy health |
| **Total** | **18** | **7** | **25 focused tests** |

---

## **Baseline Results** (To be filled after Phase 1)

### **Pre-Migration Test Results**
```
test_phase1.py:          _/6 tests passing
test_phase32.py:         _/7 tests passing  
test_openwebui_config.py: _/5 tests passing
Total Baseline:          _/18 tests passing

Manual Validation:
[ ] OpenWebUI accessible at localhost:8002
[ ] Chat functionality working
[ ] Streaming toggle functional
[ ] All expected containers running
```

### **Post-Migration Test Results** (To be filled after implementation)
```
Enhanced Tests:          _/25 tests passing
Regression Check:        _/18 baseline tests still passing
New Functionality:       _/7 new tests passing

Success: ✅/❌ All success criteria met
```

---

**This test plan focuses on practical protection against real migration risks while leveraging existing test infrastructure efficiently.**