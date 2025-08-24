from fastapi import APIRouter
from typing import Dict, List, Any
import os

router = APIRouter()

# utils 라우터는 이제 빈 상태로 유지하거나 다른 유틸리티 기능들을 위해 사용할 수 있습니다.
# providers, frameworks, schemas 엔드포인트는 각각 extraction과 evaluation 라우터로 이동했습니다.
