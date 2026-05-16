# Hardware database management endpoint

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.schemas import HardwareDevice as HardwareDeviceSchema
from app.repositories import HardwareRepository
from app.core.database import get_db_session
from app.models.hardware import HardwareDevice

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/devices", response_model=List[HardwareDeviceSchema])
async def list_devices(
    vendor: Optional[str] = Query(None),
    min_memory: Optional[float] = Query(None),
    mobile_only: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """List all hardware devices with optional filters"""
    repo = HardwareRepository(db)
    
    if mobile_only:
        devices = await repo.get_mobile_devices()
    elif min_memory:
        devices = await repo.get_devices_with_min_memory(min_memory)
    elif vendor:
        devices = await repo.get_devices_by_vendor(vendor)
    else:
        devices = await repo.get_all_devices()
    
    return [
        HardwareDeviceSchema(
            id=d.id,
            name=d.name,
            vendor=d.vendor,
            device_type=d.device_type,
            architecture=d.architecture,
            memory_size_gb=d.memory_size_gb,
            memory_bandwidth_gbps=d.memory_bandwidth_gbps,
            tensor_cores=d.tensor_cores,
            fp16_tflops=d.fp16_tflops,
            fp8_tflops=d.fp8_tflops,
            is_mobile=d.is_mobile,
            os_support=d.os_support,
            supports_offloading=d.supports_offloading,
            npu_tops=d.npu_tops
        )
        for d in devices
    ]


@router.get("/devices/search")
async def search_devices(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db_session)
):
    """Search devices by name or architecture"""
    repo = HardwareRepository(db)
    devices = await repo.search_devices(q)
    
    return [
        HardwareDeviceSchema(
            id=d.id,
            name=d.name,
            vendor=d.vendor,
            device_type=d.device_type,
            architecture=d.architecture,
            memory_size_gb=d.memory_size_gb,
            memory_bandwidth_gbps=d.memory_bandwidth_gbps,
            tensor_cores=d.tensor_cores,
            fp16_tflops=d.fp16_tflops,
            fp8_tflops=d.fp8_tflops,
            is_mobile=d.is_mobile,
            os_support=d.os_support,
            supports_offloading=d.supports_offloading,
            npu_tops=d.npu_tops
        )
        for d in devices
    ]


@router.get("/devices/{device_id}", response_model=HardwareDeviceSchema)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific device by ID"""
    repo = HardwareRepository(db)
    device = await repo.get_device_by_id(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return HardwareDeviceSchema(
        id=device.id,
        name=device.name,
        vendor=device.vendor,
        device_type=device.device_type,
        architecture=device.architecture,
        memory_size_gb=device.memory_size_gb,
        memory_bandwidth_gbps=device.memory_bandwidth_gbps,
        tensor_cores=device.tensor_cores,
        fp16_tflops=device.fp16_tflops,
        fp8_tflops=device.fp8_tflops,
        is_mobile=device.is_mobile,
        os_support=device.os_support,
        supports_offloading=device.supports_offloading,
        npu_tops=device.npu_tops
    )
