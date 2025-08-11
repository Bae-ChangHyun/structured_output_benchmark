from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
import json

router = APIRouter()

@router.get("/streamlit/{result_path:path}")
async def get_visualization_url(result_path: str):
    """Streamlit 시각화 URL을 반환합니다."""
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="결과 파일을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "message": "시각화 URL 생성 완료",
        "streamlit_url": f"http://localhost:8501/?eval_result={result_path}",
        "note": "Streamlit 서버가 별도로 실행되어야 합니다."
    }

@router.post("/generate")
async def generate_visualization(eval_result_path: str):
    """평가 결과로부터 시각화를 생성합니다."""
    if not os.path.exists(eval_result_path):
        raise HTTPException(status_code=404, detail="평가 결과 파일을 찾을 수 없습니다.")
    
    try:
        # 평가 결과 파일 읽기
        with open(eval_result_path, 'r', encoding='utf-8') as f:
            eval_result = json.load(f)
        
        # 기본적인 HTML 시각화 생성 (간단한 예시)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>평가 결과 시각화</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .score {{ font-size: 24px; margin: 20px 0; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>평가 결과</h1>
            <div class="metric">
                <h3>전체 점수</h3>
                <div class="score">{eval_result.get('overall_score', 0):.3f}</div>
            </div>
            <div class="metric">
                <h3>구조 점수</h3>
                <div class="score">{eval_result.get('structure_score', 0):.3f}</div>
            </div>
            <div class="metric">
                <h3>내용 점수</h3>
                <div class="score">{eval_result.get('content_score', 0):.3f}</div>
            </div>
        </body>
        </html>
        """
        
        # HTML 파일 저장
        viz_dir = os.path.dirname(eval_result_path)
        html_path = os.path.join(viz_dir, "visualization.html")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            "success": True,
            "message": "시각화 생성 완료",
            "html_path": html_path,
            "data": {
                "overall_score": eval_result.get('overall_score', 0),
                "structure_score": eval_result.get('structure_score', 0),
                "content_score": eval_result.get('content_score', 0)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 생성 중 오류: {str(e)}")

@router.get("/html/{result_path:path}")
async def get_visualization_html(result_path: str):
    """생성된 HTML 시각화를 반환합니다."""
    viz_dir = os.path.dirname(result_path)
    html_path = os.path.join(viz_dir, "visualization.html")
    
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="시각화 파일을 찾을 수 없습니다.")
    
    return FileResponse(html_path, media_type="text/html")
