from fastapi import APIRouter, HTTPException
from structured_output_kit.utils.types import ExtractionRequest, ExtractionResponse
from structured_output_kit.server.services.extraction_service import ExtractionService

router = APIRouter()
extraction_service = ExtractionService()

@router.post(
    "",
    response_model=ExtractionResponse,
    summary="LLM 구조화 추출 실행",
    response_description="추출 결과와 로그/성공률/지연시간 등을 포함한 응답"
)
async def run_extraction(request: ExtractionRequest):
    """
    텍스트에서 이력서 스키마에 맞는 구조화된 정보를 추출합니다.

    [Request]
    - prompt: 프롬프트 
    - input_text: 추출할 텍스트(또는 텍스트 파일 경로)
    - schema_name: extraction/schema 폴더의 스키마 이름(또는 스키마 파일 경로)
    - framework: 사용 프레임워크 이름(예: OpenAIFramework)
    - host_info: { provider, base_url, model } 필수
    - retries: Optional = 실패 시 재시도 횟수(기본 0)
    - extra_kwargs: Optional = 프레임워크/LLM 세부 파라미터 딕셔너리 (예: { "temperature": 0.1, "timeout": 900 })
    - langfuse_trace_id: Optional = langfuse의 추적 ID
    - output_dir: Optional = 결과 파일 저장 디렉토리
    - save: Optional = 결과 파일 저장 여부(default=False)

    응답 본문
    - data.result: 추출된 JSON
    - data.success_rate: 프레임워크 내부 성공률(단일 실행 시 1)
    - latency: 첫 성공 응답 지연 시간(초)
    - result_path: 추출된 json 파일 경로
    - data.langfuse_url: Langfuse Trace URL(설정 시)

    상태코드
    - 200: 성공
    - 400: 입력 오류(input_text 누락 등)
    - 500: 내부 오류
    """
    if not request.input_text:
        raise HTTPException(status_code=400, detail="input_text가 필요합니다.")
    
    try:
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