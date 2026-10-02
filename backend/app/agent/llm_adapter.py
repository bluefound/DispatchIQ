from abc import ABC, abstractmethod
from typing import Any
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()


class LLMAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        pass


class OpenAIAdapter(LLMAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key or "dummy")
        self.model = settings.llm_model

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    })

            return {
                "content": message.content or "",
                "tool_calls": tool_calls,
            }
        except Exception as e:
            return {
                "content": f"AI Operations Agent offline or provider not configured ({str(e)})",
                "tool_calls": [],
            }


def get_llm_adapter() -> LLMAdapter:
    return OpenAIAdapter()
