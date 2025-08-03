#!/usr/bin/env python3
"""
Phase 3.2 Acceptance Tests - OpenWebUI Integration & Chat Memory

Test the OpenAI-compatible endpoints and Phase 3.2 requirements.
"""

import asyncio
import json
import time
import aiohttp
import subprocess
import sys
from typing import Dict, Any, List


class Phase32Tests:
    """Test suite for Phase 3.2 acceptance criteria."""
    
    def __init__(self):
        self.base_url = "http://localhost:8009"
        self.results = {}
        
    async def run_all_tests(self):
        """Run all Phase 3.2 acceptance tests."""
        print("🧪 Starting Phase 3.2 Acceptance Tests...")
        print("=" * 60)
        
        tests = [
            ("T1: Model Discovery", self.test_models_endpoint),
            ("T2: First Token Latency", self.test_streaming_latency),
            ("T3: Session Persistence", self.test_session_persistence),
            ("T4: No Kong Container", self.test_no_kong_containers),
            ("T5: Health Route", self.test_health_endpoint),
            ("T6: OpenAI Chat Completions", self.test_chat_completions),
            ("T7: Streaming Format", self.test_streaming_format)
        ]
        
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
        """T1: Test /v1/models endpoint returns agent-model."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/models") as response:
                if response.status != 200:
                    return {"success": False, "message": f"Status {response.status}"}
                
                data = await response.json()
                
                # Validate structure
                if "data" not in data:
                    return {"success": False, "message": "Missing 'data' field"}
                
                models = [model["id"] for model in data["data"]]
                if "agent-model" not in models:
                    return {"success": False, "message": f"agent-model not found in {models}"}
                
                return {"success": True, "message": f"Found models: {models}"}
    
    async def test_streaming_latency(self) -> Dict[str, Any]:
        """T2: Test first token latency < 1s on streaming request."""
        payload = {
            "model": "agent-model",
            "messages": [{"role": "user", "content": "ping"}],
            "stream": True
        }
        
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
        success = latency < 1.0
        
        return {
            "success": success,
            "message": f"First token latency: {latency:.3f}s",
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
                    "model": "agent-model", 
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
    
    def test_no_kong_containers(self) -> Dict[str, Any]:
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
        payload = {
            "model": "agent-model",
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "stream": False
        }
        
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
        payload = {
            "model": "agent-model",
            "messages": [{"role": "user", "content": "Count to 3"}],
            "stream": True
        }
        
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
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Phase 3.2 is ready for production.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Review implementation.")
            
            print("\nFailed Tests:")
            for test_name, result in self.results.items():
                if not result["success"]:
                    print(f"  ❌ {test_name}: {result['message']}")


async def main():
    """Run Phase 3.2 acceptance tests."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Phase 3.2 Acceptance Tests")
        print("Usage: python test_phase32.py")
        print("\nTests OpenAI-compatible endpoints and Phase 3.2 requirements:")
        print("- Model discovery (/v1/models)")
        print("- Streaming latency (< 1s first token)")
        print("- Session persistence")
        print("- Kong removal verification")
        print("- Health checks")
        return
    
    tester = Phase32Tests()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())