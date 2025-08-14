from __future__ import annotations

import os
import json
import uuid
from typing import Tuple
import yaml
from importlib import resources
from loguru import logger

from structured_output_benchmark.extraction_module.utils import extract_with_framework
from structured_output_benchmark.utils import box_line, log_response, final_report, record_extraction
from .types import ExtractionRequest, ExtractionResult
from .logging import setup_logger
from .tracing import Tracer


def _load_prompt() -> str:
    try:
        with resources.files("structured_output_benchmark").joinpath("prompt.yaml").open("r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
    except Exception:
        if os.path.exists("prompt.yaml"):
            with open("prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
            return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
        return "Extract information from the given content."


def run_extraction_core(req: ExtractionRequest) -> ExtractionResult:
    output_dir, log_filename = setup_logger(task='extraction', 
                                         output_dir=req.output_dir)

    tracer = Tracer(enabled=True)
    if not req.langfuse_trace_id: trace_id = tracer.start_trace(seed=f"custom-{uuid.uuid4()}")
    else: trace_id = req.langfuse_trace_id

    host_info = req.host_info

    box_width = 48
    exp_info = [
        "*" * box_width,
        f"{'Benchmark 시작'.center(box_width)}",
        box_line(f"Provider: {host_info.provider}"),
        box_line(f"BaseURL: {host_info.base_url}"),
        box_line(f"Model: {host_info.model}"),
        box_line(f"Framework: {req.framework}"),
        box_line(f"Input: {str(req.input_text).strip()[:20]}"),
        box_line(f"Retries: {req.retries}"),
        "*" * box_width,
    ]
    for line in exp_info:
        logger.info(line)

    input_text = req.input_text
    if os.path.isfile(input_text):
        with open(input_text, "r", encoding="utf-8") as f:
            input_text = f.read()
            
    result, success, latencies = extract_with_framework(
        framework=req.framework,
        host_info=host_info,
        content=input_text,
        prompt=f"{req.prompt}\n{input_text}",
        schema_name=req.schema_name,
        retries=req.retries,
        api_delay_seconds=0.5,
        langfuse_trace_id=trace_id,
        extra_kwargs=req.extra_kwargs,
    )

    log_time = os.path.basename(output_dir)
    result_json_path = os.path.join(output_dir, f"result.json")
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
        provider=host_info.provider,
        model=host_info.model,
        prompt=f"{req.prompt}\n{input_text}",
        framework=req.framework,
        success=bool(result),
        latency=latency,
        langfuse_url=langfuse_url,
        note="",
        csv_path="result/extraction_result.csv",
        result_json_path=result_json_path,
    )

    return ExtractionResult(
        success=bool(result),
        result=result,
        success_rate=success,
        latency=latency,
        output_dir=output_dir,
        result_json_path=result_json_path,
        langfuse_url=langfuse_url,
    )
