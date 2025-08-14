## Structured Output Benchmark

LLM 구조화 출력(Structured Output) 추출 성능을 빠르게 비교·측정하고, 정답(JSON)과의 유사도를 정량화·시각화로 평가하는 경량 툴킷입니다. OpenAI / Anthropic / Google / OpenAI-Compatible / Ollama 등 다양한 호스트와 Instructor, LangChain, LlamaIndex, Marvin, Mirascope, LM Format Enforcer 등 여러 프레임워크를 통일된 인터페이스로 실험할 수 있습니다.

## 목차
1. 프로젝트 개요
2. 기술 스택 및 아키텍처
3. 설치 가이드
4. 설정 가이드(.env, config 예시)
5. 프로젝트 구조와 실행 모드(API/CLI)
6. API 사용법(요청/응답 샘플·상태코드·예시 코드)
7. CLI 사용법
8. 데이터 스키마와 평가 기준
9. 결과물 구조
10. 개발 가이드(로컬 개발, 코드 스타일, 기여)
11. 트러블슈팅
12. 빠른 시작(Quick Start)

## 1) 프로젝트 개요
- 목적: 다양한 LLM과 프레임워크에서 구조화된 JSON을 안정적으로 추출하고, 정답과의 유사도를 일관된 기준으로 평가·시각화합니다.
- 주요 기능
	- API/CLI 제공: 추출·평가·시각화를 단일 프로젝트에서 실행
	- 멀티 호스트/프레임워크: OpenAI/Anthropic/Google/OpenAI-Compatible/Ollama + 여러 추출 프레임워크
	- 평가 및 대시보드: 임베딩 유사도와 완전일치 점수를 혼합해 정량 평가, Streamlit 대시보드 제공
- 범위: 개인 이력서 등 한국어 텍스트 스키마 예시 제공(schema_han) 기반 확장 용이

## 2) 기술 스택 및 아키텍처
- 언어/런타임: Python 3.12+
- 서버: FastAPI, Uvicorn
- 데이터/ML: Pydantic v2, numpy, pandas, transformers, langchain, openai, anthropic, google-generativeai, llama-index 등
- 시각화: Streamlit, Plotly
- 로깅/추적: loguru, Langfuse(선택)
- 구조 개요
	- api_server: REST API 라우터, 서비스 계층, 설정
	- core: 추출/평가 핵심 로직, 로깅/트레이싱, 타입 정의
	- extraction_module: 프레임워크 실행 추상화, 호환성 매핑, 스키마
	- evaluation_module: 정규화/평가/시각화
	- result: 각 작업별 출력 폴더(추출/평가)

## 3) 설치 가이드
시스템 요구사항: Python 3.12 이상, Linux/macOS 권장

```bash
curl -fsSL https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync
```

옵션: Docker (예시 템플릿)
- 본 저장소는 Dockerfile을 포함하지 않습니다. 다음과 같은 최소 템플릿을 참고해 직접 구성할 수 있습니다.

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev
COPY . .
ENV API_HOST=0.0.0.0 API_PORT=8000
EXPOSE 8000
CMD ["python", "main.py"]
```

## 4) 설정 가이드(.env, config 예시)
환경 변수(.env): 프로젝트 루트에 배치합니다. 아래 예시 혹은 `.env.example`를 참고하세요.

```ini
# 공통
MODE=INFO
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODELS=gpt-4o-mini
OPENAI_EMBED_MODELS=text-embedding-3-small

# Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODELS=claude-3-5-sonnet-latest

# Google (OpenAI 호환 엔드포인트)
GOOGLE_API_KEY=...
GOOGLE_MODELS=gemini-1.5-flash

# OpenAI-Compatible (OpenAI 호환 서버)
OPENAI_COMPATIBLE_BASEURL=http://localhost:8000/v1
OPENAI_COMPATIBLE_MODELS=openai/gpt-oss-120b
OPENAI_COMPATIBLE_API_KEY=dummy

OPENAI_COMPATIBLE_EMBED_BASEURL=http://localhost:8000/v1
OPENAI_COMPATIBLE_EMBED_MODELS=Qwen/Qwen3-Embedding-8B
OPENAI_COMPATIBLE_EMBED_API_KEY=dummy

# Ollama (OpenAI 호환 서버)
OLLAMA_BASEURL=http://localhost:11434/v1
OLLAMA_MODELS=llama3.1:8b
OLLAMA_API_KEY=dummy

# HuggingFace 임베딩(로컬)
HUGGINGFACE_EMBED_MODELS=jhgan/ko-sroberta-multitask

# Langfuse(선택)
LANGFUSE_HOST=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...

# 기타
MAX_FILE_SIZE=10485760
TASK_TIMEOUT=3600
```


## 5) 프로젝트 구조와 실행 모드
```
├── main.py                     # 메인 진입점(API 서버 시작 또는 CLI 실행)
├── cli.py                      # Typer CLI
├── api_server/                 # FastAPI 서버
│   ├── main.py                # FastAPI 앱 및 라우터 등록, CORS/예외 처리
│   ├── config.py              # 서버 설정 로딩(Settings)
│   ├── routers/               # extraction/evaluation/utils/visualization 라우터
│   └── services/              # 추출/평가 서비스 계층
├── core/                       # 타입/로깅/트레이싱 + 핵심 로직(extraction/evaluation)
├── extraction_module/          # 프레임워크 추상화, 스키마, 호환성 매핑
├── evaluation_module/          # 평가/시각화
└── result/                    # 결과 저장 디렉터리
```

실행 모드
- API 서버: 기본. uvicorn을 통해 FastAPI 실행
- CLI: Typer 기반 extract/eval/viz 3가지 커맨드

## 6) API 사용법
Base URL: http://localhost:8000

참고: 각 엔드포인트의 상세 파라미터/응답/예시는 Swagger UI(/docs)에서 자동 문서로 확인할 수 있습니다.

### 6.1 추출 API
- POST /v1/extraction
- Request Body(요약)
	- input_text: 문자열 또는 텍스트 파일 경로
	- schema_name: 스키마 이름(기본 schema_han)
	- retries, framework, host_info(필수: provider/base_url/model)
	- kwargs: 프레임워크/LLM 파라미터 딕셔너리(JSON). 예: {"temperature":0.1, "timeout":900, "seed":42}
- Response(요약)
	- success, message, data.result(JSON), success_rate, latency, result_path, output_dir, langfuse_url

예시(cURL)
```bash
curl -X POST http://localhost:8000/v1/extraction \
	-H 'Content-Type: application/json' \
	-d '{
		"input_text": "안녕하세요. 제 이름은 홍길동입니다.",
		"schema_name": "schema_han",
		"retries": 1,
		"kwargs": {"temperature": 0.1, "timeout": 900},
		"framework": "OpenAIFramework",
		"host_info": {"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
	}'
```

예시(Python)
```python
import requests
payload = {
	"input_text": "안녕하세요. 제 이름은 홍길동입니다.",
	"schema_name": "schema_han",
	"framework": "OpenAIFramework",
	"kwargs": {"temperature": 0.1, "timeout": 900},
	"host_info": {"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
}
r = requests.post("http://localhost:8000/v1/extraction", json=payload)
print(r.json())
```

상태코드
- 200: 성공, 400: 입력 유효성 오류, 500: 내부 서버 오류

### 6.2 평가 API
- POST /v1/evaluation
- Request Body(요약)
	- pred_json_path, gt_json_path: 예측/정답 JSON 경로
	- schema_name, criteria_path(선택)
	- host_info: 임베딩 백엔드(provider/base_url/model)
- Response(요약)
	- success, overall_score, eval_result_path, output_dir, fields별 상세 리포트 포함(data.result)

예시(cURL)
```bash
curl -X POST http://localhost:8000/v1/evaluation \
	-H 'Content-Type: application/json' \
	-d '{
		"pred_json_path": "result/extraction/20250812_0850/result.json",
		"gt_json_path": "sample_gt/리멤버-s1.json",
		"schema_name": "schema_han",
		"host_info": {"provider": "huggingface", "base_url": "", "model": "jhgan/ko-sroberta-multitask"}
	}'
```

상태코드
- 200: 성공, 400: 경로 누락 등 요청 오류, 500: 내부 서버 오류

### 6.3 유틸리티/시각화 API
- GET /v1/utils/providers: 사용 가능한 호스트 목록
- GET /v1/utils/frameworks?provider=openai: 호스트별 지원 프레임워크 목록
- GET /v1/utils/schemas: 사용 가능한 스키마 파일 목록
- GET /v1/visualization/streamlit/{eval_result_path}: Streamlit URL 반환(서버 별도 실행 필요)
- POST /v1/visualization/generate: 간단 HTML 리포트 생성(정적)
- GET /v1/visualization/html/{eval_result_path}: 생성된 HTML 리포트 반환

요청/응답 예시 - POST /v1/visualization/generate

Request Body
```json
{
	"eval_result_path": "result/evaluation/20250812_0854/eval_result.json",
	"output_dir": "result/visualization/20250812_120000",   // optional, 기본은 eval_result와 동일 폴더
	"html_filename": "visualization.html"                    // optional, 기본값 visualization.html
}
```

Response (요약)
```json
{
	"success": true,
	"message": "시각화 생성 완료",
	"data": {
		"overall_score": 0.873,
		"html_path": "result/visualization/20250812_120000/visualization.html",
		"output_dir": "result/visualization/20250812_120000"
	},
	"html_path": "result/visualization/20250812_120000/visualization.html",
	"output_dir": "result/visualization/20250812_120000",
	"overall_score": 0.873
}
```

## 7) CLI 사용법

추출(run)
```bash
python main.py --cli run --input ./sample.txt --schema schema_han --retries 1 --kwargs '{"temperature":0.1,"timeout":900}'
```

평가(eval)
```bash
python main.py --cli eval \
	--pred-json result/extraction/<YYYYMMDD_HHMM>/result.json \
	--gt-json sample_gt/리멤버-s1.json \
	--schema schema_han
```

시각화(viz)
```bash
# Streamlit 대시보드 실행 (별도 streamlit 서버가 실행됩니다)
python main.py --cli viz --eval-result result/evaluation/<YYYYMMDD_HHMM>/eval_result.json

# 정적 HTML 생성(간단 리포트)
python main.py --cli viz --eval-result result/evaluation/<YYYYMMDD_HHMM>/eval_result.json --html

# 정적 HTML 생성 + 출력 경로 지정
python main.py --cli viz --eval-result result/evaluation/<YYYYMMDD_HHMM>/eval_result.json --html --out result/visualization/custom_dir
```

프로그램에서 직접 호출(코어 함수)
```python
from structured_output_benchmark.core.visualization import run_visualization_core

result = run_visualization_core(
	eval_result_path="result/evaluation/20250812_0854/eval_result.json",
	# output_dir=None,  # 기본은 eval_result.json과 동일 폴더에 생성
	# html_filename="visualization.html",
)
print(result["html_path"])  # 생성된 HTML 경로
```

지원 프레임워크/호스트 매핑: `extraction_module/framework_compatibility.yaml`

## 8) 데이터 스키마와 평가 기준
- 스키마: Pydantic v2 모델. 기본 스키마는 `extraction_module/schema/schema_han.py`의 `ExtractInfo`.
- 평가 기준(criteria): 최초 평가 시 자동 생성 또는 `evaluation_module/criteria.json` 로드. 각 필드별 exact/embedding 방식 선택.
- 정규화: 예측 JSON을 정답 구조에 맞춰 정렬/보정(`normalize_prediction_json`).

## 9) 결과물 구조
- 추출: `result/extraction/<timestamp>/`
	- `result.json`, `extraction.log`, 집계 CSV(`result/extraction_result.csv`)
- 평가: `result/evaluation/<timestamp>/`
	- `pred.json`, `gt.json`, `norm_pred.json`, `criteria.json`, `eval_result.json`, `evaluation.log`, 집계 CSV(`result/evaluation_result.csv`)

## 10) 개발 가이드
- 로컬 개발
	- 환경: Python 3.12+, uv 권장. `.env` 준비 후 `python main.py`로 서버 실행
	- 포맷/스타일: black/ruff 등 통일 도구 권장(프로젝트에 강제 설정은 없음)
	- 타입: Pydantic v2 모델 사용, FastAPI 스키마 자동화 활용
- 코드 구조
	- 라우터는 서비스 계층을 호출하고, 서비스는 core 로직으로 위임
	- 공용 타입(`core/types.py`)을 통해 API/CLI 모두 일관된 입력/출력
- 기여 방법
	1) 이슈 생성 → 2) 브랜치 생성 → 3) 변경사항 커밋/PR → 4) 리뷰/머지
	- 문서/주석/테스트 추가 환영. 기능 변경 시 최소 재현 예시 포함 권장

## 11) 트러블슈팅
- 포트 충돌: `--port` 변경 또는 `.env`의 `API_PORT` 조정
- 인증/키: 각 호스트의 API 키/엔드포인트 설정 필수. vLLM/Ollama는 OpenAI 호환 서버(/v1) 필요
- 대용량 파일: `MAX_FILE_SIZE` 조정. 지원 확장자: .txt/.json/.pdf/.docx/.md
- 초기 지연: 모델/임베딩 다운로드로 첫 실행이 느릴 수 있음

## 12) 빠른 시작(Quick Start)
```bash
python main.py

curl -X POST http://localhost:8000/v1/extraction \
	-H 'Content-Type: application/json' \
	-d '{
		"input_text": "안녕하세요. 저는 홍길동입니다.",
		"schema_name": "schema_han",
		"framework": "OpenAIFramework",
		"host_info": {"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
	}'
```

라이선스: 저장소에 라이선스 파일이 없으므로 사용 전 조직 정책을 따르거나 LICENSE를 추가하세요.

