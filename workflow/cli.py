"""
Workflow CLI commands
"""

import asyncio
import typer
from typing import Optional, List
from pathlib import Path

from structured_output_kit.workflow.utils import load_workflow_config
from structured_output_kit.workflow.core import WorkflowExecutor


app = typer.Typer(help="통합 워크플로우 실행 도구")


@app.command()
def run(
    config_path: str = typer.Argument(..., help="워크플로우 설정 YAML 파일 경로"),
    steps: Optional[str] = typer.Option(None, "--steps", help="실행할 단계 (parsing,extraction,evaluation). 기본값: 모든 단계"),
    parallel: Optional[bool] = typer.Option(None, "--parallel", help="병렬 실행 여부 (설정 파일 값 재정의)"),
    fail_fast: Optional[bool] = typer.Option(None, "--fail-fast", help="실패시 즉시 중단 여부 (설정 파일 값 재정의)"),
    output_dir: Optional[str] = typer.Option(None, "--output", help="결과 출력 디렉토리 (설정 파일 값 재정의)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="실제 실행 없이 설정만 검증")
):
    """YAML 설정을 기반으로 워크플로우 실행"""
    
    try:
        # 설정 파일 로드
        config = load_workflow_config(config_path)
        
        # CLI 옵션으로 설정 재정의
        if parallel is not None:
            config.parallel = parallel
        if fail_fast is not None:
            config.fail_fast = fail_fast
        if output_dir is not None:
            config.output_dir = output_dir
        
        # 실행할 단계 필터링
        if steps:
            enabled_steps = [step.strip().lower() for step in steps.split(',')]
            
            # parsing이 포함되지 않은 경우 첫 번째 extraction의 input_text를 사용해야 함
            if 'parsing' not in enabled_steps:
                typer.echo("⚠️  parsing 단계가 비활성화되었습니다. extraction 설정에서 input_text를 직접 지정해야 합니다.")
            
            # evaluation이 비활성화된 경우
            if 'evaluation' not in enabled_steps and config.evaluation:
                config.evaluation.enabled = False
                typer.echo("ℹ️  evaluation 단계가 비활성화되었습니다.")
        
        # dry-run 모드
        if dry_run:
            print_config_summary(config)
            typer.echo("✅ 설정 파일 검증 완료. 실제 실행하려면 --dry-run 옵션을 제거하세요.")
            return
        
        # 워크플로우 실행
        typer.echo(f"🚀 워크플로우 시작: {config.name}")
        executor = WorkflowExecutor(config)
        result = asyncio.run(executor.execute())
        
        if result.overall_success:
            typer.echo("🎉 모든 조합이 성공적으로 완료되었습니다!")
            raise typer.Exit(0)
        else:
            typer.echo("⚠️  일부 조합이 실패했습니다. 자세한 내용은 로그를 확인하세요.")
            raise typer.Exit(1)
        
    except FileNotFoundError as e:
        typer.echo(f"❌ 파일을 찾을 수 없습니다: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ 워크플로우 실행 중 오류가 발생했습니다: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def validate(
    config_path: str = typer.Argument(..., help="검증할 워크플로우 설정 YAML 파일 경로")
):
    """워크플로우 설정 파일 검증"""
    
    try:
        config = load_workflow_config(config_path)
        print_config_summary(config)
        typer.echo("✅ 설정 파일이 유효합니다.")
        
    except FileNotFoundError as e:
        typer.echo(f"❌ 파일을 찾을 수 없습니다: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ 설정 파일 검증 실패: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def template(
    output_path: str = typer.Option("workflow_template.yaml", "--output", help="생성할 템플릿 파일 경로"),
    include_evaluation: bool = typer.Option(True, "--eval/--no-eval", help="평가 설정 포함 여부")
):
    """워크플로우 설정 템플릿 생성"""
    
    template_content = generate_template(include_evaluation)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        typer.echo(f"✅ 워크플로우 템플릿이 생성되었습니다: {output_path}")
        typer.echo("📝 파일을 편집한 후 'workflow run' 명령으로 실행하세요.")
        
    except Exception as e:
        typer.echo(f"❌ 템플릿 생성 실패: {e}", err=True)
        raise typer.Exit(1)


def print_config_summary(config):
    """설정 요약 출력"""
    print("\n" + "="*60)
    print(f"📋 워크플로우 설정: {config.name}")
    print("="*60)
    
    if config.description:
        print(f"설명: {config.description}")
    
    print(f"🔧 실행 옵션:")
    print(f"  - 병렬 실행: {'예' if config.parallel else '아니오'}")
    print(f"  - 실패시 중단: {'예' if config.fail_fast else '아니오'}")
    
    if config.parsing:
        print(f"\n📂 파싱 설정 ({len(config.parsing)}개):")
        for i, parsing in enumerate(config.parsing):
            print(f"  {i+1}. {parsing.framework} - {Path(parsing.file_path).name}")
    else:
        print(f"\n📂 파싱 설정: 없음 (직접 입력 텍스트 사용)")
    
    print(f"\n🎯 추출 설정 ({len(config.extraction)}개):")
    for i, extraction in enumerate(config.extraction):
        print(f"  {i+1}. {extraction.framework} ({extraction.schema_name})")
    
    if config.evaluation and config.evaluation.enabled:
        print(f"\n📊 평가 설정:")
        print(f"  - Ground Truth: {Path(config.evaluation.gt_json_path).name if config.evaluation.gt_json_path else 'None'}")
        print(f"  - 기준: {config.evaluation.criteria_path}")
    
    print(f"\n🎲 총 조합 수: {config.get_total_combinations()}")
    print("="*60)


def generate_template(include_evaluation: bool) -> str:
    """워크플로우 설정 템플릿 생성"""
    
    template = '''# 워크플로우 설정 파일
# 이 파일을 편집하여 parsing, extraction, evaluation 단계를 설정하세요

# 워크플로우 기본 정보
name: "my_workflow"
description: "문서 처리 워크플로우"
output_dir: "./result/workflow"  # 선택사항, 기본값: result/workflow

# 실행 옵션
parallel: false      # 조합을 병렬로 실행할지 여부
fail_fast: true      # 실패시 즉시 중단할지 여부

# 파싱 설정 (여러 개 설정 가능)
parsing:
  - file_path: "./data/document1.pdf"
    framework: "docling"
    extra_kwargs:
      use_ocr: true
      ocr_lang: "ko"
    save: true
  
  - file_path: "./data/document2.pdf"
    framework: "pypdf"
    extra_kwargs: {}
    save: true

# 추출 설정 (여러 개 설정 가능)
extraction:
  - prompt: "Extract person information from the document"
    schema_name: "schema_han"
    framework: "openai"
    host_info:
      provider: "openai"
      model: "gpt-4"
      api_key: "${OPENAI_API_KEY}"  # 환경변수 사용
    retries: 3
    extra_kwargs:
      temperature: 0.1
    save: true
  
  - prompt: "Extract company information from the document"
    schema_name: "schema_han"
    framework: "anthropic"
    host_info:
      provider: "anthropic"
      model: "claude-3-sonnet"
      api_key: "${ANTHROPIC_API_KEY}"
    retries: 2
    extra_kwargs:
      temperature: 0.0
    save: true
'''

    if include_evaluation:
        template += '''
# 평가 설정 (선택사항)
evaluation:
  enabled: true
  gt_json_path: "./data/ground_truth.json"
  schema_name: "schema_han"
  criteria_path: "evaluation/criteria/criteria.json"
  host_info:
    provider: "openai"
    model: "text-embedding-3-small"
    api_key: "${OPENAI_API_KEY}"
  save: true
'''

    return template


if __name__ == "__main__":
    app()
