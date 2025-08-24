from fastapi import APIRouter, HTTPException, Form
from typing import Dict, List, Any, Optional
import os
import json

from structured_output_kit.utils.types import ExtractionRequest, ExtractionResponse, HostInfo
from structured_output_kit.server.services.extraction_service import ExtractionService
from structured_output_kit.extraction.utils import get_compatible_frameworks
from structured_output_kit.utils.common import check_host_info

router = APIRouter()
extraction_service = ExtractionService()

@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="LLM 구조화 추출 실행",
    response_description="추출 결과와 로그/성공률/지연시간 등을 포함한 응답"
)
async def run_extraction(
    input_text: str = Form(..., description="추출할 텍스트 또는 텍스트 파일 경로"),
    provider: str = Form(..., description="호스트 제공자",enum=['openai', 'anthropic', 'google', 'ollama', 'openai_compatible']),
    model: str = Form(..., description="사용할 모델명"),
    framework: str = Form("OpenAIFramework", description="사용할 프레임워크 이름"),
    schema_name: str = Form("schema_han", description="스키마 이름"),
    prompt: Optional[str] = Form(None, description="사용할 프롬프트 (기본값: prompt.yaml에서 로드)"),
    base_url: Optional[str] = Form(None, description="API 기본 URL (ollama, openai_compatible용)"),
    api_key: Optional[str] = Form(None, description="API 키"),
    retries: int = Form(1, description="재시도 횟수"),
    extra_kwargs: str = Form("{}", description="추가 파라미터 JSON 문자열"),
    langfuse_trace_id: Optional[str] = Form(None, description="Langfuse trace ID"),
    output_dir: Optional[str] = Form(None, description="결과 출력 디렉토리"),
    save: bool = Form(False, description="결과 저장 여부")
) -> ExtractionResponse:
    """
    텍스트에서 구조화된 정보를 추출합니다.

    상태코드:
    - 200: 성공
    - 400: 입력 오류
    - 500: 내부 오류
    """
    if not input_text:
        raise HTTPException(status_code=400, detail="input_text가 필요합니다.")
    
    try:
        # extra_kwargs JSON 파싱
        try:
            extra_kwargs_dict = json.loads(extra_kwargs) if extra_kwargs else {}
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"extra_kwargs JSON 파싱 실패: {str(e)}")
        
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
        
        # 요청 객체 생성
        request = ExtractionRequest(
            prompt=prompt,
            input_text=input_text,
            retries=retries,
            schema_name=schema_name,
            extra_kwargs=extra_kwargs_dict,
            framework=framework,
            host_info=host_info,
            langfuse_trace_id=langfuse_trace_id,
            output_dir=output_dir,
            save=save
        )
        
        result = await extraction_service.run_extraction(
            prompt=request.prompt,
            input_text=request.input_text,
            retries=request.retries,
            schema_name=request.schema_name,
            extra_kwargs=request.extra_kwargs,
            framework=request.framework,
            host_info=request.host_info,
            langfuse_trace_id=request.langfuse_trace_id,
            output_dir=request.output_dir,
            save=request.save
        )
        
        return ExtractionResponse(
            success=True,
            message="추출에 성공하였습니다" if result.success else "추출에 실패하였습니다",
            data={
                "result": result.result,
                "success_rate": result.success_rate,
            },
            result_path=result.result_json_path,
            output_dir=result.output_dir,
            langfuse_url=result.langfuse_url,
            success_rate=result.success_rate,
            latency=result.latency
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추출 실행 중 오류: {str(e)}")


@router.get("/providers", summary="사용 가능한 호스트 목록", response_description="호스트 문자열 배열 반환")
async def get_providers() -> Dict[str, Any]:
    """
    사용 가능한 제공자 목록을 반환합니다.
    """
    providers = ["openai", "anthropic", "openai_compatible", "ollama", "google"]

    return {
        "success": True,
        "data": providers
    }


@router.get("/frameworks", summary="호스트별 프레임워크 목록", response_description="framework 문자열 배열과 provider을 포함")
async def get_frameworks(provider: str = "openai") -> Dict[str, Any]:
    """
    특정 제공자에서 사용 가능한 프레임워크 목록을 반환합니다.
    
    추출 API에서 framework_choice 파라미터로 사용할 수 있는 값들을 제공합니다.
    framework_choice는 1부터 시작하는 인덱스 번호입니다.
    
    **Parameters:**
    - **provider**: 호스트 이름 (openai, anthropic, google, openai_compatible, ollama)
    
    **Example:**
    - `/v1/extraction/frameworks?provider=openai`
    - `/v1/extraction/frameworks?provider=anthropic`
    
    **Response:**
    ```json
    {
        "success": true,
        "provider": "openai",
        "data": [
            "openai",          
            "instructor",      
            "langchain_tool",
            ...
        ]
    }
    ```
    """
    try:
        frameworks = get_compatible_frameworks(provider)
        return {
            "success": True,
            "provider": provider,
            "data": frameworks
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


@router.get("/schemas", summary="사용 가능한 스키마 파일 목록", response_description="스키마 파일명 배열")
async def get_schemas() -> Dict[str, Any]:
    """로컬(extraction/schema)에서 사용 가능한 스키마 목록을 반환합니다."""
    # 스키마 디렉토리에서 스키마 파일들 스캔
    schema_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extraction", "schema")
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