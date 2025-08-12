from __future__ import annotations

import os
import json
import uuid
from typing import Tuple
import yaml
from loguru import logger

from extraction_module.utils import extract_with_framework
from utils import box_line, log_response, final_report, record_extraction
from .types import ExtractionCoreRequest, ExtractionCoreResult
from .logging import setup_extraction_logger
from .tracing import Tracer


def _load_prompt() -> str:
    with open("prompt.yaml", "r", encoding="utf-8") as f:
        prompt_yaml = yaml.safe_load(f)
    return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")


def run_extraction_core(req: ExtractionCoreRequest) -> ExtractionCoreResult:
    log_dir, log_filename = setup_extraction_logger()

    tracer = Tracer(enabled=True)
    trace_id = tracer.start_trace(seed=f"custom-{uuid.uuid4()}")

    host_info = req.host_info
    base_url = host_info.base_url
    model = host_info.model

    box_width = 48
    exp_info = [
        "*" * box_width,
        f"{'Benchmark 시작'.center(box_width)}",
        box_line(f"Host: {host_info.host}"),
        box_line(f"BaseURL: {base_url}"),
        box_line(f"Model: {model}"),
        box_line(f"Framework: {req.framework_name}"),
        box_line(f"Input: {str(req.input_text_or_path).strip()[:20]}"),
        box_line(f"Retries: {req.retries}"),
        "*" * box_width,
    ]
    for line in exp_info:
        logger.info(line)

    input_text = req.input_text_or_path
    if os.path.isfile(input_text):
        with open(input_text, "r", encoding="utf-8") as f:
            input_text = f.read()

    extract_prompt = _load_prompt()

    result, success, latencies = extract_with_framework(
        framework_name=req.framework_name,
        provider=host_info.host,
        model_name=host_info.model,
        base_url=host_info.base_url,
        content=input_text,
        prompt=f"{extract_prompt}\n{input_text}",
        schema_name=req.schema_name,
        retries=req.retries,
        api_delay_seconds=0.5,
        timeout=req.timeout,
        temperature=req.temperature,
        langfuse_trace_id=trace_id,
    )

    log_time = os.path.basename(log_dir)
    result_json_path = os.path.join(log_dir, f"result_{log_time}.json")
    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    latency = latencies[0] if isinstance(latencies, list) and latencies else latencies
    logger.success("Framework single experiment completed")
    logger.success(f"Success rate: {success:.2%}")
    log_response(logger, result, latency, prefix="Framework response ")

    langfuse_url = tracer.get_url(trace_id)
    final_report(exp_info, logger, latency, langfuse_url)

    record_extraction(
        log_filename=log_filename,
        host=host_info.host,
        model=model,
        prompt=f"{extract_prompt}\n{input_text}",
        framework=req.framework_name,
        success=bool(result),
        latency=latency,
        langfuse_url=langfuse_url,
        note="",
        csv_path="result/extraction_result.csv",
        result_json_path=result_json_path,
    )

    return ExtractionCoreResult(
        success=bool(result),
        result=result,
        success_rate=success,
        latency=latency,
        log_dir=log_dir,
        result_json_path=result_json_path,
        langfuse_url=langfuse_url,
    )
