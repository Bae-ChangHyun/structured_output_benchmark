import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

# 프로젝트 루트를 파이썬 패스에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structured_output_benchmark.api_server.routers import extraction, evaluation, visualization, utils
from structured_output_benchmark.api_server.config import settings

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    print("FastAPI 서버가 시작되었습니다.")
    yield
    # 서버 종료 시 실행
    print("FastAPI 서버가 종료되었습니다.")

app = FastAPI(
    title="Structured Output Benchmark API",
    description="""
    LLM 구조화된 출력 벤치마크 API 서버
    
    ## 주요 기능
    
    * **텍스트 추출**: 다양한 LLM 호스트와 프레임워크를 통한 구조화된 정보 추출
    * **평가**: 예측 결과와 정답 JSON 비교 평가
    
    ## 지원 호스트
    
    1. **OpenAI** - GPT-4, GPT-3.5 등
    2. **Anthropic** - Claude 모델들
    3. **vLLM** - 로컬 vLLM 서버
    4. **Ollama** - 로컬 Ollama 서버  
    5. **Google** - Gemini 모델들
    
    ## 사용법
    
    1. `/v1/utils/hosts` - 사용 가능한 호스트 목록 확인
    2. `/v1/utils/frameworks?host=<호스트명>` - 호스트별 프레임워크 목록 확인
    3. `/v1/extraction` - 텍스트 추출 실행
    3. `/v1/evaluation` - 평가 실행
    ```
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(extraction.router, prefix="/v1/extraction", tags=["extraction"])
app.include_router(evaluation.router, prefix="/v1/evaluation", tags=["evaluation"])
app.include_router(visualization.router, prefix="/v1/visualization", tags=["visualization"])
app.include_router(utils.router, prefix="/v1/utils", tags=["utils"])

@app.get("/")
async def root():
    return {
        "message": "Structured Output Benchmark API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 글로벌 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "api_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
