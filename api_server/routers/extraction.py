from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import asyncio
import uuid
from datetime import datetime

from api_server.models.extraction import (
    ExtractionRequest, ExtractionFileRequest, ExtractionResponse
)
from api_server.models.common import TaskStatus, TaskResponse
from api_server.services.extraction_service import ExtractionService
from api_server.services.file_service import FileService

router = APIRouter()
extraction_service = ExtractionService()
file_service = FileService()

# 진행 중인 작업들을 저장할 딕셔너리 (실제 프로덕션에서는 Redis나 DB 사용)
running_tasks = {}

@router.post("/run", response_model=ExtractionResponse)
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
            schema_name=request.schema,
            temperature=request.temperature,
            timeout=request.timeout,
            host_choice=request.host_choice,
            framework_choice=request.framework_choice
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

@router.post("/run-async", response_model=TaskResponse)
async def run_extraction_async(
    background_tasks: BackgroundTasks,
    request: ExtractionRequest
):
    """비동기로 텍스트 추출을 실행합니다."""
    if not request.input_text:
        raise HTTPException(status_code=400, detail="input_text가 필요합니다.")
    
    task_id = str(uuid.uuid4())
    
    # 작업 정보 저장
    running_tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "message": "작업이 시작되었습니다."
    }
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        run_extraction_background, 
        task_id, 
        request
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="작업이 시작되었습니다.",
        created_at=running_tasks[task_id]["created_at"]
    )

async def run_extraction_background(task_id: str, request: ExtractionRequest):
    """백그라운드에서 실행되는 추출 작업"""
    try:
        running_tasks[task_id]["status"] = TaskStatus.RUNNING
        running_tasks[task_id]["message"] = "추출 작업 실행 중..."
        
        result = await extraction_service.run_extraction(
            input_text=request.input_text,
            retries=request.retries,
            schema_name=request.schema,
            temperature=request.temperature,
            timeout=request.timeout,
            host_choice=request.host_choice,
            framework_choice=request.framework_choice
        )
        
        running_tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "message": "추출이 성공적으로 완료되었습니다.",
            "completed_at": datetime.now().isoformat(),
            "result": {
                "result": result.result,
                "success_rate": result.success_rate,
                "latency": result.latency,
                "log_dir": result.log_dir,
                "result_path": result.result_json_path,
                "langfuse_url": result.langfuse_url
            }
        })
        
    except Exception as e:
        running_tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "message": f"추출 실행 중 오류: {str(e)}",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })

@router.post("/upload", response_model=ExtractionResponse)
async def run_extraction_with_file(
    file: UploadFile = File(..., description="텍스트 파일 (.txt, .md, .json 등)"),
    retries: int = Form(1, description="재시도 횟수 (1-10)"),
    schema: str = Form("schema_han", description="스키마 이름"),
    temperature: float = Form(0.1, description="프롬프트 온도 (0.0-2.0)"),
    timeout: int = Form(900, description="타임아웃 시간(초)"),
    host_choice: Optional[int] = Form(None, description="호스트 선택: 1=OpenAI, 2=Anthropic, 3=vLLM, 4=Ollama, 5=Google"),
    framework_choice: Optional[int] = Form(None, description="프레임워크 선택 (호스트별로 다름)")
):
    """
    파일 업로드를 통한 텍스트 추출을 실행합니다.
    
    **지원 파일 형식:** .txt, .json, .pdf, .docx, .md
    
    **Parameters:**
    - **file**: 추출할 텍스트가 포함된 파일
    - **host_choice**: 호스트 선택 (1-5, 미지정시 OpenAI)
    - **framework_choice**: 프레임워크 선택 (호스트별로 다름)
    
    **Host Options:**
    - 1: OpenAI (GPT 모델)
    - 2: Anthropic (Claude 모델)  
    - 3: vLLM (로컬 서버)
    - 4: Ollama (로컬 서버)
    - 5: Google (Gemini 모델)
    
    호스트별 프레임워크 목록은 `/api/v1/utils/frameworks?host=<host_name>` 에서 확인 가능
    """
    
    file_info = None
    try:
        # 파일 저장
        file_info = await file_service.save_upload_file(file)
        
        # 파일 내용 읽기
        input_text = file_service.read_text_file(file_info.upload_path)
        
        # 추출 실행
        result = await extraction_service.run_extraction(
            input_text=input_text,
            retries=retries,
            schema_name=schema,
            temperature=temperature,
            timeout=timeout,
            host_choice=host_choice,
            framework_choice=framework_choice
        )
        
        return ExtractionResponse(
            success=True,
            message="파일 업로드를 통한 추출이 성공적으로 완료되었습니다.",
            data={
                "result": result.result,
                "success_rate": result.success_rate,
                "latency": result.latency,
                "log_dir": result.log_dir,
                "result_path": result.result_json_path,
                "langfuse_url": result.langfuse_url,
                "uploaded_file": file_info.filename
            },
            result_path=result.result_json_path,
            log_path=result.log_dir,
            langfuse_url=result.langfuse_url,
            success_rate=result.success_rate,
            latency=result.latency
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 추출 실행 중 오류: {str(e)}")
    
    finally:
        # 임시 파일 정리
        if file_info:
            file_service.delete_file(file_info.upload_path)

@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """작업 상태를 확인합니다."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    task_info = running_tasks[task_id]
    
    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
        created_at=task_info["created_at"],
        completed_at=task_info.get("completed_at"),
        result=task_info.get("result"),
        error=task_info.get("error")
    )
