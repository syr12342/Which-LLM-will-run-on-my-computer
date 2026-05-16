# Calculation endpoint - main VRAM calculation and hardware matching

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.schemas import CalculateRequest, CalculationResult, ModelMetadata
from app.llm import HuggingFaceService, VRAMCalculator, HardwareMatcher
from app.repositories import HardwareRepository
from app.core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CalculationResult)
async def calculate_vram(
    request: CalculateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Calculate VRAM requirements for a model and find matching hardware
    
    This endpoint:
    1. Fetches model metadata from Hugging Face
    2. Calculates VRAM requirements (weights + KV cache + overhead)
    3. Matches against available hardware database
    4. Returns compatible devices with performance estimates
    """
    try:
        # Initialize services
        hf_service = HuggingFaceService()
        vram_calculator = VRAMCalculator()
        hardware_matcher = HardwareMatcher()
        
        # Step 1: Get model metadata from Hugging Face
        logger.info(f"Fetching metadata for model: {request.model_id}")
        metadata = await hf_service.get_model_metadata(request.model_id)
        
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch metadata for model: {request.model_id}"
            )
        
        # Step 2: Calculate VRAM requirements
        logger.info("Calculating VRAM requirements")
        vram_breakdown = vram_calculator.calculate_vram(
            metadata=metadata,
            quantization=request.quantization,
            context_length=request.context_length,
            batch_size=request.batch_size,
            framework=request.framework,
            is_production=request.is_production
        )
        
        total_vram_gb = vram_breakdown['total_gb']
        
        # Step 3: Get all hardware devices
        hardware_repo = HardwareRepository(db)
        devices = await hardware_repo.get_all_devices()
        
        if not devices:
            logger.warning("No hardware devices in database")
            # Return calculation without matching
            return CalculationResult(
                model_metadata=metadata,
                vram_breakdown=vram_breakdown,
                total_vram_gb=total_vram_gb,
                kv_cache_gb=vram_breakdown['kv_cache_gb'],
                weights_gb=vram_breakdown['weights_gb'],
                overhead_gb=vram_breakdown['overhead_gb'],
                matching_devices=[],
                best_match=None
            )
        
        # Step 4: Match hardware
        logger.info(f"Matching against {len(devices)} devices")
        matching_results = hardware_matcher.match_hardware(
            metadata=metadata,
            required_vram_gb=total_vram_gb,
            devices=devices,
            framework=request.framework,
            quantization=request.quantization,
            context_length=request.context_length,
            batch_size=request.batch_size
        )
        
        # Step 5: Get best match
        best_match = hardware_matcher.get_best_match(matching_results)
        
        # Filter out devices that don't fit (for UI display)
        fitting_devices = [r for r in matching_results if r.fits]
        
        logger.info(
            f"Found {len(fitting_devices)} compatible devices, "
            f"best match: {best_match.device.name if best_match else 'None'}"
        )
        
        return CalculationResult(
            model_metadata=metadata,
            vram_breakdown=vram_breakdown,
            total_vram_gb=total_vram_gb,
            kv_cache_gb=vram_breakdown['kv_cache_gb'],
            weights_gb=vram_breakdown['weights_gb'],
            overhead_gb=vram_breakdown['overhead_gb'],
            matching_devices=fitting_devices,
            best_match=best_match
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in calculation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breakdown/{model_id}")
async def get_vram_breakdown(
    model_id: str,
    quantization: str = "FP16",
    context_length: int = 2048,
    batch_size: int = 1
):
    """Get detailed VRAM breakdown without hardware matching"""
    try:
        hf_service = HuggingFaceService()
        vram_calculator = VRAMCalculator()
        
        metadata = await hf_service.get_model_metadata(model_id)
        
        from app.schemas import QuantizationType, FrameworkType
        quant_type = QuantizationType[quantization]
        
        breakdown = vram_calculator.calculate_vram(
            metadata=metadata,
            quantization=quant_type,
            context_length=context_length,
            batch_size=batch_size,
            framework=FrameworkType.VLLM
        )
        
        return {
            "model_id": model_id,
            "parameters_billions": metadata.parameters_billions,
            "breakdown": breakdown
        }
        
    except Exception as e:
        logger.error(f"Error getting breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))
