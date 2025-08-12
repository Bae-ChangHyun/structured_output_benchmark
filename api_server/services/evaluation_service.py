import os
import json
from datetime import datetime
from typing import Optional
from loguru import logger

from evaluation_module.metric import normalize_prediction_json, eval_json
from utils import load_field_eval_criteria, record_evaluation, convert_np
from api_server.models.evaluation import EvaluationResult
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
            # JSON 파일 로드 및 복사
            with open(pred_json_path, 'r', encoding='utf-8') as f:
                pred_json = json.load(f)
            pred_json_save_path = os.path.join(eval_dir, "pred.json")
            with open(pred_json_save_path, "w", encoding="utf-8") as f:
                json.dump(pred_json, f, ensure_ascii=False, indent=2)

            with open(gt_json_path, 'r', encoding='utf-8') as f:
                gt_json = json.load(f)
            gt_json_save_path = os.path.join(eval_dir, "gt.json")
            with open(gt_json_save_path, "w", encoding="utf-8") as f:
                json.dump(gt_json, f, ensure_ascii=False, indent=2)

            logger.info(f"예측 JSON 로드 및 저장 완료: {pred_json_save_path}")
            logger.info(f"Ground truth JSON 로드 및 저장 완료: {gt_json_save_path}")

            # 스키마 및 평가 기준 로드 및 저장
            field_eval_criteria = load_field_eval_criteria(schema_name, criteria_path)
            criteria_save_path = os.path.join(eval_dir, "criteria.json")
            with open(criteria_save_path, "w", encoding="utf-8") as f:
                json.dump(field_eval_criteria, f, ensure_ascii=False, indent=2)

            logger.info(f"스키마 로드 및 저장 완료: {schema_name}")
            logger.info(f"평가 기준 로드 및 저장 완료: {criteria_save_path}")

            # 예측 JSON 정규화 및 저장
            norm_pred = normalize_prediction_json(pred_json, gt_json)
            norm_pred_save_path = os.path.join(eval_dir, "norm_pred.json")
            with open(norm_pred_save_path, "w", encoding="utf-8") as f:
                json.dump(norm_pred, f, ensure_ascii=False, indent=2)
            logger.info(f"예측 JSON 정규화 및 저장 완료: {norm_pred_save_path}")

            # 평가 실행
            eval_result = eval_json(
                gt_json,
                norm_pred,
                embed_backend=embed_backend,
                model_name=model_name,
                api_base=api_base,
                field_eval_criteria=field_eval_criteria
            )

            logger.success("API 평가 완료!")
            logger.info(f"전체 점수: {eval_result.get('overall_score', 0):.3f}")
            logger.info(f"구조 점수: {eval_result.get('structure_score', 0):.3f}")
            logger.info(f"내용 점수: {eval_result.get('content_score', 0):.3f}")

            # 평가 결과 저장
            eval_result_save_path = os.path.join(eval_dir, "eval_result.json")
            with open(eval_result_save_path, 'w', encoding='utf-8') as f:
                json.dump(eval_result, f, ensure_ascii=False, indent=2, default=convert_np)

            logger.success(f"평가 결과 저장 완료: {eval_result_save_path}")

            # 평가 결과 기록
            record_evaluation(
                pred_json_path=pred_json_path,
                gt_json_path=gt_json_path,
                embedding_model=model_name,
                embedding_host=embed_backend,
                schema_name=schema_name,
                criteria_path=criteria_save_path,
                overall_score=eval_result.get('overall_score', 0),
                structure_score=eval_result.get('structure_score', 0),
                content_score=eval_result.get('content_score', 0),
                eval_result_path=eval_result_save_path,
                run_folder=None,
                note="API Call"
            )

            return EvaluationResult(
                overall_score=eval_result.get('overall_score', 0),
                structure_score=eval_result.get('structure_score', 0),
                content_score=eval_result.get('content_score', 0),
                eval_result_path=eval_result_save_path,
                log_dir=eval_dir
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
