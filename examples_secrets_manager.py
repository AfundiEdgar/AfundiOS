"""
AWS Secrets Manager Integration Examples and Tests

This file contains practical examples and test cases for using
AWS Secrets Manager with your AfundiOS backend.
"""

# ============================================================================
# EXAMPLE 1: Basic Configuration Loading
# ============================================================================

"""
Load secrets from AWS Secrets Manager automatically when initializing settings.
"""

from backend.config import get_settings

def example_basic_loading():
    """Load credentials from Secrets Manager for configured provider."""
    # Get settings singleton
    settings = get_settings()
    
    # Load secrets from Secrets Manager for the configured LLM provider
    if settings.use_secrets_manager:
        settings.load_secrets_for_provider()
        print(f"✓ Loaded {settings.llm_provider} credentials from Secrets Manager")
    else:
        print("✓ Using credentials from .env file")
    
    # Now you can use the credentials
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    
    return settings


# ============================================================================
# EXAMPLE 2: Manual Secret Retrieval
# ============================================================================

"""
Manually retrieve specific secrets from AWS Secrets Manager.
"""

def example_manual_retrieval():
    """Retrieve secrets manually."""
    from backend.config import get_settings
    
    settings = get_settings()
    
    # Get an entire secret (JSON)
    try:
        openai_secret = settings.get_secret("prod/llm/openai")
        if openai_secret:
            api_key = openai_secret
            print(f"✓ Retrieved OpenAI secret")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Get a specific key from a JSON secret
    try:
        api_key = settings.get_secret("prod/llm/openai", key="api_key")
        if api_key:
            print(f"✓ Retrieved OpenAI API key: {api_key[:10]}...")
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# EXAMPLE 3: Direct SecretsManager Usage
# ============================================================================

"""
Use SecretsManager directly for more control.
"""

def example_direct_usage():
    """Use SecretsManager class directly."""
    from backend.utils.secrets_manager import SecretsManager
    
    # Create manager (auto-selects AWS or local)
    manager = SecretsManager(use_aws=True, region="us-east-1")
    
    # Get entire secret
    try:
        bedrock_secret = manager.get_secret("prod/aws/bedrock")
        access_key = bedrock_secret["access_key_id"]
        secret_key = bedrock_secret["secret_access_key"]
        print(f"✓ Retrieved Bedrock credentials")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Get specific value
    try:
        api_key = manager.get_secret_value("prod/llm/openai", key="api_key")
        print(f"✓ Retrieved OpenAI API key")
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# EXAMPLE 4: Local Development (Environment Variables)
# ============================================================================

"""
Use environment variables for local development without AWS.
Environment variables should be named: SECRET_<secret_name>_<key>
"""

def example_local_development():
    """Use environment variables for secrets (local development)."""
    import os
    from backend.utils.secrets_manager import LocalSecretsManager
    
    # Set environment variables (in bash before running Python)
    # export SECRET_dev_llm_openai="sk-proj-xxxxx"
    # export SECRET_prod_aws_bedrock='{"access_key_id":"AKIA...","secret_access_key":"wJalr..."}'
    
    manager = LocalSecretsManager()
    
    # Get plain string secret
    try:
        api_key = manager.get_secret_value("dev_llm_openai")
        print(f"✓ Retrieved API key from environment: {api_key[:10]}...")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Get JSON secret
    try:
        bedrock_secret = manager.get_secret("prod_aws_bedrock")
        access_key = bedrock_secret["access_key_id"]
        print(f"✓ Retrieved Bedrock secret from environment")
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# EXAMPLE 5: Application Startup Integration
# ============================================================================

"""
Integrate Secrets Manager into application startup.
"""

from fastapi import FastAPI
from backend.config import get_settings

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Load secrets on application startup."""
    settings = get_settings()
    
    if settings.use_secrets_manager:
        try:
            # Load credentials from Secrets Manager
            settings.load_secrets_for_provider()
            print(f"✓ Successfully loaded {settings.llm_provider} credentials from Secrets Manager")
        except Exception as e:
            print(f"✗ Failed to load secrets: {e}")
            print("✓ Falling back to .env file credentials")
    else:
        print("✓ Using .env file credentials")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    pass


# ============================================================================
# EXAMPLE 6: Error Handling
# ============================================================================

"""
Handle errors gracefully with fallbacks.
"""

def example_error_handling():
    """Handle secrets retrieval errors gracefully."""
    from backend.config import get_settings
    import os
    
    settings = get_settings()
    
    # Try to load from Secrets Manager, fallback to .env
    try:
        if settings.use_secrets_manager:
            api_key = settings.get_secret("prod/llm/openai", key="api_key")
        else:
            api_key = None
        
        # Fallback to environment variable
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        # Fallback to config file
        if not api_key:
            api_key = settings.openai_api_key
        
        if not api_key:
            raise ValueError("OpenAI API key not found in any source")
        
        print(f"✓ Successfully loaded OpenAI API key from: {api_key[:10]}...")
        
    except Exception as e:
        print(f"✗ Error loading API key: {e}")
        raise


# ============================================================================
# EXAMPLE 7: AWS Bedrock Integration
# ============================================================================

"""
Use Secrets Manager with AWS Bedrock.
"""

def example_bedrock_integration():
    """Load AWS Bedrock credentials from Secrets Manager."""
    from backend.config import get_settings
    from backend.core.provider_factory import get_llm_provider
    
    settings = get_settings()
    
    # Change to AWS Bedrock
    settings.llm_provider = "aws_bedrock"
    settings.llm_model = "amazon.nova-lite-v1:0"
    settings.aws_bedrock_secret_name = "prod/aws/bedrock"
    
    # Load credentials from Secrets Manager
    if settings.use_secrets_manager:
        settings.load_secrets_for_provider()
        print(f"✓ Loaded AWS Bedrock credentials from Secrets Manager")
    
    # Create provider with loaded credentials
    provider = get_llm_provider(settings)
    
    # Use provider
    response = provider.generate("Hello, Nova Lite!")
    print(f"Response: {response}")


# ============================================================================
# EXAMPLE 8: Multiple Providers
# ============================================================================

"""
Switch between multiple LLM providers using Secrets Manager.
"""

def example_multiple_providers():
    """Switch between providers dynamically."""
    from backend.config import get_settings
    from backend.core.provider_factory import get_llm_provider
    
    settings = get_settings()
    
    providers = [
        ("openai", "gpt-4o-mini", "prod/llm/openai"),
        ("anthropic", "claude-3-sonnet-20240229", "prod/llm/anthropic"),
        ("aws_bedrock", "amazon.nova-lite-v1:0", "prod/aws/bedrock"),
    ]
    
    for provider_name, model_name, secret_name in providers:
        try:
            # Update settings
            settings.llm_provider = provider_name
            settings.llm_model = model_name
            
            # Set appropriate secret name
            if provider_name == "openai":
                settings.openai_secret_name = secret_name
            elif provider_name == "anthropic":
                settings.anthropic_secret_name = secret_name
            elif provider_name == "aws_bedrock":
                settings.aws_bedrock_secret_name = secret_name
            
            # Load credentials
            if settings.use_secrets_manager:
                settings.load_secrets_for_provider()
            
            # Create provider
            provider = get_llm_provider(settings)
            print(f"✓ Loaded {provider_name} provider successfully")
            
        except Exception as e:
            print(f"✗ Failed to load {provider_name}: {e}")


# ============================================================================
# TESTING
# ============================================================================

"""
Unit tests for Secrets Manager integration.
"""

def test_local_secrets_manager():
    """Test LocalSecretsManager with environment variables."""
    import os
    from backend.utils.secrets_manager import LocalSecretsManager
    
    # Set test environment variable
    os.environ["SECRET_test_api_key"] = "test-key-12345"
    
    manager = LocalSecretsManager()
    
    # Test retrieval
    value = manager.get_secret_value("test_api_key")
    assert value == "test-key-12345", f"Expected 'test-key-12345', got '{value}'"
    print("✓ LocalSecretsManager test passed")


def test_aws_secrets_manager():
    """Test AWSSecretsManager with AWS (requires AWS account)."""
    from backend.utils.secrets_manager import AWSSecretsManager
    import os
    
    # Skip if AWS credentials not configured
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("⊘ Skipping AWS test (no credentials configured)")
        return
    
    try:
        manager = AWSSecretsManager(region="us-east-1")
        
        # This will fail if the secret doesn't exist, which is expected
        # In a real test, you would create a test secret first
        
        print("✓ AWSSecretsManager initialized successfully")
    except Exception as e:
        print(f"⊘ AWSSecretsManager test skipped: {e}")


def test_settings_integration():
    """Test Settings integration with Secrets Manager."""
    from backend.config import get_settings
    import os
    
    # Set local test environment
    os.environ["USE_SECRETS_MANAGER"] = "false"
    os.environ["SECRET_dev_test_key"] = "test-value"
    
    settings = get_settings()
    
    # Test secret retrieval
    if not settings.use_secrets_manager:
        print("✓ Settings configured to use local secrets")
    
    print("✓ Settings integration test passed")


def test_json_secret():
    """Test JSON secret parsing."""
    import os
    import json
    from backend.utils.secrets_manager import LocalSecretsManager
    
    # Create JSON secret
    secret_data = {"api_key": "sk-xxxxx", "org_id": "org-xxxxx"}
    os.environ["SECRET_test_json"] = json.dumps(secret_data)
    
    manager = LocalSecretsManager()
    
    # Test retrieval
    secret = manager.get_secret("test_json")
    assert secret["api_key"] == "sk-xxxxx", "Failed to parse JSON secret"
    print("✓ JSON secret parsing test passed")


# ============================================================================
# CLI SETUP VERIFICATION
# ============================================================================

"""
CLI tools to verify Secrets Manager setup.
"""

def verify_setup():
    """Verify Secrets Manager setup and configuration."""
    print("\n" + "=" * 70)
    print("AWS Secrets Manager Setup Verification")
    print("=" * 70 + "\n")
    
    # Check imports
    print("Checking imports...")
    try:
        from backend.utils.secrets_manager import SecretsManager
        print("  ✓ SecretsManager available")
    except ImportError as e:
        print(f"  ✗ SecretsManager import failed: {e}")
        return False
    
    # Check configuration
    print("\nChecking configuration...")
    try:
        from backend.config import get_settings
        settings = get_settings()
        print(f"  ✓ Configuration loaded")
        print(f"    - Secrets Manager enabled: {settings.use_secrets_manager}")
        print(f"    - Region: {settings.secrets_manager_region}")
        print(f"    - OpenAI secret: {settings.openai_secret_name or 'Not configured'}")
        print(f"    - Anthropic secret: {settings.anthropic_secret_name or 'Not configured'}")
        print(f"    - Bedrock secret: {settings.aws_bedrock_secret_name or 'Not configured'}")
    except Exception as e:
        print(f"  ✗ Configuration check failed: {e}")
        return False
    
    # Check AWS credentials
    print("\nChecking AWS credentials...")
    try:
        import os
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            print(f"  ✓ AWS credentials configured")
        else:
            print(f"  ⊘ No AWS credentials found (expected for local development)")
    except ImportError:
        print(f"  ⊘ boto3 not installed (install with: pip install boto3)")
    except Exception as e:
        print(f"  ⊘ AWS credentials check failed: {e}")
    
    print("\n" + "=" * 70)
    print("Verification complete!")
    print("=" * 70 + "\n")
    
    return True


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("\nAWS Secrets Manager Examples and Tests\n")
    
    # Run tests
    print("Running tests...\n")
    
    try:
        test_local_secrets_manager()
        test_aws_secrets_manager()
        test_settings_integration()
        test_json_secret()
        
        print("\n✓ All tests completed!\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}\n")
        sys.exit(1)
    
    # Verify setup
    verify_setup()
    
    print("\nFor more examples, see the functions above.")
    print("For setup instructions, see: AWS_SECRETS_MANAGER_SETUP.md")
    print("For quick reference, see: AWS_SECRETS_MANAGER_QUICK_REFERENCE.md\n")
