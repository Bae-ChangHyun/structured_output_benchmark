"""
Workflow configuration models using Pydantic
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import os


class ParsingConfig(BaseModel):
    """파싱 단계 설정"""
    file_path: str = Field(..., description="파싱할 PDF/이미지 파일 경로")
    framework: str = Field("docling", description="사용할 파싱 프레임워크")
    extra_kwargs: Dict[str, Any] = Field(default_factory=dict, description="프레임워크별 추가 파라미터")
    prompt: Optional[str] = Field(None, description="VLM 사용시 프롬프트")
    host_info: Optional[Dict[str, Any]] = Field(None, description="VLM 사용시 호스트 정보")
    save: bool = Field(True, description="결과 저장 여부")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"파일을 찾을 수 없습니다: {v}")
        return v


class ExtractionConfig(BaseModel):
    """추출 단계 설정"""
    prompt: Optional[str] = Field(None, description="사용할 프롬프트")
    input_text: Optional[str] = Field(None, description="직접 입력 텍스트 (parsing 단계 건너뛰기)")
    schema_name: str = Field("schema_han", description="스키마 이름")
    framework: str = Field("openai", description="사용할 추출 프레임워크")
    host_info: Dict[str, Any] = Field(..., description="LLM 호스트 정보")
    retries: int = Field(1, ge=1, le=10, description="재시도 횟수")
    extra_kwargs: Dict[str, Any] = Field(default_factory=dict, description="추가 파라미터")
    langfuse_trace_id: Optional[str] = Field(None, description="Langfuse trace ID")
    save: bool = Field(True, description="결과 저장 여부")


class EvaluationConfig(BaseModel):
    """평가 단계 설정"""
    enabled: bool = Field(False, description="평가 실행 여부")
    gt_json_path: Optional[str] = Field(None, description="Ground truth JSON 파일 경로")
    schema_name: str = Field("schema_han", description="스키마 이름")
    criteria_path: str = Field("evaluation/criteria/criteria.json", description="평가 기준 파일 경로")
    host_info: Optional[Dict[str, Any]] = Field(None, description="임베딩 모델 호스트 정보")
    save: bool = Field(True, description="결과 저장 여부")
    
    @validator('gt_json_path')
    def validate_gt_json_path(cls, v, values):
        if values.get('enabled', False) and v is None:
            raise ValueError("평가가 활성화된 경우 gt_json_path는 필수입니다")
        if v and not os.path.exists(v):
            raise ValueError(f"Ground truth 파일을 찾을 수 없습니다: {v}")
        return v


class WorkflowConfig(BaseModel):
    """전체 워크플로우 설정"""
    name: str = Field("workflow", description="워크플로우 이름")
    description: Optional[str] = Field(None, description="워크플로우 설명")
    output_dir: Optional[str] = Field(None, description="결과 출력 디렉토리")
    
    # 여러 설정을 지원하기 위해 리스트로 정의
    parsing: Optional[List[ParsingConfig]] = Field(None, description="파싱 설정 리스트 (선택사항)")
    extraction: List[ExtractionConfig] = Field(..., description="추출 설정 리스트")
    evaluation: Optional[EvaluationConfig] = Field(None, description="평가 설정")
    
    # 실행 옵션
    parallel: bool = Field(False, description="병렬 실행 여부")
    fail_fast: bool = Field(True, description="실패시 즉시 중단 여부")
    
    @validator('parsing')
    def validate_parsing_or_input_text(cls, v, values):
        """parsing이 없으면 extraction에 input_text가 있어야 함"""
        if not v:  # parsing이 없는 경우
            extraction = values.get('extraction', [])
            for ext_config in extraction:
                if not hasattr(ext_config, 'input_text') or not ext_config.input_text:
                    raise ValueError("parsing 설정이 없으면 extraction 설정에서 input_text를 제공해야 합니다")
        return v
    
    @validator('extraction')
    def validate_extraction_not_empty(cls, v):
        if not v:
            raise ValueError("extraction 설정은 최소 1개 이상이어야 합니다")
        return v
    
    def get_total_combinations(self) -> int:
        """전체 조합 수 계산"""
        if self.parsing:
            return len(self.parsing) * len(self.extraction)
        else:
            return len(self.extraction)  # parsing 없이 extraction만
    
    def get_combinations(self) -> List[tuple]:
        """모든 파싱-추출 조합 생성"""
        combinations = []
        if self.parsing:
            # 파싱-추출 조합
            for i, parsing_config in enumerate(self.parsing):
                for j, extraction_config in enumerate(self.extraction):
                    combinations.append((i, j, parsing_config, extraction_config))
        else:
            # 추출만 (파싱 없음)
            for j, extraction_config in enumerate(self.extraction):
                combinations.append((None, j, None, extraction_config))
        return combinations
