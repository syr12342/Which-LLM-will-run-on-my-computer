// API Types

export interface CalculateRequest {
  model_id: string;
  quantization: QuantizationType;
  context_length: number;
  batch_size: number;
  framework: FrameworkType;
  is_production: boolean;
}

export type QuantizationType = 
  | 'FP32' | 'FP16' | 'BF16' 
  | 'INT8' | 'INT4' 
  | 'Q4_K_M' | 'Q5_K_M' | 'Q8_0';

export type FrameworkType = 
  | 'vLLM' | 'llama.cpp' | 'transformers' 
  | 'MLC-LLM' | 'ExecuTorch' | 'TensorRT-LLM';

export interface ModelMetadata {
  model_id: string;
  parameters_billions: number;
  total_parameters_billions?: number;
  active_parameters_billions?: number;
  architecture?: string;
  num_attention_heads?: number;
  num_key_value_heads?: number;
  hidden_size?: number;
  num_hidden_layers?: number;
  vocab_size?: number;
  file_size_bytes?: number;
  is_moe: boolean;
}

export interface HardwareDevice {
  id: number;
  name: string;
  vendor: string;
  device_type: string;
  architecture: string;
  memory_size_gb: number;
  memory_bandwidth_gbps: number;
  tensor_cores: boolean;
  fp16_tflops: number;
  fp8_tflops?: number;
  is_mobile: boolean;
  os_support?: string;
  supports_offloading: boolean;
  npu_tops?: number;
}

export interface MatchingResult {
  device: HardwareDevice;
  fits: boolean;
  available_memory_gb: number;
  required_memory_gb: number;
  memory_utilization_percent: number;
  offloading_required: boolean;
  offloaded_layers: number;
  estimated_speed_tokens_per_sec: number;
  warnings: string[];
  recommendations: string[];
}

export interface CalculationResult {
  model_metadata: ModelMetadata;
  vram_breakdown: VRAMBreakdown;
  total_vram_gb: number;
  kv_cache_gb: number;
  weights_gb: number;
  overhead_gb: number;
  matching_devices: MatchingResult[];
  best_match?: MatchingResult;
}

export interface VRAMBreakdown {
  weights_gb: number;
  kv_cache_gb: number;
  activation_gb: number;
  overhead_gb: number;
  total_gb: number;
  overhead_factor: number;
}
