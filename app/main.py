import sys
import os

# Ensure project root is in sys.path when executed directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
from app.adk_service.server import adk_app

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
from app.api.routes.auth import router as auth_router
from app.api.routes.procurement import router as procurement_router
from app.a2a.router import router as a2a_router


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
app.include_router(auth_router, prefix="/api")
app.include_router(procurement_router, prefix="/api")
app.include_router(a2a_router)

# Mount Independent Google ADK Risk Agent service for dual-mode deployment
# (Available both on main port under /adk-service or via standalone port 8001)
app.mount("/adk-service", adk_app)

# Mount Frontend Static Directory (React 18 + TypeScript + Tailwind Build)
react_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-app", "dist")
legacy_frontend = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.exists(react_dist):
    assets_dir = os.path.join(react_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="react-assets")
    if os.path.exists(legacy_frontend):
        app.mount("/static", StaticFiles(directory=legacy_frontend), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(react_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "DealForge AI API is active. Access docs at /docs"}

elif os.path.exists(legacy_frontend):
    app.mount("/static", StaticFiles(directory=legacy_frontend), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(legacy_frontend, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "DealForge AI API is active. Access docs at /docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
