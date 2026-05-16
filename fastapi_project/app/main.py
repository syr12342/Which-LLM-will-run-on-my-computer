# Main FastAPI Application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db, seed_hardware_data
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
## LLM Router & Matching Platform

A production-ready system for routing Large Language Models to compatible hardware.

### Features:
- **Hugging Face Integration**: Parse model metadata directly from HF Hub
- **VRAM Calculation**: Accurate memory estimation including:
  - Model weights (FP16, INT8, INT4, GGUF quantizations)
  - KV Cache (MHA and GQA support)
  - Framework overhead (vLLM, llama.cpp, Transformers)
- **Hardware Matching**: Find compatible GPUs, SoCs, and mobile devices
- **Mobile Optimization**: Apple Silicon and Android NPU support

### API Endpoints:
- `POST /api/v1/calculate/`: Calculate VRAM and find matching hardware
- `GET /api/v1/hf/search`: Search Hugging Face models
- `GET /api/v1/hardware/devices`: List available hardware
        """,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up LLM Router Platform...")
        await init_db()
        await seed_hardware_data()
        logger.info("Database initialized and seeded")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
