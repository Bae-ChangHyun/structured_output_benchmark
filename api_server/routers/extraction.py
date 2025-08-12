from fastapi import APIRouter, HTTPException
from api_server.models.extraction import ExtractionRequest, ExtractionResponse
from api_server.services.extraction_service import ExtractionService

router = APIRouter()
extraction_service = ExtractionService()

@router.post("", response_model=ExtractionResponse)
async def run_extraction(request: ExtractionRequest):
    """
    텍스트 추출을 실행합니다.
    
    **Parameters:**
    - **host_choice**: 호스트 선택
        - 1: OpenAI (gpt-4o-mini 등)
        - 2: Anthropic (claude-3-sonnet 등)  
        - 3: vLLM (로컬 서버)
        - 4: Ollama (로컬 서버)
        - 5: Google (gemini-1.5-flash 등)
        - 미지정시: OpenAI 기본값
    
    - **framework_choice**: 프레임워크 선택 (호스트별로 다름)
        - 미지정시: 호스트에 호환되는 첫번째 프레임워크 사용
        - 호스트별 호환 프레임워크 목록: `/api/v1/utils/frameworks?host=<host_name>` 참조
    
    **Example:**
    ```json
    {
        "input_text": "안녕하세요. 제 이름은 김철수입니다.",
        "host_choice": 1,
        "framework_choice": 1,
        "schema": "schema_han"
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
            host_info=request.host_info
        )
        
        return ExtractionResponse(
            success=True,
            message="추출이 성공적으로 완료되었습니다.",
            data={
                "result": result.result,
                "success_rate": result.success_rate,
                "latency": result.latency,
                "log_dir": result.log_dir,
                "result_path": result.result_json_path,
                "langfuse_url": result.langfuse_url
            },
            result_path=result.result_json_path,
            log_path=result.log_dir,
            langfuse_url=result.langfuse_url,
            success_rate=result.success_rate,
            latency=result.latency
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추출 실행 중 오류: {str(e)}")