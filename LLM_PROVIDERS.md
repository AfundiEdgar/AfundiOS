# LLM Provider Flexibility

## Overview

The system now supports multiple LLM providers with a unified abstraction layer, allowing you to swap between:

- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude 3)
- **Cohere** (Command R+)
- **Local/Self-hosted** (Ollama, vLLM, etc.)

No code changes needed—configure via environment variables or `.env` file.

## Architecture

### Provider Abstraction

All providers implement a common `LLMProvider` interface:

```python
class LLMProvider(ABC):
    def generate(self, messages: List[Message]) -> str:
        """Generate response from messages."""
    
    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]]) -> str:
        """Chat-style interface with context and history."""
```

### Provider Factory

The `ProviderFactory` creates the correct provider based on configuration:

```python
from core.provider_factory import get_provider

provider = get_provider()
response = provider.chat(query="...", context="...")
```

## Configuration

### Via Environment Variables

```bash
# Provider selection
export LLM_PROVIDER="openai"          # or: anthropic, cohere, local

# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export COHERE_API_KEY="..."

# Model specification
export LLM_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.0"
export LLM_MAX_TOKENS="512"

# Local LLM (Ollama, vLLM, etc.)
export LOCAL_LLM_URL="http://localhost:8000/v1"
```

### Via `.env` File

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=512
```

### Via Python

```python
from core.provider_factory import ProviderFactory

# Create specific provider
provider = ProviderFactory.create_provider(
    provider_name="anthropic",
    model="claude-3-sonnet-20240229",
    api_key="sk-ant-...",
)

# Use it
response = provider.chat(query="...", context="...")
```

## Provider-Specific Setup

### OpenAI

**Models:** `gpt-4-turbo`, `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-...
```

**Installation:**
```bash
pip install openai
```

### Anthropic (Claude)

**Models:** `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-sonnet-20240229
export ANTHROPIC_API_KEY=sk-ant-...
```

**Installation:**
```bash
pip install anthropic
```

### Cohere

**Models:** `command-r-plus`, `command-r`, `command-light`

```bash
export LLM_PROVIDER=cohere
export LLM_MODEL=command-r-plus
export COHERE_API_KEY=...
```

**Installation:**
```bash
pip install cohere
```

### Local/Self-Hosted

Works with any OpenAI-compatible API (Ollama, vLLM, LocalAI, etc.)

**Ollama Example:**

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull mistral`
3. Start server: `ollama serve`
4. Configure:
```bash
export LLM_PROVIDER=local
export LOCAL_LLM_URL=http://localhost:11434/v1
export LLM_MODEL=mistral
```

**vLLM Example:**

```bash
python -m vllm.entrypoints.openai.api_server --model mistral-7b

export LLM_PROVIDER=local
export LOCAL_LLM_URL=http://localhost:8000/v1
export LLM_MODEL=mistral-7b
```

## Usage Examples

### Single-turn Query

```python
from core.pipeline import run_query
from models.request_models import QueryRequest

request = QueryRequest(
    query="What is machine learning?",
    top_k=5,
)
response = run_query(request)
print(response.answer)  # LLM response using configured provider
```

### Multi-turn Conversation

```python
request = QueryRequest(
    query="How is it different from deep learning?",
    session_id="user_123",
    chat_history=[
        ("What is machine learning?", "Machine learning is..."),
    ],
)
response = run_query(request)
```

### Direct Provider Usage

```python
from core.provider_factory import get_provider

provider = get_provider()

# Single generation
from core.providers import Message
messages = [
    Message("system", "You are helpful."),
    Message("user", "What is AI?"),
]
response = provider.generate(messages)

# Chat with context
response = provider.chat(
    query="Explain neural networks",
    context="Neural networks are...",
    history=[("What is ML?", "ML is...")],
)
```

## Switching Providers

### Development

Start with **local** (Ollama) for free testing:
```bash
ollama pull mistral
ollama serve

# In .env
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/v1
LLM_MODEL=mistral
```

### Production

Use **OpenAI** for reliability:
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

Or **Anthropic** for cost/quality tradeoff:
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

## Performance & Cost

| Provider | Model | Speed | Cost | Quality |
|----------|-------|-------|------|---------|
| OpenAI | gpt-4o-mini | Fast | $0.15/1M tokens | Excellent |
| Anthropic | claude-3-sonnet | Fast | $3/1M tokens | Excellent |
| Cohere | command-r-plus | Medium | $3/1M tokens | Very Good |
| Local | mistral-7b | Variable | Free | Good |

## Error Handling

If a provider fails to initialize:

1. **API Key missing**: Raises `ValueError` with clear message
2. **Network error**: Falls back to stub response
3. **Invalid model**: Provider returns error message

Example:
```python
try:
    response = synthesize_answer(query="...", contexts=[...])
except ValueError as e:
    print(f"Configuration error: {e}")  # API key not found
```

## Adding a New Provider

Create a subclass of `LLMProvider`:

```python
from .providers import LLMProvider, Message

class MyProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key
    
    def generate(self, messages: List[Message]) -> str:
        # Call your provider's API
        pass
    
    def chat(self, query: str, context: str, history=None) -> str:
        # Implement chat interface
        pass
```

Register in `provider_factory.py`:

```python
elif provider_name.lower() == "myprovider":
    api_key = kwargs.get("api_key") or os.getenv("MYPROVIDER_API_KEY")
    return MyProvider(api_key=api_key, model=model, **kwargs)
```

## Testing

```python
from core.provider_factory import ProviderFactory, set_provider
from core.providers import LLMProvider, Message

class MockProvider(LLMProvider):
    def generate(self, messages):
        return "Mock response"
    
    def chat(self, query, context, history=None):
        return "Mock response"

# In tests
mock = MockProvider("test-model")
set_provider(mock)
```

## Troubleshooting

### "LLM provider error"
- Check `LLM_PROVIDER` setting
- Verify API key is set correctly
- Check network connectivity (for API providers)

### "Unknown LLM provider: X"
- Verify provider name: openai, anthropic, cohere, local
- Check for typos in `LLM_PROVIDER` env var

### Model not found
- Verify `LLM_MODEL` is valid for the provider
- Check provider documentation for available models

### Slow responses
- Local models are slower; use cloud provider for speed
- Check system resources for local deployments
- Reduce `LLM_MAX_TOKENS` if needed

## Future Enhancements

1. **Streaming responses** - Stream tokens as generated
2. **Fallback chains** - Try provider A, fallback to B
3. **Cost tracking** - Monitor API usage per provider
4. **Model routing** - Use different models for different queries
5. **Batch processing** - Process multiple queries efficiently
6. **Fine-tuning support** - Support custom fine-tuned models
