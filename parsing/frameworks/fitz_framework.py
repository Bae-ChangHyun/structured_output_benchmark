from loguru import logger
import fitz  # PyMuPDF
from structured_output_kit.parsing.base import ParsingFramework


class FitzFramework(ParsingFramework):
    """PyMuPDF (Fitz)를 사용한 PDF 파싱 프레임워크"""
    
    @property
    def name(self) -> str:
        return "fitz"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf"]
    
    def parse(self) -> str:
        """PyMuPDF (Fitz)를 사용한 PDF 파싱"""
        
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            text_content = ""
            
            # Open PDF document
            doc = fitz.open(self.file_path)
            
            try:
                # Extract text from all pages
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    try:
                        # 텍스트 추출 옵션 설정
                        flags = self.extra_kwargs.get('flags', 0)
                        if 'get_text_dict' in self.extra_kwargs and self.extra_kwargs['get_text_dict']:
                            # 딕셔너리 형태로 상세 정보와 함께 추출
                            page_dict = page.get_text("dict", flags=flags)
                            page_text = self._extract_text_from_dict(page_dict)
                        else:
                            # 일반 텍스트 추출
                            page_text = page.get_text(flags=flags)
                        
                        text_content += page_text + "\n\n"
                        logger.debug(f"페이지 {page_num + 1} 추출 완료")
                        
                    except Exception as e:
                        logger.warning(f"페이지 {page_num + 1} 텍스트 추출 실패: {e}")
                        continue
            finally:
                doc.close()
            
            if not text_content.strip():
                raise ValueError("PDF에서 텍스트 내용을 추출할 수 없습니다")
            
            logger.info(f"PyMuPDF로 문서 파싱 완료: {len(text_content)} 문자")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PyMuPDF 파싱 중 오류 발생: {str(e)}")
            raise
    
    def _extract_text_from_dict(self, page_dict: dict) -> str:
        """딕셔너리에서 텍스트 추출"""
        text = ""
        for block in page_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text += span.get("text", "")
                    text += "\n"
                text += "\n"
        return text
