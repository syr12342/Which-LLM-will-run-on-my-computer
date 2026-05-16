# Database configuration and session management

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import logging

from app.core.config import settings
from app.models.hardware import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def seed_hardware_data():
    """Seed database with common hardware devices"""
    from sqlalchemy import select
    from app.models.hardware import HardwareDevice
    
    async with async_session_maker() as session:
        # Check if already seeded
        result = await session.execute(select(HardwareDevice))
        if result.scalars().first():
            logger.info("Database already seeded")
            return
        
        # Common GPU and mobile devices
        devices = [
            # NVIDIA Desktop GPUs
            HardwareDevice(
                name="NVIDIA GeForce RTX 4090",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ada Lovelace",
                memory_size_gb=24.0,
                memory_bandwidth_gbps=1008.0,
                tensor_cores=True,
                fp16_tflops=369.0,
                fp8_tflops=738.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            HardwareDevice(
                name="NVIDIA GeForce RTX 4080",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ada Lovelace",
                memory_size_gb=16.0,
                memory_bandwidth_gbps=716.8,
                tensor_cores=True,
                fp16_tflops=262.0,
                fp8_tflops=524.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            HardwareDevice(
                name="NVIDIA GeForce RTX 3090",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ampere",
                memory_size_gb=24.0,
                memory_bandwidth_gbps=936.0,
                tensor_cores=True,
                fp16_tflops=178.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            HardwareDevice(
                name="NVIDIA GeForce RTX 3080",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ampere",
                memory_size_gb=12.0,
                memory_bandwidth_gbps=912.0,
                tensor_cores=True,
                fp16_tflops=142.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            HardwareDevice(
                name="NVIDIA GeForce RTX 4070 Ti",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ada Lovelace",
                memory_size_gb=12.0,
                memory_bandwidth_gbps=504.0,
                tensor_cores=True,
                fp16_tflops=182.0,
                fp8_tflops=364.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            # NVIDIA Mobile GPUs
            HardwareDevice(
                name="NVIDIA GeForce RTX 4090 Laptop",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ada Lovelace",
                memory_size_gb=16.0,
                memory_bandwidth_gbps=576.0,
                tensor_cores=True,
                fp16_tflops=130.0,
                is_mobile=True,
                os_support="Windows, Linux",
                supports_offloading=True
            ),
            # AMD GPUs
            HardwareDevice(
                name="AMD Radeon RX 7900 XTX",
                vendor="AMD",
                device_type="GPU",
                architecture="RDNA 3",
                memory_size_gb=24.0,
                memory_bandwidth_gbps=960.0,
                tensor_cores=False,
                fp16_tflops=123.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            HardwareDevice(
                name="AMD Radeon RX 7900 XT",
                vendor="AMD",
                device_type="GPU",
                architecture="RDNA 3",
                memory_size_gb=20.0,
                memory_bandwidth_gbps=800.0,
                tensor_cores=False,
                fp16_tflops=102.0,
                is_mobile=False,
                os_support="Linux, Windows"
            ),
            # Apple Silicon
            HardwareDevice(
                name="Apple M3 Max",
                vendor="Apple",
                device_type="SoC",
                architecture="M3",
                memory_size_gb=128.0,
                memory_bandwidth_gbps=400.0,
                tensor_cores=True,
                fp16_tflops=50.0,
                is_mobile=True,
                os_support="macOS, iOS",
                supports_offloading=True
            ),
            HardwareDevice(
                name="Apple M3 Pro",
                vendor="Apple",
                device_type="SoC",
                architecture="M3",
                memory_size_gb=36.0,
                memory_bandwidth_gbps=150.0,
                tensor_cores=True,
                fp16_tflops=20.0,
                is_mobile=True,
                os_support="macOS, iOS",
                supports_offloading=True
            ),
            HardwareDevice(
                name="Apple M3",
                vendor="Apple",
                device_type="SoC",
                architecture="M3",
                memory_size_gb=24.0,
                memory_bandwidth_gbps=100.0,
                tensor_cores=True,
                fp16_tflops=12.0,
                is_mobile=True,
                os_support="macOS, iOS",
                supports_offloading=True
            ),
            HardwareDevice(
                name="iPhone 17 Pro Max",
                vendor="Apple",
                device_type="SoC",
                architecture="A18 Pro",
                memory_size_gb=12.0,
                memory_bandwidth_gbps=80.0,
                tensor_cores=True,
                fp16_tflops=5.0,
                is_mobile=True,
                os_support="iOS",
                supports_offloading=True
            ),
            HardwareDevice(
                name="iPhone 16 Pro",
                vendor="Apple",
                device_type="SoC",
                architecture="A18",
                memory_size_gb=8.0,
                memory_bandwidth_gbps=60.0,
                tensor_cores=True,
                fp16_tflops=4.0,
                is_mobile=True,
                os_support="iOS",
                supports_offloading=True
            ),
            # Qualcomm Snapdragon (Android)
            HardwareDevice(
                name="Snapdragon 8 Elite",
                vendor="Qualcomm",
                device_type="SoC",
                architecture="Oryon CPU + Adreno GPU",
                memory_size_gb=24.0,
                memory_bandwidth_gbps=100.0,
                tensor_cores=False,
                fp16_tflops=8.0,
                is_mobile=True,
                os_support="Android",
                npu_tops=80.0,
                supports disaggregated_inference=True
            ),
            HardwareDevice(
                name="Snapdragon 8 Gen 3",
                vendor="Qualcomm",
                device_type="SoC",
                architecture="Kryo CPU + Adreno GPU",
                memory_size_gb=16.0,
                memory_bandwidth_gbps=80.0,
                tensor_cores=False,
                fp16_tflops=6.0,
                is_mobile=True,
                os_support="Android",
                npu_tops=50.0,
                supports disaggregated_inference=True
            ),
            HardwareDevice(
                name="Snapdragon 8 Gen 2",
                vendor="Qualcomm",
                device_type="SoC",
                architecture="Kryo CPU + Adreno GPU",
                memory_size_gb=12.0,
                memory_bandwidth_gbps=64.0,
                tensor_cores=False,
                fp16_tflops=4.5,
                is_mobile=True,
                os_support="Android",
                npu_tops=35.0,
                supports disaggregated_inference=False
            ),
            # Server/Datacenter GPUs
            HardwareDevice(
                name="NVIDIA A100 80GB",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ampere",
                memory_size_gb=80.0,
                memory_bandwidth_gbps=2039.0,
                tensor_cores=True,
                fp16_tflops=312.0,
                fp8_tflops=624.0,
                is_mobile=False,
                os_support="Linux"
            ),
            HardwareDevice(
                name="NVIDIA H100",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Hopper",
                memory_size_gb=80.0,
                memory_bandwidth_gbps=3350.0,
                tensor_cores=True,
                fp16_tflops=989.0,
                fp8_tflops=1979.0,
                is_mobile=False,
                os_support="Linux"
            ),
            HardwareDevice(
                name="NVIDIA L40S",
                vendor="NVIDIA",
                device_type="GPU",
                architecture="Ada Lovelace",
                memory_size_gb=48.0,
                memory_bandwidth_gbps=864.0,
                tensor_cores=True,
                fp16_tflops=362.0,
                fp8_tflops=724.0,
                is_mobile=False,
                os_support="Linux"
            ),
        ]
        
        session.add_all(devices)
        await session.commit()
        logger.info(f"Seeded {len(devices)} hardware devices")
