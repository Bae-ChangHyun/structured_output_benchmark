from fastapi import APIRouter
from typing import Dict, List
import os

from extraction_module.utils import get_compatible_frameworks
from utils import get_available_hosts

router = APIRouter()

@router.get("/hosts")
async def get_hosts() -> Dict[str, List[Dict[str, str]]]:
    """
    사용 가능한 호스트 목록을 반환합니다.
    
    추출 API에서 host_choice 파라미터로 사용할 수 있는 값들을 제공합니다.
    
    **Response:**
    ```json
    {
        "success": true,
        "data": [
            {"id": 1, "name": "openai", "description": "OpenAI API"},
            {"id": 2, "name": "anthropic", "description": "Anthropic API"},
            ...
        ]
    }
    ```
    """
    hosts = [
        {"id": 1, "name": "openai", "description": "OpenAI API"},
        {"id": 2, "name": "anthropic", "description": "Anthropic API"},
        {"id": 3, "name": "vllm", "description": "vLLM 서버"},
        {"id": 4, "name": "ollama", "description": "Ollama 로컬 서버"},
        {"id": 5, "name": "google", "description": "Google Gemini API"}
    ]
    
    return {
        "success": True,
        "data": hosts
    }

@router.get("/frameworks")
async def get_frameworks(host: str = "openai") -> Dict[str, List[str]]:
    """
    특정 호스트에서 사용 가능한 프레임워크 목록을 반환합니다.
    
    추출 API에서 framework_choice 파라미터로 사용할 수 있는 값들을 제공합니다.
    framework_choice는 1부터 시작하는 인덱스 번호입니다.
    
    **Parameters:**
    - **host**: 호스트 이름 (openai, anthropic, google, vllm, ollama)
    
    **Example:**
    - `/api/v1/utils/frameworks?host=openai`
    - `/api/v1/utils/frameworks?host=anthropic`
    
    **Response:**
    ```json
    {
        "success": true,
        "host": "openai",
        "data": [
            "openai",           // framework_choice=1
            "instructor",       // framework_choice=2
            "langchain_tool",   // framework_choice=3
            ...
        ]
    }
    ```
    """
    try:
        frameworks = get_compatible_frameworks(host)
        return {
            "success": True,
            "host": host,
            "data": frameworks
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@router.get("/schemas")
async def get_schemas() -> Dict[str, List[str]]:
    """사용 가능한 스키마 목록을 반환합니다."""
    # 스키마 디렉토리에서 스키마 파일들 스캔
    schema_dir = "extraction_module/schema"
    schemas = []
    
    if os.path.exists(schema_dir):
        for file in os.listdir(schema_dir):
            if file.endswith(".py") and not file.startswith("__"):
                schema_name = file[:-3]  # .py 확장자 제거
                schemas.append(schema_name)
    
    return {
        "success": True,
        "data": schemas
    }

@router.get("/config")
async def get_config() -> Dict[str, dict]:
    """현재 환경 설정 정보를 반환합니다."""
    config = {
        "openai": {
            "available": bool(os.getenv("OPENAI_API_KEY")),
            "models": os.getenv("OPENAI_MODELS", "gpt-4o-mini")
        },
        "anthropic": {
            "available": bool(os.getenv("ANTHROPIC_API_KEY")),
            "models": os.getenv("ANTHROPIC_MODELS", "claude-3-sonnet-20240229")
        },
        "vllm": {
            "available": bool(os.getenv("VLLM_BASEURL")),
            "base_url": os.getenv("VLLM_BASEURL"),
            "models": os.getenv("VLLM_MODELS", "openai/gpt-oss-120b")
        },
        "ollama": {
            "available": True,  # Ollama는 로컬이므로 항상 available로 표시
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434/v1"),
            "models": os.getenv("OLLAMA_MODELS", "llama3.1:8b")
        },
        "google": {
            "available": bool(os.getenv("GOOGLE_API_KEY")),
            "models": os.getenv("GOOGLE_MODELS", "gemini-1.5-flash")
        }
    }
    
    return {
        "success": True,
        "data": config
    }
