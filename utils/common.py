from json import load
import os
from typing import Any
from pydantic import BaseModel
from dotenv import load_dotenv
from scipy.constants import h

load_dotenv()

def check_host_info(host_info: Any) -> dict:
    """Ensure minimal host_info values for supported providers.

    Accepts a dict, a Pydantic BaseModel, or a simple object with attributes.
    Converts non-dict inputs to a dict and returns the dict with defaults set.
    """
    # If passed a Pydantic model, convert to dict first (pydantic v2 -> model_dump)
    if isinstance(host_info, BaseModel):
        host_info = host_info.model_dump(exclude_none=False)

    # If object-like (has attributes but no .get), convert selective attrs to dict
    if not isinstance(host_info, dict):
        # try to pick common attributes
        host_info = {
            k: getattr(host_info, k, None)
            for k in ("provider", "base_url", "model", "api_key")
        }

    provider = (host_info.get("provider") or "").lower()
    if not provider:
        raise ValueError("host_info['provider']가 필요합니다.")

    if provider == 'openai':
        host_info.setdefault("base_url", "https://api.openai.com/v1")
        host_info.setdefault("api_key", os.getenv("OPENAI_API_KEY"))
        if not host_info.get("model"):
            raise ValueError("OpenAI 모델이름을 입력하세요. https://platform.openai.com/docs/pricing")
    elif provider == 'anthropic':
        host_info.setdefault("base_url", "https://api.anthropic.com/v1")
        host_info.setdefault("api_key", os.getenv("ANTHROPIC_API_KEY"))
        if not host_info.get("model"):
            raise ValueError("Anthropic 모델이름을 입력하세요. https://www.anthropic.com/products/claude")
    elif provider == 'google':
        host_info.setdefault("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")
        host_info.setdefault("api_key", os.getenv("GOOGLE_API_KEY"))
        if not host_info.get("model"):
            raise ValueError("Google 모델이름을 입력하세요. https://ai.google.dev/gemini-api/docs/models?hl=ko")
    elif provider == "ollama":
        host_info.setdefault("base_url", os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1")
        host_info.setdefault("api_key", os.getenv("OLLAMA_API_KEY"))
        if not host_info.get("model"):
            raise ValueError("Ollama 모델이름을 입력하세요.")
    elif provider == "openai_compatible":
        host_info.setdefault("base_url", os.getenv("OPENAI_COMPATIBLE_BASE_URL") or "http://localhost:8000/v1")
        host_info.setdefault("api_key", os.getenv("OPENAI_COMPATIBLE_API_KEY"))
        if not host_info.get("model"):
            raise ValueError("OpenAI 호환 모델이름을 입력하세요.")
    return host_info