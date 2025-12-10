from pydantic import validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import Optional
import os
import logging


class ConfigurationError(Exception):
    """Custom exception for configuration errors with developer-friendly messages."""
    pass


class Settings(BaseSettings):
    """
    Application configuration with comprehensive validation.
    
    Environment variables:
    - Can be set in .env file or OS environment
    - See .env.example for all available options
    - Run `python -m backend.config_validator` to validate your configuration
    """
    
    environment: str = "local"
    
    # LLM Provider Configuration
    llm_provider: str = "openai"  # Options: "openai", "anthropic", "cohere", "aws_bedrock", "local"
    llm_model: str = "gpt-4o-mini"  # Model name for the provider
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None  # For AWS Bedrock
    aws_secret_access_key: Optional[str] = None  # For AWS Bedrock
    aws_region: str = "us-east-1"  # AWS region for Bedrock
    
    # Local LLM configuration (for self-hosted models)
    local_llm_url: Optional[str] = None  # e.g., "http://localhost:8000/v1" for Ollama
    
    # Secrets Manager Configuration
    use_secrets_manager: bool = False  # Enable AWS Secrets Manager for credentials
    secrets_manager_region: str = "us-east-1"  # AWS region for Secrets Manager
    # Secret names for different credentials (e.g., "prod/llm/openai", "dev/aws/bedrock")
    openai_secret_name: Optional[str] = None  # Secret name for OpenAI credentials
    anthropic_secret_name: Optional[str] = None  # Secret name for Anthropic credentials
    cohere_secret_name: Optional[str] = None  # Secret name for Cohere credentials
    aws_bedrock_secret_name: Optional[str] = None  # Secret name for AWS Bedrock credentials
    # Local LLM secret/config names
    local_llm_secret_name: Optional[str] = None  # Secret name for local LLM (url, api_key)
    local_llm_api_key: Optional[str] = None  # API key or token for local LLM (if applicable)
    
    # LLM Parameters
    llm_temperature: float = 0.0
    llm_max_tokens: int = 512

    # Vector store
    vector_store_type: str = "chroma"
    vector_store_path: str = "data/vector_store"

    # Encryption Configuration
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None  # 32-byte hex key or password
    encryption_derive_from_password: bool = False  # If True, derive key from password
    encrypt_vector_texts: bool = False  # Encrypt document texts
    encrypt_metadata_fields: str = ""  # Comma-separated list of fields to encrypt (e.g., "source,author")

    # Metadata DB (could be sqlite, postgres, etc.)
    metadata_db_url: str = "sqlite:///data/metadata.db"

    # Model config
    embedding_model: str = "text-embedding-3-small"

    # Memory compaction / maintenance
    memory_compaction_enabled: bool = False
    memory_compaction_interval_hours: int = 24
    memory_compaction_keep_days: int = 365
    memory_compaction_strategy: str = "deduplicate_exact"  # options: deduplicate_exact, age_based

    # Daily briefing configuration
    daily_briefing_enabled: bool = False
    daily_briefing_interval_hours: int = 24
    daily_briefing_lookback_days: int = 1
    daily_briefing_summary_style: str = "executive"  # bullet_points, executive, narrative
    daily_briefing_max_chars: int = 4000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # ==================== Validators ====================
    
    @validator('environment')
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the expected values."""
        valid_envs = {'local', 'development', 'staging', 'production'}
        if v not in valid_envs:
            raise ValueError(
                f"Invalid environment '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_envs))}"
            )
        return v
    
    @validator('llm_provider')
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        valid_providers = {'openai', 'anthropic', 'cohere', 'aws_bedrock', 'local'}
        if v not in valid_providers:
            raise ValueError(
                f"Invalid LLM provider '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_providers))}"
            )
        return v
    
    @validator('llm_temperature')
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError(
                f"Invalid temperature {v}. "
                f"Must be between 0.0 and 2.0 (currently {v})"
            )
        return v
    
    @validator('llm_max_tokens')
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens is positive."""
        if v <= 0:
            raise ValueError(
                f"Invalid max_tokens {v}. "
                f"Must be a positive integer (currently {v})"
            )
        return v
    
    @validator('vector_store_type')
    def validate_vector_store_type(cls, v: str) -> str:
        """Validate vector store type is supported."""
        valid_types = {'chroma', 'pinecone', 'weaviate', 'milvus'}
        if v not in valid_types:
            raise ValueError(
                f"Invalid vector store type '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )
        return v
    
    @validator('vector_store_path')
    def validate_vector_store_path(cls, v: str) -> str:
        """Validate vector store path is valid."""
        path = Path(v)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f"Cannot create vector store directory '{v}': {e}"
            )
        return v
    
    @validator('memory_compaction_strategy')
    def validate_compaction_strategy(cls, v: str) -> str:
        """Validate compaction strategy is supported."""
        valid_strategies = {'deduplicate_exact', 'age_based'}
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid compaction strategy '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_strategies))}"
            )
        return v
    
    @validator('daily_briefing_summary_style')
    def validate_briefing_style(cls, v: str) -> str:
        """Validate briefing summary style is supported."""
        valid_styles = {'bullet_points', 'executive', 'narrative'}
        if v not in valid_styles:
            raise ValueError(
                f"Invalid briefing style '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_styles))}"
            )
        return v
    
    @model_validator(mode='before')
    def validate_llm_configuration(cls, values):
        """Validate LLM provider has required configuration."""
        provider = values.get('llm_provider', 'openai')
        
        if provider == 'openai' and not values.get('openai_api_key'):
            raise ValueError(
                "LLM provider is 'openai' but OPENAI_API_KEY is not set. "
                "Set it via:\n"
                "  1. Environment variable: export OPENAI_API_KEY='sk-...'\n"
                "  2. .env file: OPENAI_API_KEY=sk-...\n"
                "Get your key at: https://platform.openai.com/api-keys"
            )
        
        if provider == 'anthropic' and not values.get('anthropic_api_key'):
            raise ValueError(
                "LLM provider is 'anthropic' but ANTHROPIC_API_KEY is not set. "
                "Set it via:\n"
                "  1. Environment variable: export ANTHROPIC_API_KEY='sk-ant-...'\n"
                "  2. .env file: ANTHROPIC_API_KEY=sk-ant-...\n"
                "Get your key at: https://console.anthropic.com/account/keys"
            )
        
        if provider == 'cohere' and not values.get('cohere_api_key'):
            raise ValueError(
                "LLM provider is 'cohere' but COHERE_API_KEY is not set. "
                "Set it via:\n"
                "  1. Environment variable: export COHERE_API_KEY='...-...'\n"
                "  2. .env file: COHERE_API_KEY=...-...\n"
                "Get your key at: https://dashboard.cohere.ai/api-keys"
            )
        
        if provider == 'aws_bedrock':
            if not values.get('aws_access_key_id'):
                raise ValueError(
                    "LLM provider is 'aws_bedrock' but AWS_ACCESS_KEY_ID is not set. "
                    "Set it via:\n"
                    "  1. Environment variable: export AWS_ACCESS_KEY_ID='...'\n"
                    "  2. .env file: AWS_ACCESS_KEY_ID=...\n"
                    "Get your credentials at: https://console.aws.amazon.com/iam/"
                )
            if not values.get('aws_secret_access_key'):
                raise ValueError(
                    "LLM provider is 'aws_bedrock' but AWS_SECRET_ACCESS_KEY is not set. "
                    "Set it via:\n"
                    "  1. Environment variable: export AWS_SECRET_ACCESS_KEY='...'\n"
                    "  2. .env file: AWS_SECRET_ACCESS_KEY=...\n"
                    "Get your credentials at: https://console.aws.amazon.com/iam/"
                )
        
        if provider == 'local' and not values.get('local_llm_url'):
            raise ValueError(
                "LLM provider is 'local' but LOCAL_LLM_URL is not set. "
                "Set it via:\n"
                "  1. Environment variable: export LOCAL_LLM_URL='http://localhost:8000/v1'\n"
                "  2. .env file: LOCAL_LLM_URL=http://localhost:8000/v1\n"
                "Make sure your local LLM server (e.g., Ollama) is running."
            )
        
        return values
    
    @model_validator(mode='before')
    def validate_encryption_configuration(cls, values):
        """Validate encryption configuration is consistent."""
        if values.get('encryption_enabled'):
            if not values.get('encryption_key') and not values.get('encryption_derive_from_password'):
                raise ValueError(
                    "Encryption is enabled but neither ENCRYPTION_KEY nor "
                    "ENCRYPTION_DERIVE_FROM_PASSWORD is set. Either:\n"
                    "  1. Set ENCRYPTION_KEY='your-32-byte-hex-key'\n"
                    "  2. Set ENCRYPTION_DERIVE_FROM_PASSWORD=true to derive key from password"
                )
        
        return values
    
    # ==================== Helper Methods ====================
    
    def validate(self) -> tuple:
        """
        Validate configuration and return (is_valid, errors).
        Useful for logging all issues at startup.
        """
        errors = []
        
        # Check LLM provider
        if self.llm_provider == 'openai' and not self.openai_api_key:
            errors.append(f"❌ OpenAI API key is missing (LLM_PROVIDER='{self.llm_provider}')")
        elif self.llm_provider == 'anthropic' and not self.anthropic_api_key:
            errors.append(f"❌ Anthropic API key is missing (LLM_PROVIDER='{self.llm_provider}')")
        elif self.llm_provider == 'cohere' and not self.cohere_api_key:
            errors.append(f"❌ Cohere API key is missing (LLM_PROVIDER='{self.llm_provider}')")
        elif self.llm_provider == 'local' and not self.local_llm_url:
            errors.append(f"❌ Local LLM URL is missing (LLM_PROVIDER='{self.llm_provider}')")
        
        # Check encryption
        if self.encryption_enabled and not self.encryption_key and not self.encryption_derive_from_password:
            errors.append("❌ Encryption is enabled but no encryption key is configured")
        
        # Check paths
        try:
            Path(self.vector_store_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"❌ Cannot access vector store path: {self.vector_store_path} ({e})")
        
        return len(errors) == 0, errors
    
    def print_config_summary(self) -> None:
        """Print a summary of current configuration (with secrets masked)."""
        print("\n" + "="*60)
        print("⚙️  Configuration Summary")
        print("="*60)
        print(f"Environment:          {self.environment}")
        print(f"LLM Provider:         {self.llm_provider}")
        print(f"LLM Model:            {self.llm_model}")
        print(f"Vector Store:         {self.vector_store_type}")
        print(f"Vector Store Path:    {self.vector_store_path}")
        print(f"Embedding Model:      {self.embedding_model}")
        print(f"Encryption Enabled:   {self.encryption_enabled}")
        print(f"Memory Compaction:    {self.memory_compaction_enabled}")
        print(f"Daily Briefing:       {self.daily_briefing_enabled}")
        
        # Print API key status (masked)
        print(f"\nAPI Keys:")
        print(f"  OpenAI:             {'✓ Set' if self.openai_api_key else '✗ Not set'}")
        print(f"  Anthropic:          {'✓ Set' if self.anthropic_api_key else '✗ Not set'}")
        print(f"  Cohere:             {'✓ Set' if self.cohere_api_key else '✗ Not set'}")
        print(f"  Local LLM URL:      {'✓ Set' if self.local_llm_url else '✗ Not set'}")
        print("="*60 + "\n")
    
    def to_dict_safe(self) -> dict:
        """
        Export configuration as dictionary with secrets masked.
        Safe for logging and debugging.
        """
        config_dict = self.dict()
        # Mask sensitive values
        for key in config_dict:
            if 'key' in key.lower() or 'password' in key.lower() or 'token' in key.lower():
                if config_dict[key]:
                    config_dict[key] = f"***{config_dict[key][-4:]}" if len(str(config_dict[key])) > 4 else "***"
        return config_dict
    
    def get_secret(self, secret_name: str, key: Optional[str] = None) -> Optional[str]:
        """
        Fetch a secret from AWS Secrets Manager or environment variables.
        
        Args:
            secret_name: Name of the secret to retrieve
            key: Optional key to extract from JSON secret
            
        Returns:
            Secret value as string, or None if not found
            
        Example:
            # Fetch entire secret (if JSON, returns JSON string)
            secret = settings.get_secret("prod/llm/openai")
            
            # Fetch specific key from JSON secret
            api_key = settings.get_secret("prod/llm/openai", key="api_key")
        """
        if not self.use_secrets_manager:
            logger_obj = logging.getLogger(__name__)
            logger_obj.warning(
                "Secrets Manager is disabled. Set USE_SECRETS_MANAGER=true to enable."
            )
            return None
        
        try:
            from backend.utils.secrets_manager import SecretsManager
            
            manager = SecretsManager(
                use_aws=True,
                region=self.secrets_manager_region,
                access_key_id=self.aws_access_key_id,
                secret_access_key=self.aws_secret_access_key,
            )
            
            return manager.get_secret_value(secret_name, key)
        except Exception as e:
            logger_obj = logging.getLogger(__name__)
            logger_obj.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
            return None
    
    def load_secrets_for_provider(self) -> None:
        """
        Load credentials from Secrets Manager for the configured LLM provider.
        
        This method fetches secrets from AWS Secrets Manager and updates the
        corresponding API key fields. This is useful for production deployments
        where credentials should not be stored in .env files.
        
        Usage:
            settings = get_settings()
            settings.load_secrets_for_provider()
            # Now settings.openai_api_key, etc. are populated from Secrets Manager
        """
        if not self.use_secrets_manager:
            return
        
        logger_obj = logging.getLogger(__name__)
        logger_obj.info(
            f"Loading credentials from Secrets Manager for '{self.llm_provider}' provider"
        )
        
        # Map providers to their secret names and fields
        # field_name is the Settings attribute to populate, secret_key is the key inside the JSON secret
        provider_secrets = {
            'openai': ('openai_secret_name', 'openai_api_key', 'api_key'),
            'anthropic': ('anthropic_secret_name', 'anthropic_api_key', 'api_key'),
            'cohere': ('cohere_secret_name', 'cohere_api_key', 'api_key'),
            'aws_bedrock': ('aws_bedrock_secret_name', None, None),
            'local': ('local_llm_secret_name', None, None),
        }
        
        if self.llm_provider not in provider_secrets:
            return
        
        secret_name_attr, field_name, secret_key = provider_secrets[self.llm_provider]
        secret_name = getattr(self, secret_name_attr)
        
        if not secret_name:
            logger_obj.warning(
                f"No secret name configured for '{self.llm_provider}'. "
                f"Set {secret_name_attr.upper()} environment variable."
            )
            return
        
        try:
            if self.llm_provider == 'aws_bedrock':
                # For AWS Bedrock, fetch access key and secret key
                self.aws_access_key_id = self.get_secret(secret_name, "access_key_id")
                self.aws_secret_access_key = self.get_secret(secret_name, "secret_access_key")
                logger_obj.info(f"Loaded AWS Bedrock credentials from secret: {secret_name}")
            elif self.llm_provider == 'local':
                # For local LLMs, secret can contain 'url' and/or 'api_key'.
                # If secret is JSON with keys, extract accordingly. If it's a plain string, treat as api_key.
                raw = None
                try:
                    raw = self.get_secret(secret_name, key=None)
                except Exception:
                    raw = None

                # get_secret returns string when key specified or SecretString; for LocalSecretsManager
                # it may return dict when parsing JSON. Attempt to import manager directly for full data.
                from backend.utils.secrets_manager import SecretsManager
                manager = SecretsManager(
                    use_aws=True,
                    region=self.secrets_manager_region,
                    access_key_id=self.aws_access_key_id,
                    secret_access_key=self.aws_secret_access_key,
                )

                secret_obj = None
                try:
                    secret_obj = manager.get_secret(secret_name)
                except Exception:
                    secret_obj = None

                # If we got a dict-like secret, set fields accordingly
                if isinstance(secret_obj, dict):
                    # set URL if present
                    if 'url' in secret_obj and secret_obj.get('url'):
                        self.local_llm_url = secret_obj.get('url')
                        logger_obj.info(f"Loaded local LLM URL from secret: {secret_name}")
                    # set API key if present
                    if 'api_key' in secret_obj and secret_obj.get('api_key'):
                        self.local_llm_api_key = secret_obj.get('api_key')
                        logger_obj.info(f"Loaded local LLM API key from secret: {secret_name}")
                else:
                    # If secret is a plain string, treat as API key
                    if isinstance(raw, str) and raw:
                        self.local_llm_api_key = raw
                        logger_obj.info(f"Loaded local LLM API key (string) from secret: {secret_name}")
                    else:
                        logger_obj.warning(f"Local secret '{secret_name}' had no usable fields (url/api_key)")
            else:
                # For other providers, fetch API key
                api_key = self.get_secret(secret_name, secret_key)
                if api_key:
                    setattr(self, field_name, api_key)
                    logger_obj.info(
                        f"Loaded {self.llm_provider} API key from secret: {secret_name}"
                    )
        except Exception as e:
            logger_obj.error(
                f"Failed to load secrets for '{self.llm_provider}': {str(e)}"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get or create the settings singleton."""
    try:
        return Settings()
    except ValueError as e:
        raise ConfigurationError(
            f"\n{'='*60}\n"
            f"❌ Configuration Error:\n"
            f"{'='*60}\n"
            f"{str(e)}\n"
            f"{'='*60}\n"
            f"\n💡 Tips:\n"
            f"  • Copy .env.example to .env and fill in your values\n"
            f"  • Run: python -m backend.config_validator\n"
            f"  • Check README.md for setup instructions\n"
            f"{'='*60}\n"
        ) from e


# Initialize settings at module import time to catch config errors early
try:
    settings = get_settings()
except ConfigurationError:
    raise
