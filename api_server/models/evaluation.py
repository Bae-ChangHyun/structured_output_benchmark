from pydantic import BaseModel, Field
from typing import Optional
from .common import BaseResponse

class EvaluationRequest(BaseModel):
    pred_json_path: Optional[str] = Field(None, description="예측 결과 JSON 파일 경로")
    gt_json_path: Optional[str] = Field(None, description="Ground truth JSON 파일 경로")
    schema_name: str = Field("schema_han", description="스키마 이름")
    criteria_path: Optional[str] = Field("evaluation_module/criteria/criteria.json", description="평가 기준 파일 경로")
    embed_backend: str = Field("openai", description="임베딩 백엔드")
    model_name: Optional[str] = Field(None, description="임베딩 모델명")
    api_key: Optional[str] = Field(None, description="API 키")
    api_base: Optional[str] = Field(None, description="API 베이스 URL")

class EvaluationFileRequest(BaseModel):
    schema_name: str = Field("schema_han", description="스키마 이름")
    criteria_path: Optional[str] = Field("evaluation_module/criteria/criteria.json", description="평가 기준 파일 경로")
    embed_backend: str = Field("openai", description="임베딩 백엔드")
    model_name: Optional[str] = Field(None, description="임베딩 모델명")
    api_key: Optional[str] = Field(None, description="API 키")
    api_base: Optional[str] = Field(None, description="API 베이스 URL")

class EvaluationResponse(BaseResponse):
    task_id: Optional[str] = None
    eval_result_path: Optional[str] = None
    overall_score: Optional[float] = None
    structure_score: Optional[float] = None
    content_score: Optional[float] = None
    log_path: Optional[str] = None

class EvaluationResult(BaseModel):
    overall_score: float
    structure_score: float
    content_score: float
    eval_result_path: str
    log_dir: str
