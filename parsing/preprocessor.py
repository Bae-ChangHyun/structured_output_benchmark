"""
Parsing 전처리 모듈
VLM 모델에 따른 마크다운 전처리 기능 제공
"""

import re
from typing import Optional
from loguru import logger
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class NanonetsPreprocessor:
    """Nanonets VLM 출력을 위한 전처리기"""
    
    @staticmethod
    def process_tags(content: str) -> str:
        """
        HTML-like 태그를 escaped HTML entities로 변환
        
        Args:
            content (str): HTML-like 태그가 포함된 콘텐츠
            
        Returns:
            str: escaped HTML 태그가 적용된 콘텐츠
        """
        content = content.replace("<img>", "&lt;img&gt;")
        content = content.replace("</img>", "&lt;/img&gt;")
        content = content.replace("<watermark>", "&lt;watermark&gt;")
        content = content.replace("</watermark>", "&lt;/watermark&gt;")
        content = content.replace("<page_number>", "&lt;page_number&gt;")
        content = content.replace("</page_number>", "&lt;/page_number&gt;")
        content = content.replace("<signature>", "&lt;signature&gt;")
        content = content.replace("</signature>", "&lt;/signature&gt;")
        
        return content
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        텍스트 정리 및 정규화
        
        Args:
            text (str): 정리할 텍스트
            
        Returns:
            str: 정리된 텍스트
        """
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def preprocess(content: str, json_data: dict, image_path: str = None) -> str:
        """
        Nanonets 모델 출력 전처리
        
        Args:
            content (str): 원본 콘텐츠
            
        Returns:
            str: 전처리된 마크다운 콘텐츠
        """
        content = NanonetsPreprocessor.process_tags(content)
        content = NanonetsPreprocessor.clean_text(content)
        return content


class DotsOCRPreprocessor:
    """DotsOCR VLM 출력을 위한 전처리기"""
    
    @staticmethod
    def PILimage_to_base64(image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string for markdown embedding.
        
        Args:
            image: PIL Image 객체
            
        Returns:
            str: 마크다운 임베딩용 data URL 형식의 base64 문자열
        """
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def has_latex_markdown(text: str) -> bool:
        """
        LaTeX 마크다운 패턴 포함 여부 확인
        
        Args:
            text (str): 확인할 문자열
            
        Returns:
            bool: LaTeX 마크다운이 발견되면 True, 아니면 False
        """
        if not isinstance(text, str):
            return False
        
        latex_patterns = [
            r'\$\$.*?\$\$',           # Block-level math formula $$...$$
            r'\$[^$\n]+?\$',          # Inline math formula $...$
            r'\\begin\{.*?\}.*?\\end\{.*?\}',  # LaTeX environment
            r'\\[a-zA-Z]+\{.*?\}',    # LaTeX command \command{...}
            r'\\[a-zA-Z]+',           # Simple LaTeX command
            r'\\\[.*?\\\]',           # Display math formula \[...\]
            r'\\\(.*?\\\)',           # Inline math formula \(...\)
        ]
        
        for pattern in latex_patterns:
            if re.search(pattern, text, re.DOTALL):
                return True
        
        return False
    
    @staticmethod
    def clean_latex_preamble(latex_text: str) -> str:
        """
        LaTeX 서문 명령어 제거
        
        Args:
            latex_text (str): 원본 LaTeX 텍스트
            
        Returns:
            str: 서문이 제거된 LaTeX 텍스트
        """
        patterns = [
            r'\\documentclass\{[^}]+\}',
            r'\\usepackage\{[^}]+\}',
            r'\\usepackage\[[^\]]*\]\{[^}]+\}',
            r'\\begin\{document\}',
            r'\\end\{document\}',
        ]
        
        cleaned_text = latex_text
        for pattern in patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text
    
    @staticmethod
    def get_formula_in_markdown(text: str) -> str:
        """
        수식을 표준 마크다운 블록으로 포맷팅
        
        Args:
            text (str): 수식이 포함될 수 있는 입력 문자열
            
        Returns:
            str: 마크다운 렌더링 준비된 포맷팅된 문자열
        """
        text = text.strip()
        
        # 이미 $$로 둘러싸인 경우
        if text.startswith('$$') and text.endswith('$$'):
            text_new = text[2:-2].strip()
            if '$' not in text_new:
                return f"$$\n{text_new}\n$$"
            else:
                return text
        
        # \[...\] 형식을 $$...$$ 로 변환
        if text.startswith('\\[') and text.endswith('\\]'):
            inner_content = text[2:-2].strip()
            return f"$$\n{inner_content}\n$$"
        
        # \[ \]가 포함된 경우
        if re.findall(r'.*\\\[.*\\\].*', text):
            return text
        
        # 인라인 수식 ($...$) 처리
        pattern = r'\$([^$]+)\$'
        matches = re.findall(pattern, text)
        if matches:
            return text
        
        # LaTeX 마크다운이 없는 경우 그대로 반환
        if not DotsOCRPreprocessor.has_latex_markdown(text):
            return text
        
        # 불필요한 LaTeX 포맷팅 처리
        if 'usepackage' in text:
            text = DotsOCRPreprocessor.clean_latex_preamble(text)
        
        if text.startswith('`') and text.endswith('`'):
            text = text[1:-1]
        
        # $$ 블록으로 감싸기
        text = f"$$\n{text}\n$$"
        return text
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        마크다운 출력을 위한 텍스트 정리 및 정규화
        
        Args:
            text (str): 정리할 입력 텍스트
            
        Returns:
            str: 정리되고 정규화된 텍스트
        """
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def layoutjson2md(image: Image.Image, cells: list, text_key: str = 'text', no_page_hf: bool = False) -> str:
        """
        Converts a layout JSON format to Markdown.
        In the layout JSON, formulas are LaTeX, tables are HTML, and text is Markdown.
        
        Args:
            image: A PIL Image object.
            cells: A list of dictionaries, each representing a layout cell.
            text_key: The key for the text field in the cell dictionary.
            no_page_hf: If True, skips page headers and footers.
            
        Returns:
            str: The text in Markdown format.
        """
        text_items = []
        for i, cell in enumerate(cells):
            x1, y1, x2, y2 = [int(coord) for coord in cell['bbox']]
            text = cell.get(text_key, "")
            if no_page_hf and cell.get('category') in ['Page-header', 'Page-footer']:
                continue
            if cell.get('category') == 'Picture':
                image_crop = image.crop((x1, y1, x2, y2))
                image_base64 = DotsOCRPreprocessor.PILimage_to_base64(image_crop)
                text_items.append(f"![]({image_base64})")
            elif cell.get('category') == 'Formula':
                text_items.append(DotsOCRPreprocessor.get_formula_in_markdown(text))
            else:
                text = DotsOCRPreprocessor.clean_text(text)
                text_items.append(f"{text}")
        markdown_text = '\n\n'.join(text_items)
        return markdown_text
    
    @staticmethod
    def preprocess(content: str, json_data: dict, image_path: str = None) -> str:
        """
        DotsOCR 모델 출력 전처리
        
        Args:
            content (str): 원본 콘텐츠
            
        Returns:
            str: 전처리된 마크다운 콘텐츠
        """
        # 수식 처리
        # 텍스트 정리
        img = Image.open(image_path).convert('RGB')
        preprocessed_content = DotsOCRPreprocessor.layoutjson2md(img, json_data)
        return preprocessed_content


def get_preprocessor(model_name: str) -> Optional[type]:
    """
    모델 이름에 따른 전처리기 반환
    
    Args:
        model_name (str): VLM 모델 이름
        
    Returns:
        Optional[type]: 해당하는 전처리기 클래스, 없으면 None
    """
    if not model_name:
        return None
        
    model_name_lower = model_name.lower()
    
    if 'dots' in model_name_lower:
        return DotsOCRPreprocessor
    elif 'nanonet' in model_name_lower:
        return NanonetsPreprocessor
    
    return None


def preprocess_vlm_output(content: str, json_data:list, model_name: str, image_path: str = None) -> str:
    """
    VLM 출력을 모델에 따라 전처리
    
    Args:
        content (str): VLM 원본 출력
        model_name (str): VLM 모델 이름
        
    Returns:
        str: 전처리된 마크다운 콘텐츠
    """
    preprocessor = get_preprocessor(model_name)
    
    if preprocessor:
        logger.info("Preprocessing vlm outputs")
        return preprocessor.preprocess(content, json_data, image_path)
    
    # 기본 전처리: 앞뒤 공백 제거
    return content.strip()
