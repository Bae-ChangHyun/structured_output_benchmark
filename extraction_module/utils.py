
import importlib.util
import yaml
import os
from importlib import resources
from typing import Any
from enum import Enum
from dataclasses import asdict, is_dataclass
from pydantic import BaseModel
from loguru import logger

def load_prompt() -> str:
    try:
        with resources.files("structured_output_kit").joinpath("prompt.yaml").open("r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
    except Exception:
        if os.path.exists("prompt.yaml"):
            with open("prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
            return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
        return "Extract information from the given content."

def response_parsing(response: Any) -> Any:
    if isinstance(response, list):
        response = {
            member.value if isinstance(member, Enum) else member for member in response
        }
    elif is_dataclass(response):
        response = asdict(response)
    elif isinstance(response, BaseModel):
        response = response.model_dump(exclude_none=True)
    return response


def convert_schema(schema_name: str):
    """
    주어진 스키마 파일명(확장자 제외 또는 경로)에서 ExtractInfo 클래스를 동적으로 import하여 반환
    """
    # 경로로 들어온 경우: .py로 끝나거나 /가 포함된 경우
    if schema_name.endswith('.py') or '/' in schema_name or '\\' in schema_name:
        file_path = schema_name
        # .py 확장자 제거하여 모듈명 생성
        module_name = os.path.splitext(os.path.basename(file_path))[0]
    else:
        file_path = os.path.join(os.path.dirname(__file__), 'schema', f'{schema_name}.py')
        module_name = schema_name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, 'ExtractInfo')

def get_compatible_frameworks(provider: str):
    """선택한 host에 호환되는 프레임워크 목록을 반환하는 함수"""

    yaml_path = os.path.join(os.path.dirname(__file__), "framework_compatibility.yaml")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            compatibility_data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Framework compatibility file not found: {yaml_path}")
        return {}
    
    compatible_frameworks = []
    
    for framework_name, framework_info in compatibility_data.items():
        if 'providers' in framework_info and provider in framework_info['providers']:
            compatible_frameworks.append(framework_name)
    
    return compatible_frameworks