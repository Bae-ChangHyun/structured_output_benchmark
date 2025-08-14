import os
from datetime import datetime
from typing import Optional
from loguru import logger
from langfuse import get_client

from structured_output_benchmark.extraction_module.utils import get_compatible_frameworks
from structured_output_benchmark.core.types import ExtractionRequest, HostInfo, ExtractionResult
from structured_output_benchmark.core.extraction import run_extraction_core

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class ExtractionService:
    def __init__(self):
        self.langfuse_client = get_client()
    
    async def run_extraction(
        self,
        input_text: str,
        retries: int = 1,
        schema_name: str = "schema_han",
        extra_kwargs: Optional[dict] = None,
        framework: str = 'OpenAIFramework',
        host_info: Optional[HostInfo] = None,
        langfuse_trace_id: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> ExtractionResult:
        """추출 작업을 실행합니다."""

        # 로그 설정
        log_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = os.path.join("result", "extraction", log_time)
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, "extraction.log")

        # 로거 설정
        logger.remove()
        logger.add(log_filename, level="INFO", enqueue=True)

        try:
            # input_text가 파일 경로라면 파일 내용 읽기
            if isinstance(input_text, str) and os.path.isfile(input_text):
                try:
                    with open(input_text, "r", encoding="utf-8") as f:
                        input_text = f.read()
                except Exception as file_err:
                    logger.error(f"파일 읽기 실패: {input_text}, 에러: {str(file_err)}")
                    raise file_err

            if host_info is None:
                logger.error("host_info가 필요합니다.")
                raise ValueError("host_info가 필요합니다.")

            if framework not in get_compatible_frameworks(host_info.host):
                logger.error(f"호환되지 않는 프레임워크: {framework}")
                raise ValueError(f"호환되지 않는 프레임워크: {framework}")

            extra_kwargs = dict(extra_kwargs or {})

            core_result = run_extraction_core(
                ExtractionRequest(
                    input_text=input_text,
                    retries=retries,
                    schema_name=schema_name,
                    extra_kwargs=extra_kwargs,
                    framework=framework,
                    host_info=host_info,
                    langfuse_trace_id=langfuse_trace_id,
                    output_dir=output_dir,
                )
            )

            return ExtractionResult(
                success=core_result.success,
                result=core_result.result,
                success_rate=core_result.success_rate,
                latency=core_result.latency,
                result_json_path=core_result.result_json_path,
                langfuse_url=core_result.langfuse_url,
                output_dir=core_result.output_dir,
            )

        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise e
