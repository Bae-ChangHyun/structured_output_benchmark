"""
Docling Framework for document parsing
"""

import os
from typing import Dict, Any, Optional
from loguru import logger


from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
    smoldocling_vlm_conversion_options,
    granite_vision_vlm_ollama_conversion_options,
    AcceleratorOptions,
    PdfPipelineOptions,
    TesseractOcrOptions,
    TesseractCliOcrOptions,
    EasyOcrOptions,
    RapidOcrOptions
)
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.base_models import InputFormat
from pydantic import AnyUrl


from structured_output_kit.parsing.base import ParsingFramework
from structured_output_kit.parsing.preprocessor import preprocess_vlm_output


class DoclingFramework(ParsingFramework):
    """Docling을 사용한 문서 파싱 프레임워크"""
    
    @property
    def name(self) -> str:
        return "docling"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]
    
    def parse(self) -> str:
        """Docling을 사용한 문서 파싱"""
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            # 파이프라인 설정
            pipeline_class = self.extra_kwargs.get('pipeline_class', 'default')
            backend_name = self.extra_kwargs.get('backend', 'Docling')
            use_gpu = self.extra_kwargs.get('use_gpu', False)
            image_extract = self.extra_kwargs.get('image_extract', False)
            
            # 파이프라인 및 백엔드 설정
            if pipeline_class == 'vlm':
                pipeline_cls = VlmPipeline
                pipeline_options = VlmPipelineOptions()
                self._configure_vlm_pipeline(pipeline_options)
            else:
                pipeline_cls = StandardPdfPipeline
                pipeline_options = PdfPipelineOptions()
                self._configure_standard_pipeline(pipeline_options)
            
            # GPU 설정
            if use_gpu:
                pipeline_options.accelerator_options = AcceleratorOptions(device='cuda')
            
            # 백엔드 설정
            backend_cls = DoclingParseV4DocumentBackend if backend_name == 'Docling' else PyPdfiumDocumentBackend
            
            # DocumentConverter 생성
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=pipeline_cls,
                        pipeline_options=pipeline_options,
                        backend=backend_cls
                    ),
                    InputFormat.IMAGE: ImageFormatOption(
                        pipeline_cls=pipeline_cls,
                        pipeline_options=pipeline_options
                    )
                }
            )
            
            # 문서 변환
            logger.debug(f"Docling으로 파일 변환 시작: {self.file_path}")
            result = converter.convert(self.file_path)
            
            if not result or not result.document:
                raise ValueError("문서에서 내용을 추출할 수 없습니다")
            
            # 텍스트 추출
            content = result.document.export_to_markdown()
            
            if not content.strip():
                raise ValueError("문서에서 텍스트 내용을 추출할 수 없습니다")
            
            # VLM 파이프라인을 사용한 경우 전처리 적용
            if pipeline_class == 'vlm' and self.host_info and self.host_info.model:
                content = preprocess_vlm_output(content, self.host_info.model)
            
            logger.info(f"Docling으로 문서 파싱 완료: {len(content)} 문자")
            return content.strip()
            
        except Exception as e:
            logger.error(f"Docling 파싱 중 오류 발생: {str(e)}")
            raise
    
    def _configure_standard_pipeline(self, pipeline_options):
        """표준 파이프라인 설정"""
        use_ocr = self.extra_kwargs.get('use_ocr', True)
        
        if use_ocr:
            ocr_backend = self.extra_kwargs.get('ocr_backend', 'easyocr')
            ocr_lang = self.extra_kwargs.get('ocr_lang', 'ko')
            
            if ocr_backend == 'easyocr':
                ocr_confidence = self.extra_kwargs.get('ocr_confidence', 0.5)
                pipeline_options.ocr_options = EasyOcrOptions(
                    lang=[ocr_lang],
                    confidence_threshold=ocr_confidence
                )
            elif ocr_backend == 'tesseract':
                pipeline_options.ocr_options = TesseractOcrOptions(lang=ocr_lang)
            elif ocr_backend == 'tesseract_cli':
                pipeline_options.ocr_options = TesseractCliOcrOptions(lang=ocr_lang)
            elif ocr_backend == 'rapidocr':
                pipeline_options.ocr_options = RapidOcrOptions()
    
    def _configure_vlm_pipeline(self, pipeline_options):
        """VLM 파이프라인 설정"""
        if not self.host_info:
            raise ValueError("VLM 사용시 host_info가 필요합니다")
        
        vlm_host = self.host_info.provider
        vlm_model = self.host_info.model
        
        if vlm_host == "ollama":
            pipeline_options.enable_remote_services = True
            pipeline_options.vlm_options = granite_vision_vlm_ollama_conversion_options
            pipeline_options.vlm_options.url = AnyUrl(f"{self.host_info.base_url}/chat/completions")
            pipeline_options.vlm_options.params = {"model": vlm_model}
            pipeline_options.vlm_options.prompt = self.prompt or "Convert this page to docling"
            pipeline_options.vlm_options.scale = self.extra_kwargs.get('scale', 1.0)
        elif vlm_host == "huggingface":
            pipeline_options.vlm_options = smoldocling_vlm_conversion_options
            pipeline_options.vlm_options.repo_id = vlm_model
            pipeline_options.vlm_options.prompt = self.prompt or "Convert this page to docling"
            pipeline_options.vlm_options.response_format = "markdown"
            pipeline_options.vlm_options.inference_framework = "transformers"
        else:
            raise ValueError(f"지원하지 않는 VLM 호스트: {vlm_host}")
