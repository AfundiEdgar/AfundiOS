"""
AWS Bedrock LLM Integration

Provides integration with AWS Bedrock models including Nova Lite, Nova Pro, and Claude.
"""

import json
import logging
from typing import Optional
import boto3

logger = logging.getLogger(__name__)


class AWSBedrockLLM:
    """
    AWS Bedrock LLM client for models like Nova Lite, Nova Pro, and Claude.
    
    Supported models:
    - amazon.nova-lite-v1:0 (fastest, most cost-effective)
    - amazon.nova-pro-v1:0 (balanced performance and cost)
    - anthropic.claude-3-sonnet-20240229-v1:0
    - anthropic.claude-3-haiku-20240307-v1:0
    
    Example:
        from backend.core.aws_bedrock_llm import AWSBedrockLLM
        
        llm = AWSBedrockLLM(
            access_key_id="your-key",
            secret_access_key="your-secret",
            region="us-east-1",
            model="amazon.nova-lite-v1:0"
        )
        
        response = llm.generate(
            prompt="What is machine learning?",
            max_tokens=512,
            temperature=0.7
        )
    """
    
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
        model: str = "amazon.nova-lite-v1:0",
    ):
        """
        Initialize AWS Bedrock LLM client.
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region (default: us-east-1)
            model: Model ID (default: amazon.nova-lite-v1:0)
        """
        self.model = model
        self.region = region
        
        # Initialize Bedrock client
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        
        logger.info(f"Initialized AWS Bedrock LLM with model: {model} in region: {region}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using AWS Bedrock.
        
        Args:
            prompt: Input prompt/question
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Prepare request based on model family
            if "nova" in self.model:
                return self._generate_nova(prompt, max_tokens, temperature)
            elif "claude" in self.model:
                return self._generate_claude(prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported model: {self.model}")
                
        except Exception as e:
            logger.error(f"Error calling AWS Bedrock: {e}")
            raise RuntimeError(f"AWS Bedrock API error: {e}")
    
    def _generate_nova(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Amazon Nova models."""
        body = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 50,
        }
        
        response = self.client.invoke_model(
            modelId=self.model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        
        # Parse response
        response_body = json.loads(response["body"].read())
        
        # Extract text from Nova response
        if "generation" in response_body:
            return response_body["generation"]
        elif "text" in response_body:
            return response_body["text"]
        else:
            # Handle completion format
            if "completions" in response_body:
                return response_body["completions"][0]["data"]["text"]
            raise ValueError(f"Unexpected response format: {response_body}")
    
    def _generate_claude(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Anthropic Claude models via Bedrock."""
        body = {
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 50,
        }
        
        response = self.client.invoke_model(
            modelId=self.model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        
        # Parse response
        response_body = json.loads(response["body"].read())
        
        # Extract text from Claude response
        if "completion" in response_body:
            return response_body["completion"].strip()
        elif "content" in response_body:
            if isinstance(response_body["content"], list):
                return response_body["content"][0]["text"]
            return response_body["content"]
        else:
            raise ValueError(f"Unexpected response format: {response_body}")
    
    def __repr__(self) -> str:
        return f"AWSBedrockLLM(model={self.model}, region={self.region})"


# Model information for quick reference
NOVA_MODELS = {
    "nova-lite": {
        "id": "amazon.nova-lite-v1:0",
        "description": "Fastest and most cost-effective Nova model",
        "context_window": 4000,
        "input_cost_per_million": 0.075,
        "output_cost_per_million": 0.30,
    },
    "nova-pro": {
        "id": "amazon.nova-pro-v1:0",
        "description": "Balanced performance and cost",
        "context_window": 4000,
        "input_cost_per_million": 0.80,
        "output_cost_per_million": 3.20,
    },
}

CLAUDE_MODELS = {
    "claude-3-haiku": {
        "id": "anthropic.claude-3-haiku-20240307-v1:0",
        "description": "Fastest Claude model",
        "context_window": 200000,
    },
    "claude-3-sonnet": {
        "id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "description": "Balanced Claude model",
        "context_window": 200000,
    },
}
