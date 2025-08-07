#!/usr/bin/env python3
"""
Test Configuration - Centralized test settings and utilities
Makes tests more robust and maintainable by avoiding hard-coded values
"""

import os
import json
import aiohttp
import requests
from typing import Dict, List, Optional, Any

# Load environment variables from .env.test if available
def load_test_env():
    """Load test environment variables from .env.test file if it exists."""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env.test.local')
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env.test')
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value

load_test_env()

class TestConfig:
    """Centralized configuration for all test suites."""
    
    def __init__(self):
        self.base_url = os.getenv("AGENT_BASE_URL", "http://localhost:8009")
        self.openwebui_url = os.getenv("OPENWEBUI_URL", "http://localhost:8002")
        self.timeout = int(os.getenv("TEST_TIMEOUT", "30"))
        
        # Model configuration
        self.preferred_model = os.getenv("PREFERRED_MODEL", "")  # Empty means auto-detect
        self.fallback_model = os.getenv("FALLBACK_MODEL", "gpt-4o-mini")
        self.auto_detect = os.getenv("AUTO_DETECT_MODELS", "true").lower() == "true"
        
        # Dynamic model detection
        self._available_models = None
        self._primary_model = None
        
    @property
    def primary_model(self) -> str:
        """Get the primary model to use for tests (auto-detected from API)."""
        if self._primary_model is None:
            self._detect_models()
        return self._primary_model or "gpt-4o-mini"  # Fallback
    
    @property 
    def available_models(self) -> List[str]:
        """Get all available models from the API."""
        if self._available_models is None:
            self._detect_models()
        return self._available_models or ["gpt-4o-mini"]  # Fallback
    
    def _detect_models(self):
        """Detect available models from the /v1/models endpoint."""
        # If preferred model is set and auto-detect is disabled, use it
        if self.preferred_model and not self.auto_detect:
            self._available_models = [self.preferred_model]
            self._primary_model = self.preferred_model
            print(f"🔧 Using configured model: {self._primary_model}")
            return
        
        # Try to detect from API
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    self._available_models = [model["id"] for model in data["data"]]
                    
                    # Use preferred model if available, otherwise first detected
                    if self.preferred_model and self.preferred_model in self._available_models:
                        self._primary_model = self.preferred_model
                        print(f"🎯 Using preferred model: {self._primary_model}")
                    else:
                        self._primary_model = self._available_models[0]
                        print(f"🔍 Auto-detected models: {self._available_models}")
                        print(f"📌 Using primary model: {self._primary_model}")
                    return
        except Exception as e:
            print(f"⚠️  Model detection failed: {e}")
        
        # Fallback values
        self._available_models = [self.fallback_model]
        self._primary_model = self.fallback_model
        print(f"⚠️  Using fallback model: {self._primary_model}")
    
    async def detect_models_async(self) -> List[str]:
        """Async version of model detection for use in async test contexts."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and data["data"]:
                            models = [model["id"] for model in data["data"]]
                            self._available_models = models
                            self._primary_model = models[0]
                            return models
        except Exception as e:
            print(f"⚠️  Async model detection failed: {e}")
        
        return self._available_models or ["gpt-4o-mini"]
    
    def get_test_message_simple(self) -> str:
        """Get a simple test message for basic API tests."""
        return "ping"
    
    def get_test_message_streaming(self) -> str:
        """Get a test message that works well for streaming tests."""
        return "Count to 3"
    
    def get_test_message_rag(self) -> str:
        """Get a test message that should trigger RAG functionality."""
        return "What documents do you have access to?"
    
    def get_expected_containers(self) -> List[str]:
        """Get list of expected container names."""
        return [
            "agentic-rag-agent",
            "open-webui", 
            "supabase-db",
            "local-ai-packaged-neo4j-1",
            "qdrant",
            "caddy"
        ]
    
    def get_performance_thresholds(self) -> Dict[str, float]:
        """Get performance thresholds for various operations."""
        return {
            "first_token_latency": float(os.getenv("FIRST_TOKEN_THRESHOLD", "2.0")),
            "full_response_timeout": float(os.getenv("FULL_RESPONSE_THRESHOLD", "30.0")),
            "health_check_timeout": float(os.getenv("HEALTH_CHECK_THRESHOLD", "5.0"))
        }
    
    def create_chat_payload(self, message: str, stream: bool = False, model: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized chat completion payload."""
        return {
            "model": model or self.primary_model,
            "messages": [{"role": "user", "content": message}],
            "stream": stream
        }
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        return model_name in self.available_models
    
    def validate_openai_response(self, response_data: Dict[str, Any]) -> bool:
        """Validate that a response matches OpenAI format."""
        required_fields = ["id", "object", "created", "model", "choices"]
        return all(field in response_data for field in required_fields)
    
    def print_config_summary(self):
        """Print current test configuration."""
        print("🔧 Test Configuration:")
        print(f"  Base URL: {self.base_url}")
        print(f"  OpenWebUI URL: {self.openwebui_url}")
        print(f"  Primary Model: {self.primary_model}")
        print(f"  Available Models: {self.available_models}")
        print(f"  Timeout: {self.timeout}s")
        thresholds = self.get_performance_thresholds()
        print(f"  Latency Threshold: {thresholds['first_token_latency']}s")


# Global configuration instance
config = TestConfig()


# Utility functions for backwards compatibility
def get_primary_model() -> str:
    """Get the primary model for tests."""
    return config.primary_model

def get_available_models() -> List[str]:
    """Get all available models."""
    return config.available_models

def create_test_payload(message: str, stream: bool = False) -> Dict[str, Any]:
    """Create a test payload with auto-detected model."""
    return config.create_chat_payload(message, stream)


if __name__ == "__main__":
    # Test the configuration
    print("Testing configuration system...")
    config.print_config_summary()
    
    # Test model detection
    print(f"\n🧪 Model Detection Test:")
    print(f"Primary model: {config.primary_model}")
    print(f"All models: {config.available_models}")
    print(f"Is gpt-4o-mini available: {config.is_model_available('gpt-4o-mini')}")
    
    # Test payload creation
    payload = config.create_chat_payload("test message", stream=True)
    print(f"\n📝 Sample payload: {json.dumps(payload, indent=2)}")