from fastapi import APIRouter, HTTPException
from structured_output_benchmark.core.types import ExtractionRequest, ExtractionResponse
from structured_output_benchmark.api_server.services.extraction_service import ExtractionService

router = APIRouter()
extraction_service = ExtractionService()

@router.post("", response_model=ExtractionResponse)
async def run_extraction(request: ExtractionRequest):
    """
    텍스트 추출을 실행합니다.
    
    **Parameters:**
    - **host**: 호스트 선택
        - 1: openai (gpt-4o-mini 등)
        - 2: anthropic (claude-3-sonnet 등)
        - 3: vllm (로컬 서버)
        - 4: ollama (로컬 서버)
        - 5: google (gemini-1.5-flash 등)
        - 미지정시: openai 기본값
        
    **Example:**
    ```json
    {
        "input_text": "안녕하세요. 제 이름은 김철수입니다.",

        # 공통 실행 설정
        "retries": 1,
        "schema_name": "schema_han",
        "temperature": 0.1,
        "timeout": 900,
        "langfuse_trace_id": None,
        "output_dir": None,
        
        "framework": "OpenAIFramework",

        # 필수 호스트 정보
        "host_info": {
            "host": "vllm",
            "base_url": "http://localhost:8000"
        }
    }
    ```
    """
    if not request.input_text:
        raise HTTPException(status_code=400, detail="input_text가 필요합니다.")
    
    try:
        result = await extraction_service.run_extraction(
            input_text=request.input_text,
            retries=request.retries,
            schema_name=request.schema_name,
            temperature=request.temperature,
            timeout=request.timeout,
            framework=request.framework,
            host_info=request.host_info,
            langfuse_trace_id=request.langfuse_trace_id,
            output_dir=request.output_dir
        )
        
        return ExtractionResponse(
            success=True,
            message="추출이 성공적으로 완료되었습니다.",
            data={
                "result": result.result,
                "success_rate": result.success_rate,
                "latency": result.latency,
                "output_dir": result.output_dir,
                "result_path": result.result_json_path,
                "langfuse_url": result.langfuse_url
            },
            result_path=result.result_json_path,
            output_dir=result.output_dir,
            langfuse_url=result.langfuse_url,
            success_rate=result.success_rate,
            latency=result.latency
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추출 실행 중 오류: {str(e)}")