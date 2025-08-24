"""
파싱 프레임워크 모음

각 프레임워크별 구현체를 제공합니다.
"""

from structured_output_kit.parsing.frameworks.docling_framework import DoclingFramework
from structured_output_kit.parsing.frameworks.pypdf_framework import PyPDFFramework
from structured_output_kit.parsing.frameworks.fitz_framework import FitzFramework
from structured_output_kit.parsing.frameworks.pdfplumber_framework import PDFPlumberFramework
from structured_output_kit.parsing.frameworks.markitdown_framework import MarkItDownFramework
from structured_output_kit.parsing.frameworks.vlm_framework import VLMFramework

__all__ = [
    "DoclingFramework",
    "PyPDFFramework", 
    "FitzFramework",
    "PDFPlumberFramework",
    "MarkItDownFramework",
    "VLMFramework"
]
