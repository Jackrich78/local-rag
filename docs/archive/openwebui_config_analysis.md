# OpenWebUI Configuration Analysis

## 🔍 Current vs PRD Requirements Comparison

### Current Configuration (docker-compose.yml):
```yaml
open-webui:
  image: ghcr.io/open-webui/open-webui:main  # ❌ Should be v0.6.21
  environment:
    - OPENAI_API_BASE_URL=http://agent:8058/v1  # ✅ Correct
    - OPENAI_API_KEY=dummy                      # ❌ Should be local-dev-key
    - ENABLE_OPENAI_API=true                    # ❓ Not in PRD
    - DEFAULT_MODELS=gpt-4o-mini                # ❓ Not in PRD  
    - WEBUI_AUTH=false                          # ✅ Correct
    - ENABLE_SIGNUP=true                        # ❌ Conflicts with auth=false
```

### PRD Requirements (Section 3.1):
```yaml
open-webui:
  image: ghcr.io/open-webui/open-webui:v0.6.21  # Specific version
  environment:
    - ENABLE_PERSISTENT_CONFIG=false            # Missing!
    - OPENAI_API_BASE_URL=http://agent:8058/v1
    - OPENAI_API_KEY=local-dev-key
    - WEBUI_AUTH=false  # Implied by "zero-login"
```

## 🚨 Critical Configuration Issues

### 1. **Image Version Mismatch**
- **Current**: `:main` (latest, unstable)
- **Required**: `:v0.6.21` (specific stable version)
- **Risk**: Behavior changes, compatibility issues

### 2. **Missing ENABLE_PERSISTENT_CONFIG=false**
- **Impact**: OpenWebUI may ignore environment variables after first launch
- **PRD Context**: Required for stateless configuration
- **Risk**: Settings may not apply consistently

### 3. **Wrong API Key Format**
- **Current**: `dummy`
- **Required**: `local-dev-key`
- **Risk**: OpenWebUI might reject the key format

### 4. **Authentication Conflict**
- **Current**: `WEBUI_AUTH=false` + `ENABLE_SIGNUP=true`
- **Expected**: Just `WEBUI_AUTH=false` (or equivalent for zero-login)
- **Risk**: Signup form might still appear

## 🔧 Recommended Configuration Fix

```yaml
open-webui:
  image: ghcr.io/open-webui/open-webui:v0.6.21
  restart: unless-stopped
  container_name: open-webui
  expose:
    - 8080/tcp
  extra_hosts:
    - "host.docker.internal:host-gateway"
  volumes:
    - open-webui:/app/backend/data
  environment:
    # Phase 1 OpenWebUI Configuration (per PRD)
    - ENABLE_PERSISTENT_CONFIG=false           # Critical for stateless mode
    - OPENAI_API_BASE_URL=http://agent:8058/v1
    - OPENAI_API_KEY=local-dev-key            # PRD-specified dummy key
    - WEBUI_AUTH=false                        # Zero-login requirement
    - ENABLE_SIGNUP=false                     # Disable signup to prevent conflicts
  depends_on:
    agent:
      condition: service_healthy
```

## 🧪 Validation Tests Needed

1. **Authentication Bypass**: Verify no login/signup screens appear
2. **Model Detection**: Check if gpt-4o-mini appears in model selector
3. **API Connectivity**: Test chat functionality end-to-end
4. **Configuration Persistence**: Verify settings don't revert after restart
5. **Volume Reset**: Test PRD's volume wipe procedure

## ⚠️ Potential Risks

1. **Version Compatibility**: v0.6.21 might have different behavior than :main
2. **Authentication Edge Cases**: User might still see auth prompts in some scenarios
3. **Network Connectivity**: Container-to-container communication issues
4. **Performance**: Response time might exceed 4-second target

## 📝 Testing Strategy

1. Apply configuration changes
2. Run volume wipe procedure (per PRD)
3. Start services and wait for readiness
4. Execute validation script
5. Manual browser testing for UX verification
6. Performance testing for response time compliance