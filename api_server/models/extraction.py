from pydantic import BaseModel, Field
from typing import Optional, Union
from .common import BaseResponse, TaskResponse

class ExtractionRequest(BaseModel):
    input_text: Optional[str] = Field(None, description="프롬프트 텍스트 (파일 업로드 시 None 가능)")
    retries: int = Field(1, ge=1, le=10, description="프레임워크 재시도 횟수")
    schema_name: str = Field("schema_han", description="프레임워크 스키마 이름 (예: schema_han)")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="프롬프트 온도")
    timeout: int = Field(900, ge=30, le=3600, description="LLM request timeout 시간 (초)")
    host_choice: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="호스트 선택: 1=OpenAI, 2=Anthropic, 3=vLLM, 4=Ollama, 5=Google (미지정시 OpenAI 기본값)"
    )
    framework_choice: Optional[int] = Field(
        None, 
        description="프레임워크 선택 (호스트별로 다름, 미지정시 호환되는 첫번째 프레임워크 사용). 호스트별 프레임워크 목록은 /api/v1/utils/frameworks 엔드포인트 참조"
    )

class ExtractionFileRequest(BaseModel):
    retries: int = Field(1, ge=1, le=10, description="프레임워크 재시도 횟수")
    schema_name: str = Field("schema_han", description="프레임워크 스키마 이름 (예: schema_han)")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="프롬프트 온도")
    timeout: int = Field(900, ge=30, le=3600, description="LLM request timeout 시간 (초)")
    host_choice: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="호스트 선택: 1=OpenAI, 2=Anthropic, 3=vLLM, 4=Ollama, 5=Google (미지정시 OpenAI 기본값)"
    )
    framework_choice: Optional[int] = Field(
        None, 
        description="프레임워크 선택 (호스트별로 다름, 미지정시 호환되는 첫번째 프레임워크 사용). 호스트별 프레임워크 목록은 /api/v1/utils/frameworks 엔드포인트 참조"
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
