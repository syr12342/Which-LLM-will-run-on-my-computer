# Pydantic Schemas for Request/Response Validation

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class QuantizationType(str, Enum):
    FP32 = "FP32"
    FP16 = "FP16"
    BF16 = "BF16"
    INT8 = "INT8"
    INT4 = "INT4"
    Q4_K_M = "Q4_K_M"
    Q5_K_M = "Q5_K_M"
    Q8_0 = "Q8_0"


class FrameworkType(str, Enum):
    VLLM = "vLLM"
    LLAMA_CPP = "llama.cpp"
    TRANSFORMERS = "transformers"
    MLC_LLM = "MLC-LLM"
    EXECUTORCH = "ExecuTorch"
    TENSORRT_LLM = "TensorRT-LLM"


class CalculateRequest(BaseModel):
    model_id: str = Field(..., description="Hugging Face model ID")
    quantization: QuantizationType = Field(default=QuantizationType.FP16)
    context_length: int = Field(default=2048, ge=128, le=131072)
    batch_size: int = Field(default=1, ge=1, le=1024)
    framework: FrameworkType = Field(default=FrameworkType.VLLM)
    is_production: bool = Field(default=False, description="Use high-load overhead factor")


class ModelMetadata(BaseModel):
    model_id: str
    parameters_billions: float
    total_parameters_billions: Optional[float] = None  # For MoE models
    active_parameters_billions: Optional[float] = None  # For MoE models
    architecture: Optional[str] = None
    num_attention_heads: Optional[int] = None
    num_key_value_heads: Optional[int] = None  # For GQA
    hidden_size: Optional[int] = None
    num_hidden_layers: Optional[int] = None
    vocab_size: Optional[int] = None
    file_size_bytes: Optional[int] = None
    is_moe: bool = False


class HardwareDevice(BaseModel):
    id: int
    name: str
    vendor: str
    device_type: str  # GPU, SoC, NPU
    architecture: str
    memory_size_gb: float
    memory_bandwidth_gbps: float
    tensor_cores: bool
    fp16_tflops: float
    fp8_tflops: Optional[float] = None
    is_mobile: bool = False
    os_support: Optional[str] = None  # iOS, Android, Linux, Windows
    supports_offloading: bool = False
    npu_tops: Optional[float] = None  # For Android NPU


class MatchingResult(BaseModel):
    device: HardwareDevice
    fits: bool
    available_memory_gb: float
    required_memory_gb: float
    memory_utilization_percent: float
    offloading_required: bool
    offloaded_layers: int = 0
    estimated_speed_tokens_per_sec: float
    warnings: List[str] = []
    recommendations: List[str] = []


class CalculationResult(BaseModel):
    model_metadata: ModelMetadata
    vram_breakdown: dict
    total_vram_gb: float
    kv_cache_gb: float
    weights_gb: float
    overhead_gb: float
    matching_devices: List[MatchingResult]
    best_match: Optional[MatchingResult] = None
