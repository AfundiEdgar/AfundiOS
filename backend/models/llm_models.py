from pydantic import BaseModel


class LLMConfig(BaseModel):
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 512
