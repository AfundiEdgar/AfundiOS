# LLM Conversation Chains Implementation

## Overview

The LLM module has been enhanced with **LangChain conversation chains** to support multi-turn conversations with persistent memory. This allows the system to maintain context across multiple queries from the same user.

## Key Features

### 1. Conversation Memory
- **Session-based**: Each conversation session has its own memory store
- **Persistent across requests**: Memory is maintained in-memory during the application lifecycle
- **Automatic management**: Sessions are created on-demand and can be cleared explicitly

### 2. Multi-turn Interactions
- **Context retention**: LLM maintains conversation history within a session
- **Context-aware responses**: Each response considers both retrieved documents and conversation history
- **Graceful fallback**: If LangChain fails, falls back to simple OpenAI API calls

### 3. Flexible Query Options
- **Single-turn queries** (no session_id): Traditional RAG queries without conversation memory
- **Multi-turn conversations** (with session_id): Full conversation chain with memory
- **Optional chat history**: Can pre-load conversation history for context

## API Usage

### Basic Query (Single-turn)
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "top_k": 5
  }'
```

### Query with Conversation (Multi-turn)
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "session_id": "user_123_conv_456",
    "top_k": 5
  }'
```

### Query with Conversation History
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about its population?",
    "session_id": "user_123_conv_456",
    "top_k": 5,
    "chat_history": [
      ["What is the capital of France?", "Paris is the capital of France..."],
      ["When was it founded?", "Paris was founded in the 3rd century BC..."]
    ]
  }'
```

### List Active Sessions
```bash
curl http://localhost:8000/api/conversation/sessions
```

Response:
```json
{
  "sessions": ["user_123_conv_456", "user_789_conv_012"]
}
```

### Clear Single Session
```bash
curl -X DELETE http://localhost:8000/api/conversation/sessions/user_123_conv_456
```

### Clear All Sessions
```bash
curl -X POST http://localhost:8000/api/conversation/sessions/clear-all
```

## Architecture

### Core Components

#### `synthesize_answer()`
Main entry point that routes to the appropriate synthesis method:
- With `session_id`: Uses LangChain conversation chains
- Without `session_id`: Uses simple OpenAI API calls
- No API key: Returns structured fallback response

#### `_synthesize_with_chain()`
LangChain-based implementation with:
- `ChatOpenAI` LLM initialization
- `ConversationBufferMemory` for history tracking
- `ChatPromptTemplate` with message placeholders
- `LLMChain` for orchestration

#### `_synthesize_with_openai()`
Direct OpenAI API call for single-turn queries (no conversation memory)

#### `_synthesize_stub()`
Fallback when no API key is configured, returns formatted context

### Session Management

```python
_conversation_memory: Dict[str, ConversationBufferMemory]
```

Global dictionary mapping session IDs to their memory instances. Sessions are:
- Created automatically on first request with that `session_id`
- Persisted in memory while the application runs
- Can be explicitly cleared via API

## Configuration

The implementation respects settings from `backend/config.py`:
- `openai_api_key`: Required for LLM functionality
- `llm_model`: Model name (default: "gpt-4o-mini")
- Falls back to `OPENAI_API_KEY` environment variable

## Error Handling

1. **API Call Failures**: Gracefully falls back from LangChain to direct API calls
2. **Missing API Key**: Returns structured stub response with context preview
3. **Invalid Responses**: Checks response structure and returns safe defaults

## Model Setup

Requires LangChain package (already in `requirements.txt`):
```bash
pip install langchain
```

For LangChain 0.1.x compatibility, uses:
- `langchain.chat_models.ChatOpenAI`
- `langchain.memory.ConversationBufferMemory`
- `langchain.prompts.ChatPromptTemplate`
- `langchain.chains.LLMChain`

## Performance Considerations

- **Memory usage**: Conversation memory grows with chat history length
- **Token usage**: Every API call includes full conversation history
- **Response time**: Longer histories increase latency slightly

## Future Enhancements

1. **Persistent Storage**: Save conversation histories to database
2. **Memory Variants**: Use `ConversationSummaryMemory` for longer conversations
3. **User Analytics**: Track conversation patterns and user interactions
4. **Context Window Management**: Implement sliding window for very long conversations
5. **Streaming Responses**: Support streaming for better UX
6. **Multi-model Support**: Abstract LLM provider for flexibility
