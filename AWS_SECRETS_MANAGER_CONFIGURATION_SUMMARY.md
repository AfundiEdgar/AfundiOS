# AWS Secrets Manager Configuration Summary

## What Was Configured

A complete AWS Secrets Manager stub implementation has been integrated into your AfundiOS backend for secure credential management.

## Files Created

### 1. `backend/utils/secrets_manager.py` (460+ lines)
**Purpose:** Core Secrets Manager client with AWS and local implementations

**Key Classes:**
- `SecretsManager` - Unified interface for secrets management
- `AWSSecretsManager` - AWS Secrets Manager implementation (boto3-based)
- `LocalSecretsManager` - Local environment variable implementation
- `SecretsManagerError` - Custom exception class

**Features:**
- Automatic AWS/Local selection based on `USE_SECRETS_MANAGER` setting
- Support for JSON and plain string secrets
- Credential caching and lazy-loading
- Comprehensive error messages with troubleshooting hints
- Full boto3 integration for AWS API calls

### 2. `AWS_SECRETS_MANAGER_SETUP.md` (500+ lines)
**Purpose:** Comprehensive setup and integration guide

**Sections:**
- Prerequisites and requirements
- Step-by-step setup instructions
- Creating secrets via AWS console and CLI
- Configuration options and priority
- 10+ usage examples with code
- Troubleshooting guide (8+ common issues)
- Local development setup
- Cost estimation ($0.40-$7.40/month typical)
- Best practices and security guidelines
- Migration guide from .env to Secrets Manager
- Frequently asked questions

### 3. `AWS_SECRETS_MANAGER_QUICK_REFERENCE.md` (140+ lines)
**Purpose:** Quick reference for common operations

**Includes:**
- One-minute setup instructions
- AWS CLI command reference
- Environment variable quick setup
- Configuration options table
- Cost reference
- Troubleshooting quick lookup
- Python API examples
- Integration examples

## Files Modified

### 1. `backend/config.py` (345 → 447 lines)

**Changes:**
- Added `logging` import
- Added Secrets Manager configuration section:
  - `use_secrets_manager: bool` - Enable/disable Secrets Manager
  - `secrets_manager_region: str` - AWS region for Secrets Manager
  - `openai_secret_name: Optional[str]` - OpenAI secret name
  - `anthropic_secret_name: Optional[str]` - Anthropic secret name
  - `cohere_secret_name: Optional[str]` - Cohere secret name
  - `aws_bedrock_secret_name: Optional[str]` - AWS Bedrock secret name

- Added two new methods to Settings class:
  - `get_secret(secret_name, key=None)` - Fetch secrets from Secrets Manager
  - `load_secrets_for_provider()` - Auto-load credentials for configured LLM provider

**Features:**
- Method docstrings with examples
- Automatic provider detection
- Credentials loaded from Secrets Manager on demand
- Fallback to environment variables if Secrets Manager disabled
- Comprehensive error handling with logging

### 2. `.env.example` (182 → 210 lines)

**Added Section:**
- "AWS Secrets Manager Configuration (Optional)"
- Configuration options with defaults
- Environment variable descriptions
- Usage instructions
- Links to documentation

**New Variables:**
- `USE_SECRETS_MANAGER` - Enable/disable Secrets Manager
- `SECRETS_MANAGER_REGION` - AWS region
- `OPENAI_SECRET_NAME` - OpenAI secret name
- `ANTHROPIC_SECRET_NAME` - Anthropic secret name
- `COHERE_SECRET_NAME` - Cohere secret name
- `AWS_BEDROCK_SECRET_NAME` - AWS Bedrock secret name

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Your Application                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │    Settings (config.py)        │
        │  - get_secret()                │
        │  - load_secrets_for_provider() │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  SecretsManager            │
        │  (secrets_manager.py)      │
        │  - Unified interface       │
        └────┬──────────────┬────────┘
             │              │
             ▼              ▼
      ┌─────────────┐  ┌──────────────┐
      │   AWS       │  │   Local      │
      │ Secrets     │  │ Environment  │
      │ Manager     │  │ Variables    │
      │ (boto3)     │  │              │
      └─────────────┘  └──────────────┘
             │              │
             ▼              ▼
      AWS_REGION        ENVIRONMENT
```

### Data Flow

1. **Initialization:**
   - Settings loads configuration from .env
   - `use_secrets_manager` flag determines which backend to use

2. **Credential Retrieval:**
   - `get_secret()` called with secret name and optional key
   - SecretsManager routes to AWS or Local backend
   - Result returned to caller

3. **Provider Loading:**
   - `load_secrets_for_provider()` called on Settings object
   - Automatically determines which credentials to fetch based on `llm_provider`
   - Populates API key fields from Secrets Manager
   - Falls back to .env if secret doesn't exist

## Configuration Flow

### Using AWS Secrets Manager

1. Create secret in AWS Secrets Manager
2. Set `USE_SECRETS_MANAGER=true` in .env
3. Configure secret names: `OPENAI_SECRET_NAME=prod/llm/openai`
4. Call `settings.load_secrets_for_provider()`
5. Credentials automatically loaded from AWS

### Using Environment Variables (Local)

1. Set `USE_SECRETS_MANAGER=false` in .env
2. Or use `SECRET_*` environment variables
3. Call `settings.get_secret("secret_name")`
4. Credentials loaded from environment

### Fallback Chain

```
Secret Request
       ↓
AWS Secrets Manager? (if enabled)
       ↓ (fail)
Environment Variables?
       ↓ (fail)
.env File Values?
       ↓ (fail)
Error / None
```

## Usage Examples

### Simple Usage (Recommended)

```python
from backend.config import get_settings

settings = get_settings()

# Load secrets for configured provider
settings.load_secrets_for_provider()

# Now use credentials
print(f"Provider: {settings.llm_provider}")
print(f"API Key loaded: {settings.openai_api_key is not None}")
```

### Manual Secret Retrieval

```python
from backend.config import get_settings

settings = get_settings()

# Get secret
api_key = settings.get_secret("prod/llm/openai", key="api_key")
if api_key:
    print(f"API Key: {api_key}")
else:
    print("Secret not found")
```

### Direct Manager Usage

```python
from backend.utils.secrets_manager import SecretsManager

# Create manager (auto-selects AWS or local)
manager = SecretsManager(use_aws=True, region="us-east-1")

# Get entire secret
secret = manager.get_secret("prod/aws/bedrock")
access_key = secret["access_key_id"]
secret_key = secret["secret_access_key"]

# Or get specific key
api_key = manager.get_secret_value("prod/llm/openai", key="api_key")
```

### Environment Variable Secrets (Local Development)

```bash
# Set environment variables
export SECRET_dev_llm_openai="sk-proj-xxxxx"
export SECRET_prod_aws_bedrock='{"access_key_id":"AKIA...","secret_access_key":"wJalr..."}'

# In .env
USE_SECRETS_MANAGER=false

# In code
from backend.utils.secrets_manager import LocalSecretsManager

manager = LocalSecretsManager()
api_key = manager.get_secret_value("dev_llm_openai")
```

## Security Features

1. **No Credentials in Code**
   - Secrets retrieved at runtime
   - Never hardcoded or in version control

2. **AWS IAM Integration**
   - Credentials validated through AWS
   - IAM policies control access
   - CloudTrail logs all access

3. **Local Fallback**
   - For development without AWS
   - Environment variables kept separate from code

4. **Error Handling**
   - Graceful fallbacks
   - Detailed error messages
   - Security-conscious logging (no secret values logged)

5. **Access Control**
   - JSON secrets with multiple credentials
   - Selective key extraction
   - Role-based access via IAM

## Configuration Options

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `USE_SECRETS_MANAGER` | bool | `false` | Enable AWS Secrets Manager |
| `SECRETS_MANAGER_REGION` | str | `us-east-1` | AWS region for Secrets Manager |
| `OPENAI_SECRET_NAME` | Optional[str] | `None` | AWS secret name for OpenAI |
| `ANTHROPIC_SECRET_NAME` | Optional[str] | `None` | AWS secret name for Anthropic |
| `COHERE_SECRET_NAME` | Optional[str] | `None` | AWS secret name for Cohere |
| `AWS_BEDROCK_SECRET_NAME` | Optional[str] | `None` | AWS secret name for AWS Bedrock |

## Supported LLM Providers

All existing LLM providers are supported:

| Provider | Configuration | Secret Format |
|----------|---------------|---------------|
| OpenAI | `OPENAI_SECRET_NAME` | `{"api_key": "sk-..."}` |
| Anthropic | `ANTHROPIC_SECRET_NAME` | `{"api_key": "sk-ant-..."}` |
| Cohere | `COHERE_SECRET_NAME` | `{"api_key": "..."}` |
| AWS Bedrock | `AWS_BEDROCK_SECRET_NAME` | `{"access_key_id": "...", "secret_access_key": "..."}` |
| Local | None | N/A |

## Getting Started

### For Local Development

1. Update `.env`:
   ```dotenv
   USE_SECRETS_MANAGER=false
   ```

2. Set environment variables:
   ```bash
   export SECRET_dev_llm_openai="sk-proj-xxxxx"
   ```

3. Use in code:
   ```python
   from backend.config import get_settings
   settings = get_settings()
   settings.load_secrets_for_provider()
   ```

### For Production

1. Create secrets in AWS:
   ```bash
   aws secretsmanager create-secret \
       --name prod/llm/openai \
       --secret-string '{"api_key": "sk-proj-xxxxx"}'
   ```

2. Update `.env`:
   ```dotenv
   USE_SECRETS_MANAGER=true
   SECRETS_MANAGER_REGION=us-east-1
   OPENAI_SECRET_NAME=prod/llm/openai
   ```

3. Use in code (same as above):
   ```python
   from backend.config import get_settings
   settings = get_settings()
   settings.load_secrets_for_provider()
   ```

## Troubleshooting

### Issue: "boto3 is required"
- Install boto3: `pip install boto3`

### Issue: Secret not found
- Verify secret exists: `aws secretsmanager describe-secret --secret-id prod/llm/openai`
- Check region: `SECRETS_MANAGER_REGION=us-east-1`

### Issue: Access denied
- Check IAM policy has `secretsmanager:GetSecretValue` permission
- Verify AWS credentials are configured

### Issue: Using local variables
- Ensure `USE_SECRETS_MANAGER=false`
- Export environment variables: `export SECRET_name=value`

See `AWS_SECRETS_MANAGER_SETUP.md` for detailed troubleshooting.

## Cost Analysis

### Monthly Cost Examples

| Environment | Secrets | API Calls | Cost |
|-------------|---------|-----------|------|
| Development | 3 | 10,000 | $1.20 |
| Staging | 5 | 100,000 | $2.50 |
| Production | 8 | 1,000,000 | $7.40 |

- First secret: Free for 30 days
- Storage: $0.40/secret/month
- API calls: $0.05 per 10,000 calls

## Next Steps

1. **For Local Development:**
   - Use environment variables (no AWS needed)
   - Set `USE_SECRETS_MANAGER=false`

2. **For Staging/Production:**
   - Create secrets in AWS Secrets Manager
   - Set `USE_SECRETS_MANAGER=true`
   - Configure secret names in .env
   - Ensure IAM permissions are set

3. **For Migration:**
   - Start with environment variables
   - Gradually move to AWS Secrets Manager
   - System supports both simultaneously

## Related Documentation

- [AWS_SECRETS_MANAGER_SETUP.md](./AWS_SECRETS_MANAGER_SETUP.md) - Full setup guide
- [AWS_SECRETS_MANAGER_QUICK_REFERENCE.md](./AWS_SECRETS_MANAGER_QUICK_REFERENCE.md) - Quick reference
- [AWS Bedrock Integration](./AWS_BEDROCK_NOVA_SETUP.md) - AWS Bedrock setup
- [Configuration Documentation](./backend/config.py) - Config module

## Support

For detailed setup instructions, see:
- `AWS_SECRETS_MANAGER_SETUP.md` - Full guide with all options
- `AWS_SECRETS_MANAGER_QUICK_REFERENCE.md` - Quick lookup reference

For AWS Bedrock integration with Secrets Manager, see:
- `AWS_BEDROCK_NOVA_SETUP.md` - AWS Bedrock setup guide
