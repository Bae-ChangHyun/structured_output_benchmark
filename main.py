import os
import time
import yaml
import asyncio
import sys
import argparse
import json
import typer
from typing import Optional
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
import uuid
from langfuse import get_client
import numpy as np


from extraction_module.utils import extract_with_framework
from utils import (
    select_host, select_framework, record_extraction, record_evaluation,  box_line, 
    log_response, final_report, load_field_eval_criteria, convert_np
)
from evaluation_module.metric import normalize_prediction_json, eval_json

# 평가 결과 기록 함수



load_dotenv()
langfuse_client = get_client()

app = typer.Typer()

@app.command()
def run(
    input_text: str = typer.Option("Hello, how are you?", "--input", help="프롬프트 텍스트 또는 파일 경로"),
    retries: int = typer.Option(1, "--retries", help="프레임워크 재시도 횟수"),
    schema: str = typer.Option("schema_han", "--schema", help="프레임워크 스키마 이름"),
    temperature: float = typer.Option(0.1, "--temperature", help="프롬프트 온도"),
    timeout: int = typer.Option(900, "--timeout", help="LLM request timeout 시간")
):
    """현재 프로세스 실행 (extraction)"""
    asyncio.run(run_extraction(input, retries, schema, temperature, timeout))


@app.command() 
def eval(
    pred_json_path: str = typer.Option(..., "--pred-json", help="예측 결과 JSON 파일 경로"),
    gt_json_path: str = typer.Option(..., "--gt-json", help="Ground truth JSON 파일 경로"),
    schema_name: str = typer.Option("schema_han", "--schema", help="스키마 이름"),
    criteria_path: Optional[str] = typer.Option("evaluation_module/criteria/criteria.json", "--criteria", help="평가 기준 파일 경로"),
    embed_backend: str = typer.Option("openai", "--embed-backend", help="임베딩 백엔드 (huggingface/openai/vllm/ollama)"),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="임베딩 모델명"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API 키"),
    api_base: Optional[str] = typer.Option(None, "--api-base", help="API 베이스 URL"),
    run_folder: Optional[str] = typer.Option(None, "--run-folder", help="실행 폴더")
):
    """Evaluation 프로세스 실행"""
    asyncio.run(run_evaluation(pred_json_path, gt_json_path, schema_name, criteria_path, embed_backend, model_name, api_key, api_base, run_folder))

# viz 명령 단순화: streamlit 앱 직접 실행
@app.command()
def viz(
    eval_result_path: str = typer.Option(..., '--eval-result', help='평가 결과 JSON 파일 경로')
):
    """평가 결과 시각화: streamlit 앱을 바로 실행합니다."""
    print(f"Streamlit 시각화 실행: http://localhost:8501")
    os.system(f"streamlit run evaluation_module/visualizer.py -- --eval-result {eval_result_path}")


async def run_extraction(input_text: str, retries: int, schema_name: str, temperature: float, timeout: int):
    """Extraction 실행 함수"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    log_time = datetime.now().strftime('%Y%m%d_%H%M')
    log_dir = os.path.join("result/extraction", log_time)
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, "extraction.log")
    logger.add(log_filename, level=os.getenv("MODE", "INFO").upper(), enqueue=True)
    
    # 프롬프트가 파일 경로인지 확인
    if os.path.isfile(input_text):
        with open(input_text, 'r', encoding='utf-8') as f:
            input_text = f.read()
            
    langfuse_trace_id = langfuse_client.create_trace_id(seed=f"custom-{str(uuid.uuid4())}")

    host_info = select_host()
    framework_name = select_framework(host_info["host"])

    base_url = host_info["base_url"]
    api_key = host_info["api_key"]
    model = host_info["model"]
    
    box_width = 48
    exp_info = [
        "*" * box_width,
        f"{'Benchmark 시작'.center(box_width)}",
        box_line(f"Host: {host_info['host']}"),
        box_line(f"BaseURL: {base_url}"),
        box_line(f"Model: {model}"),
        box_line(f"Framework: {framework_name}"),
        box_line(f"Input: {input_text.strip()[:20]}"),
        box_line(f"Retries: {retries}"),
        "*" * box_width
    ]
    for line in exp_info:
        logger.info(line)

    # 벤치마크 결과 기록용 변수 초기화
    success = None
    latency = None
    note = ""
    
    # prompt.yaml에서 Extract_prompt 불러오기
    with open("prompt.yaml", "r", encoding="utf-8") as f:
        prompt_yaml = yaml.safe_load(f)
    extract_prompt = prompt_yaml.get("Extract_prompt", "Extract information from the given content.")

    result, success, latencies = extract_with_framework(
            framework_name=framework_name,
            provider=host_info["host"],
            model=host_info["model"],
            base_url=host_info["base_url"],
            content=input_text,  # content로 전달
            prompt=f"{extract_prompt}\n{input_text}",  # 기본 추출 프롬프트
            schema_name=schema_name,
            retries=retries,
            api_delay_seconds=0.5,
            timeout=timeout,
            temperature=temperature,
            langfuse_trace_id=langfuse_trace_id
        )
    # result를 json으로 저장 (log/날짜폴더에 저장)
    result_json_path = os.path.join(log_dir, f"result_{log_time}.json")
    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.success(f"Framework single experiment completed")
    logger.success(f"Success rate: {success:.2%}")
    for i, response in enumerate([result]):
        latency_i = latencies[i] if i < len(latencies) else None
        log_response(logger, response, latency_i, prefix=f"Framework response {i} ")
    
    success = bool([result])
    if not isinstance(latencies, list):
        latencies = [latencies]
    latencies = latencies[0] if latencies else None
    note = ""

    langfuse_url = langfuse_client.get_trace_url(trace_id=langfuse_trace_id)
    final_report(exp_info, logger, latencies, langfuse_url)

    # 벤치마크 결과 기록
    record_extraction(
        log_filename=log_filename,
        host=host_info["host"],
        model=model,
        prompt=f"{extract_prompt}\n{input_text}",
        framework=framework_name,
        success=success,
        latency=latency,
        langfuse_url=langfuse_url,
        note=note,
        csv_path="result/extraction_result.csv",
        result_json_path=result_json_path
    )


async def run_evaluation(pred_json_path: str, gt_json_path: str, schema_name: str, criteria_path: Optional[str],
                        embed_backend: str, model_name: Optional[str], api_key: Optional[str], 
                        api_base: Optional[str], run_folder: Optional[str]):
    """Evaluation 실행 함수"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    eval_time = datetime.now().strftime('%Y%m%d_%H%M')
    eval_dir = os.path.join("result", "evaluation", eval_time)
    os.makedirs(eval_dir, exist_ok=True)
    log_filename = os.path.join(eval_dir, "evaluation.log")
    logger.add(log_filename, level=os.getenv("MODE", "INFO").upper(), enqueue=True)
    try:
        # JSON 파일 로드 및 복사
        with open(pred_json_path, 'r', encoding='utf-8') as f:
            pred_json = json.load(f)
        pred_json_save_path = os.path.join(eval_dir, "pred.json")
        with open(pred_json_save_path, "w", encoding="utf-8") as f:
            json.dump(pred_json, f, ensure_ascii=False, indent=2)

        with open(gt_json_path, 'r', encoding='utf-8') as f:
            gt_json = json.load(f)
        gt_json_save_path = os.path.join(eval_dir, "gt.json")
        with open(gt_json_save_path, "w", encoding="utf-8") as f:
            json.dump(gt_json, f, ensure_ascii=False, indent=2)

        logger.info(f"예측 JSON 로드 및 저장 완료: {pred_json_save_path}")
        logger.info(f"Ground truth JSON 로드 및 저장 완료: {gt_json_save_path}")

        # 스키마 및 평가 기준 로드 및 저장
        field_eval_criteria = load_field_eval_criteria(schema_name, criteria_path)
        criteria_save_path = os.path.join(eval_dir, "criteria.json")
        with open(criteria_save_path, "w", encoding="utf-8") as f:
            json.dump(field_eval_criteria, f, ensure_ascii=False, indent=2)

        logger.info(f"스키마 로드 및 저장 완료: {schema_name}")
        logger.info(f"평가 기준 로드 및 저장 완료: {criteria_save_path}")

        # 예측 JSON 정규화 및 저장
        norm_pred = normalize_prediction_json(pred_json, gt_json)
        norm_pred_save_path = os.path.join(eval_dir, "norm_pred.json")
        with open(norm_pred_save_path, "w", encoding="utf-8") as f:
            json.dump(norm_pred, f, ensure_ascii=False, indent=2)
        logger.info(f"예측 JSON 정규화 및 저장 완료: {norm_pred_save_path}")

        # 평가 실행
        eval_result = eval_json(
            gt_json,
            norm_pred,
            embed_backend=embed_backend,
            model_name=model_name,
            api_key=api_key,
            api_base=api_base,
            run_folder=run_folder,
            field_eval_criteria=field_eval_criteria
        )

        logger.success("평가 완료!")
        logger.info(f"전체 점수: {eval_result.get('overall_score', 0):.3f}")
        logger.info(f"구조 점수: {eval_result.get('structure_score', 0):.3f}")
        logger.info(f"내용 점수: {eval_result.get('content_score', 0):.3f}")

        # 평가 결과 저장
        eval_result_save_path = os.path.join(eval_dir, "eval_result.json")
        with open(eval_result_save_path, 'w', encoding='utf-8') as f:
            json.dump(eval_result, f, ensure_ascii=False, indent=2, default=convert_np)

        logger.success(f"평가 결과 저장 완료: {eval_result_save_path}")

        # 평가 결과 기록
        record_evaluation(
            pred_json_path=pred_json_path,
            gt_json_path=gt_json_path,
            embedding_model=model_name,
            embedding_host=embed_backend,
            schema_name=schema_name,
            criteria_path=criteria_save_path,
            overall_score=eval_result.get('overall_score', 0),
            structure_score=eval_result.get('structure_score', 0),
            content_score=eval_result.get('content_score', 0),
            eval_result_path=eval_result_save_path,
            run_folder=run_folder,
            note=""
        )

    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파일 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"평가 중 오류 발생: {e}")


if __name__ == "__main__":
    app()
