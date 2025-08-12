from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from enum import Enum

class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None