from __future__ import annotations

import json
import os
from loguru import logger

from evaluation_module.metric import normalize_prediction_json, eval_json
from utils import load_field_eval_criteria, record_evaluation, convert_np
from .types import EvaluationCoreRequest, EvaluationCoreResult
from .logging import setup_evaluation_logger


def run_evaluation_core(req: EvaluationCoreRequest) -> EvaluationCoreResult:
    eval_dir, log_filename = setup_evaluation_logger()

    # JSON 파일 로드 및 복사
    with open(req.pred_json_path, 'r', encoding='utf-8') as f:
        pred_json = json.load(f)
    pred_json_save_path = os.path.join(eval_dir, "pred.json")
    with open(pred_json_save_path, "w", encoding="utf-8") as f:
        json.dump(pred_json, f, ensure_ascii=False, indent=2)

    with open(req.gt_json_path, 'r', encoding='utf-8') as f:
        gt_json = json.load(f)
    gt_json_save_path = os.path.join(eval_dir, "gt.json")
    with open(gt_json_save_path, "w", encoding="utf-8") as f:
        json.dump(gt_json, f, ensure_ascii=False, indent=2)

    logger.info(f"예측 JSON 로드 및 저장 완료: {pred_json_save_path}")
    logger.info(f"Ground truth JSON 로드 및 저장 완료: {gt_json_save_path}")

    # 스키마 및 평가 기준 로드 및 저장
    field_eval_criteria = load_field_eval_criteria(req.schema_name, req.criteria_path)
    criteria_save_path = os.path.join(eval_dir, "criteria.json")
    with open(criteria_save_path, "w", encoding="utf-8") as f:
        json.dump(field_eval_criteria, f, ensure_ascii=False, indent=2)

    logger.info(f"스키마 로드 및 저장 완료: {req.schema_name}")
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
        embed_backend=req.embed_backend,
        model_name=req.model_name,
        api_base=req.api_base,
        field_eval_criteria=field_eval_criteria,
    )

    logger.success("평가 완료!")
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
        pred_json_path=req.pred_json_path,
        gt_json_path=req.gt_json_path,
        embedding_model=req.model_name,
        embedding_host=req.embed_backend,
        schema_name=req.schema_name,
        criteria_path=criteria_save_path,
        overall_score=eval_result.get('overall_score', 0),
        structure_score=eval_result.get('structure_score', 0),
        content_score=eval_result.get('content_score', 0),
        eval_result_path=eval_result_save_path,
        note="",
    )

    return EvaluationCoreResult(
        overall_score=eval_result.get('overall_score', 0),
        structure_score=eval_result.get('structure_score', 0),
        content_score=eval_result.get('content_score', 0),
        eval_result_path=eval_result_save_path,
        log_dir=eval_dir,
    )
