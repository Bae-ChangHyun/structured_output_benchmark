from fastapi import APIRouter, HTTPException

from structured_output_kit.core.types import EvaluationRequest, EvaluationResponse
from structured_output_kit.api_server.services.evaluation_service import EvaluationService

router = APIRouter()
evaluation_service = EvaluationService()

@router.post(
    "",
    response_model=EvaluationResponse,
    summary="예측 JSON 평가",
    response_description="overall_score와 상세 필드 리포트를 포함한 평가 결과"
)
async def run_evaluation(request: EvaluationRequest):
    """
    예측 JSON(pred_json_path)을 정답 JSON(gt_json_path)과 비교하여 점수를 계산합니다.

    요청 본문
    - pred_json_path: 예측 JSON 경로
    - gt_json_path: 정답 JSON 경로
    - schema_name: 스키마 이름(기본: schema_han)
    - criteria_path: 필드별 평가 기준 파일 경로(없으면 자동 생성)
    - host_info: 임베딩 백엔드 정보 { provider, base_url, model }

    응답 본문
    - data.result: overall_score, fields별 세부 리포트, 사용된 criteria 포함
    - data.eval_result_path: 평가 결과 저장 파일 경로
    - data.output_dir: 작업 출력 폴더

    상태코드
    - 200: 성공
    - 400: 경로 누락 등 요청 오류
    - 500: 내부 오류
    """
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
            host_info=request.host_info,
            output_dir=request.output_dir
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