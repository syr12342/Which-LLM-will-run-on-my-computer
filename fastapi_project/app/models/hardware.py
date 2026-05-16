# SQLAlchemy ORM Models for Hardware Database

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class HardwareDevice(Base):
    """Hardware device model for GPU/SoC/NPU matching"""
    
    __tablename__ = "hardware_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    vendor = Column(String(100), nullable=False)  # NVIDIA, AMD, Apple, Qualcomm, etc.
    device_type = Column(String(50), nullable=False)  # GPU, SoC, NPU
    
    # Architecture details
    architecture = Column(String(100), nullable=False)  # Ada Lovelace, RDNA3, M3, etc.
    release_year = Column(Integer, nullable=True)
    
    # Memory specifications
    memory_size_gb = Column(Float, nullable=False)
    memory_bandwidth_gbps = Column(Float, nullable=False)
    memory_type = Column(String(50), nullable=True)  # GDDR6X, LPDDR5X, HBM3, etc.
    
    # Compute capabilities
    tensor_cores = Column(Boolean, default=False)
    fp16_tflops = Column(Float, nullable=False)
    fp32_tflops = Column(Float, nullable=True)
    fp8_tflops = Column(Float, nullable=True)
    int8_tops = Column(Float, nullable=True)
    
    # Mobile-specific fields
    is_mobile = Column(Boolean, default=False)
    os_support = Column(String(50), nullable=True)  # iOS, Android, Linux, Windows
    supports_offloading = Column(Boolean, default=False)  # Can offload to system RAM
    
    # NPU-specific (for Android/Snapdragon)
    npu_tops = Column(Float, nullable=True)  # TOPS for neural processing
    supports disaggregated_inference = Column(Boolean, default=False)  # NPU + GPU
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<HardwareDevice(name='{self.name}', memory={self.memory_size_gb}GB)>"
