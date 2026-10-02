import json
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.anomaly import Anomaly
from app.models.driver import Driver
from app.models.order import Order

AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_system_kpis",
            "description": "Get real-time operational summary including active orders, driver availability, and unresolved anomalies",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_anomalies",
            "description": "Fetch active operational anomalies",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


async def execute_agent_tool(name: str, arguments: str, session: AsyncSession) -> str:
    if name == "get_system_kpis":
        stmt_orders = select(func.count(Order.id))
        stmt_drivers = select(func.count(Driver.id)).where(Driver.is_available == True)
        stmt_anomalies = select(func.count(Anomaly.id)).where(Anomaly.status == "open")

        res_o = await session.execute(stmt_orders)
        res_d = await session.execute(stmt_drivers)
        res_a = await session.execute(stmt_anomalies)

        kpis = {
            "total_orders": res_o.scalar_one(),
            "available_drivers": res_d.scalar_one(),
            "open_anomalies": res_a.scalar_one(),
        }
        return json.dumps(kpis)

    elif name == "get_active_anomalies":
        stmt = select(Anomaly).where(Anomaly.status == "open").limit(5)
        res = await session.execute(stmt)
        anomalies = res.scalars().all()
        return json.dumps(
            [
                {
                    "id": str(a.id),
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "description": a.description,
                }
                for a in anomalies
            ]
        )

    return json.dumps({"error": f"Unknown tool {name}"})
