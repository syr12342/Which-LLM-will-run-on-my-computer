# Hardware Matching Service with mobile device support

from typing import List, Dict, Any, Optional
import logging

from app.schemas import (
    ModelMetadata, 
    FrameworkType, 
    HardwareDevice, 
    MatchingResult,
    QuantizationType
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class HardwareMatcher:
    """
    Service for matching models to compatible hardware
    
    Features:
    - Memory-based filtering
    - Framework-specific rules (vLLM vs llama.cpp offloading)
    - Mobile device constraints (Apple Silicon, Android NPU)
    - Performance estimation
    """
    
    # Mobile memory availability ratios
    MOBILE_MEMORY_RATIOS = {
        'iOS': 0.75,  # Apple Metal wired memory limit
        'Android': 0.80,  # Android typically has more available
        'macOS': 0.70,  # macOS system memory pressure
    }
    
    # Speed estimation constants
    MEMORY_BANDWIDTH_TO_SPEED = 0.015  # tokens/sec per GB/s bandwidth
    
    def __init__(self):
        pass
    
    def match_hardware(
        self,
        metadata: ModelMetadata,
        required_vram_gb: float,
        devices: List[HardwareDevice],
        framework: FrameworkType,
        quantization: QuantizationType,
        context_length: int,
        batch_size: int
    ) -> List[MatchingResult]:
        """
        Match model requirements to available hardware
        
        Returns list of MatchingResult sorted by fitness
        """
        results = []
        
        for device in devices:
            result = self._evaluate_device(
                device=device,
                metadata=metadata,
                required_vram_gb=required_vram_gb,
                framework=framework,
                quantization=quantization,
                context_length=context_length,
                batch_size=batch_size
            )
            results.append(result)
        
        # Sort by fitness: fits first, then by available memory margin
        results.sort(key=lambda r: (
            not r.fits,  # False (fits) comes before True (doesn't fit)
            -r.available_memory_gb  # More available memory is better
        ))
        
        return results
    
    def _evaluate_device(
        self,
        device: HardwareDevice,
        metadata: ModelMetadata,
        required_vram_gb: float,
        framework: FrameworkType,
        quantization: QuantizationType,
        context_length: int,
        batch_size: int
    ) -> MatchingResult:
        """Evaluate a single device for compatibility"""
        
        warnings = []
        recommendations = []
        
        # Calculate available memory based on device type
        if device.is_mobile:
            available_memory = self._calculate_mobile_available_memory(device)
        else:
            available_memory = device.memory_size_gb
        
        # Check if model fits
        fits = available_memory >= required_vram_gb
        
        # Handle offloading for llama.cpp
        offloading_required = False
        offloaded_layers = 0
        
        if framework == FrameworkType.LLAMA_CPP and not fits:
            if device.supports_offloading or device.is_mobile:
                # Calculate how many layers can fit
                offloading_required = True
                offloaded_layers = self._calculate_offloaded_layers(
                    metadata,
                    available_memory,
                    required_vram_gb,
                    quantization
                )
                if offloaded_layers > 0:
                    warnings.append(
                        f"Offloading {offloaded_layers} layers to RAM - expect slower generation"
                    )
                    fits = True  # Can still run with offloading
                else:
                    warnings.append("Model too large even with offloading")
        
        # Framework-specific validation
        if framework == FrameworkType.VLLM and not fits:
            # vLLM requires full model in VRAM
            fits = False
            warnings.append("vLLM requires full model in VRAM - no offloading support")
        
        # Mobile-specific checks
        if device.is_mobile:
            self._add_mobile_warnings(
                device, 
                required_vram_gb, 
                available_memory,
                framework,
                warnings,
                recommendations
            )
        
        # Performance estimation
        estimated_speed = self._estimate_generation_speed(
            device,
            required_vram_gb,
            offloading_required,
            framework
        )
        
        # Add recommendations
        if not fits and not offloading_required:
            recommendations.append(
                f"Consider quantization (INT4/Q4_K_M) to reduce VRAM by ~50%"
            )
            recommendations.append(
                "Reduce context length or batch size"
            )
        
        if device.tensor_cores and quantization in [QuantizationType.FP16, QuantizationType.BF16]:
            recommendations.append(
                "Tensor Cores enabled for accelerated FP16 inference"
            )
        
        if device.fp8_tflops and quantization in [QuantizationType.INT8, QuantizationType.INT4]:
            recommendations.append(
                "FP8/INT8 acceleration available on this GPU"
            )
        
        return MatchingResult(
            device=device,
            fits=fits,
            available_memory_gb=round(available_memory, 2),
            required_memory_gb=round(required_vram_gb, 2),
            memory_utilization_percent=round(
                (required_vram_gb / available_memory * 100) if available_memory > 0 else 0, 1
            ),
            offloading_required=offloading_required,
            offloaded_layers=offloaded_layers,
            estimated_speed_tokens_per_sec=round(estimated_speed, 2),
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _calculate_mobile_available_memory(self, device: HardwareDevice) -> float:
        """
        Calculate available memory for mobile devices
        
        Apple Silicon: ~70-75% of total RAM (Metal wired memory limit)
        Android: ~80% typically available
        """
        os_type = device.os_support or 'Linux'
        
        # Get memory ratio for OS
        memory_ratio = self.MOBILE_MEMORY_RATIOS.get(os_type, 0.75)
        
        # For iOS devices, apply strict limits
        if 'iOS' in os_type:
            # iPhone 17 Pro Max example: 12GB -> 8-9GB available
            memory_ratio = 0.70 if device.memory_size_gb <= 8 else 0.75
        
        available = device.memory_size_gb * memory_ratio
        
        logger.debug(
            f"Mobile device {device.name}: {device.memory_size_gb}GB -> "
            f"{available:.2f}GB available ({memory_ratio*100:.0f}%)"
        )
        
        return available
    
    def _calculate_offloaded_layers(
        self,
        metadata: ModelMetadata,
        available_memory_gb: float,
        required_vram_gb: float,
        quantization: QuantizationType
    ) -> int:
        """
        Calculate how many layers need to be offloaded to RAM
        
        Returns number of offloaded layers (0 if all fit)
        """
        if not metadata.num_hidden_layers:
            return 0
        
        total_layers = metadata.num_hidden_layers
        
        # Estimate memory per layer
        memory_per_layer = required_vram_gb / total_layers
        
        # How many layers can fit in available memory?
        layers_that_fit = int(available_memory_gb / memory_per_layer)
        
        # Layers to offload
        offloaded = max(0, total_layers - layers_that_fit)
        
        return min(offloaded, total_layers)
    
    def _estimate_generation_speed(
        self,
        device: HardwareDevice,
        required_vram_gb: float,
        offloading_required: bool,
        framework: FrameworkType
    ) -> float:
        """
        Estimate token generation speed (tokens/sec)
        
        Based on memory bandwidth and compute capabilities
        """
        base_speed = device.memory_bandwidth_gbps * self.MEMORY_BANDWIDTH_TO_SPEED
        
        # Adjust for offloading penalty
        if offloading_required:
            # Offloading to RAM significantly reduces speed
            # System RAM bandwidth is typically 50-100 GB/s vs GPU's 500+ GB/s
            ram_bandwidth = 50.0  # Conservative estimate for DDR5
            offload_penalty = ram_bandwidth / device.memory_bandwidth_gbps
            base_speed *= offload_penalty
        
        # Framework optimizations
        if framework == FrameworkType.VLLM:
            # vLLM's PagedAttention improves throughput
            base_speed *= 1.3
        elif framework == FrameworkType.TENSORRT_LLM:
            # TensorRT-LLM highly optimized
            base_speed *= 1.5
        elif framework == FrameworkType.MLC_LLM:
            # MLC-LLM optimized for mobile
            if device.is_mobile:
                base_speed *= 1.2
        
        # Tensor core boost for NVIDIA
        if device.tensor_cores and device.vendor == 'NVIDIA':
            base_speed *= 1.2
        
        return base_speed
    
    def _add_mobile_warnings(
        self,
        device: HardwareDevice,
        required_vram_gb: float,
        available_memory_gb: float,
        framework: FrameworkType,
        warnings: List[str],
        recommendations: List[str]
    ):
        """Add mobile-specific warnings and recommendations"""
        
        os_type = device.os_support or ''
        
        # Apple Silicon specific
        if 'iOS' in os_type or 'macOS' in os_type:
            if required_vram_gb > available_memory_gb * 0.9:
                warnings.append(
                    "High memory pressure on Apple Silicon - may cause thermal throttling"
                )
            
            if framework == FrameworkType.EXECUTORCH:
                recommendations.append(
                    "ExecuTorch optimized for Apple Neural Engine"
                )
            
            # MLC-LLM recommendation
            if framework == FrameworkType.MLC_LLM:
                recommendations.append(
                    "MLC-LLM provides best performance on Apple Silicon"
                )
        
        # Android specific
        if 'Android' in os_type:
            if device.npu_tops and device.supports disaggregated_inference:
                recommendations.append(
                    f"NPU available ({device.npu_tops} TOPS) - consider hybrid NPU+GPU inference"
                )
            
            if 'Snapdragon 8 Elite' in device.architecture or '8 Gen' in device.architecture:
                recommendations.append(
                    "Snapdragon 8 series supports AI Stack for efficient LLM inference"
                )
        
        # Battery warning for mobile
        if required_vram_gb > available_memory_gb * 0.5:
            warnings.append(
                "High power consumption expected - battery drain will be significant"
            )
    
    def get_best_match(
        self, 
        results: List[MatchingResult],
        prefer_mobile: bool = False
    ) -> Optional[MatchingResult]:
        """Get the best matching device from results"""
        
        # Filter to only fitting devices
        fitting = [r for r in results if r.fits]
        
        if not fitting:
            return None
        
        # Sort by efficiency (lower memory utilization is better for headroom)
        fitting.sort(key=lambda r: r.memory_utilization_percent)
        
        # If preferring mobile, prioritize mobile devices
        if prefer_mobile:
            mobile_fitting = [r for r in fitting if r.device.is_mobile]
            if mobile_fitting:
                return mobile_fitting[0]
        
        return fitting[0]
