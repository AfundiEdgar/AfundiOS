# AWS Secrets Manager Setup Guide

## Overview

AWS Secrets Manager is a secure way to store and retrieve API keys, database credentials, and other sensitive information without keeping them in `.env` files or source code.

This guide walks you through setting up AWS Secrets Manager with your AfundiOS backend for secure credential management.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Creating Secrets](#creating-secrets)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Local Development](#local-development)
8. [Cost Estimation](#cost-estimation)
9. [Best Practices](#best-practices)
10. [Migration Guide](#migration-guide)

## Prerequisites

### Required

- AWS Account with appropriate IAM permissions
- Python 3.8+ (already have this)
- `boto3` library (AWS SDK for Python)
- Access to AWS Secrets Manager service in your region

### Optional but Recommended

- AWS CLI configured with credentials
- AWS Management Console access
- Understanding of JSON and environment variables

## Setup Instructions

### Step 1: Install boto3

If not already installed (required for AWS Bedrock):

```bash
pip install boto3
```

### Step 2: Verify AWS Credentials

Ensure your AWS credentials are configured. boto3 will automatically detect credentials from:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. AWS config file (`~/.aws/config`)
4. IAM role (if running on EC2 or AWS Lambda)
5. ECS task role (if running on ECS)

Check your credentials:

```bash
# Using AWS CLI
aws sts get-caller-identity

# Or in Python
import boto3
session = boto3.Session()
print(session.get_credentials())
```

### Step 3: Create IAM Policy (Recommended)

For security, create an IAM user with minimal permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:*:ACCOUNT_ID:secret:prod/*"
        }
    ]
}
```

Replace `ACCOUNT_ID` with your AWS account ID and adjust the resource ARN pattern as needed.

### Step 4: Create a Secret in AWS

**Using AWS Management Console:**

1. Go to AWS Secrets Manager: https://console.aws.amazon.com/secretsmanager/
2. Click "Store a new secret"
3. Choose "Other type of secret"
4. Enter your secret as JSON or plain text
5. Give it a name (e.g., `prod/llm/openai`)
6. Complete the setup

**Using AWS CLI:**

```bash
# For OpenAI API key (JSON secret)
aws secretsmanager create-secret \
    --name prod/llm/openai \
    --secret-string '{"api_key": "sk-proj-xxxxx"}' \
    --region us-east-1

# For plain string secret
aws secretsmanager create-secret \
    --name prod/llm/openai \
    --secret-string "sk-proj-xxxxx" \
    --region us-east-1

# For AWS Bedrock (JSON with multiple fields)
aws secretsmanager create-secret \
    --name prod/aws/bedrock \
    --secret-string '{
        "access_key_id": "AKIA...",
        "secret_access_key": "wJalr..."
    }' \
    --region us-east-1
```

## Creating Secrets

### Secret Naming Convention

Use hierarchical names for better organization:

```
{environment}/{service}/{credential_type}

Examples:
- prod/llm/openai
- prod/llm/anthropic
- prod/aws/bedrock
- dev/llm/openai
- staging/llm/cohere
```

### Secret Formats

#### For API Key Providers (OpenAI, Anthropic, Cohere)

**As JSON:**
```json
{
    "api_key": "sk-proj-xxxxxxxxxxxxx"
}
```

**As Plain String:**
```
sk-proj-xxxxxxxxxxxxx
```

#### For AWS Bedrock

**As JSON (Required):**
```json
{
    "access_key_id": "AKIA...",
    "secret_access_key": "wJalr...",
    "region": "us-east-1"
}
```

#### For Multiple Credentials

```json
{
    "api_key": "sk-xxxxx",
    "org_id": "org-xxxxx",
    "account_id": "acc-xxxxx"
}
```

## Configuration

### Enable Secrets Manager

Update your `.env` file:

```dotenv
# Enable AWS Secrets Manager
USE_SECRETS_MANAGER=true

# Specify AWS region
SECRETS_MANAGER_REGION=us-east-1

# Configure secret names for your providers
OPENAI_SECRET_NAME=prod/llm/openai
ANTHROPIC_SECRET_NAME=prod/llm/anthropic
COHERE_SECRET_NAME=prod/llm/cohere
AWS_BEDROCK_SECRET_NAME=prod/aws/bedrock

# Set your LLM provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Local LLM (optional)
# You can store local LLM credentials (URL and/or API key) in Secrets Manager.
# Example secret (JSON):
# {
#   "url": "http://localhost:8000/v1",
#   "api_key": "sk-local-xxxxx"
# }
# Set the secret name in .env to allow automatic loading for LLM_PROVIDER=local
# Example:
# LOCAL_LLM_SECRET_NAME=dev/llm/local-ollama
```

### Configuration Priority

When you enable Secrets Manager, the configuration system follows this priority:

1. **Secrets Manager** (if `USE_SECRETS_MANAGER=true` and secret exists)
2. **Environment Variables** (AWS_ACCESS_KEY_ID, etc.)
3. **.env File** (Direct credentials)

This allows gradual migration from .env to Secrets Manager.

## Usage Examples

### Basic Usage

```python
from backend.config import get_settings

# Get configuration
settings = get_settings()

# Fetch a secret
api_key = settings.get_secret("prod/llm/openai", key="api_key")
print(f"OpenAI API Key: {api_key}")

# Load credentials for the configured provider
settings.load_secrets_for_provider()
# Now settings.openai_api_key is populated from Secrets Manager
```

### Advanced Usage

```python
from backend.utils.secrets_manager import SecretsManager

# Create manager (auto-selects AWS or local based on USE_SECRETS_MANAGER)
manager = SecretsManager(use_aws=True, region="us-east-1")

# Get entire secret
full_secret = manager.get_secret("prod/aws/bedrock")
print(full_secret)
# Output: {'access_key_id': 'AKIA...', 'secret_access_key': 'wJalr...'}

# Get specific key from JSON secret
access_key = manager.get_secret_value("prod/aws/bedrock", key="access_key_id")
print(f"Access Key: {access_key}")

# Get plain string secret
api_key = manager.get_secret_value("prod/llm/openai")
print(f"API Key: {api_key}")
```

### Using Environment Variables (Local Development)

For local development without AWS access, use environment variables:

```bash
# Instead of connecting to AWS, use local environment variables
export SECRET_prod_llm_openai=sk-proj-xxxxx
export SECRET_prod_aws_bedrock='{"access_key_id":"AKIA...","secret_access_key":"wJalr..."}'

# Set this to disable AWS Secrets Manager
export USE_SECRETS_MANAGER=false
```

Then use the same code:

```python
from backend.utils.secrets_manager import SecretsManager

# This will use environment variables instead of AWS
manager = SecretsManager(use_aws=False)
api_key = manager.get_secret_value("prod_llm_openai")
```

### Application Integration

```python
# In your main.py or startup code
from backend.config import get_settings
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    
    # Load secrets from Secrets Manager if enabled
    if settings.use_secrets_manager:
        settings.load_secrets_for_provider()
        print(f"Loaded {settings.llm_provider} credentials from Secrets Manager")
    else:
        print("Using credentials from .env file")
```

## Troubleshooting

### Issue: "boto3 is required for AWS Secrets Manager"

**Solution:**
```bash
pip install boto3
```

### Issue: "ResourceNotFoundException"

**Symptoms:** Error says secret doesn't exist

**Causes:**
- Secret name is incorrect
- Secret is in a different AWS region
- IAM user doesn't have permission to access the secret

**Solutions:**
```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1

# Check secret exists
aws secretsmanager describe-secret --secret-id prod/llm/openai --region us-east-1

# Grant permissions (update IAM policy)
# See "Step 3: Create IAM Policy" above
```

### Issue: "InvalidRequestException" or "InvalidParameterException"

**Causes:**
- Invalid AWS credentials
- Incorrect region
- IAM permissions insufficient

**Solutions:**
```bash
# Test credentials
aws sts get-caller-identity

# Check current region
echo $AWS_DEFAULT_REGION
aws configure get region

# Update credentials
aws configure
```

### Issue: Credentials not loading in application

**Check:**
1. `USE_SECRETS_MANAGER=true` is set in `.env`
2. Secret name is configured: `OPENAI_SECRET_NAME=prod/llm/openai`
3. AWS credentials are configured
4. Secret exists: `aws secretsmanager describe-secret --secret-id prod/llm/openai`

**Debug:**
```python
from backend.config import get_settings
import logging

logging.basicConfig(level=logging.DEBUG)

settings = get_settings()
print(f"Secrets Manager Enabled: {settings.use_secrets_manager}")
print(f"Region: {settings.secrets_manager_region}")
print(f"OpenAI Secret Name: {settings.openai_secret_name}")

# Try loading
settings.load_secrets_for_provider()
```

### Issue: "NoCredentialsError"

**Causes:**
- AWS credentials not configured
- boto3 can't find credentials
- IAM role not attached (if on AWS service)

**Solutions:**
```bash
# Option 1: Configure AWS CLI
aws configure

# Option 2: Set environment variables
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=wJalr...
export AWS_DEFAULT_REGION=us-east-1

# Option 3: Check IAM role (if on EC2/ECS)
# Ensure instance has IAM role with Secrets Manager permissions
```

## Local Development

### Development Setup (without AWS)

For local development, use environment variables:

```bash
# .env file
USE_SECRETS_MANAGER=false

# Or use environment variables for specific secrets
export SECRET_dev_llm_openai=sk-proj-xxxxx
```

### Staging Setup (with AWS)

For staging/testing with AWS Secrets Manager:

```bash
# .env file
USE_SECRETS_MANAGER=true
SECRETS_MANAGER_REGION=us-east-1
OPENAI_SECRET_NAME=dev/llm/openai
LLM_PROVIDER=openai
```

### Production Setup

For production:

```bash
# .env file
USE_SECRETS_MANAGER=true
SECRETS_MANAGER_REGION=us-east-1
OPENAI_SECRET_NAME=prod/llm/openai
AWS_BEDROCK_SECRET_NAME=prod/aws/bedrock
```

## Cost Estimation

### AWS Secrets Manager Pricing (as of 2024)

- **Storage:** $0.40 per secret per month
- **API Calls:** $0.05 per 10,000 API calls
- **Rotation:** Free (if using built-in rotation, additional service charges apply)

### Example Monthly Costs

| Setup | Secrets | API Calls/Month | Monthly Cost |
|-------|---------|-----------------|--------------|
| Development | 3 | 10,000 | $1.20 |
| Staging | 5 | 100,000 | $2.50 |
| Production | 8 | 1,000,000 | $7.40 |

**Notes:**
- First secret is free for 30 days
- API call volume depends on application traffic
- Consider CloudFront caching to reduce API calls
- Enable secret caching in your application for better performance

## Best Practices

### 1. Secret Naming

✓ Do:
- Use hierarchical names: `env/service/credential`
- Use lowercase with hyphens: `prod/llm-providers/openai`
- Include environment: `prod`, `staging`, `dev`

✗ Don't:
- Use generic names: `api_key`, `secret`
- Mix environments: don't store prod and dev in same secret
- Include sensitive data in names

### 2. Security

✓ Do:
- Use IAM policies to restrict access
- Rotate secrets regularly
- Enable CloudTrail logging
- Use separate credentials per environment
- Monitor secret access

✗ Don't:
- Share access credentials widely
- Store multiple services' secrets in one secret
- Commit Secrets Manager configuration to source control (use secure secret management for that too)
- Log or print secret values

### 3. Performance

✓ Do:
- Cache secrets in memory (avoid repeated API calls)
- Use secret caching clients
- Batch secret retrievals
- Consider secret expiration and rotation

✗ Don't:
- Fetch secrets on every request
- Store secrets in logs
- Make unnecessary API calls

### 4. Monitoring

✓ Do:
- Enable CloudTrail for audit logging
- Set up CloudWatch alarms for secret access
- Monitor failed authentication attempts
- Track secret rotation events

✗ Don't:
- Ignore failed secret access attempts
- Leave CloudTrail disabled in production
- Disable audit logging

## Migration Guide

### From .env to Secrets Manager

**Step 1: Create secrets in AWS**

```bash
# Create OpenAI secret
aws secretsmanager create-secret \
    --name prod/llm/openai \
    --secret-string '{"api_key": "sk-proj-xxxxx"}'

# Create other secrets as needed
```

**Step 2: Update .env configuration**

```dotenv
# Before
USE_SECRETS_MANAGER=false
OPENAI_API_KEY=sk-proj-xxxxx

# After
USE_SECRETS_MANAGER=true
OPENAI_SECRET_NAME=prod/llm/openai
```

**Step 3: Update application code (optional)**

```python
# Option 1: Automatic (recommended)
from backend.config import get_settings

settings = get_settings()
settings.load_secrets_for_provider()
# credentials are now loaded from Secrets Manager

# Option 2: Manual
api_key = settings.get_secret("prod/llm/openai", key="api_key")
```

**Step 4: Verify and test**

```bash
# Test application
python -m backend.config_validator

# Check logs
grep -i "secret" application.log
```

**Step 5: Remove old .env credentials (optional)**

```dotenv
# Remove these lines after migration
# OPENAI_API_KEY=sk-proj-xxxxx
# AWS_ACCESS_KEY_ID=AKIA...
```

### Gradual Migration

You don't need to migrate all secrets at once:

1. Create secrets in Secrets Manager
2. Configure in `.env`
3. Enable Secrets Manager: `USE_SECRETS_MANAGER=true`
4. The system will use Secrets Manager for configured secrets, fall back to .env for others

## Frequently Asked Questions

### Q: Can I rotate secrets automatically?

**A:** Yes. AWS Secrets Manager supports automatic rotation:
1. Configure rotation in Secrets Manager console
2. Use Lambda functions for custom rotation logic
3. Application automatically gets new secrets

### Q: What if Secrets Manager is unavailable?

**A:** The application will:
1. Log an error
2. Fall back to environment variables or .env file if configured
3. Continue running (secrets won't be updated)

Implement fallback strategy:
```python
try:
    api_key = settings.get_secret("prod/llm/openai", key="api_key")
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")
```

### Q: Can I use Secrets Manager with local development?

**A:** Yes! Use the local secrets manager:
```bash
export USE_SECRETS_MANAGER=false
export SECRET_dev_llm_openai=sk-proj-xxxxx
```

### Q: How do I grant team members access?

**A:** Use IAM policies:
```json
{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:*:*:secret:prod/*"
}
```

### Q: Is there a free tier?

**A:** 
- First secret: free for 30 days
- $0.40/secret/month after that
- API calls: $0.05 per 10,000 calls

Perfect for small teams and development environments.

### Q: Can I use Secrets Manager for database passwords?

**A:** Yes! Store database credentials the same way:
```json
{
    "host": "db.example.com",
    "username": "admin",
    "password": "secure-password",
    "port": 5432
}
```

## Related Documentation

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [boto3 Secrets Manager Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [IAM Policy Examples](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_examples.html)

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
3. Check CloudWatch logs for application errors
4. Test credentials with AWS CLI: `aws sts get-caller-identity`
