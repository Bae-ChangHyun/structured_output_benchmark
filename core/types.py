from __future__ import annotations

from typing import Optional, Dict, Any
import langfuse
from pydantic import BaseModel, Field, model_validator


class HostInfo(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key: Optional[str]


class ExtractionRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="사용할 프롬프트 (기본값: prompt.yaml에서 로드)")
    input_text: str = Field(..., description="프롬프트 텍스트 또는 파일 경로")

    # 공통 실행 설정
    retries: int = Field(1, ge=1, le=10, description="프레임워크 재시도 횟수")
    schema_name: str = Field("schema_han", description="프레임워크 스키마 이름 (예: schema_han)")
    extra_kwargs: Dict[str, Any] = Field(default_factory=dict, description="추가 LLM/프레임워크 파라미터를 담는 딕셔너리. 예: { 'temperature': 0.1, 'timeout': 900, 'seed': 42 }")
    langfuse_trace_id: Optional[str] = Field(None, description="Langfuse trace ID")
    output_dir: Optional[str] = Field(None, description="결과 출력 디렉토리")

    framework: str = Field("OpenAIFramework", description="사용할 프레임워크 이름")
    # 필수 호스트 정보
    host_info: HostInfo

    
class ExtractionResult(BaseModel):
    success: bool
    result: Dict[str, Any]
    success_rate: float
    latency: Optional[float]
    output_dir: str
    result_json_path: str
    langfuse_url: Optional[str] = None

class EvaluationRequest(BaseModel):
    pred_json_path: str
    gt_json_path: str
    schema_name: str = "schema_han"
    criteria_path: Optional[str] = "evaluation_module/criteria.json"
    host_info: HostInfo
    output_dir: Optional[str] = None

class EvaluationResult(BaseModel):
    result: Dict[str, Any]
    overall_score: float
    eval_result_path: str
    output_dir: str

class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class ExtractionResponse(BaseResponse):
    task_id: Optional[str] = None
    result_path: Optional[str] = None
    output_dir: Optional[str] = None
    langfuse_url: Optional[str] = None
    success_rate: Optional[float] = None
    latency: Optional[float] = None

class EvaluationResponse(BaseResponse):
    task_id: Optional[str] = None
    eval_result_path: Optional[str] = None
    overall_score: Optional[float] = None
    output_dir: Optional[str] = None

class VisualizationRequest(BaseModel):
    eval_result_path: str
    output_dir: Optional[str] = None
    html_filename: Optional[str] = "visualization.html"

class VisualizationResponse(BaseResponse):
    html_path: Optional[str] = None
    output_dir: Optional[str] = None
    overall_score: Optional[float] = None
