"""
Local LLM inference using llama.cpp
Offline Gemma model (4-bit GGUF)
"""

import logging
from typing import Optional

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not available - LLM simulation mode")

from config import (
    LLM_MODEL_PATH, LLM_N_CTX, LLM_N_GPU_LAYERS,
    LLM_N_THREADS, LLM_TEMPERATURE, LLM_TOP_P,
    LLM_MAX_TOKENS, LLM_VERBOSE, LLM_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

# =============================================
# LOCAL LLM
# =============================================
class LocalLLM:
    """Runs Gemma LLM locally using llama.cpp"""
    
    def __init__(self):
        """Initialize LLM"""
        self.model: Optional[object] = None
        self._loaded = False
        
        if LLAMA_CPP_AVAILABLE:
            self._load_model()
        else:
            logger.warning("llama-cpp-python not available - LLM will not work")
    
    def _load_model(self) -> None:
        """Load Gemma model from disk"""
        try:
            logger.info(f"Loading LLM: {LLM_MODEL_PATH}")
            
            if not os.path.exists(LLM_MODEL_PATH):
                logger.error(f"Model file not found: {LLM_MODEL_PATH}")
                logger.info("Download Gemma 4-bit GGUF model:")
                logger.info("  wget https://huggingface.co/TheBloke/Gemma-2B-it-GGUF/resolve/main/gemma-2b-it-q4_k_m.gguf")
                return
            
            self.model = Llama(
                model_path=LLM_MODEL_PATH,
                n_ctx=LLM_N_CTX,
                n_threads=LLM_N_THREADS,
                n_gpu_layers=LLM_N_GPU_LAYERS,
                verbose=LLM_VERBOSE,
                use_mlock=True  # Lock model in RAM
            )
            
            self._loaded = True
            logger.info(f"✓ LLM loaded: {LLM_MODEL_PATH}")
            logger.info(f"  Context: {LLM_N_CTX}, Threads: {LLM_N_THREADS}, GPU layers: {LLM_N_GPU_LAYERS}")
            
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._loaded
    
    def generate(self, prompt: str, context: Optional[str] = None, max_tokens: int = LLM_MAX_TOKENS) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User question/prompt
            context: Optional RAG context to inject
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        try:
            if not self._loaded or not self.model:
                logger.error("Model not loaded")
                return "Sorry, I'm not ready yet. Please try again."
            
            # Build full prompt with system prompt and context
            full_prompt = LLM_SYSTEM_PROMPT + "\n\n"
            
            if context:
                full_prompt += f"Memory/Context:\n{context}\n\n"
            
            full_prompt += f"User: {prompt}\nAssistant:"
            
            logger.info(f"Generating response (max_tokens={max_tokens})...")
            
            # Generate
            response = self.model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=LLM_TEMPERATURE,
                top_p=LLM_TOP_P,
                stop=["User:", "\n\n"],  # Stop sequences
                echo=False
            )
            
            # Extract text
            text = response["choices"][0]["text"].strip()
            logger.info(f"Generation complete: {len(text)} chars")
            
            return text if text else "I'm not sure how to respond to that."
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return f"Error generating response: {str(e)}"
    
    def explain_detections(self, detections: list) -> str:
        """
        Generate natural language explanation of detected objects
        
        Args:
            detections: List of detection dicts from YOLO
            
        Returns:
            Natural language explanation
        """
        if not detections:
            return "No objects detected in the scene."
        
        # Format detections for LLM
        detection_str = "Detected objects:\n"
        for det in detections:
            name = det.get('name', 'Unknown')
            conf = det.get('confidence', 0)
            detection_str += f"- {name} (confidence: {conf:.2%})\n"
        
        prompt = f"""Based on these object detections, provide a brief, natural explanation of what you see:

{detection_str}

Keep the explanation to 1-2 sentences."""
        
        return self.generate(prompt, max_tokens=150)
    
    def cleanup(self) -> None:
        """Cleanup model"""
        if self.model:
            try:
                # llama_cpp doesn't have explicit cleanup, but we can clear
                self.model = None
                self._loaded = False
                logger.info("✓ LLM model unloaded")
            except Exception as e:
                logger.error(f"LLM cleanup failed: {e}")


# Import os for file checking
import os
