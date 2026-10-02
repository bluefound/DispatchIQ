from pydantic import BaseModel
from fastapi import APIRouter
from app.agent.orchestrator import AgentOrchestrator
from app.api.deps import CurrentUserDep, SessionDep

router = APIRouter(prefix="/agent", tags=["AI Operations Agent"])


class AgentQueryRequest(BaseModel):
    query: str


class AgentQueryResponse(BaseModel):
    query: str
    response: str


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    req: AgentQueryRequest,
    session: SessionDep,
    _: CurrentUserDep,
):
    orchestrator = AgentOrchestrator()
    res = await orchestrator.run(req.query, session)
    return AgentQueryResponse(query=req.query, response=res)
