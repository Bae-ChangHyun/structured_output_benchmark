"""
Parsing 모듈

PDF 및 이미지 파일에서 텍스트를 추출하는 다양한 프레임워크를 제공합니다.

지원 프레임워크:
- docling: 고급 문서 파싱 및 OCR/VLM 지원
- pypdf: 기본 PDF 텍스트 추출
- fitz: PyMuPDF를 사용한 빠른 PDF 파싱
- pdfplumber: 정확한 PDF 텍스트 추출
- markitdown: 다양한 문서 형식 마크다운 변환
- vlm: Vision Language Model 기반 파싱
"""

from structured_output_kit.parsing.core import run_parsing_core
from structured_output_kit.parsing.base import ParsingFramework
from structured_output_kit.parsing.factory import factory
from structured_output_kit.parsing.preprocessor import (
    DotsOCRPreprocessor, 
    NanonetsPreprocessor, 
    preprocess_vlm_output,
    get_preprocessor
)

__all__ = [
    "run_parsing_core", 
    "ParsingFramework", 
    "factory",
    "DotsOCRPreprocessor",
    "NanonetsPreprocessor", 
    "preprocess_vlm_output",
    "get_preprocessor"
]
