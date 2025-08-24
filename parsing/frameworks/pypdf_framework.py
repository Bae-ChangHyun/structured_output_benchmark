from loguru import logger
import pypdf
from structured_output_kit.parsing.base import ParsingFramework


class PyPDFFramework(ParsingFramework):
    """PyPDF를 사용한 PDF 파싱 프레임워크"""
    
    @property
    def name(self) -> str:
        return "pypdf"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf"]
    
    def parse(self) -> str:
        """PyPDF를 사용한 PDF 파싱"""
        
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            text_content = ""
            
            with open(self.file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # extraction_mode 설정
                extraction_mode = self.extra_kwargs.get('extraction_mode', 'layout')
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        if hasattr(page, 'extract_text'):
                            if extraction_mode in ['layout', 'plain']:
                                page_text = page.extract_text(extraction_mode=extraction_mode)
                            else:
                                page_text = page.extract_text()
                        else:
                            page_text = page.extract_text()
                        
                        text_content += page_text + "\n\n"
                        logger.debug(f"페이지 {page_num} 추출 완료")
                        
                    except Exception as e:
                        logger.warning(f"페이지 {page_num} 텍스트 추출 실패: {e}")
                        continue
            
            if not text_content.strip():
                raise ValueError("PDF에서 텍스트 내용을 추출할 수 없습니다")
            
            logger.info(f"PyPDF로 문서 파싱 완료: {len(text_content)} 문자")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PyPDF 파싱 중 오류 발생: {str(e)}")
            raise
