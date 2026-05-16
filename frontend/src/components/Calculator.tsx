// Multi-step Calculator Component

import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import debounce from 'lodash.debounce';
import { hfService, calculateService } from '../services/api';
import { useDebounce } from '../hooks';
import type { 
  CalculateRequest, 
  QuantizationType, 
  FrameworkType,
  CalculationResult 
} from '../types';
import './Calculator.css';

const QUANTIZATION_OPTIONS: { value: QuantizationType; label: string; bytes: number }[] = [
  { value: 'FP16', label: 'FP16 (Half Precision)', bytes: 2 },
  { value: 'BF16', label: 'BF16 (Brain Float)', bytes: 2 },
  { value: 'INT8', label: 'INT8 (8-bit)', bytes: 1 },
  { value: 'Q8_0', label: 'GGUF Q8_0', bytes: 1 },
  { value: 'Q5_K_M', label: 'GGUF Q5_K_M', bytes: 0.625 },
  { value: 'Q4_K_M', label: 'GGUF Q4_K_M', bytes: 0.5 },
  { value: 'INT4', label: 'INT4 (4-bit)', bytes: 0.5 },
];

const FRAMEWORK_OPTIONS: { value: FrameworkType; label: string }[] = [
  { value: 'vLLM', label: 'vLLM (High Performance)' },
  { value: 'llama.cpp', label: 'llama.cpp (CPU/GPU Hybrid)' },
  { value: 'MLC-LLM', label: 'MLC-LLM (Mobile Optimized)' },
  { value: 'ExecuTorch', label: 'ExecuTorch (Apple/Android)' },
  { value: 'TensorRT-LLM', label: 'TensorRT-LLM (NVIDIA)' },
  { value: 'transformers', label: 'HuggingFace Transformers' },
];

export default function Calculator() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  
  // Step 1: Model Selection
  const [modelId, setModelId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  
  // Step 2: Parameters
  const [quantization, setQuantization] = useState<QuantizationType>('FP16');
  const [contextLength, setContextLength] = useState(4096);
  const [batchSize, setBatchSize] = useState(1);
  const [framework, setFramework] = useState<FrameworkType>('vLLM');
  const [isProduction, setIsProduction] = useState(false);
  
  // Results
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search models with debounce
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['hf-search', debouncedSearchQuery],
    queryFn: () => hfService.searchModels(debouncedSearchQuery, 10),
    enabled: debouncedSearchQuery.length >= 2,
    staleTime: 5 * 60 * 1000,
  });

  // Handle model selection
  const handleSelectModel = (selectedModel: string) => {
    setModelId(selectedModel);
    setSearchQuery('');
    setStep(2);
  };

  // Debounced search handler
  const handleSearchChange = useCallback(
    debounce((value: string) => {
      setSearchQuery(value);
    }, 300),
    []
  );

  // Calculate VRAM and match hardware
  const handleCalculate = async () => {
    if (!modelId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const request: CalculateRequest = {
        model_id: modelId,
        quantization,
        context_length: contextLength,
        batch_size: batchSize,
        framework,
        is_production: isProduction,
      };
      
      const calculationResult = await calculateService.calculate(request);
      setResult(calculationResult);
      setStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to calculate VRAM');
    } finally {
      setIsLoading(false);
    }
  };

  // Reset calculator
  const handleReset = () => {
    setStep(1);
    setModelId('');
    setSearchQuery('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="calculator">
      {/* Progress Indicator */}
      <div className="progress-bar">
        <div className={`step ${step >= 1 ? 'active' : ''}`}>
          <span className="step-number">1</span>
          <span className="step-label">Select Model</span>
        </div>
        <div className={`step ${step >= 2 ? 'active' : ''}`}>
          <span className="step-number">2</span>
          <span className="step-label">Configure</span>
        </div>
        <div className={`step ${step >= 3 ? 'active' : ''}`}>
          <span className="step-number">3</span>
          <span className="step-label">Results</span>
        </div>
      </div>

      {/* Step 1: Model Search */}
      {step === 1 && (
        <div className="step-content">
          <h2>Select a Model</h2>
          <p className="step-description">
            Search for a model on Hugging Face. Type at least 2 characters to search.
          </p>
          
          <div className="search-container">
            <input
              type="text"
              className="search-input"
              placeholder="e.g., Llama-2-7b, mistralai/Mixtral-8x7B..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => searchQuery && setSearchQuery(searchQuery)}
            />
            
            {isSearching && <div className="loading-spinner">Searching...</div>}
            
            {searchResults && searchResults.length > 0 && (
              <ul className="search-results">
                {searchResults.map((model) => (
                  <li
                    key={model}
                    className="search-result-item"
                    onClick={() => handleSelectModel(model)}
                  >
                    {model}
                  </li>
                ))}
              </ul>
            )}
          </div>
          
          {modelId && (
            <div className="selected-model">
              <strong>Selected:</strong> {modelId}
              <button className="btn-change" onClick={() => setModelId('')}>
                Change
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Configuration */}
      {step === 2 && (
        <div className="step-content">
          <h2>Configure Parameters</h2>
          
          <div className="form-group">
            <label>Quantization Format</label>
            <select
              value={quantization}
              onChange={(e) => setQuantization(e.target.value as QuantizationType)}
              className="form-select"
            >
              {QUANTIZATION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} ({opt.bytes} bytes/param)
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Context Length</label>
              <input
                type="number"
                value={contextLength}
                onChange={(e) => setContextLength(Number(e.target.value))}
                className="form-input"
                min={128}
                max={131072}
                step={128}
              />
              <small>tokens (128 - 131,072)</small>
            </div>
            
            <div className="form-group">
              <label>Batch Size</label>
              <input
                type="number"
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="form-input"
                min={1}
                max={1024}
              />
              <small>concurrent sequences</small>
            </div>
          </div>
          
          <div className="form-group">
            <label>Inference Framework</label>
            <select
              value={framework}
              onChange={(e) => setFramework(e.target.value as FrameworkType)}
              className="form-select"
            >
              {FRAMEWORK_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isProduction}
                onChange={(e) => setIsProduction(e.target.checked)}
              />
              <span>Production Mode (higher overhead for stability)</span>
            </label>
          </div>
          
          <div className="selected-model-summary">
            <strong>Model:</strong> {modelId}
          </div>
          
          <div className="button-row">
            <button className="btn-secondary" onClick={() => setStep(1)}>
              Back
            </button>
            <button 
              className="btn-primary" 
              onClick={handleCalculate}
              disabled={isLoading}
            >
              {isLoading ? 'Calculating...' : 'Calculate VRAM'}
            </button>
          </div>
          
          {error && <div className="error-message">{error}</div>}
        </div>
      )}

      {/* Step 3: Results */}
      {step === 3 && result && (
        <div className="step-content results-content">
          <h2>VRAM Calculation Results</h2>
          
          <div className="model-info-card">
            <h3>{result.model_metadata.model_id}</h3>
            <div className="model-stats">
              <span className="stat">
                <strong>{result.model_metadata.parameters_billions}B</strong> Parameters
              </span>
              {result.model_metadata.is_moe && (
                <span className="stat moe-badge">MoE Architecture</span>
              )}
            </div>
          </div>
          
          {/* VRAM Breakdown */}
          <div className="vram-breakdown">
            <h3>Memory Breakdown</h3>
            <div className="breakdown-grid">
              <div className="breakdown-item">
                <span className="label">Weights</span>
                <span className="value">{result.vram_breakdown.weights_gb} GB</span>
              </div>
              <div className="breakdown-item">
                <span className="label">KV Cache</span>
                <span className="value">{result.vram_breakdown.kv_cache_gb} GB</span>
              </div>
              <div className="breakdown-item">
                <span className="label">Activations</span>
                <span className="value">{result.vram_breakdown.activation_gb} GB</span>
              </div>
              <div className="breakdown-item">
                <span className="label">Overhead</span>
                <span className="value">{result.vram_breakdown.overhead_gb} GB</span>
              </div>
              <div className="breakdown-item total">
                <span className="label">Total Required</span>
                <span className="value">{result.total_vram_gb} GB</span>
              </div>
            </div>
          </div>
          
          {/* Compatible Hardware */}
          <div className="hardware-results">
            <h3>Compatible Hardware ({result.matching_devices.length})</h3>
            
            {result.matching_devices.length === 0 ? (
              <div className="no-results">
                <p>No compatible devices found.</p>
                <p>Try using a lower precision quantization (INT4/Q4_K_M) or reduce context length.</p>
              </div>
            ) : (
              <div className="hardware-grid">
                {result.matching_devices.slice(0, 12).map((match, idx) => (
                  <div 
                    key={match.device.id} 
                    className={`hardware-card ${match.device.is_mobile ? 'mobile' : ''}`}
                  >
                    <div className="card-header">
                      <h4>{match.device.name}</h4>
                      <span className={`badge ${match.device.device_type.toLowerCase()}`}>
                        {match.device.device_type}
                      </span>
                    </div>
                    
                    <div className="card-specs">
                      <div className="spec">
                        <span className="spec-label">Memory:</span>
                        <span className="spec-value">{match.device.memory_size_gb} GB</span>
                      </div>
                      <div className="spec">
                        <span className="spec-label">Bandwidth:</span>
                        <span className="spec-value">{match.device.memory_bandwidth_gbps} GB/s</span>
                      </div>
                      {match.device.tensor_cores && (
                        <div className="spec">
                          <span className="spec-label">Tensor Cores:</span>
                          <span className="spec-value">✓</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="memory-bar">
                      <div 
                        className={`memory-fill ${match.memory_utilization_percent > 90 ? 'critical' : match.memory_utilization_percent > 70 ? 'warning' : 'good'}`}
                        style={{ width: `${Math.min(match.memory_utilization_percent, 100)}%` }}
                      />
                      <span className="memory-percent">{match.memory_utilization_percent}%</span>
                    </div>
                    
                    {match.warnings.length > 0 && (
                      <div className="warnings">
                        {match.warnings.map((warning, i) => (
                          <div key={i} className="warning">⚠️ {warning}</div>
                        ))}
                      </div>
                    )}
                    
                    {match.offloading_required && (
                      <div className="offload-notice">
                        Offloading {match.offloaded_layers} layers to RAM
                      </div>
                    )}
                    
                    <div className="performance-estimate">
                      ~{match.estimated_speed_tokens_per_sec} tokens/sec
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="button-row">
            <button className="btn-secondary" onClick={() => setStep(2)}>
              Adjust Parameters
            </button>
            <button className="btn-primary" onClick={handleReset}>
              New Calculation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
