import os
import time
import traceback
from tqdm import tqdm
from loguru import logger
from typing import Any, Callable
from abc import ABC, abstractmethod

from structured_output_kit.extraction.utils import response_parsing


def experiment(
    retries: int = 1,
) -> Callable[..., tuple[list[Any], float, list[float]]]:
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
                    break
                except Exception as e:
                    logger.error(f"실험 실행 {i+1}/{retries} Failure: {str(e)}")
                    logger.error(traceback.format_exc())
                    if api_delay_seconds > 0:
                        time.sleep(api_delay_seconds)
                    responses=[f"ERROR:{str(e)}"]
            num_successful = len(responses)
            percent_successful = num_successful / actual_runs
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
    provider: str
    model: str
    base_url: str
    api_key: str
    response_model: Any
    device: str
    api_delay_seconds: float
    extra_kwargs: dict

    def __init__(self, *args, **kwargs) -> None:
        self.prompt = kwargs.get("prompt", "")
        self.provider: str = kwargs.get("provider", "openai")
        self.model = kwargs.get("model", "gpt-3.5-turbo")
        self.base_url = kwargs.get('base_url', self.load_base_url())
        self.api_key = kwargs.get('api_key', self.load_api_key())
        self.device = kwargs.get("device", "cpu")
        self.api_delay_seconds = kwargs.get("api_delay_seconds", 0)
        self.retries = kwargs.get("retries", 3)
        self.timeout = kwargs.get("timeout", 900)
        self.temperature = kwargs.get("temperature", 1.0)
        self.response_model = kwargs.get("response_model", None)
        self.langfuse_trace_id = kwargs.get("langfuse_trace_id", None)
        self.extra_kwargs = {k: v for k, v in kwargs.get("extra_kwargs", {}).items()}
        logger.info(f"{self.__class__.__name__} 초기화 완료")
    
    def load_base_url(self):
        if self.provider == 'ollama':
            return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        elif self.provider == 'openai_compatible':
            return os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://localhost:8000/v1")
        else:
            return ""
    
    def load_api_key(self):
        if self.provider == 'ollama':
            return os.getenv("OLLAMA_API_KEY", "dummy")
        elif self.provider == 'openai_compatible':
            return os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy")
        else:
            return ""

    @abstractmethod
    def run(self, retries: int, expected_response: Any = None, inputs: dict = {}) -> tuple[list[Any], float, list[float]]: 
        pass