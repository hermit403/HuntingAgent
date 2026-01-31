import httpx
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel

from core.config import settings


class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


class LLMResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Dict[str, Any]


class LLMClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.OPENAI_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, str]]] = None
    ) -> LLMResponse:
        """调用LLM进行聊天完成"""
        payload = {
            "model": model or settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return LLMResponse(**response.json())
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")
    
    async def close(self):
        await self.client.aclose()


llm_client = LLMClient()