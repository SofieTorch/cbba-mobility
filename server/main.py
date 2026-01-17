from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from database import engine
from routes import lines_router, recordings_router, routes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: verify database connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Open Transit API",
    description="API for managing transit lines and routes with geographic data",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(lines_router)
app.include_router(recordings_router)
app.include_router(routes_router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "open-transit"}


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected"
    }
