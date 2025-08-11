from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List
import uuid
from datetime import datetime

from api_server.models.evaluation import (
    EvaluationRequest, EvaluationFileRequest, EvaluationResponse
)
from api_server.models.common import TaskStatus, TaskResponse
from api_server.services.evaluation_service import EvaluationService
from api_server.services.file_service import FileService

router = APIRouter()
evaluation_service = EvaluationService()
file_service = FileService()

# 진행 중인 작업들을 저장할 딕셔너리
running_tasks = {}

@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(request: EvaluationRequest):
    """평가를 실행합니다."""
    if not request.pred_json_path or not request.gt_json_path:
        raise HTTPException(
            status_code=400, 
            detail="pred_json_path와 gt_json_path가 모두 필요합니다."
        )
    
    try:
        result = await evaluation_service.run_evaluation(
            pred_json_path=request.pred_json_path,
            gt_json_path=request.gt_json_path,
            schema_name=request.schema_name,
            criteria_path=request.criteria_path,
            embed_backend=request.embed_backend,
            model_name=request.model_name,
            api_base=request.api_base
        )
        
        return EvaluationResponse(
            success=True,
            message="평가가 성공적으로 완료되었습니다.",
            data={
                "overall_score": result.overall_score,
                "structure_score": result.structure_score,
                "content_score": result.content_score,
                "eval_result_path": result.eval_result_path,
                "log_dir": result.log_dir
            },
            eval_result_path=result.eval_result_path,
            overall_score=result.overall_score,
            structure_score=result.structure_score,
            content_score=result.content_score,
            log_path=result.log_dir
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 실행 중 오류: {str(e)}")

@router.post("/run-async", response_model=TaskResponse)
async def run_evaluation_async(
    background_tasks: BackgroundTasks,
    request: EvaluationRequest
):
    """비동기로 평가를 실행합니다."""
    if not request.pred_json_path or not request.gt_json_path:
        raise HTTPException(
            status_code=400, 
            detail="pred_json_path와 gt_json_path가 모두 필요합니다."
        )
    
    task_id = str(uuid.uuid4())
    
    # 작업 정보 저장
    running_tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "message": "평가 작업이 시작되었습니다."
    }
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        run_evaluation_background, 
        task_id, 
        request
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="평가 작업이 시작되었습니다.",
        created_at=running_tasks[task_id]["created_at"]
    )

async def run_evaluation_background(task_id: str, request: EvaluationRequest):
    """백그라운드에서 실행되는 평가 작업"""
    try:
        running_tasks[task_id]["status"] = TaskStatus.RUNNING
        running_tasks[task_id]["message"] = "평가 작업 실행 중..."
        
        result = await evaluation_service.run_evaluation(
            pred_json_path=request.pred_json_path,
            gt_json_path=request.gt_json_path,
            schema_name=request.schema_name,
            criteria_path=request.criteria_path,
            embed_backend=request.embed_backend,
            model_name=request.model_name,
            api_base=request.api_base
        )
        
        running_tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "message": "평가가 성공적으로 완료되었습니다.",
            "completed_at": datetime.now().isoformat(),
            "result": {
                "overall_score": result.overall_score,
                "structure_score": result.structure_score,
                "content_score": result.content_score,
                "eval_result_path": result.eval_result_path,
                "log_dir": result.log_dir
            }
        })
        
    except Exception as e:
        running_tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "message": f"평가 실행 중 오류: {str(e)}",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })

@router.post("/upload", response_model=EvaluationResponse)
async def run_evaluation_with_files(
    pred_file: UploadFile = File(..., description="예측 결과 JSON 파일"),
    gt_file: UploadFile = File(..., description="Ground truth JSON 파일"),
    schema_name: str = Form("schema_han"),
    criteria_path: Optional[str] = Form("evaluation_module/criteria/criteria.json"),
    embed_backend: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    api_base: Optional[str] = Form(None)
):
    """파일 업로드를 통한 평가를 실행합니다."""
    
    pred_file_info = None
    gt_file_info = None
    
    try:
        # 파일들 저장
        pred_file_info = await file_service.save_upload_file(pred_file)
        gt_file_info = await file_service.save_upload_file(gt_file)
        
        # 평가 실행
        result = await evaluation_service.run_evaluation(
            pred_json_path=pred_file_info.upload_path,
            gt_json_path=gt_file_info.upload_path,
            schema_name=schema_name,
            criteria_path=criteria_path,
            embed_backend=embed_backend,
            model_name=model_name,
            api_base=api_base
        )
        
        return EvaluationResponse(
            success=True,
            message="파일 업로드를 통한 평가가 성공적으로 완료되었습니다.",
            data={
                "overall_score": result.overall_score,
                "structure_score": result.structure_score,
                "content_score": result.content_score,
                "eval_result_path": result.eval_result_path,
                "log_dir": result.log_dir,
                "uploaded_files": {
                    "pred_file": pred_file_info.filename,
                    "gt_file": gt_file_info.filename
                }
            },
            eval_result_path=result.eval_result_path,
            overall_score=result.overall_score,
            structure_score=result.structure_score,
            content_score=result.content_score,
            log_path=result.log_dir
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 평가 실행 중 오류: {str(e)}")
    
    finally:
        # 임시 파일 정리
        if pred_file_info:
            file_service.delete_file(pred_file_info.upload_path)
        if gt_file_info:
            file_service.delete_file(gt_file_info.upload_path)

@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """평가 작업 상태를 확인합니다."""
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
