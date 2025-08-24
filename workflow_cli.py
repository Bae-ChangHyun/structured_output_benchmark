"""
Main workflow CLI entry point
기존 cli.py를 수정하지 않고 독립적으로 실행 가능한 워크플로우 CLI
"""

import typer
from structured_output_kit.workflow.cli import app as workflow_app

# 워크플로우 전용 CLI 앱
main_app = typer.Typer(
    help="StructuredOutputKit 워크플로우 도구",
    no_args_is_help=True
)

# 워크플로우 명령들을 메인 앱에 추가
main_app.add_typer(workflow_app, name="workflow", help="통합 워크플로우 실행")

if __name__ == "__main__":
    main_app()
