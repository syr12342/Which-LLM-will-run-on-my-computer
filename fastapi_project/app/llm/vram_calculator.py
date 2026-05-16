# VRAM Calculation Engine with MHA/GQA support

import math
from typing import Dict, Any, Optional
from app.schemas import ModelMetadata, QuantizationType, FrameworkType
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class VRAMCalculator:
    """
    Mathematical engine for calculating VRAM requirements
    
    Components:
    1. Model Weights (based on precision/quantization)
    2. KV Cache (MHA or GQA)
    3. Framework Overhead (10-50%)
    """
    
    # Bytes per parameter for different quantization types
    PRECISION_BYTES = {
        QuantizationType.FP32: 4.0,
        QuantizationType.BF16: 2.0,
        QuantizationType.FP16: 2.0,
        QuantizationType.INT8: 1.0,
        QuantizationType.INT4: 0.5,
        QuantizationType.Q4_K_M: 0.5,  # ~4-bit mixed precision
        QuantizationType.Q5_K_M: 0.625,  # ~5-bit mixed precision
        QuantizationType.Q8_0: 1.0,  # 8-bit
    }
    
    # Framework overhead factors
    FRAMEWORK_OVERHEAD = {
        FrameworkType.VLLM: 0.15,  # vLLM is efficient
        FrameworkType.LLAMA_CPP: 0.10,  # llama.cpp is lightweight
        FrameworkType.TRANSFORMERS: 0.25,  # Transformers has higher overhead
        FrameworkType.MLC_LLM: 0.12,  # MLC-LLM optimized
        FrameworkType.EXECUTORCH: 0.10,  # ExecuTorch for mobile
        FrameworkType.TENSORRT_LLM: 0.18,  # TensorRT-LLM
    }
    
    def __init__(self):
        pass
    
    def calculate_vram(
        self,
        metadata: ModelMetadata,
        quantization: QuantizationType,
        context_length: int,
        batch_size: int,
        framework: FrameworkType,
        is_production: bool = False
    ) -> Dict[str, float]:
        """
        Calculate total VRAM requirement
        
        Returns dict with breakdown:
        - weights_gb: Memory for model weights
        - kv_cache_gb: Memory for KV cache
        - overhead_gb: Framework overhead
        - total_gb: Total VRAM required
        """
        # 1. Calculate weights memory
        weights_gb = self._calculate_weights_memory(
            metadata.parameters_billions,
            metadata.total_parameters_billions,
            metadata.is_moe,
            quantization
        )
        
        # 2. Calculate KV cache memory
        kv_cache_gb = self._calculate_kv_cache(
            metadata,
            context_length,
            batch_size,
            quantization
        )
        
        # 3. Calculate activation memory (intermediate tensors)
        activation_gb = self._calculate_activation_memory(
            metadata,
            batch_size,
            context_length,
            quantization
        )
        
        # 4. Calculate overhead
        base_overhead_factor = self.FRAMEWORK_OVERHEAD.get(framework, 0.20)
        if is_production:
            # High-load production: 30-50% overhead
            overhead_factor = max(base_overhead_factor + 0.20, 0.35)
        else:
            # Development/inference: 10-30% overhead
            overhead_factor = base_overhead_factor
        
        compute_memory = weights_gb + kv_cache_gb + activation_gb
        overhead_gb = compute_memory * overhead_factor
        
        total_gb = compute_memory + overhead_gb
        
        return {
            'weights_gb': round(weights_gb, 2),
            'kv_cache_gb': round(kv_cache_gb, 2),
            'activation_gb': round(activation_gb, 2),
            'overhead_gb': round(overhead_gb, 2),
            'total_gb': round(total_gb, 2),
            'overhead_factor': overhead_factor
        }
    
    def _calculate_weights_memory(
        self,
        params_billions: float,
        total_params_billions: Optional[float],
        is_moe: bool,
        quantization: QuantizationType
    ) -> float:
        """
        Calculate memory for model weights
        
        For MoE models: use total_parameters, not active_parameters
        """
        bytes_per_param = self.PRECISION_BYTES.get(quantization, 2.0)
        
        # For MoE, always use total parameters for weight memory
        if is_moe and total_params_billions:
            effective_params = total_params_billions
        else:
            effective_params = params_billions
        
        # Convert to GB: params * bytes / 1024^3
        weights_gb = (effective_params * 1e9 * bytes_per_param) / (1024 ** 3)
        
        return weights_gb
    
    def _calculate_kv_cache(
        self,
        metadata: ModelMetadata,
        context_length: int,
        batch_size: int,
        quantization: QuantizationType
    ) -> float:
        """
        Calculate KV cache memory
        
        Supports both MHA (Multi-Head Attention) and GQA (Grouped-Query Attention)
        
        Formula:
        - MHA: 2 * num_layers * num_heads * head_dim * seq_len * batch_size * bytes_per_param
        - GQA: 2 * num_layers * num_kv_heads * head_dim * seq_len * batch_size * bytes_per_param
        
        The factor of 2 is for K and V caches
        """
        if not all([
            metadata.num_hidden_layers,
            metadata.hidden_size,
            metadata.num_attention_heads
        ]):
            # Fallback estimation: ~1GB per 1B params per 1K context
            return (metadata.parameters_billions * context_length * batch_size) / 1024
        
        num_layers = metadata.num_hidden_layers
        hidden_size = metadata.hidden_size
        num_attn_heads = metadata.num_attention_heads
        num_kv_heads = metadata.num_key_value_heads or num_attn_heads  # GQA detection
        
        # Calculate head dimension
        head_dim = hidden_size // num_attn_heads
        
        # Determine effective number of KV heads (GQA optimization)
        # If num_kv_heads < num_attn_heads, it's GQA
        effective_kv_heads = num_kv_heads
        
        # Bytes per parameter for KV cache (typically FP16 even with quantized weights)
        kv_bytes_per_param = 2.0  # KV cache usually in FP16
        
        # Calculate KV cache size in bytes
        # 2 for K and V
        kv_cache_bytes = (
            2 *  # K and V
            num_layers *
            effective_kv_heads *
            head_dim *
            context_length *
            batch_size *
            kv_bytes_per_param
        )
        
        # Convert to GB
        kv_cache_gb = kv_cache_bytes / (1024 ** 3)
        
        return kv_cache_gb
    
    def _calculate_activation_memory(
        self,
        metadata: ModelMetadata,
        batch_size: int,
        context_length: int,
        quantization: QuantizationType
    ) -> float:
        """
        Calculate activation memory for intermediate tensors
        
        This includes:
        - Attention scores and probabilities
        - Feed-forward network intermediate activations
        - Layer normalization buffers
        """
        if not metadata.hidden_size or not metadata.num_hidden_layers:
            # Rough estimate: 10-20% of weights
            return self._calculate_weights_memory(
                metadata.parameters_billions,
                None,
                metadata.is_moe,
                quantization
            ) * 0.15
        
        hidden_size = metadata.hidden_size
        num_layers = metadata.num_hidden_layers
        
        # Estimate intermediate size (typically 4x hidden for FFN)
        intermediate_size = hidden_size * 4
        
        # Activation memory per layer per token
        bytes_per_activation = 4.0  # FP32 for activations during compute
        
        # Total activation memory
        activation_bytes = (
            num_layers *
            batch_size *
            context_length *
            (hidden_size + intermediate_size) *  # Hidden + FFN intermediate
            bytes_per_activation
        )
        
        activation_gb = activation_bytes / (1024 ** 3)
        
        return activation_gb
    
    def get_quantization_description(self, quantization: QuantizationType) -> str:
        """Get human-readable description of quantization type"""
        descriptions = {
            QuantizationType.FP32: "Full precision (32-bit float)",
            QuantizationType.FP16: "Half precision (16-bit float)",
            QuantizationType.BF16: "Brain float (16-bit)",
            QuantizationType.INT8: "8-bit integer quantization",
            QuantizationType.INT4: "4-bit integer quantization",
            QuantizationType.Q4_K_M: "GGUF Q4_K_M (mixed 4-bit)",
            QuantizationType.Q5_K_M: "GGUF Q5_K_M (mixed 5-bit)",
            QuantizationType.Q8_0: "GGUF Q8_0 (8-bit)",
        }
        return descriptions.get(quantization, "Unknown quantization")
