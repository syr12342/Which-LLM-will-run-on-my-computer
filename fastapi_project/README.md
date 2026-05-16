# LLM Router & Matching Platform

Production-ready system for routing Large Language Models to compatible hardware.

## Features

- **Hugging Face Integration**: Parse model metadata directly from HF Hub
- **VRAM Calculation**: Accurate memory estimation including:
  - Model weights (FP16, INT8, INT4, GGUF quantizations)
  - KV Cache (MHA and GQA support)
  - Framework overhead (vLLM, llama.cpp, Transformers)
- **Hardware Matching**: Find compatible GPUs, SoCs, and mobile devices
- **Mobile Optimization**: Apple Silicon and Android NPU support

## Architecture

```
/fastapi_project
├── /app
│   ├── /api/v1/endpoints/    # API controllers
│   ├── /core/                # Configuration & database
│   ├── /llm/                 # Domain logic (HF parsing, VRAM calc, matching)
│   ├── /schemas/             # Pydantic models
│   ├── /models/              # SQLAlchemy ORM models
│   └── /repositories/        # Data access layer
└── requirements.txt
```

## Quick Start

### Backend

```bash
cd fastapi_project
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:5173

## API Endpoints

- `POST /api/v1/calculate/` - Calculate VRAM and find matching hardware
- `GET /api/v1/hf/search?q={query}` - Search Hugging Face models
- `GET /api/v1/hardware/devices` - List hardware devices

## Mathematical Formulas

### Weights Memory
```
weights_gb = (parameters_billions × 1e9 × bytes_per_param) / 1024³
```

### KV Cache (GQA-aware)
```
kv_cache_gb = (2 × num_layers × num_kv_heads × head_dim × context_length × batch_size × 2) / 1024³
```

### Mobile Memory (Apple Silicon)
```
available_memory = total_ram × 0.75  # Metal wired memory limit
```

## Supported Quantization Types

| Type | Bytes/Param | Description |
|------|-------------|-------------|
| FP16 | 2.0 | Half precision |
| BF16 | 2.0 | Brain float |
| INT8 | 1.0 | 8-bit integer |
| Q8_0 | 1.0 | GGUF 8-bit |
| Q5_K_M | 0.625 | GGUF mixed 5-bit |
| Q4_K_M | 0.5 | GGUF mixed 4-bit |
| INT4 | 0.5 | 4-bit integer |

## Hardware Database

Pre-seeded with 20+ devices including:
- NVIDIA RTX 30/40 series
- AMD RX 7000 series
- Apple M3/M3 Pro/M3 Max
- iPhone 16/17 series
- Snapdragon 8 Gen 2/3/Elite
- Datacenter GPUs (A100, H100, L40S)
