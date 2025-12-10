# AWS Secrets Manager Quick Reference

## One-Minute Setup

### 1. Create a Secret (AWS CLI)

```bash
# OpenAI
aws secretsmanager create-secret \
    --name prod/llm/openai \
    --secret-string '{"api_key": "sk-proj-xxxxx"}' \
    --region us-east-1

# AWS Bedrock
aws secretsmanager create-secret \
    --name prod/aws/bedrock \
    --secret-string '{"access_key_id": "AKIA...", "secret_access_key": "wJalr..."}' \
    --region us-east-1
```

### 2. Configure .env

```dotenv
USE_SECRETS_MANAGER=true
SECRETS_MANAGER_REGION=us-east-1
OPENAI_SECRET_NAME=prod/llm/openai
AWS_BEDROCK_SECRET_NAME=prod/aws/bedrock
LLM_PROVIDER=openai
```

### 3. Use in Code

```python
from backend.config import get_settings

settings = get_settings()
settings.load_secrets_for_provider()
# API keys now loaded from Secrets Manager
```

## Commands Reference

### Create Secret
```bash
aws secretsmanager create-secret \
    --name <secret-name> \
    --secret-string <secret-value> \
    --region us-east-1
```

### Get Secret
```bash
aws secretsmanager get-secret-value \
    --secret-id <secret-name> \
    --region us-east-1
```

### List Secrets
```bash
aws secretsmanager list-secrets --region us-east-1
```

### Update Secret
```bash
aws secretsmanager update-secret \
    --secret-id <secret-name> \
    --secret-string <new-value> \
    --region us-east-1
```

### Delete Secret
```bash
aws secretsmanager delete-secret \
    --secret-id <secret-name> \
    --force-delete-without-recovery \
    --region us-east-1
```

## Environment Variables (Local Development)

Instead of AWS, use environment variables:

```bash
# Plain string
export SECRET_dev_llm_openai="sk-proj-xxxxx"

# JSON (must be escaped)
export SECRET_prod_aws_bedrock='{"access_key_id":"AKIA...","secret_access_key":"wJalr..."}'
```

Then in code:
```python
from backend.utils.secrets_manager import LocalSecretsManager

manager = LocalSecretsManager()
api_key = manager.get_secret_value("dev_llm_openai")
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `USE_SECRETS_MANAGER` | `false` | Enable AWS Secrets Manager |
| `SECRETS_MANAGER_REGION` | `us-east-1` | AWS region |
| `OPENAI_SECRET_NAME` | - | Secret name for OpenAI |
| `ANTHROPIC_SECRET_NAME` | - | Secret name for Anthropic |
| `COHERE_SECRET_NAME` | - | Secret name for Cohere |
| `AWS_BEDROCK_SECRET_NAME` | - | Secret name for AWS Bedrock |

## Secret Name Conventions

```
{environment}/{service}/{type}

Examples:
- prod/llm/openai
- prod/llm/anthropic
- prod/aws/bedrock
- dev/llm/openai
- staging/llm/cohere
```

## Cost Reference

| Item | Cost |
|------|------|
| Per secret/month | $0.40 |
| Per 10K API calls | $0.05 |
| First secret | Free (30 days) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `boto3 is required` | `pip install boto3` |
| Secret not found | Check secret name and region |
| Access denied | Update IAM policy |
| No credentials error | Configure AWS credentials |

## Python API

```python
from backend.utils.secrets_manager import SecretsManager

# Create manager
manager = SecretsManager(use_aws=True, region="us-east-1")

# Get entire secret
secret = manager.get_secret("prod/llm/openai")

# Get specific key
api_key = manager.get_secret_value("prod/llm/openai", key="api_key")

# Get plain string secret
value = manager.get_secret_value("prod/llm/openai")
```

## Integration Example

```python
from backend.config import get_settings
from backend.core.provider_factory import get_llm_provider

# Get configuration
settings = get_settings()

# Load secrets from Secrets Manager
if settings.use_secrets_manager:
    settings.load_secrets_for_provider()

# Create LLM provider (now with Secrets Manager credentials)
provider = get_llm_provider(settings)

# Use provider
response = provider.generate("Hello, how are you?")
```

## Links

- [AWS Secrets Manager Console](https://console.aws.amazon.com/secretsmanager/)
- [AWS CLI Secrets Manager Reference](https://docs.aws.amazon.com/cli/latest/reference/secretsmanager/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [Full Setup Guide](./AWS_SECRETS_MANAGER_SETUP.md)
