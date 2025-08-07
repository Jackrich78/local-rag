# Flexible Testing Architecture

**Purpose**: Make tests robust and maintainable by eliminating hard-coded values and supporting different model configurations.

**Problem Solved**: Tests were brittle because they hard-coded "gpt-4o-mini" everywhere. This made them fragile when switching models or updating configurations.

---

## Overview

### Before: Brittle Hard-coded Tests
```python
# ❌ Hard-coded everywhere
payload = {"model": "gpt-4o-mini", ...}
if "gpt-4o-mini" not in models: ...
```

### After: Flexible Configuration-Driven Tests  
```python  
# ✅ Dynamic and configurable
payload = config.create_chat_payload(message, stream=False)
if config.primary_model not in models: ...
```

---

## Configuration System

### 1. Test Configuration (`tests/test_config.py`)
Centralized configuration that:
- **Auto-detects models** from `/v1/models` endpoint
- **Falls back gracefully** if detection fails
- **Supports environment overrides** for different setups
- **Provides consistent test utilities**

### 2. Environment Configuration (`.env.test`)
```bash
# Model Configuration
PREFERRED_MODEL=                    # Auto-detect if empty
FALLBACK_MODEL=gpt-4o-mini         # Fallback if detection fails
AUTO_DETECT_MODELS=true            # Enable/disable auto-detection

# Performance Thresholds  
FIRST_TOKEN_THRESHOLD=2.0          # Latency expectations
FULL_RESPONSE_THRESHOLD=30.0       # Full response timeout
HEALTH_CHECK_THRESHOLD=5.0         # Health check timeout

# API Endpoints
AGENT_BASE_URL=http://localhost:8009
OPENWEBUI_URL=http://localhost:8002
```

### 3. Local Overrides (`.env.test.local`) 
Create this file to override defaults without affecting version control:
```bash
# For testing with different models
PREFERRED_MODEL=gpt-4-turbo
FIRST_TOKEN_THRESHOLD=3.0
```

---

## Model Selection Logic

### Priority Order:
1. **Environment Override**: `PREFERRED_MODEL` if set and `AUTO_DETECT_MODELS=false`
2. **Preferred Available**: `PREFERRED_MODEL` if available in API response  
3. **First Detected**: First model from `/v1/models` endpoint
4. **Fallback**: `FALLBACK_MODEL` if all else fails

### Examples:

**Auto-detection (default)**:
```bash
# System detects ["gpt-4o-mini", "gpt-4"] → uses "gpt-4o-mini"
```

**Preferred model available**:
```bash
PREFERRED_MODEL=gpt-4
# System detects ["gpt-4o-mini", "gpt-4"] → uses "gpt-4"
```

**Preferred model not available**:
```bash  
PREFERRED_MODEL=gpt-5-turbo
# System detects ["gpt-4o-mini", "gpt-4"] → uses "gpt-4o-mini" (first detected)
```

**API detection fails**:
```bash
# Network error → uses FALLBACK_MODEL="gpt-4o-mini"
```

---

## Test Configuration Usage

### In Test Files:
```python
from test_config import TestConfig

class MyTestSuite:
    def __init__(self):
        self.config = TestConfig()
        
    def test_something(self):
        # ✅ Dynamic model selection
        payload = self.config.create_chat_payload("test message", stream=True)
        
        # ✅ Configurable thresholds
        threshold = self.config.get_performance_thresholds()["first_token_latency"]
        
        # ✅ Auto-detected containers
        expected = self.config.get_expected_containers()
```

### Utility Functions:
```python
# Create test payloads
payload = config.create_chat_payload("Hello", stream=False)

# Check model availability  
if config.is_model_available("gpt-4"):
    # Use gpt-4 specific test

# Get performance thresholds
thresholds = config.get_performance_thresholds()
assert latency < thresholds["first_token_latency"]

# Validate responses
assert config.validate_openai_response(response_data)
```

---

## Benefits

### 1. **Future-Proof**
- Adding new models: No test changes needed
- Switching default models: Change one environment variable
- Different deployment environments: Override via `.env.test.local`

### 2. **Maintainable**
- Single source of truth for test configuration
- No scattered hard-coded values across 20+ test files
- Consistent payload creation and validation

### 3. **Robust**
- Graceful fallbacks if API changes
- Environment-specific overrides
- Clear error messages when things break

### 4. **Flexible**
- Support multiple deployment scenarios
- Easy A/B testing with different models
- Performance threshold tuning per environment

---

## Migration Path

### Phase 1: ✅ COMPLETE
- Created `test_config.py` with auto-detection
- Updated `test_api_streaming.py` and `test_system_health.py`  
- Added `.env.test` configuration file
- All tests pass with dynamic model detection

### Phase 2: Future Enhancement  
- Update remaining test files (`test_user_interface.py`, `test_master_validation.py`)
- Add support for multiple model testing
- Create test profiles for different environments
- Add model-specific test variations

---

## Configuration Examples

### Development Environment
```bash
# .env.test.local
AUTO_DETECT_MODELS=true           # Use whatever the API provides
FIRST_TOKEN_THRESHOLD=2.0         # Relaxed for development
VERBOSE_OUTPUT=true               # Detailed test output
```

### Production Testing
```bash  
# .env.test.local
PREFERRED_MODEL=gpt-4o-mini       # Specific model for consistency
FIRST_TOKEN_THRESHOLD=1.0         # Stricter performance requirements
AUTO_DETECT_MODELS=false          # No surprises
```

### CI/CD Pipeline
```bash
# Environment variables in CI
export PREFERRED_MODEL=gpt-4o-mini
export FIRST_TOKEN_THRESHOLD=3.0  # Slower CI environment
export AUTO_DETECT_MODELS=true    # Flexible for different deployments
```

---

## Testing the Configuration

### Quick Test:
```bash
python3 tests/test_config.py
```

### Full Validation:
```bash
# Test with current configuration
python3 tests/test_api_streaming.py

# Test with different model (if available)
PREFERRED_MODEL=gpt-4 python3 tests/test_api_streaming.py

# Test with different thresholds
FIRST_TOKEN_THRESHOLD=1.0 python3 tests/test_api_streaming.py
```

---

## Key Files

| File | Purpose | Status |
|------|---------|---------|
| `tests/test_config.py` | Central configuration and utilities | ✅ Complete |  
| `.env.test` | Default test environment settings | ✅ Complete |
| `.env.test.local` | Local overrides (user-created) | 📝 Template |
| `tests/test_api_streaming.py` | Updated with flexible config | ✅ Complete |
| `tests/test_system_health.py` | Updated with flexible config | ✅ Complete |

---

**Result**: Tests are now robust, maintainable, and future-proof. No more brittle hard-coded model names! 🎯