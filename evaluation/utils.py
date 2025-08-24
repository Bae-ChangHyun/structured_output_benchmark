import os
import json
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from typing import get_origin, get_args, Union
from loguru import logger

from structured_output_kit.extraction.utils import convert_schema


def load_field_eval_criteria(schema_name: str, criteria_path: str = "evaluation/criteria/criteria.json") -> Optional[Dict[str, str]]:
    """스키마별 필드 평가 기준을 로드하거나 없으면 생성합니다.

    우선순위: 새 표준 경로만 사용합니다.
    """
    # 기존 criteria 파일 탐색(신규 경로만)
    candidates = [
        criteria_path,
    ]
    existing_path = next((p for p in candidates if os.path.exists(p)), None)
    if existing_path:
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"평가 기준 로드 오류: {e}")

    # 생성
    try:
        ExtractInfo = convert_schema(schema_name)
        criteria = generate_default_criteria(ExtractInfo)
        os.makedirs(os.path.dirname(criteria_path), exist_ok=True)
        with open(criteria_path, 'w', encoding='utf-8') as f:
            json.dump(criteria, f, ensure_ascii=False, indent=2)
        return criteria
    except Exception as e:
        logger.error(f"기본 평가 기준 생성 오류: {e}")
        return {}


def generate_default_criteria(schema_class) -> Dict[str, str]:
    """Pydantic 모델로부터 기본 평가 기준을 생성합니다."""
    criteria: Dict[str, str] = {}

    for field_name, field_info in schema_class.model_fields.items():
        field_type = field_info.annotation

        if get_origin(field_type) is list:
            inner_type = get_args(field_type)[0]
            if hasattr(inner_type, 'model_fields'):
                for sub_field_name in inner_type.model_fields:
                    full_path = f"{field_name}.{sub_field_name}"
                    criteria[full_path] = get_default_criteria_for_type(inner_type.model_fields[sub_field_name].annotation)
            else:
                criteria[field_name] = get_default_criteria_for_type(inner_type)
        elif get_origin(field_type) is Union and type(None) in get_args(field_type):
            non_none_types = [t for t in get_args(field_type) if t is not type(None)]
            if non_none_types:
                inner_type = non_none_types[0]
                if hasattr(inner_type, 'model_fields'):
                    for sub_field_name in inner_type.model_fields:
                        full_path = f"{field_name}.{sub_field_name}"
                        criteria[full_path] = get_default_criteria_for_type(inner_type.model_fields[sub_field_name].annotation)
                else:
                    criteria[field_name] = get_default_criteria_for_type(inner_type)
        else:
            if hasattr(field_type, 'model_fields'):
                for sub_field_name in field_type.model_fields:
                    full_path = f"{field_name}.{sub_field_name}"
                    criteria[full_path] = get_default_criteria_for_type(field_type.model_fields[sub_field_name].annotation)
            else:
                criteria[field_name] = get_default_criteria_for_type(field_type)

    return criteria


def get_default_criteria_for_type(field_type) -> str:
    if field_type in [int, float, bool]:
        return 'exact'
    if field_type == str:
        return 'embedding'
    return 'embedding'


def convert_np(obj: Any):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def record_evaluation(
    pred_json_path: str,
    gt_json_path: str,
    provider: str,
    model: str,
    schema_name: str,
    criteria_path: str,
    overall_score: float,
    eval_result_path: str,
    save: Optional[bool] = False,
):
    if save:
        csv_path = "result/evaluation_result.csv"
        record = {
            "pred_json_path": pred_json_path,
            "gt_json_path": gt_json_path,
            "embedding_provider": provider,
            "embedding_model": model,
            "schema_name": schema_name,
            "criteria_path": criteria_path,
            "overall_score": overall_score,
            "eval_result_path": eval_result_path,
        }
        if os.path.isfile(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            df = pd.DataFrame([record])
        df.to_csv(csv_path, index=False)
