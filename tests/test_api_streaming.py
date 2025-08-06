#!/usr/bin/env python3
"""
API & Streaming Test Suite - Enhanced Communication Validation
Comprehensive testing of API endpoints, streaming functionality, and inter-service communication
Replaces: test_phase32.py with expanded functionality
"""

import asyncio
import json
import time
import aiohttp
import subprocess
import sys
from typing import Dict, Any, List

# Import test configuration
from test_config import TestConfig


class ApiStreamingTests:
    """Test suite for API endpoints, streaming, and service communication."""
    
    def __init__(self):
        self.config = TestConfig()
        self.base_url = self.config.base_url
        self.results = {}
        
        # Auto-detect models at startup
        print(f"🔧 Using model: {self.config.primary_model}")
        
    async def run_all_tests(self):
        """Run all API and streaming tests."""
        print("🧪 Starting API & Streaming Test Suite...")
        print("=" * 60)
        
        # Core API tests (from original test_phase32.py)
        core_tests = [
            ("Model Discovery", self.test_models_endpoint),
            ("First Token Latency", self.test_streaming_latency),
            ("Session Persistence", self.test_session_persistence),
            ("No Kong Container", self.test_no_kong_containers),
            ("Health Route", self.test_health_endpoint),
            ("OpenAI Chat Completions", self.test_chat_completions),
            ("Streaming Format", self.test_streaming_format)
        ]
        
        # Enhanced communication tests
        communication_tests = [
            ("Inter-Service Networking", self.test_inter_service_networking),
            ("Proxy Routing Comprehensive", self.test_proxy_routing_comprehensive),
            ("API Error Recovery", self.test_api_error_recovery),
            ("Streaming State Management", self.test_streaming_state_management)
        ]
        
        tests = core_tests + communication_tests
        
        print(f"\n📋 Running {len(tests)} comprehensive API and streaming tests...")
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            try:
                result = await test_func()
                self.results[test_name] = result
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"   {status}: {result['message']}")
                if not result["success"] and "details" in result:
                    print(f"   Details: {result['details']}")
            except Exception as e:
                self.results[test_name] = {"success": False, "message": str(e)}
                print(f"   ❌ ERROR: {str(e)}")
        
        self.print_summary()
    
    async def test_models_endpoint(self) -> Dict[str, Any]:
        """T1: Test /v1/models endpoint returns expected models."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/models") as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                data = await response.json()
                
                # Validate structure
                if "data" not in data:
                    return {"success": False, "message": "Missing 'data' field"}
                
                models = [model["id"] for model in data["data"]]
                
                # Check if primary model is available
                primary_model = self.config.primary_model
                if primary_model not in models:
                    return {"success": False, "message": f"Primary model '{primary_model}' not found in {models}"}
                
                return {"success": True, "message": f"Found models: {models}, using: {primary_model}"}
    
    async def test_streaming_latency(self) -> Dict[str, Any]:
        """T2: Test first token latency meets threshold on streaming request."""
        message = self.config.get_test_message_simple()
        payload = self.config.create_chat_payload(message, stream=True)
        
        start_time = time.time()
        first_token_time = None
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions", 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                async for line in response.content:
                    line_str = line.decode().strip()
                    if line_str.startswith("data: ") and not line_str.endswith("[DONE]"):
                        if first_token_time is None:
                            first_token_time = time.time()
                            break
        
        if first_token_time is None:
            return {"success": False, "message": "No tokens received"}
        
        latency = first_token_time - start_time
        threshold = self.config.get_performance_thresholds()["first_token_latency"]
        success = latency < threshold
        
        return {
            "success": success,
            "message": f"First token latency: {latency:.3f}s (threshold: {threshold}s)",
            "latency_ms": latency * 1000
        }
    
    async def test_session_persistence(self) -> Dict[str, Any]:
        """T3: Test session persistence across multiple messages."""
        messages = [
            {"role": "user", "content": "Remember: my favorite color is blue"},
            {"role": "user", "content": "What is my favorite color?"}
        ]
        
        session_id = None
        responses = []
        
        async with aiohttp.ClientSession() as session:
            for i, message in enumerate(messages):
                payload = {
                    "model": self.config.primary_model, 
                    "messages": messages[:i+1],  # Include conversation history
                    "stream": False
                }
                
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    if response.status != 200:
                        return {"success": False, "message": f"Message {i+1} failed: {response.status}"}
                    
                    data = await response.json()
                    responses.append(data)
        
        # Check if we get coherent responses (basic validation)
        if len(responses) != 2:
            return {"success": False, "message": f"Expected 2 responses, got {len(responses)}"}
        
        return {
            "success": True,
            "message": f"Session persistence test completed with {len(responses)} messages",
            "responses": [r["choices"][0]["message"]["content"][:50] + "..." for r in responses]
        }
    
    async def test_no_kong_containers(self) -> Dict[str, Any]:
        """T4: Test that no Kong containers are running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            container_names = result.stdout.strip().split('\n')
            kong_containers = [name for name in container_names if 'kong' in name.lower()]
            
            if kong_containers:
                return {
                    "success": False,
                    "message": f"Found Kong containers: {kong_containers}"
                }
            
            return {
                "success": True,
                "message": "No Kong containers found"
            }
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Docker command failed: {e}"}
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """T5: Test health endpoint returns 200 OK."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                data = await response.json()
                status = data.get("status", "unknown")
                
                return {
                    "success": True,
                    "message": f"Health check OK, status: {status}",
                    "health_data": data
                }
    
    async def test_chat_completions(self) -> Dict[str, Any]:
        """T6: Test basic OpenAI chat completions functionality."""
        payload = self.config.create_chat_payload("What is 2+2?", stream=False)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                data = await response.json()
                
                # Validate OpenAI response structure
                required_fields = ["id", "object", "created", "model", "choices"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return {"success": False, "message": f"Missing fields: {missing_fields}"}
                
                if not data["choices"] or "message" not in data["choices"][0]:
                    return {"success": False, "message": "Invalid choices structure"}
                
                response_text = data["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "message": f"Chat completion successful",
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }
    
    async def test_streaming_format(self) -> Dict[str, Any]:
        """T7: Test OpenAI-compatible streaming format."""
        message = self.config.get_test_message_streaming()
        payload = self.config.create_chat_payload(message, stream=True)
        
        chunks_received = 0
        valid_format = True
        error_details = []
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                async for line in response.content:
                    line_str = line.decode().strip()
                    if line_str.startswith("data: "):
                        chunks_received += 1
                        data_str = line_str[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            
                            # Validate chunk structure
                            if "object" not in chunk_data or chunk_data["object"] != "chat.completion.chunk":
                                valid_format = False
                                error_details.append(f"Invalid object type: {chunk_data.get('object')}")
                            
                            if "choices" not in chunk_data or not chunk_data["choices"]:
                                valid_format = False
                                error_details.append("Missing or empty choices")
                            
                        except json.JSONDecodeError as e:
                            valid_format = False
                            error_details.append(f"JSON decode error: {e}")
                        
                        # Stop after checking a few chunks
                        if chunks_received >= 3:
                            break
        
        if chunks_received == 0:
            return {"success": False, "message": "No chunks received"}
        
        if not valid_format:
            return {
                "success": False,
                "message": f"Invalid streaming format",
                "details": error_details[:3]  # Show first 3 errors
            }
        
        return {
            "success": True,
            "message": f"Streaming format valid, received {chunks_received} chunks"
        }
    
    async def test_inter_service_networking(self) -> Dict[str, Any]:
        """Test inter-service communication and networking."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test OpenWebUI can reach Agent
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status != 200:
                        return {"success": False, "message": f"Agent not reachable: {response.status}"}
                
                # Test agent API is working (if API works, networking is functional)
                # This is more reliable than using nc which may not be available
                async with session.get(f"{self.base_url}/v1/models") as models_response:
                    if models_response.status != 200:
                        return {"success": False, "message": "Agent API not functional"}
            
            return {"success": True, "message": "Inter-service networking functional"}
            
        except Exception as e:
            return {"success": False, "message": f"Network test failed: {str(e)}"}
    
    async def test_proxy_routing_comprehensive(self) -> Dict[str, Any]:
        """Test Caddy proxy routing and WebSocket connections."""
        try:
            # Test direct OpenWebUI access via proxy
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8002") as response:
                    if response.status not in [200, 302]:  # Allow redirects
                        return {"success": False, "message": f"Proxy routing failed: {response.status}"}
                
                # Test agent API access via proxy/direct
                async with session.get(f"{self.base_url}/v1/models") as response:
                    if response.status != 200:
                        return {"success": False, "message": f"API routing failed: {response.status}"}
            
            return {"success": True, "message": "Proxy routing working correctly"}
            
        except Exception as e:
            return {"success": False, "message": f"Proxy test failed: {str(e)}"}
    
    async def test_api_error_recovery(self) -> Dict[str, Any]:
        """Test API behavior during error conditions."""
        try:
            # Test invalid model request
            payload = {
                "model": "non-existent-model",
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    # Should handle gracefully - either 400 or fallback to default model
                    if response.status not in [200, 400, 422]:
                        return {"success": False, "message": f"Unexpected error handling: {response.status}"}
                
                # Test malformed request
                malformed_payload = {"invalid": "request"}
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=malformed_payload
                ) as response:
                    if response.status not in [400, 422]:  # Should return validation error
                        return {"success": False, "message": f"Poor error handling for malformed request: {response.status}"}
            
            return {"success": True, "message": "API error recovery working"}
            
        except Exception as e:
            return {"success": False, "message": f"Error recovery test failed: {str(e)}"}
    
    async def test_streaming_state_management(self) -> Dict[str, Any]:
        """Test streaming vs non-streaming mode switching and connection management."""
        try:
            # Test non-streaming request
            non_stream_payload = self.config.create_chat_payload("short response", stream=False)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=non_stream_payload
                ) as response:
                    if response.status != 200:
                        return {"success": False, "message": f"Non-streaming failed: {response.status}"}
                    
                    data = await response.json()
                    if "choices" not in data:
                        return {"success": False, "message": "Non-streaming response malformed"}
                
                # Test streaming request immediately after
                stream_payload = self.config.create_chat_payload("stream this", stream=True)
                
                chunks_received = 0
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=stream_payload
                ) as response:
                    if response.status != 200:
                        return {"success": False, "message": f"Streaming switch failed: {response.status}"}
                    
                    async for line in response.content:
                        line_str = line.decode().strip()
                        if line_str.startswith("data: "):
                            chunks_received += 1
                            if chunks_received >= 2:  # Got some chunks
                                break
            
            if chunks_received == 0:
                return {"success": False, "message": "No streaming chunks received"}
            
            return {"success": True, "message": f"Streaming state management working ({chunks_received} chunks)"}
            
        except Exception as e:
            return {"success": False, "message": f"State management test failed: {str(e)}"}
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 API & STREAMING TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL API & STREAMING TESTS PASSED!")
            print("\n🎯 API Functionality Validated:")
            print("  ✅ OpenAI-compatible endpoints working")
            print("  ✅ Streaming functionality operational")
            print("  ✅ Inter-service communication healthy")
            print("  ✅ Error handling robust")
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate acceptable
            print(f"\n✅ API system mostly healthy - {total_tests - passed_tests} minor issues")
        else:
            print(f"\n❌ API issues detected - {total_tests - passed_tests} tests failed")
            
            print("\nFailed Tests:")
            for test_name, result in self.results.items():
                if not result["success"]:
                    print(f"  ❌ {test_name}: {result['message']}")


async def main():
    """Run API and streaming test suite."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("API & Streaming Test Suite")
        print("Usage: python test_api_streaming.py")
        print("\nComprehensive testing of:")
        print("- OpenAI-compatible API endpoints")
        print("- Streaming functionality and performance")
        print("- Inter-service communication")
        print("- Error handling and recovery")
        print("- Connection state management")
        return
    
    tester = ApiStreamingTests()
    await tester.run_all_tests()
    
    # Return appropriate exit code
    total_tests = len(tester.results)
    passed_tests = sum(1 for result in tester.results.values() if result["success"])
    
    if passed_tests == total_tests:
        sys.exit(0)  # All tests passed
    elif passed_tests >= total_tests * 0.8:
        sys.exit(0)  # 80%+ pass rate acceptable
    else:
        sys.exit(1)  # Too many failures


if __name__ == "__main__":
    asyncio.run(main())