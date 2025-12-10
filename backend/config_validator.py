#!/usr/bin/env python3
"""
Configuration Validator - Standalone tool to validate backend configuration.

Usage:
    python -m backend.config_validator       # Validate configuration
    python backend/config_validator.py       # Direct execution
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_env_file() -> Tuple[bool, List[str]]:
    """Check if .env file exists and is readable."""
    messages = []
    
    env_files = [
        Path(".env"),
        Path("backend/.env"),
        Path("/home/edgar/Documents/AOSBAckend/.env"),
    ]
    
    found_env = False
    for env_file in env_files:
        if env_file.exists():
            messages.append(f"✓ Found .env file at: {env_file.absolute()}")
            found_env = True
            break
    
    if not found_env:
        messages.append("⚠ No .env file found. Using environment variables only.")
        messages.append("  💡 Copy .env.example to .env and fill in your values")
    
    return True, messages


def validate_environment_variables() -> Tuple[bool, List[str]]:
    """Check for critical environment variables."""
    messages = []
    warnings = []
    
    # Check LLM provider
    llm_provider = os.getenv('LLM_PROVIDER', 'openai')
    messages.append(f"ℹ LLM Provider: {llm_provider}")
    
    if llm_provider == 'openai':
        if os.getenv('OPENAI_API_KEY'):
            messages.append("✓ OPENAI_API_KEY is set")
        else:
            warnings.append("❌ OPENAI_API_KEY is not set (required for OpenAI provider)")
    
    elif llm_provider == 'anthropic':
        if os.getenv('ANTHROPIC_API_KEY'):
            messages.append("✓ ANTHROPIC_API_KEY is set")
        else:
            warnings.append("❌ ANTHROPIC_API_KEY is not set (required for Anthropic provider)")
    
    elif llm_provider == 'cohere':
        if os.getenv('COHERE_API_KEY'):
            messages.append("✓ COHERE_API_KEY is set")
        else:
            warnings.append("❌ COHERE_API_KEY is not set (required for Cohere provider)")
    
    elif llm_provider == 'local':
        if os.getenv('LOCAL_LLM_URL'):
            messages.append("✓ LOCAL_LLM_URL is set")
        else:
            warnings.append("❌ LOCAL_LLM_URL is not set (required for local provider)")
    
    else:
        warnings.append(f"❌ Invalid LLM_PROVIDER: {llm_provider}")
    
    is_valid = len(warnings) == 0
    return is_valid, messages + warnings


def validate_configuration() -> Tuple[bool, List[str]]:
    """Load and validate actual configuration."""
    messages = []
    
    try:
        # Try relative import first (when run as module)
        try:
            from config import settings, ConfigurationError
        except ImportError:
            # Fall back to direct import from current package
            from backend.config import settings, ConfigurationError
        
        messages.append("✓ Configuration loaded successfully")
        
        # Run validation method
        is_valid, errors = settings.validate()
        if is_valid:
            messages.append("✓ All configuration validations passed")
        else:
            messages.extend(errors)
        
        # Print summary
        print("\n" + "="*60)
        settings.print_config_summary()
        print("="*60)
        
        return is_valid, messages
    
    except Exception as e:
        error_msg = str(e)
        return False, [f"❌ Configuration error: {error_msg}"]


def main():
    """Main validator function."""
    print("\n" + "="*60)
    print("🔍 Backend Configuration Validator")
    print("="*60 + "\n")
    
    all_valid = True
    all_messages = []
    
    # Check 1: Environment file
    print("📋 Checking environment files...")
    valid, msgs = check_env_file()
    all_messages.extend(msgs)
    all_valid = all_valid and valid
    
    # Check 2: Environment variables
    print("\n🔐 Checking environment variables...")
    valid, msgs = validate_environment_variables()
    all_messages.extend(msgs)
    all_valid = all_valid and valid
    
    # Check 3: Full configuration
    print("\n⚙️  Loading configuration...")
    valid, msgs = validate_configuration()
    all_messages.extend(msgs)
    all_valid = all_valid and valid
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Validation Results")
    print("="*60)
    for msg in all_messages:
        print(msg)
    
    print("\n" + "="*60)
    if all_valid:
        print("✅ Configuration is valid and ready to use!")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ Configuration has errors. Please fix them above.")
        print("="*60)
        print("\n💡 Quick fixes:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your API keys")
        print("  3. Run: python -m backend.config_validator")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
