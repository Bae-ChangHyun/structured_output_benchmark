from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from structured_output_benchmark.core.types import (
    VisualizationRequest,
    VisualizationResponse,
)
from structured_output_benchmark.api_server.services.visualization_service import (
    VisualizationService,
)

router = APIRouter()
viz_service = VisualizationService()


@router.get(
    "/streamlit/{result_path:path}",
    summary="Streamlit 시각화 URL 반환",
    response_description="Streamlit 대시보드 접속 URL"
)
async def get_visualization_url(result_path: str):
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="결과 파일을 찾을 수 없습니다.")
    return {
        "success": True,
        "message": "시각화 URL 생성 완료",
        "streamlit_url": f"http://localhost:8501/?eval_result={result_path}",
        "note": "Streamlit 서버가 별도로 실행되어야 합니다.",
    }


@router.post(
    "/generate",
    response_model=VisualizationResponse,
    summary="평가 결과로 정적 HTML 시각화 생성",
    response_description="생성된 HTML 경로와 주요 지표 반환",
)
async def generate_visualization(request: VisualizationRequest):
    if not request.eval_result_path:
        raise HTTPException(status_code=400, detail="eval_result_path가 필요합니다.")

    try:
        result = await viz_service.generate_html(
            eval_result_path=request.eval_result_path,
            output_dir=request.output_dir,
            html_filename=request.html_filename or "visualization.html",
        )

        return VisualizationResponse(
            success=True,
            message="시각화 생성 완료",
            data={
                "overall_score": result.get("overall_score", 0.0),
                "html_path": result.get("html_path"),
                "output_dir": result.get("output_dir"),
            },
            html_path=result.get("html_path"),
            output_dir=result.get("output_dir"),
            overall_score=result.get("overall_score", 0.0),
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="평가 결과 파일을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 생성 중 오류: {str(e)}")


@router.get(
    "/html/{result_path:path}",
    summary="생성된 HTML 시각화 반환",
    response_description="HTML 파일 응답",
)
async def get_visualization_html(result_path: str):
    viz_dir = os.path.dirname(result_path)
    html_path = os.path.join(viz_dir, "visualization.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="시각화 파일을 찾을 수 없습니다.")
    return FileResponse(html_path, media_type="text/html")
