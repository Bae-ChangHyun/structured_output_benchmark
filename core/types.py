from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HostInfo(BaseModel):
    host: str
    base_url: str
    model: str


class ExtractionCoreRequest(BaseModel):
    input_text_or_path: str = Field(..., description="프롬프트 텍스트 또는 파일 경로")
    retries: int = 1
    schema_name: str = "schema_han"
    temperature: float = 0.1
    timeout: int = 900
    framework_name: str = "OpenAIFramework"
    host_info: HostInfo


class ExtractionCoreResult(BaseModel):
    success: bool
    result: Dict[str, Any]
    success_rate: float
    latency: Optional[float]
    log_dir: str
    result_json_path: str
    langfuse_url: Optional[str] = None


class EvaluationCoreRequest(BaseModel):
    pred_json_path: str
    gt_json_path: str
    schema_name: str = "schema_han"
    criteria_path: Optional[str] = "evaluation_module/criteria/criteria.json"
    embed_backend: str = "openai"
    model_name: Optional[str] = None
    api_base: Optional[str] = None


class EvaluationCoreResult(BaseModel):
    overall_score: float
    structure_score: float
    content_score: float
    eval_result_path: str
    log_dir: str
