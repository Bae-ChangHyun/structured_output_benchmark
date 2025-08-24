import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


def save_parsing_result(
    content: str,
    file_path: str,
    framework: str,
    output_dir: str,
    extra_kwargs: Optional[Dict[str, Any]] = None
) -> str:
    """파싱 결과를 파일로 저장"""
    
    # 결과 파일명 생성
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"{base_name}_{framework}_{timestamp}.txt"
    result_path = os.path.join(output_dir, result_filename)
    
    # 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 파싱 결과 저장
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 메타데이터 저장
    metadata = {
        "file_path": file_path,
        "framework": framework,
        "timestamp": timestamp,
        "result_file": result_filename,
        "extra_kwargs": extra_kwargs or {}
    }
    
    metadata_path = os.path.join(output_dir, f"{base_name}_{framework}_{timestamp}_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"파싱 결과 저장 완료: {result_path}")
    return result_path


def validate_pdf_file(file_path: str) -> bool:
    """PDF 파일 유효성 검사"""
    if not os.path.exists(file_path):
        return False
    
    if os.path.getsize(file_path) == 0:
        return False
    
    # PDF 파일 헤더 확인
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception:
        return False


def validate_image_file(file_path: str) -> bool:
    """이미지 파일 유효성 검사"""
    if not os.path.exists(file_path):
        return False
    
    if os.path.getsize(file_path) == 0:
        return False
    
    # 이미지 파일 확장자 확인
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']


def get_file_info(file_path: str) -> Dict[str, Any]:
    """파일 정보 조회"""
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_size": stat.st_size,
        "file_extension": os.path.splitext(file_path)[1].lower(),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def get_available_frameworks() -> list[str]:
    """사용 가능한 파싱 프레임워크 목록"""
    return ["docling", "pypdf", "fitz", "pdfplumber", "markitdown", "vlm"]


def record_parsing(
    file_name: str,
    framework: str,
    elapsed_time: float,
    success: bool,
    output_dir: str,
    extra_kwargs: Optional[Dict[str, Any]] = None
) -> list[str]:
    """파싱 로그 기록"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "file_name": file_name,
        "framework": framework,
        "elapsed_time": elapsed_time,
        "success": success,
        "extra_kwargs": extra_kwargs or {}
    }
    
    # 로그 파일 경로
    log_file = os.path.join(output_dir, "parsing_log.jsonl")
    
    # 로그 기록
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    log_lines = [
        f"파싱 완료: {file_name}",
        f"프레임워크: {framework}",
        f"처리 시간: {elapsed_time:.2f}초",
        f"성공 여부: {'성공' if success else '실패'}"
    ]
    
    logger.info(" | ".join(log_lines))
    return log_lines
