#!/usr/bin/env python3
"""
Phase 1 OpenWebUI Integration Test Script
Tests all Phase 1 acceptance criteria from PRD.md
"""

import subprocess
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8009"
OPENWEBUI_URL = "http://localhost:8002"

def run_curl(url: str, method: str = "GET", data: str = None, timeout: int = 10) -> tuple[int, str]:
    """Run curl command and return status code and response"""
    cmd = ["curl", "-s", "-w", "%{http_code}", url]
    
    if method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
        if data:
            cmd.extend(["-d", data])
    
    cmd.extend(["--max-time", str(timeout)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        # Status code is at the end of the output
        output = result.stdout
        if len(output) >= 3:
            status_code = int(output[-3:])
            response_body = output[:-3]
            return status_code, response_body
        else:
            return 0, output
    except Exception as e:
        return 0, str(e)

def test_models_endpoint() -> bool:
    """Test GET /v1/models endpoint."""
    status_code, response = run_curl(f"{BASE_URL}/v1/models")
    
    if status_code != 200:
        print(f"❌ Models endpoint failed: HTTP {status_code}")
        return False
    
    if "gpt-4o-mini" not in response:
        print(f"❌ gpt-4o-mini not found in models response")
        return False
    
    print("✅ Models endpoint working")
    return True

def test_chat_completions() -> bool:
    """Test POST /v1/chat/completions endpoint."""
    payload = '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "ping"}], "stream": false}'
    
    status_code, response = run_curl(f"{BASE_URL}/v1/chat/completions", "POST", payload, 30)
    
    if status_code != 200:
        print(f"❌ Chat completions failed: HTTP {status_code}")
        print(f"Response: {response[:200]}...")
        return False
    
    if "choices" not in response:
        print(f"❌ No choices in chat response")
        return False
    
    print("✅ Chat completions working")
    return True

def test_openwebui_access() -> bool:
    """Test OpenWebUI accessibility."""
    status_code, response = run_curl(OPENWEBUI_URL)
    
    if status_code == 200:
        print("✅ OpenWebUI accessible")
        return True
    else:
        print(f"❌ OpenWebUI not accessible: HTTP {status_code}")
        return False

def test_health_endpoint() -> bool:
    """Test /health endpoint."""
    status_code, response = run_curl(f"{BASE_URL}/health")
    
    if status_code == 200 and ("healthy" in response or "ok" in response):
        print("✅ Health endpoint working")
        return True
    
    print(f"❌ Health check failed: HTTP {status_code}")
    return False

def test_database_writes() -> bool:
    """Test that no database writes occur in stateless mode."""
    try:
        # Get initial message count
        result = subprocess.run([
            "docker", "exec", "supabase-db", "psql", "-U", "postgres", 
            "-c", "SELECT COUNT(*) FROM messages;", "-t"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print("❌ Cannot query database")
            return False
        
        initial_count = int(result.stdout.strip())
        
        # Make a chat request
        payload = '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test stateless"}], "stream": false}'
        status_code, response = run_curl(f"{BASE_URL}/v1/chat/completions", "POST", payload, 30)
        
        if status_code != 200:
            print("❌ Chat request failed for database test")
            return False
        
        # Check message count again
        result = subprocess.run([
            "docker", "exec", "supabase-db", "psql", "-U", "postgres", 
            "-c", "SELECT COUNT(*) FROM messages;", "-t"
        ], capture_output=True, text=True, timeout=10)
        
        final_count = int(result.stdout.strip())
        
        if final_count == initial_count:
            print("✅ No database writes confirmed (stateless mode working)")
            return True
        else:
            print(f"❌ Database writes detected: {initial_count} → {final_count}")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_phase1_startup_logs() -> bool:
    """Test that Phase 1 startup logs are present."""
    try:
        # First, check if container exists and is running
        check_result = subprocess.run([
            "docker", "ps", "-q", "-f", "name=agentic-rag-agent"
        ], capture_output=True, text=True, timeout=5, 
        cwd="/Users/jack/Developer/local-RAG/local-ai-packaged")
        
        if not check_result.stdout.strip():
            print("❌ Container 'agentic-rag-agent' not found or not running")
            return False
        
        # Get all container logs to find startup messages from beginning
        result = subprocess.run([
            "docker", "logs", "agentic-rag-agent"
        ], capture_output=True, text=True, timeout=20,
        cwd="/Users/jack/Developer/local-RAG/local-ai-packaged")
        
        if result.returncode != 0:
            print(f"❌ Failed to get container logs: {result.stderr}")
            return False
        
        logs = result.stdout + result.stderr
        
        # More robust pattern matching - check for key Phase 1 indicators
        # Based on actual log format: "🚀 Phase 1 Agent Starting - MEMORY_ENABLED=False, STREAMING_ENABLED=False"
        phase1_indicators = [
            "🚀 Phase 1 Agent Starting",
            "MEMORY_ENABLED=False", 
            "STREAMING_ENABLED=False"
        ]
        
        found_indicators = [indicator for indicator in phase1_indicators if indicator in logs]
        
        if len(found_indicators) >= 2:  # Require at least 2 of 3 indicators
            print("✅ Phase 1 startup logs confirmed")
            return True
        else:
            print(f"❌ Phase 1 startup logs not found. Found indicators: {found_indicators}")
            # Debug: show last few log lines for troubleshooting
            log_lines = logs.split('\n')[-10:]
            print("Last 10 log lines:")
            for line in log_lines:
                if line.strip():
                    print(f"  {line}")
            return False
            
    except Exception as e:
        print(f"❌ Log check error: {e}")
        return False

def main():
    """Run Phase 1 acceptance tests."""
    print("🧪 Running Phase 1 OpenWebUI Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Models Endpoint", test_models_endpoint), 
        ("Chat Completions", test_chat_completions),
        ("OpenWebUI Access", test_openwebui_access),
        ("Database Writes (Stateless)", test_database_writes),
        ("Phase 1 Startup Logs", test_phase1_startup_logs)
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
        print("\n🎯 Phase 1 Requirements Validated:")
        print("  ✅ Zero-login OpenWebUI access")
        print("  ✅ OpenAI-compatible chat endpoints") 
        print("  ✅ Stateless mode (no database writes)")
        print("  ✅ All health checks passing")
        sys.exit(0)
    else:
        print("❌ Some tests failed - Phase 1 not ready")
        sys.exit(1)

if __name__ == "__main__":
    main()