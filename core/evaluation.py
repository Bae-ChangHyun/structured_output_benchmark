from __future__ import annotations

import json
import os
from loguru import logger

from structured_output_benchmark.evaluation_module.metric import normalize_prediction_json, eval_json
from structured_output_benchmark.utils import load_field_eval_criteria, record_evaluation, convert_np
from .types import EvaluationRequest, EvaluationResult
from .logging import setup_logger


def run_evaluation_core(req: EvaluationRequest) -> EvaluationResult:
    output_dir, log_filename = setup_logger(task='evaluation', 
                                         output_dir=req.output_dir)
    
    host_info = req.host_info

    # JSON 파일 로드 및 복사
    with open(req.pred_json_path, 'r', encoding='utf-8') as f:
        pred_json = json.load(f)
    pred_json_save_path = os.path.join(output_dir, "pred.json")
    with open(pred_json_save_path, "w", encoding="utf-8") as f:
        json.dump(pred_json, f, ensure_ascii=False, indent=2)

    with open(req.gt_json_path, 'r', encoding='utf-8') as f:
        gt_json = json.load(f)
    gt_json_save_path = os.path.join(output_dir, "gt.json")
    with open(gt_json_save_path, "w", encoding="utf-8") as f:
        json.dump(gt_json, f, ensure_ascii=False, indent=2)

    logger.info(f"예측 JSON 로드 및 저장 완료: {pred_json_save_path}")
    logger.info(f"Ground truth JSON 로드 및 저장 완료: {gt_json_save_path}")

    # 스키마 및 평가 기준 로드 및 저장
    field_eval_criteria = load_field_eval_criteria(req.schema_name, req.criteria_path)
    criteria_save_path = os.path.join(output_dir, "criteria.json")
    with open(criteria_save_path, "w", encoding="utf-8") as f:
        json.dump(field_eval_criteria, f, ensure_ascii=False, indent=2)

    logger.info(f"스키마 로드 및 저장 완료: {req.schema_name}")
    logger.info(f"평가 기준 로드 및 저장 완료: {criteria_save_path}")

    # 예측 JSON 정규화 및 저장
    norm_pred = normalize_prediction_json(pred_json, gt_json)
    norm_pred_save_path = os.path.join(output_dir, "norm_pred.json")
    with open(norm_pred_save_path, "w", encoding="utf-8") as f:
        json.dump(norm_pred, f, ensure_ascii=False, indent=2)
    logger.info(f"예측 JSON 정규화 및 저장 완료: {norm_pred_save_path}")

    # 평가 실행
    eval_result = eval_json(
        gt=gt_json,
        pred=norm_pred,
        host_info=host_info,
        field_eval_criteria=field_eval_criteria,
    )

    logger.success("평가 완료!")
    logger.info(f"점수: {eval_result.get('overall_score', 0):.3f}")

    # 평가 결과 저장
    eval_result_save_path = os.path.join(output_dir, "eval_result.json")
    with open(eval_result_save_path, 'w', encoding='utf-8') as f:
        json.dump(eval_result, f, ensure_ascii=False, indent=2, default=convert_np)

    logger.success(f"평가 결과 저장 완료: {eval_result_save_path}")

    # 평가 결과 기록
    record_evaluation(
        pred_json_path=req.pred_json_path,
        gt_json_path=req.gt_json_path,
        embedding_host=host_info.host,
        embedding_model=host_info.model,
        schema_name=req.schema_name,
        criteria_path=criteria_save_path,
        overall_score=eval_result.get('overall_score', 0),
        eval_result_path=eval_result_save_path,
        note="",
    )

    return EvaluationResult(
        result=eval_result,
        overall_score=eval_result.get('overall_score', 0),
        eval_result_path=eval_result_save_path,
        output_dir=output_dir
    )
