// API Service

import axios from 'axios';
import type { 
  CalculateRequest, 
  CalculationResult,
  HardwareDevice 
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
});

export const calculateService = {
  /**
   * Calculate VRAM requirements and find matching hardware
   */
  async calculate(request: CalculateRequest): Promise<CalculationResult> {
    const response = await api.post<CalculationResult>('/calculate/', request);
    return response.data;
  },

  /**
   * Get VRAM breakdown without hardware matching
   */
  async getBreakdown(
    modelId: string,
    quantization: string = 'FP16',
    contextLength: number = 2048,
    batchSize: number = 1
  ): Promise<any> {
    const response = await api.get(`/calculate/breakdown/${encodeURIComponent(modelId)}`, {
      params: { quantization, context_length: contextLength, batch_size: batchSize }
    });
    return response.data;
  }
};

export const hfService = {
  /**
   * Search Hugging Face models (for debounced autocomplete)
   */
  async searchModels(query: string, limit: number = 20): Promise<string[]> {
    const response = await api.get<string[]>('/hf/search', {
      params: { q: query, limit }
    });
    return response.data;
  },

  /**
   * Get model information
   */
  async getModelInfo(modelId: string): Promise<any> {
    const response = await api.get(`/hf/model/${encodeURIComponent(modelId)}`);
    return response.data;
  }
};

export const hardwareService = {
  /**
   * List all hardware devices with optional filters
   */
  async listDevices(options?: {
    vendor?: string;
    min_memory?: number;
    mobile_only?: boolean;
  }): Promise<HardwareDevice[]> {
    const response = await api.get<HardwareDevice[]>('/hardware/devices', {
      params: options
    });
    return response.data;
  },

  /**
   * Search hardware devices
   */
  async searchDevices(query: string): Promise<HardwareDevice[]> {
    const response = await api.get<HardwareDevice[]>('/hardware/devices/search', {
      params: { q: query }
    });
    return response.data;
  },

  /**
   * Get a specific device by ID
   */
  async getDevice(deviceId: number): Promise<HardwareDevice> {
    const response = await api.get<HardwareDevice>(`/hardware/devices/${deviceId}`);
    return response.data;
  }
};
