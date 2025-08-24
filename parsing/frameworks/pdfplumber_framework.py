from loguru import logger

import pdfplumber
from structured_output_kit.parsing.base import ParsingFramework


class PDFPlumberFramework(ParsingFramework):
    """PDFPlumber를 사용한 PDF 파싱 프레임워크"""
    
    @property
    def name(self) -> str:
        return "pdfplumber"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf"]
    
    def parse(self) -> str:
        """PDFPlumber를 사용한 PDF 파싱"""
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            text_content = ""
            
            with pdfplumber.open(self.file_path) as pdf:
                # Extract text from all pages
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # 텍스트 추출 설정
                        extract_kwargs = {}
                        
                        # layout 모드 설정
                        if 'layout' in self.extra_kwargs:
                            extract_kwargs['layout'] = self.extra_kwargs['layout']
                        
                        # x_tolerance, y_tolerance 설정
                        if 'x_tolerance' in self.extra_kwargs:
                            extract_kwargs['x_tolerance'] = self.extra_kwargs['x_tolerance']
                        if 'y_tolerance' in self.extra_kwargs:
                            extract_kwargs['y_tolerance'] = self.extra_kwargs['y_tolerance']
                        
                        # 테이블 추출 여부
                        extract_tables = self.extra_kwargs.get('extract_tables', False)
                        
                        # 텍스트 추출
                        if extract_kwargs:
                            page_text = page.extract_text(**extract_kwargs) or ""
                        else:
                            page_text = page.extract_text() or ""
                        
                        text_content += page_text + "\n\n"
                        
                        # 테이블 추출 (옵션)
                        if extract_tables:
                            tables = page.extract_tables()
                            for table_idx, table in enumerate(tables):
                                text_content += f"\n[테이블 {table_idx + 1}]\n"
                                for row in table:
                                    if row:
                                        text_content += " | ".join(cell or "" for cell in row) + "\n"
                                text_content += "\n"
                        
                        logger.debug(f"페이지 {page_num} 추출 완료")
                        
                    except Exception as e:
                        logger.warning(f"페이지 {page_num} 텍스트 추출 실패: {e}")
                        continue
            
            if not text_content.strip():
                raise ValueError("PDF에서 텍스트 내용을 추출할 수 없습니다")
            
            logger.info(f"PDFPlumber로 문서 파싱 완료: {len(text_content)} 문자")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PDFPlumber 파싱 중 오류 발생: {str(e)}")
            raise
