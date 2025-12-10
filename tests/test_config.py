"""
Tests for backend configuration management and validation.

Run tests with:
    pytest tests/test_config.py -v
    pytest tests/test_config.py::TestConfigValidation -v
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# Import config classes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigValidation:
    """Test configuration validation for various scenarios."""
    
    def test_openai_provider_requires_api_key(self):
        """OpenAI provider should require OPENAI_API_KEY."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': '',  # Empty key
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
                Settings()
    
    def test_anthropic_provider_requires_api_key(self):
        """Anthropic provider should require ANTHROPIC_API_KEY."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'anthropic',
            'ANTHROPIC_API_KEY': '',  # Empty key
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
                Settings()
    
    def test_cohere_provider_requires_api_key(self):
        """Cohere provider should require COHERE_API_KEY."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'cohere',
            'COHERE_API_KEY': '',  # Empty key
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="COHERE_API_KEY is not set"):
                Settings()
    
    def test_local_provider_requires_url(self):
        """Local provider should require LOCAL_LLM_URL."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'local',
            'LOCAL_LLM_URL': '',  # Empty URL
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="LOCAL_LLM_URL is not set"):
                Settings()
    
    def test_invalid_provider(self):
        """Invalid LLM provider should raise error."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'invalid_provider',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid LLM provider"):
                Settings()
    
    def test_invalid_environment(self):
        """Invalid environment should raise error."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'invalid_env',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid environment"):
                Settings()
    
    def test_invalid_temperature(self):
        """Temperature outside range should raise error."""
        with patch.dict(os.environ, {
            'LLM_TEMPERATURE': '5.0',  # Out of range
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid temperature"):
                Settings()
    
    def test_valid_temperature_boundaries(self):
        """Valid temperature values should work."""
        for temp in ['0.0', '1.0', '2.0']:
            with patch.dict(os.environ, {
                'LLM_TEMPERATURE': temp,
                'LLM_PROVIDER': 'openai',
                'OPENAI_API_KEY': 'sk-test',
            }, clear=True):
                from backend.config import Settings, get_settings
                # Clear cache before creating new settings
                get_settings.cache_clear()
                settings = Settings()
                assert float(settings.llm_temperature) == float(temp)
    
    def test_invalid_max_tokens(self):
        """Invalid max tokens should raise error."""
        with patch.dict(os.environ, {
            'LLM_MAX_TOKENS': '0',  # Must be positive
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid max_tokens"):
                Settings()
    
    def test_invalid_vector_store_type(self):
        """Invalid vector store type should raise error."""
        with patch.dict(os.environ, {
            'VECTOR_STORE_TYPE': 'invalid_store',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid vector store type"):
                Settings()
    
    def test_invalid_compaction_strategy(self):
        """Invalid compaction strategy should raise error."""
        with patch.dict(os.environ, {
            'MEMORY_COMPACTION_STRATEGY': 'invalid_strategy',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid compaction strategy"):
                Settings()
    
    def test_invalid_briefing_style(self):
        """Invalid briefing style should raise error."""
        with patch.dict(os.environ, {
            'DAILY_BRIEFING_SUMMARY_STYLE': 'invalid_style',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Invalid briefing style"):
                Settings()
    
    def test_encryption_requires_key_or_password(self):
        """Encryption enabled requires key or password derivation."""
        with patch.dict(os.environ, {
            'ENCRYPTION_ENABLED': 'true',
            'ENCRYPTION_KEY': '',
            'ENCRYPTION_DERIVE_FROM_PASSWORD': 'false',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings
            with pytest.raises(ValueError, match="Encryption is enabled but"):
                Settings()
    
    def test_valid_configuration_openai(self):
        """Valid OpenAI configuration should load."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'local',
            'LLM_PROVIDER': 'openai',
            'LLM_MODEL': 'gpt-4o-mini',
            'OPENAI_API_KEY': 'sk-test-key',
            'LLM_TEMPERATURE': '0.7',
            'LLM_MAX_TOKENS': '1024',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            assert settings.environment == 'local'
            assert settings.llm_provider == 'openai'
            assert settings.openai_api_key == 'sk-test-key'
            assert settings.llm_temperature == 0.7
            assert settings.llm_max_tokens == 1024
    
    def test_valid_configuration_anthropic(self):
        """Valid Anthropic configuration should load."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'anthropic',
            'ANTHROPIC_API_KEY': 'sk-ant-test-key',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            assert settings.llm_provider == 'anthropic'
            assert settings.anthropic_api_key == 'sk-ant-test-key'
    
    def test_valid_configuration_local(self):
        """Valid local LLM configuration should load."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'local',
            'LOCAL_LLM_URL': 'http://localhost:8000/v1',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            assert settings.llm_provider == 'local'
            assert settings.local_llm_url == 'http://localhost:8000/v1'
    
    def test_valid_configuration_with_encryption(self):
        """Valid configuration with encryption key should load."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
            'ENCRYPTION_ENABLED': 'true',
            'ENCRYPTION_KEY': 'a' * 64,  # 32-byte hex key
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            assert settings.encryption_enabled is True
            assert settings.encryption_key == 'a' * 64


class TestConfigSafeMethods:
    """Test configuration helper methods."""
    
    def test_validate_method(self):
        """Configuration.validate() should check all settings."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            is_valid, errors = settings.validate()
            assert is_valid is True
            assert len(errors) == 0
    
    def test_to_dict_safe_masks_secrets(self):
        """to_dict_safe() should mask sensitive values."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test-key-12345',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            safe_dict = settings.to_dict_safe()
            
            # Key should be masked
            assert safe_dict['openai_api_key'].startswith('***')
            assert '5' in safe_dict['openai_api_key']  # Last 4 chars visible
            assert 'sk-test' not in safe_dict['openai_api_key']
    
    def test_print_config_summary(self, capsys):
        """print_config_summary() should display configuration."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            settings.print_config_summary()
            
            captured = capsys.readouterr()
            assert 'Configuration Summary' in captured.out
            assert 'production' in captured.out
            assert 'openai' in captured.out
            assert '✓ Set' in captured.out or '✗ Not set' in captured.out


class TestConfigurationError:
    """Test custom ConfigurationError exception."""
    
    def test_configuration_error_message(self):
        """ConfigurationError should provide helpful message."""
        from backend.config import ConfigurationError
        
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"
    
    def test_get_settings_wraps_error(self):
        """get_settings() should wrap validation errors."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': '',
        }, clear=True):
            from backend.config import get_settings, ConfigurationError
            get_settings.cache_clear()
            
            with pytest.raises(ConfigurationError):
                get_settings()


class TestConfigDefaults:
    """Test default configuration values."""
    
    def test_default_values(self):
        """Configuration should have sensible defaults."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test',
        }, clear=True):
            from backend.config import Settings, get_settings
            get_settings.cache_clear()
            settings = Settings()
            
            assert settings.environment == 'local'
            assert settings.llm_temperature == 0.0
            assert settings.llm_max_tokens == 512
            assert settings.vector_store_type == 'chroma'
            assert settings.embedding_model == 'text-embedding-3-small'
            assert settings.encryption_enabled is False
            assert settings.memory_compaction_enabled is False
            assert settings.daily_briefing_enabled is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
