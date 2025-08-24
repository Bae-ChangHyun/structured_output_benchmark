"""
파싱 API 라우터
"""

import enum
import os
import json
import requests
import urllib.parse
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger
import tempfile

from structured_output_kit.utils.types import ParsingRequest, ParsingResponse, HostInfo
from structured_output_kit.parsing.core import run_parsing_core
from structured_output_kit.parsing.factory import get_available_frameworks, get_framework_info
from structured_output_kit.extraction.utils import check_host_info

router = APIRouter()


class ParsingFramework(str, enum.Enum):
    """파싱 프레임워크 열거형"""
    DOCLING = "docling"
    PYPDF = "pypdf"
    FITZ = "fitz"
    PDFPLUMBER = "pdfplumber"
    MARKITDOWN = "markitdown"
    VLM = "vlm"


def get_framework_extra_kwargs(framework: ParsingFramework) -> Dict[str, Any]:
    """프레임워크별 사용 가능한 extra_kwargs 반환"""
    
    framework_configs = {
        ParsingFramework.DOCLING: {
            "description": "Docling 프레임워크 - IBM의 고급 문서 파싱 도구",
            "supported_extensions": [".pdf", ".docx", ".pptx", ".html", ".md", ".txt", ".png", ".jpg", ".jpeg"],
            "extra_kwargs": {
                "pipeline_class": {
                    "type": "str",
                    "description": "파이프라인 클래스 선택",
                    "allowed_values": ["default", "vlm"],
                    "default": "default"
                },
                "backend": {
                    "type": "str", 
                    "description": "백엔드 선택",
                    "allowed_values": ["Docling", "PyPdfium"],
                    "default": "Docling"
                },
                "use_gpu": {
                    "type": "bool",
                    "description": "GPU 사용 여부",
                    "default": False
                },
                "image_extract": {
                    "type": "bool",
                    "description": "이미지 추출 여부",
                    "default": False
                },
                "ocr_engine": {
                    "type": "str",
                    "description": "OCR 엔진 선택",
                    "allowed_values": ["tesseract", "tesseract_cli", "easyocr", "rapidocr"],
                    "default": "tesseract"
                }
            }
        },
        
        ParsingFramework.PYPDF: {
            "description": "PyPDF 프레임워크 - 순수 Python PDF 처리 라이브러리",
            "supported_extensions": [".pdf"],
            "extra_kwargs": {
                "extraction_mode": {
                    "type": "str",
                    "description": "텍스트 추출 모드",
                    "allowed_values": ["layout", "plain"],
                    "default": "layout"
                }
            }
        },
        
        ParsingFramework.FITZ: {
            "description": "PyMuPDF(Fitz) 프레임워크 - 빠른 PDF 처리 라이브러리",
            "supported_extensions": [".pdf"],
            "extra_kwargs": {
                "flags": {
                    "type": "int",
                    "description": "텍스트 추출 플래그 (비트마스크)",
                    "default": 0
                },
                "get_text_dict": {
                    "type": "bool",
                    "description": "딕셔너리 형태로 상세 정보와 함께 추출",
                    "default": False
                }
            }
        },
        
        ParsingFramework.PDFPLUMBER: {
            "description": "PDFPlumber 프레임워크 - 테이블과 레이아웃을 잘 처리하는 PDF 라이브러리",
            "supported_extensions": [".pdf"],
            "extra_kwargs": {
                "layout": {
                    "type": "bool",
                    "description": "레이아웃 모드 사용 여부",
                    "default": True
                },
                "x_tolerance": {
                    "type": "float",
                    "description": "X축 허용 오차",
                    "default": 3.0
                },
                "y_tolerance": {
                    "type": "float", 
                    "description": "Y축 허용 오차",
                    "default": 3.0
                },
                "extract_tables": {
                    "type": "bool",
                    "description": "테이블 추출 여부",
                    "default": False
                }
            }
        },
        
        ParsingFramework.MARKITDOWN: {
            "description": "MarkItDown 프레임워크 - Microsoft의 다양한 형식 지원 변환 도구",
            "supported_extensions": [".pdf", ".docx", ".pptx", ".xlsx", ".html", ".txt", ".md", ".png", ".jpg", ".jpeg"],
            "extra_kwargs": {
                "llm_client": {
                    "type": "object",
                    "description": "LLM 클라이언트 객체",
                    "default": None
                },
                "llm_model": {
                    "type": "str",
                    "description": "LLM 모델명",
                    "default": None
                }
            }
        },
        
        ParsingFramework.VLM: {
            "description": "VLM(Vision Language Model) 프레임워크 - 이미지와 PDF를 AI로 분석",
            "supported_extensions": [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"],
            "extra_kwargs": {
                "temperature": {
                    "type": "float",
                    "description": "응답 생성의 무작위성 조절 (0.0-2.0)",
                    "default": 0.0
                },
                "max_tokens": {
                    "type": "int",
                    "description": "최대 토큰 수",
                    "default": 4096
                },
                "top_p": {
                    "type": "float",
                    "description": "핵심 확률 누적 (0.0-1.0)",
                    "default": 1.0
                },
                "stream": {
                    "type": "bool",
                    "description": "스트리밍 모드 (Ollama만 지원)",
                    "default": False
                },
                "num_ctx": {
                    "type": "int",
                    "description": "컨텍스트 윈도우 크기 (Ollama만 지원)",
                    "default": 2048
                }
            },
            "required_params": ["provider", "model"],
            "optional_params": ["base_url", "api_key", "prompt"]
        }
    }
    
    return framework_configs.get(framework, {})


@router.get("/frameworks")
async def list_frameworks():
    """사용 가능한 파싱 프레임워크 목록 조회"""
    try:
        frameworks = get_available_frameworks()
        framework_info = {}
        
        for framework in frameworks:
            try:
                info = get_framework_info(framework)
                framework_info[framework] = info
            except Exception as e:
                logger.warning(f"프레임워크 {framework} 정보 조회 실패: {str(e)}")
                framework_info[framework] = {
                    "name": framework,
                    "supported_extensions": [],
                    "error": str(e)
                }
        
        return {
            "success": True,
            "message": "프레임워크 목록 조회 성공",
            "data": {
                "frameworks": frameworks,
                "framework_info": framework_info
            }
        }
    except Exception as e:
        logger.error(f"프레임워크 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frameworks/{framework}/extra-kwargs")
async def get_framework_extra_kwargs_endpoint(framework: ParsingFramework):
    """특정 프레임워크의 사용 가능한 extra_kwargs 조회"""
    try:
        config = get_framework_extra_kwargs(framework)
        
        if not config:
            raise HTTPException(
                status_code=404, 
                detail=f"프레임워크 '{framework}'에 대한 설정을 찾을 수 없습니다"
            )
        
        return {
            "success": True,
            "message": f"프레임워크 '{framework}' extra_kwargs 조회 성공",
            "data": {
                "framework": framework,
                "description": config.get("description", ""),
                "supported_extensions": config.get("supported_extensions", []),
                "extra_kwargs": config.get("extra_kwargs", {}),
                "required_params": config.get("required_params", []),
                "optional_params": config.get("optional_params", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프레임워크 extra_kwargs 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frameworks/extra-kwargs")
async def get_all_frameworks_extra_kwargs():
    """모든 프레임워크의 사용 가능한 extra_kwargs 조회"""
    try:
        all_configs = {}
        
        for framework in ParsingFramework:
            config = get_framework_extra_kwargs(framework)
            if config:
                all_configs[framework.value] = {
                    "description": config.get("description", ""),
                    "supported_extensions": config.get("supported_extensions", []),
                    "extra_kwargs": config.get("extra_kwargs", {}),
                    "required_params": config.get("required_params", []),
                    "optional_params": config.get("optional_params", [])
                }
        
        return {
            "success": True,
            "message": "모든 프레임워크 extra_kwargs 조회 성공",
            "data": {
                "frameworks": all_configs,
                "available_frameworks": [f.value for f in ParsingFramework]
            }
        }
    except Exception as e:
        logger.error(f"전체 프레임워크 extra_kwargs 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    framework: ParsingFramework = Form(ParsingFramework.DOCLING, description="사용할 파싱 프레임워크"),
    extra_kwargs: str = Form("{}"),
    provider: Optional[str] = Form(None, description="vlm 사용시 LLM provider", enum=["openai", "anthropic", "google", "ollama" ,"openai_compatible"]),
    base_url: Optional[str] = Form(None, description="vlm 사용시 API 기본 URL"),
    model: Optional[str] = Form(None, description="vlm 사용시 모델명"),
    api_key: Optional[str] = Form(None, description="vlm 사용시 API 키"),
    prompt: Optional[str] = Form(None, description="vlm 사용시 프롬프트"),
    save: bool = Form(False)
) -> ParsingResponse:
    """파일 업로드 및 파싱"""
    
    try:
        # 업로드된 파일을 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            # extra_kwargs 파싱
            extra_kwargs_dict = json.loads(extra_kwargs) if extra_kwargs else {}
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"extra_kwargs JSON 파싱 실패: {str(e)}")
        
        # 호스트 정보 설정 (VLM 사용시)
        host_info = None
        if framework == ParsingFramework.VLM or provider:
            if not all([provider, model]):
                raise HTTPException(
                    status_code=400, 
                    detail="VLM 사용시 provider와 model이 필요합니다"
                )
                
            host_info_dict = check_host_info({
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "api_key": api_key
            })
            
            host_info = HostInfo(
                provider=host_info_dict['provider'],
                base_url=host_info_dict['base_url'],
                model=host_info_dict['model'],
                api_key=host_info_dict['api_key']
            )

        # 파싱 요청 생성
        req = ParsingRequest(
            file_path=temp_path,
            framework=framework.value,  
            extra_kwargs=extra_kwargs_dict,
            host_info=host_info,
            prompt=prompt,
            save=save
        )
        
        # 파싱 실행
        result = run_parsing_core(req)
        
        # 임시 파일 정리
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        
        if result.success:
            return ParsingResponse(
                success=True,
                message="파싱 성공",
                data={
                    "content": result.content,
                    "framework": result.framework,
                    "file_name": file.filename,
                    "content_length": len(result.content)
                },
                result_path=result.result_txt_path,
                output_dir=result.output_dir,
                framework=result.framework
            )
        else:
            return ParsingResponse(
                success=False,
                message=f"파싱 실패: {result.content}",
                framework=result.framework
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파싱 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-url")
async def parse_from_url(
    file_url: str,
    framework: str = "docling",
    extra_kwargs: Dict[str, Any] = {},
    host_info: Optional[HostInfo] = None,
    prompt: Optional[str] = None,
    save: bool = False
) -> ParsingResponse:
    """URL에서 파일을 다운로드하여 파싱"""
    
    try:
        # URL에서 파일 다운로드
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        
        # 임시 파일로 저장
        parsed_url = urllib.parse.urlparse(file_url)
        filename = os.path.basename(parsed_url.path) or "downloaded_file"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        # 파싱 요청 생성
        req = ParsingRequest(
            file_path=temp_path,
            framework=framework,
            extra_kwargs=extra_kwargs,
            host_info=host_info,
            prompt=prompt,
            save=save
        )
        
        # 파싱 실행
        result = run_parsing_core(req)
        
        # 임시 파일 정리
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        
        if result.success:
            return ParsingResponse(
                success=True,
                message="파싱 성공",
                data={
                    "content": result.content,
                    "framework": result.framework,
                    "file_url": file_url,
                    "content_length": len(result.content)
                },
                result_path=result.result_txt_path,
                output_dir=result.output_dir,
                framework=result.framework
            )
        else:
            return ParsingResponse(
                success=False,
                message=f"파싱 실패: {result.content}",
                framework=result.framework
            )
            
    except Exception as e:
        logger.error(f"URL 파싱 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
