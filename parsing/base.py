from __future__ import annotations

import os
import time
import traceback
from tqdm import tqdm
from loguru import logger
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod


from structured_output_kit.utils.types import HostInfo


def parsing_experiment(
    retries: int = 1,
) -> Callable[..., tuple[str, bool, float]]:
    """파싱 실험 데코레이터"""
    def experiment_decorator(func):
        def wrapper(*args, **kwargs):
            for i in tqdm(range(retries), leave=False, desc="Parsing"):
                try:
                    start_time = time.time()
                    logger.debug(f"파싱 실행 {i+1}/{retries} 시작")
                    content = func(*args, **kwargs)
                    end_time = time.time()
                    
                    if content and isinstance(content, str):
                        logger.debug(f"파싱 실행 {i+1}/{retries} 성공 (시간: {end_time - start_time:.2f}초)")
                        return content, True, end_time - start_time
                    else:
                        logger.warning(f"파싱 실행 {i+1}/{retries}: 빈 내용 반환")
                        
                except Exception as e:
                    logger.error(f"파싱 실행 {i+1}/{retries} 실패: {str(e)}")
                    logger.error(traceback.format_exc())
                    if i == retries - 1:  # 마지막 시도
                        return f"ERROR: {str(e)}", False, 0
                        
            return "ERROR: 모든 재시도 실패", False, 0
        return wrapper
    return experiment_decorator


class ParsingFramework(ABC):
    """파싱 프레임워크 추상 기본 클래스"""
    
    def __init__(
        self,
        file_path: str,
        extra_kwargs: Optional[Dict[str, Any]] = None,
        host_info: Optional[HostInfo] = None,
        prompt: Optional[str] = None,
        **kwargs
    ):
        self.file_path = file_path
        self.extra_kwargs = extra_kwargs or {}
        self.host_info = host_info
        self.prompt = prompt
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        # 파일 확장자 확인
        self.file_extension = os.path.splitext(file_path)[1].lower()
        if self.file_extension not in self.supported_extensions():
            raise ValueError(f"지원하지 않는 파일 형식입니다: {self.file_extension}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """프레임워크 이름"""
        pass
    
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """지원하는 파일 확장자 목록"""
        pass
    
    @parsing_experiment(retries=1)
    def run(self, retries: int = 1, **kwargs) -> str:
        """파싱 실행"""
        logger.debug(f"{self.name} 프레임워크로 파싱 시작: {self.file_path}")
        return self.parse()
    
    @abstractmethod
    def parse(self) -> str:
        """실제 파싱 로직 구현"""
        pass
    
    def validate_file(self) -> bool:
        """파일 유효성 검사"""
        if not os.path.exists(self.file_path):
            return False
        if os.path.getsize(self.file_path) == 0:
            return False
        return True
