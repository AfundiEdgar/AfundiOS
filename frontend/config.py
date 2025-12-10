"""
Frontend configuration module.

Centralized configuration for the Streamlit frontend with environment
variable support and sensible defaults.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class FrontendConfig:
    """Frontend application configuration."""

    # Backend Connection Settings
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "10.0"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    backoff_factor: float = float(os.getenv("BACKOFF_FACTOR", "0.5"))
    retry_on_status_codes: list = None

    # Caching Settings
    enable_cache: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour

    # Health Check Settings
    health_check_interval_seconds: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    health_check_endpoint: str = "/health"

    # UI Settings
    page_title: str = "AfundiOS"
    page_layout: str = "wide"
    show_advanced_settings: bool = os.getenv("SHOW_ADVANCED_SETTINGS", "false").lower() == "true"

    # Logging Settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Feature Flags
    enable_ingest: bool = os.getenv("ENABLE_INGEST", "true").lower() == "true"
    enable_query: bool = os.getenv("ENABLE_QUERY", "true").lower() == "true"
    enable_stats: bool = os.getenv("ENABLE_STATS", "true").lower() == "true"
    enable_offline_mode: bool = os.getenv("ENABLE_OFFLINE_MODE", "true").lower() == "true"

    # Query Settings
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    max_top_k: int = int(os.getenv("MAX_TOP_K", "20"))
    max_query_length: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))

    # File Upload Settings
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    allowed_file_types: list = ["txt", "md", "pdf"]

    def __post_init__(self):
        """Post-initialization configuration validation."""
        if self.retry_on_status_codes is None:
            self.retry_on_status_codes = [502, 503, 504, 408]

        # Validate settings
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.backoff_factor < 0:
            raise ValueError("backoff_factor must be non-negative")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "backend_url": self.backend_url,
            "request_timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "enable_cache": self.enable_cache,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "log_level": self.log_level,
            "enable_ingest": self.enable_ingest,
            "enable_query": self.enable_query,
            "enable_stats": self.enable_stats,
            "enable_offline_mode": self.enable_offline_mode,
            "default_top_k": self.default_top_k,
            "max_file_size_mb": self.max_file_size_mb,
        }

    @staticmethod
    def from_env() -> "FrontendConfig":
        """Create configuration from environment variables."""
        return FrontendConfig()

    @staticmethod
    def for_development() -> "FrontendConfig":
        """Create configuration for development."""
        config = FrontendConfig()
        config.log_level = "DEBUG"
        config.show_advanced_settings = True
        config.enable_offline_mode = True
        return config

    @staticmethod
    def for_production() -> "FrontendConfig":
        """Create configuration for production."""
        config = FrontendConfig()
        config.log_level = "WARNING"
        config.show_advanced_settings = False
        config.enable_offline_mode = False
        return config


# Global configuration instance
config = FrontendConfig.from_env()
