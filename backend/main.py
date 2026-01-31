import logging
import os
import asyncio
import time
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from core.config import settings
from core.task_processor import task_processor
from core.agent_registry import agent_registry
from core.cleanup import cleanup_old_data
from database import init_db
from api.routes import api_router
from api.websocket import websocket_endpoint
from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.static_analysis_agent import StaticAnalysisAgent
from agents.skill_agent import SkillAgent
from agents.supervisor_agent import SupervisorAgent
from tools.vulnerability_scanner import VulnerabilityScanner
from tools.code_linter import CodeLinter
from tools.dependency_checker import DependencyChecker
from tools.registry import skill_registry
from core.rate_limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

agents: Dict[str, Any] = {}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}, path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": request.url.path,
            "timestamp": time.time()
        },
        headers=getattr(exc, "headers", {})
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}, path: {request.url.path}", exc_info=True)

    detail = "Internal server error" if settings.ENVIRONMENT == "production" else str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": detail,
            "path": request.url.path,
            "timestamp": time.time()
        }
    )


def configure_cors_middleware(app: FastAPI) -> None:
    if settings.ENVIRONMENT == "production":
        allow_origins: List[str] = settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else [
            "https://yourdomain.com"
        ]
        allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
        allow_headers: List[str] = ["Content-Type", "Authorization", "X-Requested-With"]
    else:
        allow_origins = ["*"]
        allow_methods = ["*"]
        allow_headers = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        max_age=600,
    )


async def periodic_cleanup():
    while True:
        try:
            await asyncio.sleep(24 * 60 * 60)
            await cleanup_old_data(days=30)
            logger.info("Periodic cleanup completed successfully")
        except Exception as e:
            logger.error(f"Periodic cleanup failed: {str(e)}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HuntingAgent...")

    init_db()

    skill_registry.register_tool(VulnerabilityScanner())
    skill_registry.register_tool(CodeLinter())
    skill_registry.register_tool(DependencyChecker())

    agents["user_agent"] = UserAgent()
    agents["coordinator_agent"] = CoordinatorAgent()
    agents["static_analysis_agent"] = StaticAnalysisAgent()
    agents["skill_agent"] = SkillAgent()
    agents["supervisor_agent"] = SupervisorAgent()

    for agent_id, agent in agents.items():
        agent_registry.register_agent(agent_id, agent)
        await agent.start()

    await task_processor.start()

    asyncio.create_task(periodic_cleanup())

    logger.info("All agents started")

    yield

    logger.info("Shutting down HuntingAgent...")

    await task_processor.stop()

    for agent in agents.values():
        await agent.stop()

    logger.info("All agents stopped")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.state.limiter = limiter

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

configure_cors_middleware(app)

app.include_router(api_router, prefix="/api/v1")
app.websocket("/ws/{client_id}")(websocket_endpoint)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/{full_path:path}")
async def catch_all(full_path: str):

    if full_path.startswith("api/") or full_path.startswith("ws/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")

    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return RedirectResponse(url="/")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/agents/status")
async def get_agents_status():
    return {
        agent_id: agent.get_status()
        for agent_id, agent in agents.items()
    }
