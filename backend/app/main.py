from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.anomalies import router as anomalies_router
from app.api.auth import router as auth_router
from app.api.dispatch import router as dispatch_router
from app.api.drivers import router as drivers_router
from app.api.orders import router as orders_router
from app.api.policies import router as policies_router
from app.api.restaurants import router as restaurants_router
from app.api.websocket import router as ws_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Real-Time Delivery Intelligence & Dispatch Optimization Platform API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(restaurants_router, prefix="/api/v1")
app.include_router(drivers_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(dispatch_router, prefix="/api/v1")
app.include_router(policies_router, prefix="/api/v1")
app.include_router(anomalies_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    }
