import os
import json
from datetime import datetime
from typing import Optional
from loguru import logger

from api_server.models.evaluation import EvaluationResult
from core.types import EvaluationCoreRequest
from core.evaluation import run_evaluation_core
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class EvaluationService:
    
    async def run_evaluation(
        self,
        pred_json_path: str,
        gt_json_path: str,
        schema_name: str = "schema_han",
        criteria_path: Optional[str] = "evaluation_module/criteria/criteria.json",
        embed_backend: str = "openai",
        model_name: Optional[str] = None,
        api_base: Optional[str] = None
    ) -> EvaluationResult:
        """평가 작업을 실행합니다."""
        
        # 로그 설정
        eval_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        eval_dir = os.path.join("result", "evaluation", eval_time)
        os.makedirs(eval_dir, exist_ok=True)
        log_filename = os.path.join(eval_dir, "evaluation.log")
        
        # 로거 설정
        logger.remove()
        logger.add(log_filename, level="INFO", enqueue=True)
        
        try:
            core_result = run_evaluation_core(
                EvaluationCoreRequest(
                    pred_json_path=pred_json_path,
                    gt_json_path=gt_json_path,
                    schema_name=schema_name,
                    criteria_path=criteria_path,
                    embed_backend=embed_backend,
                    model_name=model_name,
                    api_base=api_base,
                )
            )

            return EvaluationResult(
                overall_score=core_result.overall_score,
                structure_score=core_result.structure_score,
                content_score=core_result.content_score,
                eval_result_path=core_result.eval_result_path,
                log_dir=core_result.log_dir,
            )
            
        except FileNotFoundError as e:
            logger.error(f"파일을 찾을 수 없습니다: {e}")
            raise e
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파일 파싱 오류: {e}")
            raise e
        except Exception as e:
            logger.error(f"평가 중 오류 발생: {e}")
            raise e
