import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
import yaml
from langfuse import get_client

from extraction_module.utils import extract_with_framework
from utils import (
    select_host_by_choice, select_framework_by_choice, record_extraction, 
    box_line, log_response, final_report
)
from api_server.models.extraction import ExtractionResult

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class ExtractionService:
    def __init__(self):
        self.langfuse_client = get_client()
    
    def get_host_info(self, host_choice: Optional[int] = None) -> Dict[str, Any]:
        """호스트 정보를 가져옵니다."""
        if host_choice:
            return select_host_by_choice(host_choice)
        else:
            # 기본값으로 OpenAI 사용
            return {
                "host": "openai",
                "base_url": "https://api.openai.com/v1",
                "model": os.getenv("OPENAI_MODELS", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
            }
    
    def get_framework_name(self, host: str, framework_choice: Optional[int] = None) -> str:
        """프레임워크 이름을 가져옵니다."""
        if framework_choice:
            return select_framework_by_choice(host, framework_choice)
        else:
            # 기본값으로 첫 번째 호환 프레임워크 사용
            from extraction_module.utils import get_compatible_frameworks
            frameworks = get_compatible_frameworks(host)
            return frameworks[0] if frameworks else "openai"
    
    async def run_extraction(
        self,
        input_text: str,
        retries: int = 1,
        schema_name: str = "schema_han",
        temperature: float = 0.1,
        timeout: int = 900,
        host_choice: Optional[int] = None,
        framework_choice: Optional[int] = None
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
            # Langfuse 트레이스 ID 생성
            langfuse_trace_id = self.langfuse_client.create_trace_id(seed=f"custom-{str(uuid.uuid4())}")
            
            # 호스트 및 프레임워크 정보 가져오기
            host_info = self.get_host_info(host_choice)
            framework_name = self.get_framework_name(host_info["host"], framework_choice)
            
            base_url = host_info["base_url"]
            api_key = host_info["api_key"]
            model = host_info["model"]
            
            # 실험 정보 로깅
            box_width = 48
            exp_info = [
                "*" * box_width,
                f"{'API Extraction 시작'.center(box_width)}",
                box_line(f"Host: {host_info['host']}"),
                box_line(f"BaseURL: {base_url}"),
                box_line(f"Model: {model}"),
                box_line(f"Framework: {framework_name}"),
                box_line(f"Input: {input_text.strip()[:20]}..."),
                box_line(f"Retries: {retries}"),
                "*" * box_width
            ]
            for line in exp_info:
                logger.info(line)
            
            # prompt.yaml에서 Extract_prompt 불러오기
            with open("prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
            extract_prompt = prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
            
            # 추출 실행
            result, success, latencies = extract_with_framework(
                framework_name=framework_name,
                provider=host_info["host"],
                model_name=host_info["model"],
                base_url=host_info["base_url"],
                content=input_text,
                prompt=f"{extract_prompt}\n{input_text}",
                schema_name=schema_name,
                retries=retries,
                api_delay_seconds=0.5,
                timeout=timeout,
                temperature=temperature,
                langfuse_trace_id=langfuse_trace_id
            )
            
            # 결과 저장
            result_json_path = os.path.join(log_dir, f"result_{log_time}.json")
            with open(result_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 성공률 및 지연시간 계산
            success_rate = success
            latency = latencies[0] if isinstance(latencies, list) and latencies else latencies
            
            # 로깅
            logger.success(f"API Extraction completed")
            logger.success(f"Success rate: {success_rate:.2%}")
            log_response(logger, result, latency, prefix="API response ")
            
            # Langfuse URL 생성
            langfuse_url = self.langfuse_client.get_trace_url(trace_id=langfuse_trace_id)
            final_report(exp_info, logger, latency, langfuse_url)
            
            # 결과 기록
            record_extraction(
                log_filename=log_filename,
                host=host_info["host"],
                model=model,
                prompt=f"{extract_prompt}\n{input_text}",
                framework=framework_name,
                success=bool(result),
                latency=latency,
                langfuse_url=langfuse_url,
                note="API Call",
                csv_path="result/extraction_result.csv",
                result_json_path=result_json_path
            )
            
            return ExtractionResult(
                success=bool(result),
                result=result,
                success_rate=success_rate,
                latency=latency,
                log_dir=log_dir,
                result_json_path=result_json_path,
                langfuse_url=langfuse_url
            )
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise e
