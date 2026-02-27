"""Main FastAPI application - refactored modular architecture."""
import logging
from fastapi import FastAPI, WebSocket
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .database import connect_db, close_db
from .utils.seed import seed_demo_data

# Import routers
from .routes import auth, overview, learn, markets, portfolio, risk, advisor, alerts, community

# Import WebSocket handlers
from .websockets.alerts import alerts_websocket_handler
from .websockets.chat import chat_websocket_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DHAN-DRAFT API",
    description="AI-Powered Unified Financial Intelligence Ecosystem",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(overview.router, prefix=API_PREFIX)
app.include_router(learn.router, prefix=API_PREFIX)
app.include_router(markets.router, prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(risk.router, prefix=API_PREFIX)
app.include_router(advisor.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(community.router, prefix=API_PREFIX)


# WebSocket endpoints
@app.websocket("/api/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await alerts_websocket_handler(websocket)


@app.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for community chat."""
    await chat_websocket_handler(websocket)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and seed demo data."""
    logger.info("🚀 Starting DHAN-DRAFT API v2.0.0 (Refactored)")
    await connect_db()
    await seed_demo_data()
    logger.info("✅ Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection."""
    logger.info("Shutting down...")
    await close_db()
    logger.info("✅ Application shutdown complete")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "modular"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DHAN-DRAFT API v2.0.0",
        "docs": "/docs",
        "health": "/health"
    }
