# AWS Bedrock Nova Lite Integration

Quick setup guide for using AWS Nova Lite with AfundiOS.

## Overview

AWS Bedrock now supports Amazon Nova models:
- **Nova Lite** (fastest, most cost-effective)
- **Nova Pro** (balanced)
- **Haiku** (through Claude)

## Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS Credentials** (Access Key ID + Secret Access Key)
3. **boto3** installed (already in requirements.txt)

## Setup Steps

### 1. Get AWS Credentials

Visit: https://console.aws.amazon.com/iam/

1. Click "Users" in left sidebar
2. Click your username
3. Go to "Security credentials" tab
4. Click "Create access key"
5. Copy the **Access Key ID** and **Secret Access Key**

### 2. Update Configuration

Edit your `.env` file:

```bash
# Enable AWS Bedrock
LLM_PROVIDER=aws_bedrock

# Choose a model
LLM_MODEL=amazon.nova-lite-v1:0

# Add AWS credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Optional: Set region (default: us-east-1)
AWS_REGION=us-east-1
```

### 3. Validate Configuration

```bash
python -m backend.config_validator
```

Expected output:
```
✅ Environment variables validated
✅ LLM Configuration valid (Provider: aws_bedrock)
✅ Vector Store Configuration valid
✅ All configurations OK
```

### 4. Test It

```bash
python -c "
from backend.core.provider_factory import ProviderFactory
provider = ProviderFactory.create_provider('aws_bedrock', 'amazon.nova-lite-v1:0')
response = provider.chat('Hello', 'Say hello back', None)
print('Response:', response)
"
```

## Available Models

### Amazon Nova Models

| Model | ID | Speed | Cost | Context |
|-------|-----|-------|------|---------|
| Nova Lite | `amazon.nova-lite-v1:0` | ⚡⚡⚡ Fast | 💰 Cheapest | 4K tokens |
| Nova Pro | `amazon.nova-pro-v1:0` | ⚡⚡ Medium | 💰💰 Moderate | 4K tokens |

### Via AWS Bedrock (Anthropic)

| Model | ID | Speed | Cost |
|-------|-----|-------|------|
| Claude 3 Haiku | `anthropic.claude-3-haiku-20240307-v1:0` | ⚡⚡⚡ | 💰 |
| Claude 3 Sonnet | `anthropic.claude-3-sonnet-20240229-v1:0` | ⚡⚡ | 💰💰 |

## Pricing (as of 2024)

### Amazon Nova Lite
- Input: $0.075 per 1M tokens (~40% cheaper than GPT-3.5)
- Output: $0.30 per 1M tokens

### Amazon Nova Pro
- Input: $0.80 per 1M tokens
- Output: $3.20 per 1M tokens

## Environment Variables

```bash
# Required
LLM_PROVIDER=aws_bedrock
LLM_MODEL=amazon.nova-lite-v1:0
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional
AWS_REGION=us-east-1  # Default: us-east-1
LLM_TEMPERATURE=0.7   # 0.0-1.0, default: 0.0
LLM_MAX_TOKENS=512    # default: 512
```

## Usage in Code

### Basic Usage

```python
from backend.core.provider_factory import ProviderFactory

# Create provider
provider = ProviderFactory.create_provider()

# Generate response
response = provider.chat(
    query="What is machine learning?",
    context="Machine learning is...",
    history=None
)
print(response)
```

### Using AWSBedrockLLM Directly

```python
from backend.core.aws_bedrock_llm import AWSBedrockLLM

llm = AWSBedrockLLM(
    access_key_id="your-key",
    secret_access_key="your-secret",
    region="us-east-1",
    model="amazon.nova-lite-v1:0"
)

response = llm.generate(
    prompt="Explain machine learning in 50 words",
    max_tokens=100,
    temperature=0.7
)
print(response)
```

## Troubleshooting

### Error: "No credentials found"

Make sure AWS credentials are set:
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

Or add to `.env`:
```
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### Error: "InvalidSignatureException"

Check that:
1. Access Key ID is correct
2. Secret Access Key is correct
3. Region is valid (e.g., `us-east-1`)

### Error: "AccessDenied"

Check that:
1. Your AWS account has Bedrock enabled
2. Your IAM user has `bedrock:InvokeModel` permission
3. You have the correct region where models are available

### Model Not Available

Amazon Nova is available in these regions:
- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)

Set correct region:
```bash
AWS_REGION=eu-west-1
```

## Performance Tips

### 1. Use Nova Lite for Speed & Cost
- 40% cheaper than GPT-3.5
- Great for RAG retrieval-augmented generation
- Perfect for production use

### 2. Cache Responses
AfundiOS already caches LLM responses. Enable caching in config:
```bash
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

### 3. Optimize Token Usage
- Reduce `LLM_MAX_TOKENS` for shorter responses
- Summarize long context before passing to LLM
- Use lower `CHUNK_SIZE` for more focused context

### 4. Batch Requests
For multiple queries, batch them to reduce overhead.

## Pricing Comparison

Approximate cost for processing 100K document tokens:

| Model | Input Cost | Output Cost (if 2x input) | Total |
|-------|-----------|--------------------------|-------|
| Nova Lite | $0.0075 | $0.030 | **$0.0375** ✅ |
| GPT-3.5 | $0.0125 | $0.050 | $0.0625 |
| Nova Pro | $0.080 | $0.320 | $0.40 |
| GPT-4 | $0.30 | $0.60 | $0.90 |

**Nova Lite saves ~40% vs GPT-3.5 and ~95% vs GPT-4!**

## Migration from OpenAI

```python
# Before (OpenAI)
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-...

# After (AWS Bedrock)
LLM_PROVIDER=aws_bedrock
LLM_MODEL=amazon.nova-lite-v1:0
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

No code changes needed! Just update `.env` and restart.

## Support & Documentation

- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/
- **Nova Models**: https://aws.amazon.com/bedrock/nova/
- **IAM Setup**: https://docs.aws.amazon.com/iam/latest/userguide/id_credentials_access-keys.html

## FAQ

**Q: Is Nova Lite suitable for production?**
A: Yes! It's designed for production use with good quality and fast responses.

**Q: Can I switch between providers without code changes?**
A: Yes! Just update `.env` and restart the application.

**Q: What's the difference between Nova Lite and Nova Pro?**
A: Nova Pro is more capable but slower and more expensive. Nova Lite is optimized for speed and cost.

**Q: Do I need to enable Bedrock in AWS Console?**
A: Check your Bedrock access. Visit https://console.aws.amazon.com/bedrock/

**Q: How do I get better responses from Nova?**
A: Provide clear context, use appropriate temperature (0.0-0.7), and keep prompts concise.

---

Ready to use AWS Nova Lite? Let's go! 🚀
