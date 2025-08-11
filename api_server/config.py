import os
from typing import Optional

class Settings:
    # 서버 설정
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 파일 저장 설정
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {".txt", ".json", ".pdf", ".docx", ".md"}
    
    # 결과 저장 경로
    RESULT_DIR: str = "result"
    
    # 백그라운드 작업 설정
    TASK_TIMEOUT: int = int(os.getenv("TASK_TIMEOUT", "3600"))  # 1시간
    
    def __init__(self):
        # 필요한 디렉토리 생성
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESULT_DIR, exist_ok=True)

settings = Settings()
