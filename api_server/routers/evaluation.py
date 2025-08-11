from fastapi import APIRouter, HTTPException

from api_server.models.evaluation import EvaluationRequest, EvaluationResponse
from api_server.services.evaluation_service import EvaluationService

router = APIRouter()
evaluation_service = EvaluationService()

@router.post("", response_model=EvaluationResponse)
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