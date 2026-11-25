import sys
import os

# Prevent app/ directory from shadowing the installed 'mcp' library package
script_dir = os.path.dirname(os.path.abspath(__file__))
while script_dir in sys.path:
    sys.path.remove(script_dir)

# Ensure project root is at the front of sys.path
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine, check_db_connection
from app.db.seed import seed_database
from app.adk_service.server import adk_app, handle_a2a_message
from app.a2a.schemas import A2AMessageEnvelope

# Import API Routers
from app.api.routes.requests import router as requests_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.vendors import router as vendors_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.negotiations import router as negotiations_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.purchase_orders import router as purchase_orders_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.replanning import router as replanning_router
from app.api.routes.observability import router as observability_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing DealForge AI Enterprise Platform...")

    # Verify and initialize database tables
    try:
        is_connected = check_db_connection()
        if is_connected:
            logger.info("Connected to primary database. Creating tables if not present...")
            Base.metadata.create_all(bind=engine)
            seed_database()
            logger.info("Database initialization and seed verification complete.")
        else:
            logger.warning("Database connection failed on startup. Verify MySQL credentials in .env.")
    except Exception as e:
        logger.error(f"Database startup error: {e}")

    yield

    logger.info("Shutting down DealForge AI...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "DealForge AI: An Integrated Multi-Agent Enterprise Procurement Automation System. "
        "Powered by CrewAI, Google ADK, Model Context Protocol (MCP), A2A Protocol, and MySQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend dashboard and inter-agent integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoints
@app.get("/api/health", tags=["Health"])
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "database_connected": db_ok,
        "google_adk_mounted": True,
        "protocol": "A2A/1.0"
    }


@app.get("/api/health/db", tags=["Health"])
def db_health_check():
    db_ok = check_db_connection()
    return {"database": "mysql", "connected": db_ok}


# Include All Procurement API Routers under /api
app.include_router(requests_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(vendors_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(negotiations_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(replanning_router, prefix="/api")
app.include_router(observability_router, prefix="/api")

# Mount Independent Google ADK Risk Agent service for dual-mode deployment
# (Available both on main port under /adk-service or via standalone port 8001)
app.mount("/adk-service", adk_app)

# Expose primary A2A Protocol root endpoint (Requirement 6: POST /a2a/v1/message)
@app.post("/a2a/v1/message", response_model=A2AMessageEnvelope, tags=["A2A Protocol"])
def a2a_root_message_handler(envelope: A2AMessageEnvelope):
    return handle_a2a_message(envelope)

# Mount Frontend Static Directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "DealForge AI API is active. Access docs at /docs"}


if __name__ == "__main__":
    import uvicorn
    # Use direct app object or project root app_dir to guarantee clean startup in any terminal
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
