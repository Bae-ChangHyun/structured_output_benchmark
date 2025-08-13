from fastapi import APIRouter
from typing import Dict, List, Any
import os

from structured_output_benchmark.extraction_module.utils import get_compatible_frameworks

router = APIRouter()

@router.get("/hosts", summary="사용 가능한 호스트 목록", response_description="호스트 문자열 배열 반환")
async def get_hosts() -> Dict[str, Any]:
    """
    사용 가능한 호스트 목록을 반환합니다.
    """
    hosts = ["openai", "anthropic", "vllm", "ollama", "google"]
    
    return {
        "success": True,
        "data": hosts
    }

@router.get("/frameworks", summary="호스트별 프레임워크 목록", response_description="framework 문자열 배열과 host를 포함")
async def get_frameworks(host: str = "openai") -> Dict[str, Any]:
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

@router.get("/schemas", summary="사용 가능한 스키마 파일 목록", response_description="스키마 파일명 배열")
async def get_schemas() -> Dict[str, List[str]]:
    """사용 가능한 스키마 목록을 반환합니다."""
    # 스키마 디렉토리에서 스키마 파일들 스캔
    schema_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extraction_module", "schema")
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
