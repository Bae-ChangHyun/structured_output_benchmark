import os
import tempfile
from typing import Dict, Any, List
from loguru import logger

from PIL import Image
from pdf2image import convert_from_path
from structured_output_kit.parsing.base import ParsingFramework


class VLMFramework(ParsingFramework):
    """VLM을 사용한 문서 파싱 프레임워크"""
    
    
    @property
    def name(self) -> str:
        return "vlm"
    
    def supported_extensions(self) -> list[str]:
        return [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]
    
    def parse(self) -> str:
        """VLM을 사용한 문서 파싱"""
        
        if not self.host_info:
            raise ValueError("VLM 사용시 host_info가 필요합니다")
        
        if not self.prompt:
            raise ValueError("VLM 사용시 prompt가 필요합니다")
        
        if not self.validate_file():
            raise ValueError(f"유효하지 않은 파일입니다: {self.file_path}")
        
        try:
            # 이미지 파일들 준비
            image_paths = self._prepare_images()
            
            # VLM으로 각 이미지 처리
            results = []
            for idx, image_path in enumerate(image_paths):
                logger.debug(f"이미지 {idx + 1}/{len(image_paths)} 처리 중: {image_path}")
                result = self._process_single_image(image_path, idx + 1)
                results.append(result)
            
            # 결과 통합
            combined_content = self._combine_results(results)
            
            logger.info(f"VLM으로 문서 파싱 완료: {len(combined_content)} 문자")
            return combined_content
            
        except Exception as e:
            logger.error(f"VLM 파싱 중 오류 발생: {str(e)}")
            raise
    
    def _prepare_images(self) -> List[str]:
        """파일을 이미지로 변환하여 준비"""
        if self.file_extension == '.pdf':
            # PDF를 이미지로 변환
            images = convert_from_path(self.file_path)
            image_paths = []
            
            # 임시 디렉토리에 이미지 저장
            temp_dir = tempfile.mkdtemp()
            for idx, image in enumerate(images):
                image_path = os.path.join(temp_dir, f"page_{idx + 1}.png")
                image.save(image_path, "PNG")
                image_paths.append(image_path)
            
            return image_paths
        else:
            # 이미 이미지 파일인 경우
            return [self.file_path]
    
    def _process_single_image(self, image_path: str, page_num: int) -> str:
        """단일 이미지를 VLM으로 처리"""
        try:
            # 이미지를 base64로 인코딩
            image_base64 = self._encode_image_to_base64(image_path)
            
            # VLM API 호출
            if self.host_info.provider == "ollama":
                result = self._call_ollama_vlm(image_base64, page_num)
            elif self.host_info.provider == "openai_compatible":
                result = self._call_openai_compatible_vlm(image_base64, page_num)
            elif self.host_info.provider == "openai":
                result = self._call_openai_vlm(image_base64, page_num)
            elif self.host_info.provider == "anthropic":
                result = self._call_anthropic_vlm(image_base64, page_num)
            elif self.host_info.provider == "google":
                result = self._call_google_vlm(image_base64, page_num)
            else:
                raise ValueError(f"지원하지 않는 VLM 호스트: {self.host_info.provider}")
            
            return result
            
        except Exception as e:
            logger.error(f"페이지 {page_num} VLM 처리 실패: {str(e)}")
            return f"[페이지 {page_num} 처리 실패: {str(e)}]"
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        import base64
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _call_ollama_vlm(self, image_base64: str, page_num: int) -> str:
        """Ollama VLM API 호출"""
        import requests
        
        url = f"{self.host_info.base_url}/api/generate"
        
        payload = {
            "model": self.host_info.model,
            "prompt": self.prompt,
            "images": [image_base64],
            "stream": False
        }
        
        # extra_kwargs에서 추가 파라미터 적용
        if self.extra_kwargs:
            payload.update(self.extra_kwargs)
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            logger.debug(f"페이지 {page_num} Ollama VLM 처리 완료")
            return content
            
        except Exception as e:
            logger.error(f"Ollama VLM API 호출 실패: {str(e)}")
            raise
    
    def _call_openai_compatible_vlm(self, image_base64: str, page_num: int) -> str:
        """OpenAI Compatible VLM API 호출"""
        import requests
        
        url = f"{self.host_info.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.host_info.api_key:
            headers["Authorization"] = f"Bearer {self.host_info.api_key}"
        
        payload = {
            "model": self.host_info.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ]
        }
        
        # extra_kwargs에서 추가 파라미터 적용
        if self.extra_kwargs:
            payload.update(self.extra_kwargs)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.debug(f"페이지 {page_num} OpenAI Compatible VLM 처리 완료")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI Compatible VLM API 호출 실패: {str(e)}")
            raise
    
    def _call_openai_vlm(self, image_base64: str, page_num: int) -> str:
        """OpenAI VLM API 호출"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.host_info.api_key,
                base_url=self.host_info.base_url
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ]
            
            # 기본 파라미터
            kwargs = {
                "model": self.host_info.model,
                "messages": messages
            }
            
            # extra_kwargs에서 추가 파라미터 적용
            if self.extra_kwargs:
                kwargs.update(self.extra_kwargs)
            
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            logger.debug(f"페이지 {page_num} OpenAI VLM 처리 완료")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI VLM API 호출 실패: {str(e)}")
            raise
    
    def _call_anthropic_vlm(self, image_base64: str, page_num: int) -> str:
        """Anthropic VLM API 호출"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(
                api_key=self.host_info.api_key,
                base_url=self.host_info.base_url
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
            
            # 기본 파라미터
            kwargs = {
                "model": self.host_info.model,
                "messages": messages,
                "max_tokens": 4000
            }
            
            # extra_kwargs에서 추가 파라미터 적용
            if self.extra_kwargs:
                kwargs.update(self.extra_kwargs)
            
            response = client.messages.create(**kwargs)
            content = response.content[0].text
            
            logger.debug(f"페이지 {page_num} Anthropic VLM 처리 완료")
            return content
            
        except Exception as e:
            logger.error(f"Anthropic VLM API 호출 실패: {str(e)}")
            raise
    
    def _call_google_vlm(self, image_base64: str, page_num: int) -> str:
        """Google VLM API 호출"""
        try:
            import google.generativeai as genai
            import base64
            
            # API 키 설정
            genai.configure(api_key=self.host_info.api_key)
            
            # 모델 초기화
            model = genai.GenerativeModel(self.host_info.model)
            
            # base64를 바이트로 디코딩
            image_data = base64.b64decode(image_base64)
            
            # 이미지 객체 생성
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }
            
            # 콘텐츠 구성
            contents = [self.prompt, image_part]
            
            # 생성 설정
            generation_config = {}
            if self.extra_kwargs:
                generation_config.update(self.extra_kwargs)
            
            response = model.generate_content(
                contents=contents,
                generation_config=generation_config if generation_config else None
            )
            
            content = response.text
            
            logger.debug(f"페이지 {page_num} Google VLM 처리 완료")
            return content
            
        except Exception as e:
            logger.error(f"Google VLM API 호출 실패: {str(e)}")
            raise
    
    def _combine_results(self, results: List[str]) -> str:
        """여러 페이지 결과를 하나로 통합"""
        if not results:
            return ""
        
        if len(results) == 1:
            return results[0].strip()
        
        # 여러 페이지를 구분자로 연결
        combined = ""
        for idx, result in enumerate(results, 1):
            if result.strip():
                combined += f"# 페이지 {idx}\n\n{result.strip()}\n\n"
        
        return combined.strip()
