"""Main entry point for memecoin trading system."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memecoin_trader.backend.core.config import settings, init_settings
from memecoin_trader.backend.core.logging import setup_logging, main_logger
from memecoin_trader.backend.api import create_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    main_logger.info("Starting memecoin trading system")
    
    # Initialize data directory
    os.makedirs("./data/trades", exist_ok=True)
    os.makedirs("./data/modifications", exist_ok=True)
    
    yield
    
    # Shutdown
    main_logger.info("Shutting down memecoin trading system")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Memecoin Trading System",
        description="AI-powered memecoin trading with multi-agent debate",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(create_router(), prefix="/api", tags=["trading"])
    
    return app


app = create_app()


def main():
    """Run the application."""
    import uvicorn
    
    # Setup logging
    setup_logging(
        level=settings.log_level,
        json_format=settings.environment == "production"
    )
    
    # Get port from environment
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "memecoin_trader.backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment == "development"
    )


if __name__ == "__main__":
    main()