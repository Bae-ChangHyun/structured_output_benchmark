from fastapi import APIRouter, HTTPException, Form
from typing import Dict, List, Any, Optional
import os
from structured_output_kit.utils.common import check_host_info
from structured_output_kit.utils.types import EvaluationRequest, EvaluationResponse, HostInfo
from structured_output_kit.server.services.evaluation_service import EvaluationService

router = APIRouter()
evaluation_service = EvaluationService()

@router.post(
    "/eval",
    response_model=EvaluationResponse,
    summary="예측 JSON 평가",
    response_description="overall_score와 상세 필드 리포트를 포함한 평가 결과"
)
async def run_evaluation(
    pred_json_path: str = Form(..., description="예측 JSON 파일 경로"),
    gt_json_path: str = Form(..., description="정답 JSON 파일 경로"),
    schema_name: str = Form("schema_han", description="스키마 이름"),
    criteria_path: Optional[str] = Form(None, description="필드별 평가 기준 파일 경로"),
    provider: Optional[str] = Form(None, description="임베딩 제공자 (openai, anthropic, google, ollama, openai_compatible)"),
    model: Optional[str] = Form(None, description="임베딩 모델명"),
    base_url: Optional[str] = Form(None, description="API 기본 URL"),
    api_key: Optional[str] = Form(None, description="API 키"),
    output_dir: Optional[str] = Form(None, description="결과 출력 디렉토리"),
    save: bool = Form(True, description="결과 저장 여부")
):
    """
    예측 JSON(pred_json_path)을 정답 JSON(gt_json_path)과 비교하여 점수를 계산합니다.

    상태코드
    - 200: 성공
    - 400: 경로 누락 등 요청 오류
    - 500: 내부 오류
    """
    if not pred_json_path or not gt_json_path:
        raise HTTPException(
            status_code=400, 
            detail="pred_json_path와 gt_json_path가 모두 필요합니다."
        )
    
    try:
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
        request = EvaluationRequest(
            pred_json_path=pred_json_path,
            gt_json_path=gt_json_path,
            schema_name=schema_name,
            criteria_path=criteria_path,
            host_info=host_info,
            output_dir=output_dir,
            save=save
        )
        
        result = await evaluation_service.run_evaluation(
            pred_json_path=request.pred_json_path,
            gt_json_path=request.gt_json_path,
            schema_name=request.schema_name,
            criteria_path=request.criteria_path,
            host_info=request.host_info,
            output_dir=request.output_dir,
            save=request.save
        )
        
        return EvaluationResponse(
            success=True,
            message="평가가 성공적으로 완료되었습니다.",
            data={
                "result": result.result,
                "overall_score": result.overall_score,
                "eval_result_path": result.eval_result_path,
                "output_dir": result.output_dir
            },
            eval_result_path=result.eval_result_path,
            overall_score=result.overall_score,
            output_dir=result.output_dir
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 실행 중 오류: {str(e)}")


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