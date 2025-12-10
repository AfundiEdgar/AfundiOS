"""
LLM Provider Factory

Creates and configures LLM providers based on settings.
"""

import os
import logging
from typing import Optional
from config import settings
from .providers import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    CohereProvider,
    LocalProvider,
)
from .aws_bedrock_llm import AWSBedrockLLM

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider.

        Args:
            provider_name: Provider type (openai, anthropic, cohere, local)
                          Defaults to settings.llm_provider
            model: Model name. Defaults to settings.llm_model
            **kwargs: Additional provider-specific arguments

        Returns:
            Configured LLM provider instance
        """
        provider_name = provider_name or settings.llm_provider
        model = model or settings.llm_model

        logger.info(f"Creating {provider_name} provider with model {model}")

        if provider_name.lower() == "openai":
            api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not found in config or environment")
            return OpenAIProvider(
                api_key=api_key,
                model=model,
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 512),
            )

        elif provider_name.lower() == "anthropic":
            api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY") or settings.anthropic_api_key
            if not api_key:
                raise ValueError("Anthropic API key not found in config or environment")
            return AnthropicProvider(
                api_key=api_key,
                model=model,
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 512),
            )

        elif provider_name.lower() == "cohere":
            api_key = kwargs.get("api_key") or os.getenv("COHERE_API_KEY") or settings.cohere_api_key
            if not api_key:
                raise ValueError("Cohere API key not found in config or environment")
            return CohereProvider(
                api_key=api_key,
                model=model,
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 512),
            )

        elif provider_name.lower() == "aws_bedrock":
            access_key = kwargs.get("access_key_id") or os.getenv("AWS_ACCESS_KEY_ID") or settings.aws_access_key_id
            secret_key = kwargs.get("secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY") or settings.aws_secret_access_key
            region = kwargs.get("region") or os.getenv("AWS_REGION") or settings.aws_region
            
            if not access_key:
                raise ValueError("AWS_ACCESS_KEY_ID not found in config or environment")
            if not secret_key:
                raise ValueError("AWS_SECRET_ACCESS_KEY not found in config or environment")
            
            bedrock_client = AWSBedrockLLM(
                access_key_id=access_key,
                secret_access_key=secret_key,
                region=region,
                model=model,
            )
            
            # Wrap in AWSBedrockProvider adapter
            return AWSBedrockProvider(
                bedrock_client=bedrock_client,
                model=model,
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 512),
            )

        elif provider_name.lower() == "local":
            base_url = kwargs.get("base_url") or os.getenv("LOCAL_LLM_URL") or settings.local_llm_url
            if not base_url:
                raise ValueError("Local LLM base URL not found in config or environment")
            return LocalProvider(
                base_url=base_url,
                model=model,
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 512),
            )

        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")


# Global provider instance (lazy-loaded)
_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Get or create the global LLM provider."""
    global _provider
    if _provider is None:
        _provider = ProviderFactory.create_provider()
    return _provider


def set_provider(provider: LLMProvider) -> None:
    """Set the global LLM provider (useful for testing)."""
    global _provider
    _provider = provider
