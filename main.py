#!/usr/bin/env python3
"""
Structured Output Benchmark - 메인 진입점

이 파일은 다음 중 하나를 실행할 수 있습니다:
1. FastAPI 서버 시작 (기본값)
2. CLI 명령어 실행

사용법:
  python main.py                    # FastAPI 서버 시작
  python main.py --cli [args...]    # CLI 명령어 실행
"""

import sys
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Structured Output Benchmark")
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="CLI 모드로 실행 (기본값: FastAPI 서버 시작)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="API 서버 호스트 (기본값: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="API 서버 포트 (기본값: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="개발 모드 (자동 리로드)"
    )
    
    # --cli 옵션이 있으면 나머지 인수를 CLI로 전달
    if "--cli" in sys.argv:
        cli_index = sys.argv.index("--cli")
        # --cli 이후의 모든 인수를 CLI로 전달
        cli_args = sys.argv[cli_index + 1:]
        
        # CLI 모듈 실행
        from structured_output_benchmark.cli import app as cli_app
        sys.argv = ["cli.py"] + cli_args
        cli_app()
    else:
        # FastAPI 서버 시작
        args, unknown = parser.parse_known_args()
        
        print("🚀 Structured Output Benchmark API 서버를 시작합니다...")
        print(f"📍 서버 주소: http://{args.host}:{args.port}")
        print(f"📖 API 문서: http://{args.host}:{args.port}/docs")
        print("🛑 서버 종료: Ctrl+C")
        
        uvicorn.run(
            "structured_output_benchmark.api_server.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )


if __name__ == "__main__":
    main()
