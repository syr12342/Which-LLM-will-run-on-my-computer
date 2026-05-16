# Repository pattern for hardware database access

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import List, Optional
import logging

from app.models.hardware import HardwareDevice

logger = logging.getLogger(__name__)


class HardwareRepository:
    """Repository for hardware device data access"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_all_devices(self) -> List[HardwareDevice]:
        """Get all hardware devices"""
        result = await self.db.execute(select(HardwareDevice))
        return result.scalars().all()
    
    async def get_device_by_id(self, device_id: int) -> Optional[HardwareDevice]:
        """Get a specific device by ID"""
        result = await self.db.execute(
            select(HardwareDevice).where(HardwareDevice.id == device_id)
        )
        return result.scalar_one_or_none()
    
    async def get_devices_by_vendor(self, vendor: str) -> List[HardwareDevice]:
        """Get all devices from a specific vendor"""
        result = await self.db.execute(
            select(HardwareDevice).where(HardwareDevice.vendor == vendor)
        )
        return result.scalars().all()
    
    async def get_devices_with_min_memory(self, min_memory_gb: float) -> List[HardwareDevice]:
        """Get devices with at least the specified memory"""
        result = await self.db.execute(
            select(HardwareDevice)
            .where(HardwareDevice.memory_size_gb >= min_memory_gb)
            .order_by(HardwareDevice.memory_size_gb)
        )
        return result.scalars().all()
    
    async def get_mobile_devices(self) -> List[HardwareDevice]:
        """Get all mobile devices (smartphones, tablets)"""
        result = await self.db.execute(
            select(HardwareDevice).where(HardwareDevice.is_mobile == True)
        )
        return result.scalars().all()
    
    async def get_devices_by_os(self, os_name: str) -> List[HardwareDevice]:
        """Get devices supporting a specific OS"""
        result = await self.db.execute(
            select(HardwareDevice)
            .where(or_(
                HardwareDevice.os_support == os_name,
                HardwareDevice.os_support.like(f"%{os_name}%")
            ))
        )
        return result.scalars().all()
    
    async def search_devices(self, query: str) -> List[HardwareDevice]:
        """Search devices by name or architecture"""
        search_pattern = f"%{query}%"
        result = await self.db.execute(
            select(HardwareDevice)
            .where(
                or_(
                    HardwareDevice.name.ilike(search_pattern),
                    HardwareDevice.architecture.ilike(search_pattern),
                    HardwareDevice.vendor.ilike(search_pattern)
                )
            )
            .limit(20)
        )
        return result.scalars().all()
