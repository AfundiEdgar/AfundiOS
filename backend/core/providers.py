"""
LLM Provider Abstraction

Supports multiple LLM providers with a unified interface:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Azure OpenAI
- Local/Self-hosted (via API compatibility)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Message:
    """Unified message format."""
    def __init__(self, role: str, content: str):
        self.role = role  # "system", "user", "assistant"
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 512):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def generate(self, messages: List[Message]) -> str:
        """Generate response from messages."""
        pass

    @abstractmethod
    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Chat-style interface with context and history."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider supporting GPT-4, GPT-3.5, etc."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, messages: List[Message]) -> str:
        """Generate using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[msg.to_dict() for msg in messages],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Chat with context and history."""
        messages = [
            Message("system", (
                "You are a helpful assistant that answers questions using provided context. "
                "Cite the context ids when referring to facts. Keep answers concise and accurate."
            )),
        ]

        # Add conversation history
        if history:
            for user_msg, assistant_msg in history:
                messages.append(Message("user", user_msg))
                messages.append(Message("assistant", assistant_msg))

        # Add current query with context
        messages.append(Message("user", (
            f"Context (each item has an id and source):\n{context}\n\n"
            f"Question: {query}"
        )))

        return self.generate(messages)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def generate(self, messages: List[Message]) -> str:
        """Generate using Anthropic API."""
        try:
            # Separate system message from others
            system_msg = None
            api_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    api_messages.append({"role": msg.role, "content": msg.content})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_msg or "",
                messages=api_messages,
                temperature=self.temperature,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise

    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Chat with context and history."""
        messages = [
            Message("system", (
                "You are a helpful assistant that answers questions using provided context. "
                "Cite the context ids when referring to facts. Keep answers concise and accurate."
            )),
        ]

        if history:
            for user_msg, assistant_msg in history:
                messages.append(Message("user", user_msg))
                messages.append(Message("assistant", assistant_msg))

        messages.append(Message("user", (
            f"Context (each item has an id and source):\n{context}\n\n"
            f"Question: {query}"
        )))

        return self.generate(messages)


class CohereProvider(LLMProvider):
    """Cohere provider."""

    def __init__(self, api_key: str, model: str = "command-r-plus", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy load Cohere client."""
        if self._client is None:
            import cohere
            self._client = cohere.ClientV2(api_key=self.api_key)
        return self._client

    def generate(self, messages: List[Message]) -> str:
        """Generate using Cohere API."""
        try:
            # Cohere uses a simpler interface
            prompt = "\n".join(f"{msg.role}: {msg.content}" for msg in messages)
            response = self.client.chat(
                model=self.model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.message.content[0].text
        except Exception as e:
            logger.error(f"Cohere generation error: {e}")
            raise

    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Chat with context and history."""
        messages = [
            Message("system", (
                "You are a helpful assistant that answers questions using provided context. "
                "Cite the context ids when referring to facts. Keep answers concise and accurate."
            )),
        ]

        if history:
            for user_msg, assistant_msg in history:
                messages.append(Message("user", user_msg))
                messages.append(Message("assistant", assistant_msg))

        messages.append(Message("user", (
            f"Context (each item has an id and source):\n{context}\n\n"
            f"Question: {query}"
        )))

        return self.generate(messages)


class LocalProvider(LLMProvider):
    """Local/self-hosted LLM via compatible API (e.g., Ollama, vLLM)."""

    def __init__(self, base_url: str, model: str, **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self._client = None

    @property
    def client(self):
        """Lazy load OpenAI-compatible client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key="not-needed")
        return self._client

    def generate(self, messages: List[Message]) -> str:
        """Generate using local API-compatible endpoint."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[msg.to_dict() for msg in messages],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Local provider generation error: {e}")
            raise

    def chat(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Chat with context and history."""
        messages = [
            Message("system", (
                "You are a helpful assistant that answers questions using provided context. "
                "Cite the context ids when referring to facts. Keep answers concise and accurate."
            )),
        ]

        if history:
            for user_msg, assistant_msg in history:
                messages.append(Message("user", user_msg))
                messages.append(Message("assistant", assistant_msg))

        messages.append(Message("user", (
            f"Context (each item has an id and source):\n{context}\n\n"
            f"Question: {query}"
        )))

        return self.generate(messages)
