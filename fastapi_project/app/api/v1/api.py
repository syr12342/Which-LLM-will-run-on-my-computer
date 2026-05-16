# API v1 Router

from fastapi import APIRouter

from app.api.v1.endpoints import calculate, hf_search, hardware

api_router = APIRouter()

api_router.include_router(calculate.router, prefix="/calculate", tags=["calculation"])
api_router.include_router(hf_search.router, prefix="/hf", tags=["huggingface"])
api_router.include_router(hardware.router, prefix="/hardware", tags=["hardware"])
