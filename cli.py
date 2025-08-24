import os
import asyncio
import typer
from typing import Optional, Dict, Any
import json
from dotenv import load_dotenv
from langfuse import get_client

from structured_output_kit.utils.cli_helpers import select_llm, select_embed, select_framework
from structured_output_kit.utils.types import ExtractionRequest, EvaluationRequest, ParsingRequest, HostInfo
from structured_output_kit.utils.common import check_host_info
from structured_output_kit.extraction.core import run_extraction_core
from structured_output_kit.extraction.utils import load_prompt
from structured_output_kit.evaluation.core import run_evaluation_core
from structured_output_kit.parsing.core import run_parsing_core
from structured_output_kit.utils.visualization import run_visualization_core


load_dotenv()
langfuse_client = get_client()

app = typer.Typer()

@app.command()
def extract(
    prompt: Optional[str] = typer.Option(None, "--prompt", help="사용할 프롬프트 (기본값: prompt.yaml에서 로드)"),
    input_text: str = typer.Option("Hello, how are you?", "--input", help="텍스트 또는 파일 경로"),
    retries: int = typer.Option(1, "--retries", help="프레임워크 재시도 횟수"),
    schema_name: str = typer.Option("schema_han", "--schema", help="프레임워크 스키마 이름"),
    extra_kwargs: str = typer.Option("{}", "--kwargs", help='프레임워크/LLM 파라미터 JSON 문자열. 예: "{\"temperature\":0.1,\"timeout\":900}"'),
    langfuse_trace_id: Optional[str] = typer.Option(None, "--trace-id", help="Langfuse trace ID"),
    save: Optional[bool] = typer.Option(False, "--save", help="결과 저장 여부"),
    # Host info 딕셔너리 형태로 전달
    host_info: Optional[str] = typer.Option(None, "--host-info", help='Host 정보 JSON 문자열. 예: "{\"provider\":\"openai\",\"model\":\"gpt-4\",\"api_key\":\"sk-...\"}"'),
    framework: Optional[str] = typer.Option(None, "--framework", help="사용할 프레임워크")
):
    """현재 프로세스 실행 (extraction)"""
    try:
        extra_kwargs: Dict[str, Any] = json.loads(extra_kwargs) if extra_kwargs else {}
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"--kwargs JSON 파싱 실패: {e}")

    asyncio.run(run_extraction(prompt, input_text, retries, schema_name, extra_kwargs, langfuse_trace_id, save, host_info, framework))


@app.command() 
def eval(
    pred_json_path: str = typer.Option(..., "--pred", help="예측 결과 JSON 파일 경로"),
    gt_json_path: str = typer.Option(..., "--gt", help="Ground truth JSON 파일 경로"),
    schema_name: str = typer.Option("schema_han", "--schema", help="스키마 이름"),
    criteria_path: Optional[str] = typer.Option("evaluation/criteria/criteria.json", "--criteria", help="평가 기준 파일 경로"),
    save: Optional[bool] = typer.Option(False, "--save", help="평가 결과 저장 여부"),
    # Host info 딕셔너리 형태로 전달
    host_info: Optional[str] = typer.Option(None, "--host-info", help='Host 정보 JSON 문자열. 예: "{\"provider\":\"openai\",\"model\":\"text-embedding-3-small\",\"api_key\":\"sk-...\"}"')
):
    """Evaluation 프로세스 실행"""
    asyncio.run(run_evaluation(pred_json_path, gt_json_path, schema_name, criteria_path, save, host_info))


@app.command()
def parse(
    file_path: str = typer.Option(..., "--file", help="파싱할 PDF/이미지 파일 경로"),
    framework: str = typer.Option("docling", "--framework", help="파싱 프레임워크 (docling, pypdf, fitz, pdfplumber, markitdown, vlm)"),
    extra_kwargs: str = typer.Option("{}", "--kwargs", help='프레임워크별 추가 파라미터 JSON 문자열. 예: "{\"use_ocr\":true,\"ocr_lang\":\"ko\"}"'),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="VLM 사용시 프롬프트"),
    save: Optional[bool] = typer.Option(False, "--save", help="결과 저장 여부"),
    # Host info 딕셔너리 형태로 전달 (VLM 사용시에만 필요)
    host_info: Optional[str] = typer.Option(None, "--host-info", help='Host 정보 JSON 문자열 (VLM 사용시). 예: "{\"provider\":\"openai\",\"model\":\"gpt-4\",\"api_key\":\"sk-...\"}"')
):
    """PDF/이미지 파싱 프로세스 실행"""
    try:
        extra_kwargs_dict: Dict[str, Any] = json.loads(extra_kwargs) if extra_kwargs else {}
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"--kwargs JSON 파싱 실패: {e}")

    asyncio.run(run_parsing_process(file_path, framework, extra_kwargs_dict, prompt, save, host_info))

# viz 명령 단순화: streamlit 앱 직접 실행
@app.command()
def viz(
    eval_result_path: str = typer.Option(..., '--eval-result', help='평가 결과 JSON 파일 경로'),
    html: bool = typer.Option(False, '--html', help='Streamlit 대신 정적 HTML 생성'),
    output_dir: Optional[str] = typer.Option(None, '--out', help='HTML 출력 디렉토리'),
):
    """평가 결과 시각화: Streamlit 또는 정적 HTML 방식 지원."""
    if html:
        result = run_visualization_core(eval_result_path=eval_result_path, output_dir=output_dir)
        print(f"HTML 생성 완료: {result['html_path']}")
    else:
        print(f"Streamlit 시각화 실행: http://localhost:8501")
        os.system(f"streamlit run evaluation/visualizer.py -- --eval-result {eval_result_path}")


async def run_extraction(prompt: Optional[str], 
                         input_text: str, 
                         retries: int, 
                         schema_name: str, 
                         extra_kwargs: Dict[str, Any], 
                         langfuse_trace_id: Optional[str] = None,
                         save: Optional[bool] = False,
                         host_info_json: Optional[str] = None,
                         framework_name: Optional[str] = None):
    """Extraction 실행 함수 (core 유즈케이스 호출)"""
    
    # host_info가 제공되었다면 JSON 파싱하여 사용, 아니면 interactive 선택
    if host_info_json:
        try:
            host_info_dict = json.loads(host_info_json)
            host_info_dict = check_host_info(host_info_dict)
            
            # framework가 제공되지 않았다면 provider에서 자동 선택
            if not framework_name:
                framework_name = select_framework(host_info_dict["provider"])
            
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--host-info JSON 파싱 실패: {e}")
    else:
        # interactive 모드
        host_info_dict = select_llm()
        host_info_dict = check_host_info(host_info_dict)
        framework_name = select_framework(host_info_dict["provider"])

    extra_kwargs = dict(extra_kwargs or {})

    core_req = ExtractionRequest(
        prompt=prompt if prompt else load_prompt(),
        input_text=input_text,
        retries=retries,
        schema_name=schema_name,
        extra_kwargs=extra_kwargs,
        framework=framework_name,
        host_info=HostInfo(**{
            "provider": host_info_dict["provider"],
            "base_url": host_info_dict["base_url"],
            "model": host_info_dict["model"],
            "api_key": host_info_dict["api_key"]
        }),
        langfuse_trace_id=langfuse_trace_id,
        save=save
    )
    _ = run_extraction_core(core_req)


async def run_evaluation(pred_json_path: str, 
                         gt_json_path: str, 
                         schema_name: str, 
                         criteria_path: Optional[str],
                         save: Optional[bool] = False,
                         host_info_json: Optional[str] = None):
    """Evaluation 실행 함수 (core 유즈케이스 호출)"""
    
    # host_info가 제공되었다면 JSON 파싱하여 사용, 아니면 interactive 선택
    if host_info_json:
        try:
            host_info_dict = json.loads(host_info_json)
            host_info_dict = check_host_info(host_info_dict)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--host-info JSON 파싱 실패: {e}")
    else:
        # interactive 모드
        host_info_dict = select_embed()
        host_info_dict = check_host_info(host_info_dict)
    
    core_req = EvaluationRequest(
        pred_json_path=pred_json_path,
        gt_json_path=gt_json_path,
        schema_name=schema_name,
        criteria_path=criteria_path,
        host_info=HostInfo(**{
            "provider": host_info_dict["provider"],
            "base_url": host_info_dict["base_url"],
            "model": host_info_dict["model"],
            "api_key": host_info_dict["api_key"]
        }),
        save=save
    )
    _ = run_evaluation_core(core_req)


async def run_parsing_process(file_path: str, 
                             framework: str, 
                             extra_kwargs: Dict[str, Any], 
                             prompt: Optional[str] = None,
                             save: Optional[bool] = False,
                             host_info_json: Optional[str] = None):
    """Parsing 실행 함수 (core 유즈케이스 호출)"""
    host_info = None
    
    # VLM 프레임워크 사용시 호스트 정보 필요
    if framework == "vlm":
        if host_info_json:
            try:
                host_info_dict = json.loads(host_info_json)
                host_info_dict = check_host_info(host_info_dict)
                host_info = HostInfo(**{
                    "provider": host_info_dict["provider"],
                    "base_url": host_info_dict["base_url"],
                    "model": host_info_dict["model"],
                    "api_key": host_info_dict["api_key"]
                })
            except json.JSONDecodeError as e:
                raise typer.BadParameter(f"--host-info JSON 파싱 실패: {e}")
        else:
            # interactive 모드
            host_info_dict = select_llm()
            host_info_dict = check_host_info(host_info_dict)
            host_info = HostInfo(**{
                "provider": host_info_dict["provider"],
                "base_url": host_info_dict["base_url"],
                "model": host_info_dict["model"],
                "api_key": host_info_dict["api_key"]
            })
        
        if not prompt:
            print("VLM 프레임워크 사용시 프롬프트가 필요합니다.")
            prompt = input("프롬프트를 입력하세요: ")
    
    core_req = ParsingRequest(
        file_path=file_path,
        framework=framework,
        extra_kwargs=extra_kwargs,
        host_info=host_info,
        prompt=prompt,
        save=save
    )
    
    result = run_parsing_core(core_req)
    
    if result.success:
        print(f"✅ 파싱 성공!")
        print(f"📁 파일: {result.file_path}")
        print(f"🔧 프레임워크: {result.framework}")
        print(f"📝 추출된 텍스트 길이: {len(result.content)} 문자")
        if result.result_txt_path:
            print(f"💾 결과 저장: {result.result_txt_path}")
        
        # 텍스트 미리보기 (처음 500자)
        preview = result.content[:500]
        if len(result.content) > 500:
            preview += "..."
        print(f"\n📖 텍스트 미리보기:\n{preview}")
    else:
        print(f"❌ 파싱 실패: {result.content}")


if __name__ == "__main__":
    app()
