import os
from typing import Optional

class Settings:
    # 서버 설정
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 결과 저장 경로
    RESULT_DIR: str = "result"
    
    def __init__(self):
        # 필요한 디렉토리 생성
        os.makedirs(self.RESULT_DIR, exist_ok=True)

settings = Settings()
