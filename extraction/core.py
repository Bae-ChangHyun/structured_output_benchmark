from __future__ import annotations

import os
import json
import uuid
from typing import Dict, Any, Optional

from loguru import logger
from structured_output_kit.extraction.utils import record_extraction, convert_schema
from structured_output_kit.utils.types import HostInfo, ExtractionRequest, ExtractionResult
from structured_output_kit.utils.logging import setup_logger, box_line, log_response, final_report
from structured_output_kit.utils.tracing import Tracer


def extract_with_framework(
	framework: str,
	host_info: HostInfo,
	content: str,
	prompt: str,
	schema_name: str,
	retries: int = 1,
	api_delay_seconds: float = 0,
	langfuse_trace_id: Optional[str] = None,
	extra_kwargs: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], bool, Any]:
	"""선택된 프레임워크를 사용하여 JSON 추출 수행"""
	try:
		response_model = convert_schema(schema_name)

		init_kwargs = {
			"provider": host_info.provider,
			"model": host_info.model,
			"base_url": host_info.base_url,
			"api_key": host_info.api_key,
			"prompt": prompt,
			"response_model": response_model,
			"api_delay_seconds": api_delay_seconds,
			"langfuse_trace_id": langfuse_trace_id,
			"extra_kwargs": extra_kwargs,
		}

		# 프레임워크 인스턴스 생성
		try:
			from structured_output_kit.extraction.factory import factory
			framework_instance = factory(framework, **init_kwargs)
			logger.debug(f"{framework} 초기화 완료")
		except Exception as e:
			logger.error(f"{framework} 초기화 실패: {str(e)}")
			return {"error": f"프레임워크 초기화 실패: {str(e)}"}, False, 0

		# 입력 데이터 준비
		inputs = {"content": content}

		# 프레임워크 실행
		try:
			predictions, percent_successful, latencies = framework_instance.run(
				retries=retries,
				inputs=inputs,
				langfuse_trace_id=langfuse_trace_id,
			)
			logger.debug(
				f"프레임워크 실행 완료: 성공률 {percent_successful:.2%}, 응답 수 {len(predictions) if predictions else 0}"
			)
		except Exception as e:
			logger.error(f"프레임워크 실행 중 오류: {str(e)}")
			return {"error": f"프레임워크 실행 실패: {str(e)}"}, False, 0

		# 결과 처리
		if predictions and len(predictions) > 0 and isinstance(predictions[0], dict):
			result = predictions[0]
			if hasattr(result, "model_dump"):
				result = result.model_dump(exclude_none=True)
			elif hasattr(result, "dict"):
				result = result.dict(exclude_none=True)
			logger.debug(f"Framework {framework} 실행 성공: 성공률 {percent_successful:.2%}")
			return result, True, latencies
		else:
			if predictions and isinstance(predictions[0], str) and predictions[0].startswith("ERROR"):
				logger.error(f"Framework {framework} 실행 실패: {predictions[0]}")
			else:
				logger.error("Framework 실행 실패: 성공한 응답 없음")
			return {"error": f"성공한 응답이 없습니다: {predictions[0] if predictions else 'no predictions'}"}, False, 0

	except Exception as e:
		logger.error(f"Framework {framework} 실행 중 예상치 못한 오류 발생: {str(e)}")
		return {"error": str(e)}, False, 0


def run_extraction_core(req: ExtractionRequest) -> ExtractionResult:
	output_dir, log_filename = setup_logger(task="extraction", output_dir=req.output_dir)

	tracer = Tracer(enabled=True)
	if not req.langfuse_trace_id:
		trace_id = tracer.start_trace(seed=f"custom-{uuid.uuid4()}")
	else:
		trace_id = req.langfuse_trace_id

	host_info = req.host_info

	box_width = 48
	exp_info = [
		"*" * box_width,
		f"{'Extraction Start'.center(box_width)}",
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

	result_json_path = os.path.join(output_dir, "result.json")
	with open(result_json_path, "w", encoding="utf-8") as f:
		json.dump(result, f, ensure_ascii=False, indent=2)

	latency = latencies[0] if isinstance(latencies, list) and latencies else latencies
	logger.info("Framework single experiment completed")
	logger.info(f"Success rate: {success:.2%}")
	log_response(logger, result, latency, success)

	langfuse_url = tracer.get_url(trace_id)
	final_report(exp_info, logger, latency, langfuse_url, success)

	record_extraction(
		log_filename=log_filename,
		provider=host_info.provider,
		model=host_info.model,
		prompt=f"{req.prompt}\n{input_text}",
		framework=req.framework,
		success=success,
		latency=latency,
		langfuse_url=langfuse_url,
		csv_path="result/extraction_result.csv",
		result_json_path=result_json_path,
		save=req.save
	)

	return ExtractionResult(
		success=success,
		result=result,
		success_rate=success,
		latency=latency,
		output_dir=output_dir,
		result_json_path=result_json_path,
		langfuse_url=langfuse_url,
	)
