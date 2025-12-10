# Backend Configuration Management - Developer Guide

## Overview

The AOSB Backend now has **enterprise-grade configuration management** with comprehensive validation and developer-friendly error messages. Instead of cryptic errors at runtime, you get clear guidance on what's wrong and how to fix it.

## Quick Start

### 1. Copy Configuration Template
```bash
cp .env.example .env
```

### 2. Fill in Your Values
Edit `.env` and set your API keys and preferences:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-actual-key
```

### 3. Validate Configuration
```bash
python -m backend.config_validator
```

If all checks pass:
```
✅ Configuration is valid and ready to use!
```

### 4. Start the Backend
```bash
python -m backend.main
# or
uvicorn backend.main:app --reload
```

## Configuration Validation

### Automatic Validation at Startup

Configuration is validated automatically when the backend starts. If validation fails, you'll see a clear error message:

**Before (Cryptic):**
```
KeyError: 'OPENAI_API_KEY'
Traceback (most recent call last):
  File "backend/core/llm.py", line 45, in __init__
    api_key = os.environ['OPENAI_API_KEY']
KeyError: 'OPENAI_API_KEY'
```

**After (Developer-Friendly):**
```
============================================================
❌ Configuration Error:
============================================================
LLM provider is 'openai' but OPENAI_API_KEY is not set.
Set it via:
  1. Environment variable: export OPENAI_API_KEY='sk-...'
  2. .env file: OPENAI_API_KEY=sk-...

Get your key at: https://platform.openai.com/api-keys
============================================================

💡 Tips:
  • Copy .env.example to .env and fill in your values
  • Run: python -m backend.config_validator
  • Check README.md for setup instructions
============================================================
```

### Manual Validation

Use the configuration validator tool anytime:

```bash
python -m backend.config_validator
```

Output:
```
============================================================
🔍 Backend Configuration Validator
============================================================

📋 Checking environment files...
✓ Found .env file at: /home/edgar/Documents/AOSBAckend/.env

🔐 Checking environment variables...
ℹ LLM Provider: openai
✓ OPENAI_API_KEY is set

⚙️  Loading configuration...
✓ Configuration loaded successfully
✓ All configuration validations passed

============================================================
⚙️  Configuration Summary
============================================================
Environment:          local
LLM Provider:         openai
LLM Model:            gpt-4o-mini
Vector Store:         chroma
Vector Store Path:    data/vector_store
Embedding Model:      text-embedding-3-small
Encryption Enabled:   False
Memory Compaction:    False
Daily Briefing:       False

API Keys:
  OpenAI:             ✓ Set
  Anthropic:          ✗ Not set
  Cohere:             ✗ Not set
  Local LLM URL:      ✗ Not set
============================================================

✅ Configuration is valid and ready to use!
```

## Configuration Options

### Environment Variables

All configuration is via environment variables in `.env` or OS environment:

#### LLM Provider Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `LLM_PROVIDER` | string | Yes | One of: `openai`, `anthropic`, `cohere`, `local` |
| `LLM_MODEL` | string | Yes | Model name for the provider |
| `LLM_TEMPERATURE` | float | No | 0.0 (deterministic) to 2.0 (creative), default: 0.0 |
| `LLM_MAX_TOKENS` | int | No | Max response length, default: 512 |

#### API Keys (Choose One Based on Provider)

| Variable | Type | Required For |
|----------|------|--------------|
| `OPENAI_API_KEY` | string | OpenAI provider |
| `ANTHROPIC_API_KEY` | string | Anthropic provider |
| `COHERE_API_KEY` | string | Cohere provider |
| `LOCAL_LLM_URL` | string | Local provider |

#### Vector Store Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `VECTOR_STORE_TYPE` | string | No | `chroma`, `pinecone`, `weaviate`, `milvus` |
| `VECTOR_STORE_PATH` | string | No | Local storage path, auto-created if needed |
| `EMBEDDING_MODEL` | string | No | Model for embeddings, default: `text-embedding-3-small` |

#### Encryption

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `ENCRYPTION_ENABLED` | bool | No | Enable/disable encryption |
| `ENCRYPTION_KEY` | string | If enabled | 32-byte hex key |
| `ENCRYPTION_DERIVE_FROM_PASSWORD` | bool | No | Derive key from password |
| `ENCRYPT_VECTOR_TEXTS` | bool | No | Encrypt document texts |
| `ENCRYPT_METADATA_FIELDS` | string | No | Comma-separated fields to encrypt |

#### Database

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `METADATA_DB_URL` | string | No | Database URL, default: `sqlite:///data/metadata.db` |

#### Maintenance

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `MEMORY_COMPACTION_ENABLED` | bool | No | Enable periodic cleanup |
| `MEMORY_COMPACTION_INTERVAL_HOURS` | int | No | Cleanup frequency |
| `MEMORY_COMPACTION_KEEP_DAYS` | int | No | Retention period |
| `MEMORY_COMPACTION_STRATEGY` | string | No | `deduplicate_exact` or `age_based` |

#### Daily Briefing

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `DAILY_BRIEFING_ENABLED` | bool | No | Enable automatic briefing |
| `DAILY_BRIEFING_INTERVAL_HOURS` | int | No | Generation frequency |
| `DAILY_BRIEFING_LOOKBACK_DAYS` | int | No | Days to include |
| `DAILY_BRIEFING_SUMMARY_STYLE` | string | No | `bullet_points`, `executive`, `narrative` |
| `DAILY_BRIEFING_MAX_CHARS` | int | No | Max briefing length |

## Validation Features

### 1. Provider-Specific Validation

Each LLM provider validates that required configuration is present:

```python
# OpenAI validation
if provider == 'openai' and not openai_api_key:
    raise ValueError(
        "LLM provider is 'openai' but OPENAI_API_KEY is not set. "
        "Set it via:\n"
        "  1. Environment variable: export OPENAI_API_KEY='sk-...'\n"
        "  2. .env file: OPENAI_API_KEY=sk-...\n"
        "Get your key at: https://platform.openai.com/api-keys"
    )
```

### 2. Value Range Validation

Validates that numeric values are in valid ranges:

```python
# Temperature must be 0.0-2.0
if not 0.0 <= temperature <= 2.0:
    raise ValueError(f"Temperature {temp} out of range [0.0, 2.0]")
```

### 3. Path Validation

Automatically creates directories if they don't exist:

```python
# Vector store path is created automatically
path = Path(vector_store_path)
path.parent.mkdir(parents=True, exist_ok=True)
```

### 4. Enum Validation

Validates that enum values are valid:

```python
# Valid environments: local, development, staging, production
if environment not in {'local', 'development', 'staging', 'production'}:
    raise ValueError(f"Invalid environment '{environment}'")
```

### 5. Consistency Validation

Validates that configurations are compatible:

```python
# Encryption requires either key or password derivation
if encryption_enabled and not encryption_key and not derive_from_password:
    raise ValueError("Encryption enabled but no key configured")
```

## Error Messages

### Error: Missing API Key

```
LLM provider is 'openai' but OPENAI_API_KEY is not set.
Set it via:
  1. Environment variable: export OPENAI_API_KEY='sk-...'
  2. .env file: OPENAI_API_KEY=sk-...

Get your key at: https://platform.openai.com/api-keys
```

**Fix:**
```bash
# Option 1: Set environment variable
export OPENAI_API_KEY='sk-proj-...'
python -m backend.main

# Option 2: Add to .env
echo "OPENAI_API_KEY=sk-proj-..." >> .env
python -m backend.main
```

### Error: Invalid Provider

```
Invalid LLM provider 'gpt4'. 
Must be one of: anthropic, cohere, local, openai
```

**Fix:**
```bash
# Check .env for correct provider
grep LLM_PROVIDER .env
# Change to valid provider
sed -i 's/LLM_PROVIDER=gpt4/LLM_PROVIDER=openai/' .env
```

### Error: Invalid Temperature

```
Invalid temperature 5.0. 
Must be between 0.0 and 2.0 (currently 5.0)
```

**Fix:**
```bash
# Update temperature to valid range
sed -i 's/LLM_TEMPERATURE=5.0/LLM_TEMPERATURE=0.7/' .env
```

### Error: Path Not Writable

```
Cannot create vector store directory 'data/vector_store': Permission denied
```

**Fix:**
```bash
# Check permissions
ls -la data/
# Fix permissions
chmod 755 data/
# Or use different path
VECTOR_STORE_PATH=/tmp/vector_store python -m backend.main
```

## Programmatic Usage

### In Your Code

```python
from backend.config import settings, ConfigurationError

# Safely access configuration
try:
    llm_provider = settings.llm_provider
    api_key = settings.openai_api_key
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    exit(1)
```

### Validation Methods

```python
from backend.config import settings

# Check if configuration is valid
is_valid, errors = settings.validate()
if not is_valid:
    for error in errors:
        print(error)

# Print configuration summary
settings.print_config_summary()

# Export safe config (secrets masked)
safe_config = settings.to_dict_safe()
print(safe_config)
# {'llm_provider': 'openai', 'openai_api_key': '***aZmk', ...}
```

## Best Practices

### 1. Never Commit API Keys

```bash
# Add .env to .gitignore
echo ".env" >> .gitignore

# Use .env.example for template
git add .env.example
git commit -m "Add config template"
```

### 2. Validate on Startup

The backend automatically validates configuration on startup. If validation fails, the process exits with a clear error message.

### 3. Use Environment Variables in Production

```bash
# In production, use environment variables, not .env file
export OPENAI_API_KEY='sk-prod-...'
export ENVIRONMENT=production
python -m backend.main
```

### 4. Run Validator Before Starting

```bash
# Always validate before starting
python -m backend.config_validator

# Then start
python -m backend.main
```

### 5. Use Sensible Defaults

```python
# Temperature defaults to 0.0 (deterministic)
LLM_TEMPERATURE=0.0

# Max tokens defaults to 512
LLM_MAX_TOKENS=512

# Encryption is disabled by default
ENCRYPTION_ENABLED=false
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Check 1: Is .env file present?**
```bash
ls -la .env
```

**Check 2: Is environment variable set?**
```bash
echo $OPENAI_API_KEY
```

**Check 3: Run validator**
```bash
python -m backend.config_validator
```

### Issue: "Invalid environment 'dev'"

**Error:** Invalid environment 'dev'. Must be one of: local, development, staging, production

**Fix:**
```bash
# Change dev to development
sed -i 's/ENVIRONMENT=dev/ENVIRONMENT=development/' .env
```

### Issue: "Cannot create vector store directory"

**Error:** Cannot create vector store directory '/root/data': Permission denied

**Fix:**
```bash
# Use writable path
VECTOR_STORE_PATH=/tmp/aosb_vectors python -m backend.main

# Or fix permissions
sudo mkdir -p /root/data
sudo chmod 777 /root/data
```

### Issue: Validation passes but LLM calls fail

**Possible cause:** API key syntax is invalid or expired

**Check:**
```bash
# Validate key format
echo $OPENAI_API_KEY | grep -E "^sk-"

# Test API connection
python -c "from backend.core.provider_factory import get_llm; print(get_llm())"
```

## Advanced Configuration

### Multiple Environments

Create separate `.env` files for each environment:

```bash
# Development
cp .env.example .env.dev
# Edit .env.dev with dev settings

# Production
cp .env.example .env.prod
# Edit .env.prod with prod settings
```

Load with environment variable:

```bash
# Load specific env file
ENV_FILE=.env.prod python -m backend.main
```

### Configuration Profiles

Python code can use configuration profiles:

```python
from backend.config import Settings

# Development profile
dev_config = Settings.for_development()

# Production profile
prod_config = Settings.for_production()
```

### Configuration Validation Script

Create `validate_config.sh`:

```bash
#!/bin/bash
set -e

echo "Validating configuration..."
python -m backend.config_validator

if [ $? -eq 0 ]; then
    echo "✅ Configuration valid"
    exit 0
else
    echo "❌ Configuration invalid"
    exit 1
fi
```

Make executable and use in CI/CD:

```bash
chmod +x validate_config.sh
./validate_config.sh
```

## Summary

✅ **Before:** Cryptic runtime errors, no guidance
✅ **After:** Clear error messages, actionable fixes, automatic validation
✅ **Better UX:** Developers know exactly what to do

The configuration system catches errors at startup, not at runtime, and provides helpful guidance for fixing them.
