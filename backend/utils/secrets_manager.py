"""
AWS Secrets Manager integration for secure credential storage and retrieval.

This module provides a stub implementation for AWS Secrets Manager that allows
applications to fetch secrets securely without storing them in .env files.

Usage:
    from backend.utils.secrets_manager import SecretsManager
    
    manager = SecretsManager(region='us-east-1')
    secret = manager.get_secret('my-secret-name')
    
Configuration:
    Set environment variables:
    - USE_SECRETS_MANAGER: "true" to enable (default: "false")
    - SECRETS_MANAGER_REGION: AWS region (default: "us-east-1")
    - SECRETS_MANAGER_ENABLED: Enable/disable secrets manager
"""

import json
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class SecretsManagerBase(ABC):
    """Abstract base class for secrets manager implementations."""
    
    @abstractmethod
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret by name."""
        pass
    
    @abstractmethod
    def get_secret_value(self, secret_name: str, key: Optional[str] = None) -> str:
        """Retrieve a secret value, optionally extracting a specific key."""
        pass


class AWSSecretsManager(SecretsManagerBase):
    """
    AWS Secrets Manager implementation for retrieving secrets from AWS.
    
    This implementation uses boto3 to fetch secrets stored in AWS Secrets Manager.
    Secrets should be stored as JSON objects or plain strings.
    
    Example secret in AWS:
        {
            "username": "admin",
            "password": "secret-password",
            "api_key": "sk-xxxxx"
        }
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        """
        Initialize AWS Secrets Manager client.
        
        Args:
            region: AWS region name (default: us-east-1)
            access_key_id: AWS access key ID (uses boto3 default if not provided)
            secret_access_key: AWS secret access key (uses boto3 default if not provided)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            self.ClientError = ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for AWS Secrets Manager. "
                "Install it with: pip install boto3"
            )
        
        self.region = region
        self.boto3 = boto3
        self._client = None
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        
    @property
    def client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            kwargs = {"region_name": self.region}
            if self._access_key_id and self._secret_access_key:
                kwargs["aws_access_key_id"] = self._access_key_id
                kwargs["aws_secret_access_key"] = self._secret_access_key
            
            self._client = self.boto3.client("secretsmanager", **kwargs)
        
        return self._client
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name or ARN of the secret
            
        Returns:
            Dictionary with secret data. If secret is JSON, parses and returns dict.
            If secret is plain string, returns {"SecretString": value}
            
        Raises:
            SecretsManagerError: If secret retrieval fails
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Handle binary secret
            if "SecretBinary" in response:
                logger.warning(
                    f"Secret '{secret_name}' is binary. Use get_secret_value() instead."
                )
                return {"SecretBinary": response["SecretBinary"]}
            
            # Handle string secret
            secret_string = response.get("SecretString", "")
            
            # Try to parse as JSON
            try:
                secret_dict = json.loads(secret_string)
                logger.debug(f"Successfully retrieved and parsed secret: {secret_name}")
                return secret_dict
            except json.JSONDecodeError:
                # If not JSON, return as plain string
                logger.debug(f"Secret '{secret_name}' is not JSON, returning as string")
                return {"SecretString": secret_string}
                
        except self.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                raise SecretsManagerError(
                    f"Secret '{secret_name}' not found in AWS Secrets Manager. "
                    f"Create it in AWS console or using AWS CLI."
                )
            elif error_code == "InvalidRequestException":
                raise SecretsManagerError(
                    f"Invalid request for secret '{secret_name}'. "
                    f"Check the secret name and permissions."
                )
            elif error_code == "InvalidParameterException":
                raise SecretsManagerError(
                    f"Invalid parameter for secret '{secret_name}'. "
                    f"Verify the secret exists and is accessible."
                )
            else:
                raise SecretsManagerError(
                    f"Failed to retrieve secret '{secret_name}': {error_code} - {str(e)}"
                )
        except Exception as e:
            raise SecretsManagerError(
                f"Unexpected error retrieving secret '{secret_name}': {str(e)}"
            )
    
    def get_secret_value(
        self,
        secret_name: str,
        key: Optional[str] = None
    ) -> str:
        """
        Retrieve a secret value with optional key extraction.
        
        Args:
            secret_name: Name or ARN of the secret
            key: Optional key to extract from JSON secret
            
        Returns:
            Secret value as string
            
        Raises:
            SecretsManagerError: If secret retrieval or extraction fails
        """
        try:
            secret = self.get_secret(secret_name)
            
            if key:
                # Extract specific key from secret
                if key not in secret:
                    raise SecretsManagerError(
                        f"Key '{key}' not found in secret '{secret_name}'. "
                        f"Available keys: {list(secret.keys())}"
                    )
                value = secret[key]
            else:
                # If single key in dict, return that value
                if len(secret) == 1:
                    value = list(secret.values())[0]
                else:
                    # Multiple keys without key specified
                    if "SecretString" in secret:
                        value = secret["SecretString"]
                    else:
                        raise SecretsManagerError(
                            f"Multiple keys in secret '{secret_name}' but no key specified. "
                            f"Call get_secret_value('{secret_name}', key='<key_name>')"
                        )
            
            return str(value)
            
        except SecretsManagerError:
            raise
        except Exception as e:
            raise SecretsManagerError(
                f"Error extracting value from secret '{secret_name}': {str(e)}"
            )


class LocalSecretsManager(SecretsManagerBase):
    """
    Local stub implementation of Secrets Manager for development/testing.
    
    This implementation uses environment variables instead of AWS.
    Useful for local development and CI/CD pipelines without AWS access.
    
    Environment variables should be named: SECRET_<secret_name>_<key>
    Example:
        SECRET_llm_credentials_openai_api_key=sk-xxxxx
        SECRET_llm_credentials_access_key_id=AKIA...
    """
    
    def __init__(self):
        """Initialize local secrets manager."""
        import os
        self.os = os
        logger.info("Using local secrets manager (environment variables)")
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve a secret from environment variables.
        
        Environment variable format: SECRET_<secret_name>
        If the value is JSON, it will be parsed.
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Dictionary with secret data
            
        Raises:
            SecretsManagerError: If secret not found
        """
        env_key = f"SECRET_{secret_name}".upper().replace("-", "_")
        value = self.os.getenv(env_key)
        
        if value is None:
            raise SecretsManagerError(
                f"Secret '{secret_name}' not found in environment. "
                f"Set environment variable: {env_key}=<value>"
            )
        
        # Try to parse as JSON
        try:
            secret_dict = json.loads(value)
            logger.debug(f"Retrieved and parsed secret from {env_key}")
            return secret_dict
        except json.JSONDecodeError:
            # Return as plain string in a dict
            logger.debug(f"Secret from {env_key} is not JSON, returning as string")
            return {"SecretString": value}
    
    def get_secret_value(
        self,
        secret_name: str,
        key: Optional[str] = None
    ) -> str:
        """
        Retrieve a secret value from environment variable.
        
        Environment variable format options:
        - SECRET_<secret_name> (for plain string secrets)
        - SECRET_<secret_name>_<key> (for specific key from JSON secret)
        
        Args:
            secret_name: Name of the secret
            key: Optional key to extract
            
        Returns:
            Secret value as string
            
        Raises:
            SecretsManagerError: If secret not found
        """
        if key:
            # Look for specific key: SECRET_<secret_name>_<key>
            env_key = f"SECRET_{secret_name}_{key}".upper().replace("-", "_")
            value = self.os.getenv(env_key)
            
            if value is None:
                raise SecretsManagerError(
                    f"Secret key '{secret_name}.{key}' not found in environment. "
                    f"Set environment variable: {env_key}=<value>"
                )
        else:
            # Look for secret: SECRET_<secret_name>
            env_key = f"SECRET_{secret_name}".upper().replace("-", "_")
            value = self.os.getenv(env_key)
            
            if value is None:
                raise SecretsManagerError(
                    f"Secret '{secret_name}' not found in environment. "
                    f"Set environment variable: {env_key}=<value>"
                )
        
        return value


class SecretsManager:
    """
    Unified interface for secrets management.
    
    Automatically selects between AWS Secrets Manager and local (environment variable)
    based on configuration.
    
    Environment Configuration:
        USE_SECRETS_MANAGER: "true" to enable AWS Secrets Manager (default: "false")
        SECRETS_MANAGER_REGION: AWS region for Secrets Manager (default: "us-east-1")
        AWS_ACCESS_KEY_ID: AWS credentials (optional, uses default boto3 chain if not set)
        AWS_SECRET_ACCESS_KEY: AWS credentials (optional)
    
    Usage:
        # Using default configuration
        manager = SecretsManager()
        
        # Using AWS Secrets Manager
        manager = SecretsManager(use_aws=True, region="eu-west-1")
        
        # Using local environment variables
        manager = SecretsManager(use_aws=False)
    """
    
    def __init__(
        self,
        use_aws: bool = True,
        region: str = "us-east-1",
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        """
        Initialize SecretsManager.
        
        Args:
            use_aws: Use AWS Secrets Manager (True) or local (False)
                    Defaults to env var USE_SECRETS_MANAGER or False
            region: AWS region for Secrets Manager (default: us-east-1)
                   Can override with SECRETS_MANAGER_REGION env var
            access_key_id: AWS access key ID (uses boto3 default if not provided)
            secret_access_key: AWS secret access key (uses boto3 default if not provided)
        """
        import os
        
        # Check environment variables
        env_use_aws = os.getenv("USE_SECRETS_MANAGER", "false").lower() == "true"
        env_region = os.getenv("SECRETS_MANAGER_REGION", region)
        
        # Use provided args, fall back to environment
        self.use_aws = use_aws if use_aws is not None else env_use_aws
        self.region = env_region
        
        # Get AWS credentials from args or environment
        self.access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # Initialize the appropriate backend
        if self.use_aws:
            try:
                self._manager = AWSSecretsManager(
                    region=self.region,
                    access_key_id=self.access_key_id,
                    secret_access_key=self.secret_access_key,
                )
                logger.info(
                    f"Initialized AWS Secrets Manager (region: {self.region})"
                )
            except ImportError as e:
                logger.warning(
                    f"AWS Secrets Manager not available ({e}). "
                    "Falling back to local secrets manager."
                )
                self._manager = LocalSecretsManager()
                self.use_aws = False
        else:
            self._manager = LocalSecretsManager()
            logger.info("Using local secrets manager (environment variables)")
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve a secret.
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Dictionary with secret data
        """
        return self._manager.get_secret(secret_name)
    
    def get_secret_value(
        self,
        secret_name: str,
        key: Optional[str] = None
    ) -> str:
        """
        Retrieve a secret value.
        
        Args:
            secret_name: Name of the secret
            key: Optional key to extract from JSON secret
            
        Returns:
            Secret value as string
        """
        return self._manager.get_secret_value(secret_name, key)


class SecretsManagerError(Exception):
    """Custom exception for secrets manager errors."""
    pass
