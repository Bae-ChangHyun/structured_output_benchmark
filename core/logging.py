from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Tuple
from loguru import logger


def setup_extraction_logger() -> Tuple[str, str]:
    """Create extraction run folder and configure loguru.
    Returns (log_dir, log_filename).
    """
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    log_time = datetime.now().strftime('%Y%m%d_%H%M')
    log_dir = os.path.join("result/extraction", log_time)
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, "extraction.log")
    logger.add(log_filename, level=os.getenv("MODE", "INFO").upper(), enqueue=True)
    return log_dir, log_filename


def setup_evaluation_logger() -> Tuple[str, str]:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    eval_time = datetime.now().strftime('%Y%m%d_%H%M')
    eval_dir = os.path.join("result", "evaluation", eval_time)
    os.makedirs(eval_dir, exist_ok=True)
    log_filename = os.path.join(eval_dir, "evaluation.log")
    logger.add(log_filename, level=os.getenv("MODE", "INFO").upper(), enqueue=True)
    return eval_dir, log_filename
