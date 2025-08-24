"""
Workflow utility functions
"""

import os
import yaml
import json
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from .config import WorkflowConfig


def load_workflow_config(config_path: str) -> WorkflowConfig:
    """YAML 설정 파일을 로드하고 WorkflowConfig 객체로 변환"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # 환경변수 치환
    config_data = substitute_env_vars(config_data)
    
    return WorkflowConfig(**config_data)


def substitute_env_vars(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """설정에서 ${ENV_VAR} 형태의 환경변수를 실제 값으로 치환"""
    def _substitute_recursive(obj):
        if isinstance(obj, dict):
            return {k: _substitute_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_recursive(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            value = os.getenv(env_var)
            if value is None:
                logger.warning(f"환경변수 {env_var}가 설정되지 않았습니다")
                return obj
            return value
        else:
            return obj
    
    return _substitute_recursive(config_data)


def create_workflow_output_dir(workflow_name: str, base_dir: str = None) -> str:
    """워크플로우 결과 출력 디렉토리 생성"""
    if base_dir is None:
        base_dir = "result/workflow"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, f"{workflow_name}_{timestamp}")
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def save_workflow_config(config: WorkflowConfig, output_dir: str):
    """워크플로우 설정을 출력 디렉토리에 저장"""
    config_path = os.path.join(output_dir, "workflow_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.dict(), f, ensure_ascii=False, indent=2)
    logger.info(f"워크플로우 설정 저장: {config_path}")


def create_combination_output_dir(base_output_dir: str, parsing_idx: int, extraction_idx: int) -> str:
    """조합별 출력 디렉토리 생성"""
    combination_dir = os.path.join(base_output_dir, f"combination_{parsing_idx}_{extraction_idx}")
    os.makedirs(combination_dir, exist_ok=True)
    return combination_dir


def format_combination_name(parsing_idx: int, extraction_idx: int, 
                          parsing_config, extraction_config) -> str:
    """조합 이름을 사람이 읽기 쉬운 형태로 포맷"""
    parsing_name = f"{parsing_config.framework}"
    if hasattr(parsing_config, 'file_path'):
        file_name = os.path.basename(parsing_config.file_path)
        parsing_name += f"({file_name})"
    
    extraction_name = f"{extraction_config.framework}({extraction_config.schema_name})"
    
    return f"P{parsing_idx+1}({parsing_name}) → E{extraction_idx+1}({extraction_name})"
