from app.api.health import router as health_router
from app.api.v1 import simulations as v1_simulations
from app.core.database import engine, test_db_connection
from app.core.redis_client import redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

app = FastAPI(title="Office Simulation Backend")

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])

app.include_router(v1_simulations.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    await test_db_connection()
    await redis_client.initialize()


@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()
    await engine.dispose()
