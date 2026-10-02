import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.llm_adapter import get_llm_adapter
from app.agent.tools import AGENT_TOOLS_SCHEMA, execute_agent_tool

SYSTEM_PROMPT = """You are DispatchIQ AI Operations Assistant.
You analyze delivery logistics, driver availability, ETA performance, and operational anomalies.
Use tools to query platform state before answering. Be concise, professional, and clear."""


class AgentOrchestrator:
    def __init__(self):
        self.llm = get_llm_adapter()

    async def run(self, user_query: str, session: AsyncSession) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        response = await self.llm.chat(messages, tools=AGENT_TOOLS_SCHEMA)
        tool_calls = response.get("tool_calls", [])

        if not tool_calls:
            return response.get("content", "")

        messages.append({"role": "assistant", "content": response.get("content"), "tool_calls": tool_calls})

        for tc in tool_calls:
            tool_output = await execute_agent_tool(tc["name"], tc["arguments"], session)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_output,
                }
            )

        final_response = await self.llm.chat(messages)
        return final_response.get("content", "")
