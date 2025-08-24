"""
파싱 핵심 실행 로직
"""

import os
import uuid
from datetime import datetime
from loguru import logger
from typing import Optional


from structured_output_kit.utils.types import ParsingRequest, ParsingResult
from structured_output_kit.utils.logging import setup_logger

from structured_output_kit.parsing.factory import factory
from structured_output_kit.parsing.utils import save_parsing_result, record_parsing, get_file_info


def run_parsing_core(req: ParsingRequest) -> ParsingResult:
    """파싱 핵심 실행 함수"""
    
    # 로거 설정
    output_dir, log_filename = setup_logger(task="parsing", output_dir=req.output_dir)
    
    logger.info("파싱 프로세스 시작")
    logger.info(f"파일: {req.file_path}")
    logger.info(f"프레임워크: {req.framework}")
    
    try:
        # 파일 정보 확인
        file_info = get_file_info(req.file_path)
        if not file_info:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {req.file_path}")
        
        logger.info(f"파일 정보: {file_info['file_name']} ({file_info['file_size']} bytes)")
        
        # 프레임워크 인스턴스 생성
        framework_instance = factory(
            framework=req.framework,
            file_path=req.file_path,
            extra_kwargs=req.extra_kwargs,
            host_info=req.host_info,
            prompt=req.prompt
        )
        
        # 파싱 실행
        logger.info(f"{req.framework} 프레임워크로 파싱 시작")
        start_time = datetime.now()
        
        content, success, latency = framework_instance.run(retries=1)
        
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        
        if success:
            logger.info(f"파싱 성공: {len(content)} 문자 추출 (소요시간: {elapsed_time:.2f}초)")
            
            # 결과 저장
            result_txt_path = None
            if req.save:
                result_txt_path = save_parsing_result(
                    content=content,
                    file_path=req.file_path,
                    framework=req.framework,
                    output_dir=output_dir,
                    extra_kwargs=req.extra_kwargs
                )
                logger.info(f"결과 저장 완료: {result_txt_path}")
            
            # 로그 기록
            record_parsing(
                file_name=file_info['file_name'],
                framework=req.framework,
                elapsed_time=elapsed_time,
                success=True,
                output_dir=output_dir,
                extra_kwargs=req.extra_kwargs
            )
            
            return ParsingResult(
                success=True,
                content=content,
                framework=req.framework,
                file_path=req.file_path,
                output_dir=output_dir,
                result_txt_path=result_txt_path
            )
        else:
            logger.error(f"파싱 실패: {content}")
            
            # 실패 로그 기록
            record_parsing(
                file_name=file_info['file_name'],
                framework=req.framework,
                elapsed_time=elapsed_time,
                success=False,
                output_dir=output_dir,
                extra_kwargs=req.extra_kwargs
            )
            
            return ParsingResult(
                success=False,
                content=content,  # 오류 메시지
                framework=req.framework,
                file_path=req.file_path,
                output_dir=output_dir
            )
            
    except Exception as e:
        error_msg = f"파싱 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        
        # 오류 로그 기록
        file_name = os.path.basename(req.file_path) if os.path.exists(req.file_path) else "unknown"
        record_parsing(
            file_name=file_name,
            framework=req.framework,
            elapsed_time=0,
            success=False,
            output_dir=output_dir,
            extra_kwargs=req.extra_kwargs
        )
        
        return ParsingResult(
            success=False,
            content=error_msg,
            framework=req.framework,
            file_path=req.file_path,
            output_dir=output_dir
        )
