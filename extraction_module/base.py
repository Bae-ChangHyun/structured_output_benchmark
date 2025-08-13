import os
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger

from pydantic import BaseModel
from tqdm import tqdm
import traceback

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

def experiment(
    retries: int = 1,
) -> Callable[..., tuple[list[Any], float, list[float]]]:
    """Decorator to run an LLM call function multiple times and return the responses

    Args:
        retries (int): Number of times to run the function

    Returns:
        Callable[..., Tuple[List[Any], float, List[float]]]: A function that returns a list of outputs from the function runs, percent of successful runs, and list of latencies for each call.
    """

    def experiment_decorator(func):
        def wrapper(*args, **kwargs):
            
            api_delay_seconds = getattr(args[0], "api_delay_seconds", 0)

            responses, latencies = [], []
            actual_runs = 0
        
            for i in tqdm(range(retries), leave=False, desc="Extracting"):
                actual_runs = i + 1
                try:
                    start_time = time.time()
                    logger.debug(f"실험 실행 {i+1}/{retries} 시작")
                    response = func(*args, **kwargs)
                    end_time = time.time()
                    
                    logger.debug(f"Response: {str(response)[:200]}...")
                    response = response_parsing(response)

                    if "classes" in response:
                        response = response_parsing(response["classes"])

                    responses.append(response)
                    latencies.append(end_time - start_time)
                    logger.debug(f"실험 실행 {i+1}/{retries} Success (Time: {end_time - start_time:.2f}초)")
                    break  # 성공하면 즉시 중단
                except Exception as e:
                    logger.error(f"실험 실행 {i+1}/{retries} Failure: {str(e)}")
                    logger.error(traceback.format_exc())
                    if api_delay_seconds > 0:
                        time.sleep(api_delay_seconds)

            num_successful = len(responses)
            percent_successful = num_successful / actual_runs  # 실제 시도 횟수로 계산
            logger.debug(f"총 {actual_runs}회 시도 중 {num_successful}회 성공 (성공률: {percent_successful:.2%})")
            
            return (
                responses,
                percent_successful,
                latencies,
            )

        return wrapper

    return experiment_decorator


class BaseFramework(ABC):
    prompt: str
    llm_model: str
    llm_host: str
    base_url: str
    response_model: Any
    device: str
    api_delay_seconds: float  # API 요청 사이의 지연 시간(초)
    timeout: float
    temperature: Optional[float] = None 

    def __init__(self, *args, **kwargs) -> None:
        self.prompt = kwargs.get("prompt", "")
        self.llm_model = kwargs.get("llm_model", "gpt-3.5-turbo")
        self.llm_host = kwargs.get("llm_host", "openai")
        self.base_url = kwargs.get("base_url", os.environ.get("VLLM_BASEURL", ""))
        self.device = kwargs.get("device", "cpu")
        self.api_delay_seconds = kwargs.get("api_delay_seconds", 0)  # API 지연 시간 설정
        self.retries = kwargs.get("retries", 3)  # 기본 재시도 횟수 설정
        self.timeout = kwargs.get("timeout", 900)  # LLM 응답 시간 제한 (초)
        self.temperature = kwargs.get("temperature", 1.0)
        self.response_model = kwargs.get("response_model", None)
        self.langfuse_trace_id = kwargs.get("langfuse_trace_id", None)

        logger.info(f"Framework {self.__class__.__name__} 초기화 완료")

    @abstractmethod
    def run(self, retries: int, expected_response: Any = None, inputs: dict = {}) -> tuple[list[Any], float, list[float]]: 
        """
        프레임워크를 실행하여 결과를 반환합니다.
        
        Args:
            retries: 재시도 횟수
            expected_response: 예상 응답 (선택사항)
            inputs: 입력 데이터
            
        Returns:
            tuple: (응답 리스트, 성공률, 지연 시간 리스트)
        """
        pass
