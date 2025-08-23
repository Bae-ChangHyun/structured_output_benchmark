import os
import json
from datetime import datetime
from typing import Optional
from loguru import logger

from structured_output_kit.utils.types import EvaluationRequest, HostInfo, EvaluationResult
from structured_output_kit.evaluation.core import run_evaluation_core
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class EvaluationService:
    
    async def run_evaluation(
        self,
        pred_json_path: str,
        gt_json_path: str,
        schema_name: str = "schema_han",
    criteria_path: Optional[str] = "evaluation/criteria/criteria.json",
        host_info: Optional[HostInfo] = None,
        output_dir: Optional[str] = None,
        save: Optional[bool] = False
    ) -> EvaluationResult:
        """평가 작업을 실행합니다."""
        
        # 로그 설정
        log_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = os.path.join("result", "evaluation", log_time)
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, "evaluation.log")
        
        # 로거 설정
        logger.remove()
        logger.add(log_filename, level="INFO", enqueue=True)
        
        try:
            core_result = run_evaluation_core(
                EvaluationRequest(
                    pred_json_path=pred_json_path,
                    gt_json_path=gt_json_path,
                    schema_name=schema_name,
                    criteria_path=criteria_path,
                    host_info=host_info,
                    output_dir=output_dir,
                    save=save
                )
            )

            return EvaluationResult(
                result=core_result.result,
                overall_score=core_result.overall_score,
                eval_result_path=core_result.eval_result_path,
                output_dir=core_result.output_dir
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
