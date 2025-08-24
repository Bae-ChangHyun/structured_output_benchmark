"""
파싱 프레임워크 팩토리
"""

from typing import Dict, Any, Optional
from loguru import logger

from .frameworks import (
    DoclingFramework,
    PyPDFFramework,
    FitzFramework,
    PDFPlumberFramework,
    MarkItDownFramework,
    VLMFramework
)

try:
    from utils.types import HostInfo
except ImportError:
    from structured_output_kit.utils.types import HostInfo


# 프레임워크 매핑
FRAMEWORK_MAPPING = {
    "docling": DoclingFramework,
    "pypdf": PyPDFFramework,
    "fitz": FitzFramework,
    "pdfplumber": PDFPlumberFramework,
    "markitdown": MarkItDownFramework,
    "vlm": VLMFramework
}


def factory(
    framework: str,
    file_path: str,
    extra_kwargs: Optional[Dict[str, Any]] = None,
    host_info: Optional[HostInfo] = None,
    prompt: Optional[str] = None,
    **kwargs
):
    """파싱 프레임워크 팩토리 함수"""
    
    if framework not in FRAMEWORK_MAPPING:
        available_frameworks = list(FRAMEWORK_MAPPING.keys())
        raise ValueError(f"지원하지 않는 프레임워크: {framework}. 사용 가능한 프레임워크: {available_frameworks}")
    
    framework_class = FRAMEWORK_MAPPING[framework]
    
    logger.debug(f"Creating {framework} framework instance")
    
    try:
        instance = framework_class(
            file_path=file_path,
            extra_kwargs=extra_kwargs,
            host_info=host_info,
            prompt=prompt,
            **kwargs
        )
        
        logger.debug(f"{framework} framework instance created successfully")
        return instance
        
    except Exception as e:
        logger.error(f"Failed to create {framework} framework instance: {str(e)}")
        raise


def get_available_frameworks() -> list[str]:
    """사용 가능한 파싱 프레임워크 목록 반환"""
    return list(FRAMEWORK_MAPPING.keys())


def get_framework_info(framework: str) -> Dict[str, Any]:
    """특정 프레임워크의 정보 반환"""
    if framework not in FRAMEWORK_MAPPING:
        raise ValueError(f"지원하지 않는 프레임워크: {framework}")
    
    framework_class = FRAMEWORK_MAPPING[framework]
    
    # 임시 인스턴스를 생성해서 정보 추출 (실제 파일 없이)
    try:
        # 가짜 파일 경로로 임시 인스턴스 생성
        temp_instance = framework_class.__new__(framework_class)
        temp_instance.file_path = ""
        temp_instance.extra_kwargs = {}
        temp_instance.host_info = None
        temp_instance.prompt = None
        
        return {
            "name": temp_instance.name,
            "supported_extensions": temp_instance.supported_extensions(),
            "class_name": framework_class.__name__
        }
    except Exception:
        return {
            "name": framework,
            "supported_extensions": [],
            "class_name": framework_class.__name__
        }
