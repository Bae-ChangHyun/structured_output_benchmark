import os
from typing import Dict, Any
from loguru import logger

from markitdown import MarkItDown
from structured_output_kit.parsing.base import ParsingFramework


class MarkItDownFramework(ParsingFramework):
    """MarkItDown을 사용한 문서 파싱 프레임워크"""
    
    @property
    def name(self) -> str:
        return "markitdown"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]
    
    def parse(self) -> str:
        """MarkItDown을 사용한 문서 파싱"""
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            # MarkItDown 인스턴스 생성
            md = MarkItDown()
            
            # 추가 설정 적용
            if 'llm_client' in self.extra_kwargs:
                md.client = self.extra_kwargs['llm_client']
            
            if 'llm_model' in self.extra_kwargs:
                md.model = self.extra_kwargs['llm_model']
            
            # 문서 변환
            logger.debug(f"MarkItDown으로 파일 변환 시작: {self.file_path}")
            result = md.convert(self.file_path)
            
            if not result or not result.text_content:
                raise ValueError("문서에서 텍스트 내용을 추출할 수 없습니다")
            
            content = result.text_content.strip()
            logger.info(f"MarkItDown으로 문서 파싱 완료: {len(content)} 문자")
            return content
            
        except Exception as e:
            logger.error(f"MarkItDown 파싱 중 오류 발생: {str(e)}")
            raise
