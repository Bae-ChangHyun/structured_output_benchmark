import os
import json
import numpy as np
import pandas as pd
from typing import Any, Dict, Optional
from langfuse import observe, get_client
from typing import get_origin, get_args, Union
from extraction_module.utils import get_compatible_frameworks, convert_schema


def select_host_by_choice(choice: int):
    """선택된 번호에 따라 호스트 정보를 반환합니다 (API용)"""
    if choice == 1:
        return {
            "host": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODELS", "gpt-4o-mini"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    elif choice == 2:
        return {
            "host": "anthropic",
            "base_url": "https://api.anthropic.com/v1",
            "model": os.getenv("ANTHROPIC_MODELS", "claude-3-sonnet-20240229"),
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
    elif choice == 3:
        return {
            "host": "vllm",
            "base_url": os.getenv("VLLM_BASEURL"),
            "model": os.getenv("VLLM_MODELS", "openai/gpt-oss-120b"),
            "api_key": "dummy",
        }
    elif choice == 4:
        return {
            "host": "ollama",
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434/v1"),
            "model": os.getenv("OLLAMA_MODELS", "llama3.1:8b"),
            "api_key": "dummy",
        }
    elif choice == 5:
        return {
            "host": "google",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": os.getenv("GOOGLE_MODELS", "gemini-1.5-flash"),
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
    else:
        raise ValueError(f"Invalid host choice: {choice}")

def select_framework_by_choice(host: str, choice: int):
    """선택된 번호에 따라 프레임워크를 반환합니다 (API용)"""
    compatible_frameworks = get_compatible_frameworks(host)
    
    if not compatible_frameworks:
        raise ValueError(f"No compatible frameworks for host '{host}'")
    
    if choice < 1 or choice > len(compatible_frameworks):
        raise ValueError(f"Invalid framework choice: {choice}")
    
    return compatible_frameworks[choice - 1]

def get_available_hosts():
    """사용 가능한 호스트 목록을 반환합니다"""
    return [
        {"id": 1, "name": "openai", "description": "OpenAI API"},
        {"id": 2, "name": "anthropic", "description": "Anthropic API"},
        {"id": 3, "name": "vllm", "description": "vLLM 서버"},
        {"id": 4, "name": "ollama", "description": "Ollama 로컬 서버"},
        {"id": 5, "name": "google", "description": "Google Gemini API"}
    ]

# host 선택 메뉴 함수
def select_host():
    print("=== Host 선택 ===")
    print("1. openai")
    print("2. anthropic")
    print("3. vllm")
    print("4. ollama")
    print("5. google")
    choice = input("번호를 입력하세요 (1/2/3/4/5): ").strip()
    if choice == "1":
        return {
            "host": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODELS", "gpt-4.1-nano"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    elif choice == "2":
        return {
            "host": "anthropic",
            "base_url": "https://api.anthropic.com/v1",
            "model": os.getenv("ANTHROPIC_MODELS", "claude-sonnet-4-20250514"),
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
    elif choice == "3":
        return {
            "host": "vllm",
            "base_url": os.getenv("VLLM_BASEURL"),
            "model": os.getenv("VLLM_MODELS", "openai/gpt-oss-120b"),
            "api_key": "dummy",
        }
    elif choice == "4":
        return {
            "host": "ollama",
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434/v1"),
            "model": os.getenv("OLLAMA_MODELS", "llama3.1:8b"),
            "api_key": "dummy",
        }
    elif choice == "5":
        return {
            "host": "google",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": os.getenv("GOOGLE_MODELS", "gemini-1.5-flash"),
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
    else:
        print("잘못된 입력입니다. 기본값(vllm)으로 진행합니다.")
        raise ValueError("Invalid host selection")
    
def select_framework(host):
    """host에 따라 호환되는 프레임워크를 선택하는 함수"""

    compatible_frameworks = get_compatible_frameworks(host)
    
    if not compatible_frameworks:
        print(f"선택한 host '{host}'에 호환되는 프레임워크가 없습니다.")
        return None
    
    print(f"\n=== {host}에 호환되는 프레임워크 목록 ===")
    for i, framework in enumerate(compatible_frameworks, 1):
        print(f"{i}. {framework}")
    
    while True:
        try:
            choice = input(f"번호를 입력하세요 (1-{len(compatible_frameworks)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(compatible_frameworks):
                return compatible_frameworks[choice_idx]
            else:
                print("잘못된 번호입니다. 다시 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
            
def record_extraction(
    log_filename, host, model, prompt, framework,
    success, latency, langfuse_url,
    note, csv_path="result/extraction_result.csv", result_json_path=None
):
    record = {
        "log_filename": log_filename,
        "host": host,
        "model": model,
        "prompt": prompt,
        "framework": framework,
        "success": success,
        "latency": latency,
        "langfuse_url": langfuse_url,
        "note": note,
        "result_json_path": result_json_path
    }
    if os.path.isfile(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        import pandas as pd
        df = pd.DataFrame([record])
    df.to_csv(csv_path, index=False)
    
def record_evaluation(
    pred_json_path,
    gt_json_path,
    embedding_model,
    embedding_host,
    schema_name,
    criteria_path,
    overall_score,
    structure_score,
    content_score,
    eval_result_path,
    note=""
):
    csv_path = "result/evaluation_result.csv"
    record = {
        "pred_json_path": pred_json_path,
        "gt_json_path": gt_json_path,
        "embedding_model": embedding_model,
        "embedding_host": embedding_host,
        "schema_name": schema_name,
        "criteria_path": criteria_path,
        "overall_score": overall_score,
        "structure_score": structure_score,
        "content_score": content_score,
        "eval_result_path": eval_result_path,
        "note": note
    }
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    df.to_csv(csv_path, index=False)
    
def box_line(text, box_width=48):
    # 너무 길면 잘라내기
    trimmed = text[:box_width-2]
    return f" {trimmed:<{box_width-2}}"

def log_response(logger, response, latency, prefix=""):
    if latency == -1:
        logger.error(f"{prefix}Response failed: {response}")
    else:
        logger.success(f"{prefix}Response completed | Latency: {latency:.3f}s | Content: {response}")

def final_report(exp_info, logger, latencies, langfuse_trace_url):
        logger.info("-"*50)
        logger.success("[Final Report]")
        for i in range(2, len(exp_info)-2):
            logger.success(exp_info[i])
        if not isinstance(latencies, list):
            latencies = [latencies]
        if latencies and latencies[0] != -1:
            logger.success(f"Latency: {latencies[0]:.3f}s")
        else:
            logger.error("Request failed. Latency not available.")

        langfuse = get_client()
        logger.success(f"Request Langfuse Trace URLs: {langfuse_trace_url}")


def load_extract_info(schema_name: str):
    """
    스키마 이름에서 ExtractInfo 클래스를 로드합니다.
    
    Args:
        schema_name: 스키마 파일명 (확장자 제외)
        
    Returns:
        ExtractInfo 클래스
    """
    return convert_schema(schema_name)


def load_field_eval_criteria(schema_name: str, criteria_path = f"evaluation_module/criteria/criteria.json") -> Optional[Dict[str, str]]:
    """
    스키마에 대한 필드 평가 기준을 로드하거나 생성합니다.
    
    Args:
        schema_name: 스키마 파일명 (확장자 제외)
        
    Returns:
        필드별 평가 기준 딕셔너리 (field_name: 'exact' or 'embedding')
    """
    
    # 기존 criteria 파일이 있으면 로드
    if os.path.exists(criteria_path):
        try:
            with open(criteria_path, 'r', encoding='utf-8') as f:
                criteria = json.load(f)
            print(f"기존 평가 기준을 로드했습니다: {criteria_path}")
            return criteria
        except Exception as e:
            print(f"평가 기준 로드 중 오류 발생: {e}")
    
    # 기본 criteria 생성
    try:
        ExtractInfo = load_extract_info(schema_name)
        criteria = generate_default_criteria(ExtractInfo)
        
        # 생성된 criteria를 파일로 저장
        with open(criteria_path, 'w', encoding='utf-8') as f:
            json.dump(criteria, f, ensure_ascii=False, indent=2)
        print(f"기본 평가 기준을 생성하고 저장했습니다: {criteria_path}")
        
        return criteria
    except Exception as e:
        print(f"기본 평가 기준 생성 중 오류 발생: {e}")
        return {}


def generate_default_criteria(schema_class) -> Dict[str, str]:
    """
    스키마 클래스에서 기본 평가 기준을 생성합니다.
    
    Args:
        schema_class: Pydantic BaseModel 클래스
        
    Returns:
        필드별 기본 평가 기준
    """    
    criteria = {}
    
    for field_name, field_info in schema_class.model_fields.items():
        field_type = field_info.annotation
        
        # List 타입 처리
        if get_origin(field_type) is list:
            inner_type = get_args(field_type)[0]
            if hasattr(inner_type, 'model_fields'):
                # List 내부 객체의 필드들
                for sub_field_name in inner_type.model_fields:
                    full_path = f"{field_name}.{sub_field_name}"
                    criteria[full_path] = get_default_criteria_for_type(inner_type.model_fields[sub_field_name].annotation)
            else:
                criteria[field_name] = get_default_criteria_for_type(inner_type)
        
        # Optional 타입 처리
        elif get_origin(field_type) is Union and type(None) in get_args(field_type):
            # NoneType이 아닌 첫 번째 타입 사용
            non_none_types = [t for t in get_args(field_type) if t is not type(None)]
            if non_none_types:
                inner_type = non_none_types[0]
                if hasattr(inner_type, 'model_fields'):
                    # 중첩 객체의 필드들
                    for sub_field_name in inner_type.model_fields:
                        full_path = f"{field_name}.{sub_field_name}"
                        criteria[full_path] = get_default_criteria_for_type(inner_type.model_fields[sub_field_name].annotation)
                else:
                    criteria[field_name] = get_default_criteria_for_type(inner_type)
        
        # 일반 타입
        else:
            if hasattr(field_type, 'model_fields'):
                # 중첩 객체의 필드들
                for sub_field_name in field_type.model_fields:
                    full_path = f"{field_name}.{sub_field_name}"
                    criteria[full_path] = get_default_criteria_for_type(field_type.model_fields[sub_field_name].annotation)
            else:
                criteria[field_name] = get_default_criteria_for_type(field_type)
    
    return criteria


def get_default_criteria_for_type(field_type) -> str:
    """
    필드 타입에 따른 기본 평가 기준을 반환합니다.
    
    Args:
        field_type: 필드의 타입
        
    Returns:
        'exact' 또는 'embedding'
    """
    # 숫자, 불린 타입은 정확한 일치
    if field_type in [int, float, bool]:
        return 'exact'
    
    # 문자열은 임베딩 유사도
    if field_type == str:
        return 'embedding'
    
    # 기본값은 임베딩 유사도
    return 'embedding'

def convert_np(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)