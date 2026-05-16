# Hugging Face search endpoint with debounced autocomplete

from fastapi import APIRouter, Query, HTTPException
from typing import List
import logging

from app.llm import HuggingFaceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search_models(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100)
) -> List[str]:
    """
    Search for models on Hugging Face
    
    Used for debounced autocomplete in the frontend
    """
    try:
        hf_service = HuggingFaceService()
        models = await hf_service.search_models(q, limit=limit)
        return models
    except Exception as e:
        logger.error(f"Error searching models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id:path}")
async def get_model_info(model_id: str):
    """
    Get detailed information about a specific model
    
    Path parameter allows slashes in model_id (e.g., meta-llama/Llama-2-7b)
    """
    try:
        hf_service = HuggingFaceService()
        metadata = await hf_service.get_model_metadata(model_id)
        
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Model not found: {model_id}"
            )
        
        return {
            "model_id": metadata.model_id,
            "parameters_billions": metadata.parameters_billions,
            "architecture": metadata.architecture,
            "is_moe": metadata.is_moe,
            "num_attention_heads": metadata.num_attention_heads,
            "num_key_value_heads": metadata.num_key_value_heads,
            "hidden_size": metadata.hidden_size,
            "num_hidden_layers": metadata.num_hidden_layers,
            "file_size_bytes": metadata.file_size_bytes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
