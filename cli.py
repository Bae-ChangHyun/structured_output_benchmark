import os
import asyncio
import typer
from typing import Optional
from dotenv import load_dotenv
from langfuse import get_client

from utils import select_host, select_framework
from core.types import ExtractionCoreRequest, EvaluationCoreRequest, HostInfo
from core.extraction import run_extraction_core
from core.evaluation import run_evaluation_core


load_dotenv()
langfuse_client = get_client()

app = typer.Typer()

@app.command()
def run(
    input_text: str = typer.Option("Hello, how are you?", "--input", help="프롬프트 텍스트 또는 파일 경로"),
    retries: int = typer.Option(1, "--retries", help="프레임워크 재시도 횟수"),
    schema_name: str = typer.Option("schema_han", "--schema", help="프레임워크 스키마 이름"),
    temperature: float = typer.Option(0.1, "--temperature", help="프롬프트 온도"),
    timeout: int = typer.Option(900, "--timeout", help="LLM request timeout 시간")
):
    """현재 프로세스 실행 (extraction)"""
    asyncio.run(run_extraction(input_text, retries, schema_name, temperature, timeout))


@app.command() 
def eval(
    pred_json_path: str = typer.Option(..., "--pred-json", help="예측 결과 JSON 파일 경로"),
    gt_json_path: str = typer.Option(..., "--gt-json", help="Ground truth JSON 파일 경로"),
    schema_name: str = typer.Option("schema_han", "--schema", help="스키마 이름"),
    criteria_path: Optional[str] = typer.Option("evaluation_module/criteria/criteria.json", "--criteria", help="평가 기준 파일 경로"),
    embed_backend: str = typer.Option("openai", "--embed-backend", help="임베딩 백엔드 (huggingface/openai/vllm/ollama)"),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="임베딩 모델명"),
    api_base: Optional[str] = typer.Option(None, "--api-base", help="API 베이스 URL")
):
    """Evaluation 프로세스 실행"""
    asyncio.run(run_evaluation(pred_json_path, gt_json_path, schema_name, criteria_path, embed_backend, model_name, api_base))

# viz 명령 단순화: streamlit 앱 직접 실행
@app.command()
def viz(
    eval_result_path: str = typer.Option(..., '--eval-result', help='평가 결과 JSON 파일 경로')
):
    """평가 결과 시각화: streamlit 앱을 바로 실행합니다."""
    print(f"Streamlit 시각화 실행: http://localhost:8501")
    os.system(f"streamlit run evaluation_module/visualizer.py -- --eval-result {eval_result_path}")


async def run_extraction(input_text: str, retries: int, schema_name: str, temperature: float, timeout: int):
    """Extraction 실행 함수 (core 유즈케이스 호출)"""
    host_info = select_host()
    framework_name = select_framework(host_info["host"])

    core_req = ExtractionCoreRequest(
        input_text_or_path=input_text,
        retries=retries,
        schema_name=schema_name,
        temperature=temperature,
        timeout=timeout,
        framework_name=framework_name,
        host_info=HostInfo(**{
            "host": host_info["host"],
            "base_url": host_info["base_url"],
            "model": host_info["model"],
        }),
    )
    _ = run_extraction_core(core_req)


async def run_evaluation(pred_json_path: str, gt_json_path: str, schema_name: str, criteria_path: Optional[str],
                        embed_backend: str, model_name: Optional[str], api_base: Optional[str]):
    """Evaluation 실행 함수 (core 유즈케이스 호출)"""
    core_req = EvaluationCoreRequest(
        pred_json_path=pred_json_path,
        gt_json_path=gt_json_path,
        schema_name=schema_name,
        criteria_path=criteria_path,
        embed_backend=embed_backend,
        model_name=model_name,
        api_base=api_base,
    )
    _ = run_evaluation_core(core_req)


if __name__ == "__main__":
    app()
