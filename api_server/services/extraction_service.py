import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
import yaml
from langfuse import get_client

from extraction_module.utils import get_compatible_frameworks
from api_server.models.extraction import ExtractionResult
from core.types import ExtractionCoreRequest, HostInfo
from core.extraction import run_extraction_core

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
        temperature: float = 0.1,
        timeout: int = 900,
        framework: str = 'OpenAIFramework',
        host_info: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """추출 작업을 실행합니다."""
        
        # 로그 설정
        log_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = os.path.join("result/extraction", log_time)
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
            if framework not in get_compatible_frameworks(host_info['host']):
                logger.error(f"호환되지 않는 프레임워크: {framework}")
                raise ValueError(f"호환되지 않는 프레임워크: {framework}")
            # core 유즈케이스 호출
            core_result = run_extraction_core(
                ExtractionCoreRequest(
                    input_text_or_path=input_text,
                    retries=retries,
                    schema_name=schema_name,
                    temperature=temperature,
                    timeout=timeout,
                    framework_name=framework,
                    host_info=HostInfo(host=host_info["host"], base_url=host_info["base_url"], model=host_info["model"]),
                )
            )

            return ExtractionResult(
                success=core_result.success,
                result=core_result.result,
                success_rate=core_result.success_rate,
                latency=core_result.latency,
                log_dir=core_result.log_dir,
                result_json_path=core_result.result_json_path,
                langfuse_url=core_result.langfuse_url,
            )
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise e
