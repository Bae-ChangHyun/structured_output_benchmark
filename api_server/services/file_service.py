import os
import shutil
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from api_server.config import settings
from api_server.models.common import FileInfo


class FileService:
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
    
    def validate_file(self, file: UploadFile) -> None:
        """파일 유효성을 검사합니다."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 파일 확장자 검사
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"지원되지 않는 파일 형식입니다. 허용된 확장자: {', '.join(self.allowed_extensions)}"
            )
    
    async def save_upload_file(self, file: UploadFile) -> FileInfo:
        """업로드된 파일을 저장합니다."""
        self.validate_file(file)
        
        # 고유한 파일명 생성
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_ext}"
        upload_path = os.path.join(self.upload_dir, unique_filename)
        
        try:
            # 파일 저장
            with open(upload_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 파일 크기 확인
            file_size = os.path.getsize(upload_path)
            if file_size > self.max_file_size:
                os.remove(upload_path)
                raise HTTPException(
                    status_code=413, 
                    detail=f"파일 크기가 제한을 초과했습니다. 최대 크기: {self.max_file_size} bytes"
                )
            
            return FileInfo(
                filename=file.filename,
                size=file_size,
                content_type=file.content_type or "application/octet-stream",
                upload_path=upload_path
            )
        
        except Exception as e:
            # 저장 실패 시 파일 삭제
            if os.path.exists(upload_path):
                os.remove(upload_path)
            raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")
    
    async def save_multiple_files(self, files: List[UploadFile]) -> List[FileInfo]:
        """여러 파일을 저장합니다."""
        file_infos = []
        for file in files:
            file_info = await self.save_upload_file(file)
            file_infos.append(file_info)
        return file_infos
    
    def read_text_file(self, file_path: str) -> str:
        """텍스트 파일을 읽습니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 읽기 실패: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """파일을 삭제합니다."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """임시 파일들을 정리합니다."""
        for file_path in file_paths:
            self.delete_file(file_path)
