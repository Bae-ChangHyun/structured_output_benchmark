from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Tuple
from loguru import logger

def setup_logger(task = "extraction", output_dir: str = None) -> Tuple[str, str]:
    """Create extraction run folder and configure loguru.
    Returns (log_dir, log_filename).
    """
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    if not output_dir:
        log_time = datetime.now().strftime('%Y%m%d_%H%M')
        output_dir = os.path.join("result", task, log_time)
    os.makedirs(output_dir, exist_ok=True)
    log_filename = os.path.join(output_dir, f"{task}.log")
    logger.add(log_filename, level=os.getenv("MODE", "INFO").upper(), enqueue=True)
    return output_dir, log_filename
