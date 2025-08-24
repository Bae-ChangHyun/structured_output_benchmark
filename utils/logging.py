from __future__ import annotations

from math import e
import os
import sys
from typing import Tuple
from loguru import logger
from datetime import datetime
from langfuse import observe, get_client

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

def box_line(text, box_width=48):
    # 너무 길면 잘라내기
    trimmed = text[:box_width-2]
    return f" {trimmed:<{box_width-2}}"

def log_response(logger, response, latency, success):
    if latency == -1:
        logger.error(f"Response failed: {response}")
    else:
        if success: logger.success(f"Response completed | Latency: {latency:.3f}s | Content: {response}")
        else: logger.error(f"Response failed | Latency: {latency:.3f}s | Content: {response}")

def final_report(exp_info, logger, latencies, langfuse_trace_url, success):
        logger.info("-"*50)
        if success: logger.success("[Final Report]")
        else: success = False; logger.error("[Final Report]")
        for i in range(2, len(exp_info)-2):
            if success:logger.success(exp_info[i])
            else: logger.error(exp_info[i])
        if not isinstance(latencies, list):
            latencies = [latencies]
        if latencies and latencies[0] != -1:
            if success:logger.success(f"Latency: {latencies[0]:.3f}s")
            else: logger.error(f"Latency: {latencies[0]:.3f}s")
        else:
            logger.error("Request failed. Latency not available.")

        langfuse = get_client()
        if success: logger.success(f"Request Langfuse Trace URLs: {langfuse_trace_url}")
        else: logger.error(f"Request Langfuse Trace URLs: {langfuse_trace_url}")
