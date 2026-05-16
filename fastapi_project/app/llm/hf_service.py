# Hugging Face Service for model metadata extraction

import re
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from huggingface_hub import HfApi, AsyncHfApi, model_info
from huggingface_hub.hf_api import ModelInfo
import logging

from app.schemas import ModelMetadata

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """Service for extracting model metadata from Hugging Face Hub"""
    
    # Regex pattern to extract parameters from model name/id
    PARAMS_PATTERN = re.compile(r'(\d+(?:\.\d+)?)[BbMm]')
    
    # Common file extensions for model weights
    WEIGHT_FILE_EXTENSIONS = ['.safetensors', '.bin', '.gguf', '.pth', '.pt']
    
    def __init__(self, hf_token: Optional[str] = None):
        self.api = HfApi(token=hf_token)
        self.async_api = AsyncHfApi(token=hf_token)
        self.hf_token = hf_token
    
    async def get_model_metadata(self, model_id: str) -> ModelMetadata:
        """
        Fetch and parse model metadata from Hugging Face
        
        Args:
            model_id: Hugging Face model ID (e.g., 'meta-llama/Llama-2-7b-hf')
        
        Returns:
            ModelMetadata object with parsed information
        """
        try:
            # Get model info from HF Hub
            info = await asyncio.to_thread(
                self.api.model_info, 
                model_id, 
                files_metadata=True
            )
            
            # Parse parameters from model name
            params_billions = self._parse_parameters_from_name(model_id, info)
            
            # Try to get config.json for architecture details
            config = await self._fetch_config_json(model_id)
            
            # Get file sizes for weight files
            file_size_bytes = await self._get_total_weights_size(model_id, info)
            
            # Check if MoE model
            is_moe = self._detect_moe_architecture(config, model_id)
            
            # Extract architecture details
            architecture = config.get('architectures', [None])[0] if config else None
            
            return ModelMetadata(
                model_id=model_id,
                parameters_billions=params_billions,
                total_parameters_billions=params_billions if not is_moe else None,
                active_parameters_billions=params_billions if is_moe else None,
                architecture=architecture,
                num_attention_heads=config.get('num_attention_heads') if config else None,
                num_key_value_heads=config.get('num_key_value_heads') if config else None,
                hidden_size=config.get('hidden_size') if config else None,
                num_hidden_layers=config.get('num_hidden_layers') if config else None,
                vocab_size=config.get('vocab_size') if config else None,
                file_size_bytes=file_size_bytes,
                is_moe=is_moe
            )
            
        except Exception as e:
            logger.error(f"Error fetching metadata for {model_id}: {str(e)}")
            # Return minimal metadata from name parsing
            params_billions = self._parse_parameters_from_name(model_id, None)
            return ModelMetadata(
                model_id=model_id,
                parameters_billions=params_billions,
                is_moe=self._detect_moe_architecture(None, model_id)
            )
    
    def _parse_parameters_from_name(self, model_id: str, info: Optional[ModelInfo]) -> float:
        """Extract parameter count from model name or tags"""
        # Try model name first
        matches = self.PARAMS_PATTERN.findall(model_id)
        if matches:
            value = float(matches[0])
            # Check if it's in millions or billions
            if 'M' in model_id or 'm' in model_id.split('/')[-1]:
                return value / 1000  # Convert to billions
            return value
        
        # Try tags if available
        if info and info.tags:
            for tag in info.tags:
                matches = self.PARAMS_PATTERN.findall(tag)
                if matches:
                    return float(matches[0])
        
        # Default fallback
        logger.warning(f"Could not parse parameters from model name: {model_id}")
        return 7.0  # Default to 7B as fallback
    
    async def _fetch_config_json(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Fetch config.json from model repository"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://huggingface.co/{model_id}/resolve/main/config.json"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.debug(f"Could not fetch config.json for {model_id}: {e}")
        return None
    
    async def _get_total_weights_size(self, model_id: str, info: ModelInfo) -> Optional[int]:
        """
        Get total size of weight files using HEAD requests
        
        Uses HTTP Range requests for GGUF files to read quantization keys
        """
        if not info or not info.siblings:
            return None
        
        total_size = 0
        weight_files = []
        
        # Find weight files
        for file_info in info.siblings:
            if any(file_info.rfilename.endswith(ext) for ext in self.WEIGHT_FILE_EXTENSIONS):
                weight_files.append(file_info)
        
        if not weight_files:
            return None
        
        # Get file sizes
        async with aiohttp.ClientSession() as session:
            tasks = []
            for file_info in weight_files:
                task = self._get_file_size(session, model_id, file_info.rfilename)
                tasks.append(task)
            
            sizes = await asyncio.gather(*tasks, return_exceptions=True)
            
            for size in sizes:
                if isinstance(size, int) and size > 0:
                    total_size += size
        
        return total_size if total_size > 0 else None
    
    async def _get_file_size(self, session: aiohttp.ClientSession, model_id: str, filename: str) -> int:
        """Get file size using HEAD request, with Range support for GGUF"""
        try:
            url = f"https://huggingface.co/{model_id}/resolve/main/{filename}"
            
            # For GGUF files, use Range request to read header
            if filename.endswith('.gguf'):
                headers = {'Range': 'bytes=0-65536'}  # Read first 64KB for header
                async with session.head(url, headers=headers, timeout=10) as response:
                    if response.status in [200, 206]:
                        # Try to get Content-Length from full file
                        content_range = response.headers.get('Content-Range', '')
                        if content_range and '/' in content_range:
                            return int(content_range.split('/')[-1])
                        return int(response.headers.get('Content-Length', 0))
            else:
                # Standard HEAD request for other formats
                async with session.head(url, timeout=10) as response:
                    if response.status == 200:
                        return int(response.headers.get('Content-Length', 0))
        except Exception as e:
            logger.debug(f"Error getting size for {filename}: {e}")
        return 0
    
    def _detect_moe_architecture(self, config: Optional[Dict], model_id: str) -> bool:
        """Detect if model uses Mixture of Experts architecture"""
        moe_indicators = [
            'mixtral', 'moa', 'qwen-moe', 'gemma-2', 'olmoe',
            'switch', 'sparse', 'expert'
        ]
        
        # Check model name
        model_lower = model_id.lower()
        if any(indicator in model_lower for indicator in moe_indicators):
            return True
        
        # Check config for MoE-specific fields
        if config:
            moe_fields = [
                'num_experts', 'num_experts_per_tok', 'expert_intermediate_size',
                'router_aux_loss_coef', 'shared_expert_intermediate_size'
            ]
            if any(field in config for field in moe_fields):
                return True
        
        return False
    
    async def search_models(self, query: str, limit: int = 20) -> List[str]:
        """Search for models matching query"""
        try:
            models = await asyncio.to_thread(
                self.api.list_models,
                search=query,
                limit=limit,
                sort='downloads',
                direction=-1
            )
            return [model.id for model in models]
        except Exception as e:
            logger.error(f"Error searching models: {e}")
            return []
