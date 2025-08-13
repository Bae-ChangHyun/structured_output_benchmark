
import importlib.util
import yaml
import os
from typing import Dict, List, Any, Optional
from loguru import logger

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

def extract_with_framework(
    framework: str,
    llm_host: str,
    llm_model: str,
    base_url: str,
    content: str,
    prompt: str,
    schema_name: str ,
    retries: int = 1,
    api_delay_seconds: float = 0,
    timeout: int = 900,
    temperature: float = 1.0,
    langfuse_trace_id: Optional[str] = None,
    
) -> tuple[Dict[str, Any], bool, Any]:
    """
    선택된 프레임워크를 사용하여 JSON 추출 수행
    
    Args:
        framework: 사용할 프레임워크 이름
        llm_host: LLM 호스트 (ollama, openai, google, vllm)
        llm_model: 사용할 LLM 모델 이름
        base_url: API 기본 URL
        content: 추출할 텍스트 내용
        prompt: 사용할 프롬프트
        retries: 재시도 횟수
        api_delay_seconds: API 호출 간 지연 시간
    
    Returns:
        tuple[Dict[str, Any], bool, Any]: (추출된 데이터, 성공 여부, 지연시간(단일 값 또는 리스트))
    """
    try:
        response_model = convert_schema(schema_name)
        
        init_kwargs = {
            "llm_model": llm_model,
            "llm_host": llm_host,
            "base_url": base_url,
            "prompt": prompt,
            "response_model": response_model,
            "api_delay_seconds": api_delay_seconds,
            "langfuse_trace_id": langfuse_trace_id,
            "timeout": timeout,
            "temperature": temperature
        }
        
        # 프레임워크 인스턴스 생성
        try:
            # 패키지 내부 상대 임포트로 변경 (wheel 설치 환경에서도 동작)
            from . import factory  # 순환 import 방지용 함수 내부 import
            framework_instance = factory(framework, **init_kwargs)
            logger.debug(f"프레임워크 {framework} 초기화 완료")
        except Exception as e:
            logger.error(f"프레임워크 {framework} 초기화 실패: {str(e)}")
            return {"error": f"프레임워크 초기화 실패: {str(e)}"}, False, 0

        # 입력 데이터 준비
        inputs = {"content": content}
        
        # 프레임워크 실행
        try:
            predictions, percent_successful, latencies = framework_instance.run(
                retries=retries,
                inputs=inputs,
                langfuse_trace_id=langfuse_trace_id
            )
            
            logger.debug(f"프레임워크 실행 완료: 성공률 {percent_successful:.2%}, 응답 수 {len(predictions) if predictions else 0}")
        except Exception as e:
            logger.error(f"프레임워크 실행 중 오류: {str(e)}")
            return {"error": f"프레임워크 실행 실패: {str(e)}"}, False, 0
        
        # 결과 처리
        if predictions and len(predictions) > 0:
            result = predictions[0]  # 첫 번째 성공한 결과 사용
            
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(result, 'model_dump'):
                result = result.model_dump(exclude_none=True)
            elif hasattr(result, 'dict'):
                result = result.dict(exclude_none=True)
            
            logger.debug(f"Framework {framework} 실행 성공: 성공률 {percent_successful:.2%}")
            return result, True, latencies
        else:
            logger.error(f"Framework {framework} 실행 실패: 성공한 응답 없음")
            return {"error": "성공한 응답이 없습니다"}, False, 0
            
    except Exception as e:
        logger.error(f"Framework {framework} 실행 중 예상치 못한 오류 발생: {str(e)}")
        return {"error": str(e)}, False, 0

def get_compatible_frameworks(host: str):
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
        if 'hosts' in framework_info and host in framework_info['hosts']:
            compatible_frameworks.append(framework_name)
    
    return compatible_frameworks