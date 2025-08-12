from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from typing import Optional, Union, TypedDict, Literal
from .common import BaseResponse

class HostInfo(TypedDict, total=False):
    """호스트 정보 스키마
    - dict 형태 유지로 서비스 레이어의 host_info["host"] 접근 호환
    """
    host: Literal["openai", "anthropic", "vllm", "ollama", "google"]
    base_url: str
    model: str

class ExtractionRequest(BaseModel):
    input_text: Optional[str] = Field(None, description="프롬프트 텍스트 (파일 업로드 시 None 가능)")
    retries: int = Field(1, ge=1, le=10, description="프레임워크 재시도 횟수")
    schema_name: str = Field("schema_han", description="프레임워크 스키마 이름 (예: schema_han)")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="프롬프트 온도")
    timeout: int = Field(900, ge=30, le=3600, description="LLM request timeout 시간 (초)")
    framework: str = Field("OpenAIFramework", description="사용할 프레임워크 이름")
    host_info: Optional[HostInfo] = Field(
        None,
        description='호스트 정보 예) {"host":"openai","base_url":"https://api.openai.com/v1","model":"gpt-4o-mini","api_key":"..."}'
    )

class ExtractionResponse(BaseResponse):
    task_id: Optional[str] = None
    result_path: Optional[str] = None
    log_path: Optional[str] = None
    langfuse_url: Optional[str] = None
    success_rate: Optional[float] = None
    latency: Optional[float] = None

class ExtractionResult(BaseModel):
    success: bool
    result: dict
    success_rate: float
    latency: Optional[float]
    log_dir: str
    result_json_path: str
    langfuse_url: Optional[str]
