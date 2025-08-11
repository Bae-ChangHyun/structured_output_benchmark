## Structured Output Benchmark

LLM 구조화 출력(Structured Output) 추출 성능을 빠르게 비교·측정하고, 정답(JSON)과의 유사도를 정량/시각화로 평가하는 경량 툴킷입니다.
OpenAI / Anthropic / Google / Ollama / vLLM 등 다양한 호스트와 Instructor, LangChain, LlamaIndex, Marvin, Mirascope, LM Format Enforcer 등 여러 프레임워크를 통일된 인터페이스로 실험할 수 있습니다.

## 목차
- 주요 기능
- 설치
- 환경 변수(.env)
- 사용법: 프로젝트 구조 · 실행 모드(API/CLI)
- API 사용법
- CLI 사용법
- 빠른 시작 예시
- 데이터 스키마
- 결과물 구조 요약
- 확장 가이드
- 트러블슈팅

## 주요 기능
- CLI 모드: 인터랙티브 Host/Framework 선택 후 JSON 스키마 기반 추출 실행
- API 서버 모드: FastAPI 기반 REST API 서버 제공(동기/비동기 작업, 파일 업로드 지원)
- 평가: 예측(JSON) vs 정답(JSON) 비교(구조 정규화 + 임베딩 유사도/완전일치 혼합)
- 시각화: Streamlit 기반 평가 결과 대시보드

## 설치
요구 사항: Python 3.12 이상

```bash
curl -fsSL https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync
```

## 환경 변수(.env)
프로젝트 루트에 `.env` 파일을 만들고 필요한 키를 설정하세요(선택한 Host에 따라 일부만 필요).

```ini
# 공통(선택)
MODE=INFO

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODELS=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODELS=claude-3-sonnet-20240229

# Google (OpenAI 호환 엔드포인트)
GOOGLE_API_KEY=...
GOOGLE_MODELS=gemini-1.5-flash

# Ollama (로컬 OpenAI 호환)
OLLAMA_HOST=http://localhost:11434/v1
OLLAMA_MODELS=llama3.1:8b

# vLLM (OpenAI 호환 서버)
VLLM_BASEURL=http://localhost:8000
VLLM_MODELS=openai/gpt-oss-120b

# Langfuse (선택: 추적/리포트)
LANGFUSE_HOST=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

## 사용법

### 프로젝트 구조
```
├── main.py                    # 메인 진입점(API 서버 시작 또는 CLI 실행)
├── cli.py                     # Typer CLI
├── api_server/                # FastAPI 서버
│   ├── main.py               # FastAPI 애플리케이션 및 라우터 등록
│   ├── config.py             # 서버/업로드 설정
│   ├── models/               # Pydantic 모델
│   ├── routers/              # extraction/evaluation/utils/visualization
│   └── services/             # 추출/평가/파일 서비스 로직
├── extraction_module/         # 추출 모듈 및 프레임워크
├── evaluation_module/         # 평가/시각화 모듈
└── result/                   # 결과 저장 디렉터리
```

### 실행 모드

#### 1) API 서버 모드(기본)
```bash
# 기본 설정으로 시작
python main.py

# 커스텀 호스트/포트
python main.py --host 127.0.0.1 --port 8080

# 개발 모드(자동 리로드)
python main.py --reload
```
접속 정보
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 2) CLI 모드
```bash
# 추출 실행
python main.py --cli run --input "안녕하세요. 제 이력은 ..." \
	--schema schema_han \
	--retries 1 \
	--temperature 0.1 \
	--timeout 900

# 평가 실행
python main.py --cli eval \
	--pred-json result/extraction/<YYYYMMDD_HHMM>/result_<ts>.json \
	--gt-json sample_gt/리멤버-s1.json \
	--schema schema_han \
	--embed-backend openai

# 시각화 실행
python main.py --cli viz --eval-result result/evaluation/<YYYYMMDD_HHMM>/eval_result.json
```

## API 사용법

### 1) 추출 API
- 동기: POST /api/v1/extraction/run
- 비동기: POST /api/v1/extraction/run-async → GET /api/v1/extraction/status/{task_id}
- 파일 업로드: POST /api/v1/extraction/upload

예시(동기)
```bash
curl -X POST "http://localhost:8000/api/v1/extraction/run" \
	-H "Content-Type: application/json" \
	-d '{
		"input_text": "안녕하세요. 제 이름은 김철수입니다...",
		"schema_name": "schema_han",
		"temperature": 0.1,
		"retries": 1,
		"host_choice": 1,
		"framework_choice": 1
	}'
```

### 2) 평가 API
- 동기: POST /api/v1/evaluation/run
- 비동기: POST /api/v1/evaluation/run-async → GET /api/v1/evaluation/status/{task_id}
- 파일 업로드: POST /api/v1/evaluation/upload

예시(동기)
```bash
curl -X POST "http://localhost:8000/api/v1/evaluation/run" \
	-H "Content-Type: application/json" \
	-d '{
		"pred_json_path": "result/extraction/.../result.json",
		"gt_json_path": "sample_gt/리멤버-s1.json",
		"schema_name": "schema_han",
		"embed_backend": "openai"
	}'
```

### 3) 유틸리티/시각화 API
- 유틸: GET /api/v1/utils/hosts, /frameworks?host=..., /schemas, /config
- 시각화: GET /api/v1/visualization/streamlit/{result_path}, POST /api/v1/visualization/generate, GET /api/v1/visualization/html/{result_path}

## CLI 사용법

### 1) 추출(run)
프롬프트 문자열 또는 텍스트 파일 경로 입력. 실행 중 터미널에서 Host/Framework를 선택합니다.

```bash
python main.py --cli run --input ./sample.txt --schema schema_han --retries 1 --temperature 0.1
```

지원 프레임워크
- OpenAIFramework, AnthropicFramework, GoogleFramework, OllamaFramework, InstructorFramework,
	LangchainToolFramework, LangchainParserFramework, LlamaIndexFramework, MarvinFramework,
	MirascopeFramework, LMFormatEnforcerFramework

호환성 매핑: extraction_module/framework_compatibility.yaml

### 2) 평가(eval)
```bash
python main.py --cli eval \
	--pred-json result/extraction/<YYYYMMDD_HHMM>/result_<ts>.json \
	--gt-json sample_gt/리멤버-s1.json \
	--schema schema_han \
	--embed-backend huggingface \
	--model-name jhgan/ko-sroberta-multitask
```

임베딩 백엔드: huggingface(기본)/openai/vllm/ollama
- vLLM/Ollama 사용 시 OpenAI 호환 엔드포인트 API Base 필요(`--api-base http://host:port`)

### 3) 시각화(viz)
```bash
python main.py --cli viz --eval-result result/evaluation/<YYYYMMDD_HHMM>/eval_result.json
```

## 데이터 스키마
- 스키마는 Pydantic v2 기반이며 파일명으로 지정합니다.
- 기본 스키마: extraction_module/schema/schema_han.py 내 최상위 모델 `ExtractInfo`
- 평가 기준(criteria)은 최초 평가 시 자동 생성되어 criteria.json으로 저장됩니다.

## 결과물 구조 요약
- 추출: result/extraction/<timestamp>/result_<ts>.json, extraction.log, 집계 CSV(result/extraction_result.csv)
- 평가: result/evaluation/<timestamp>/eval_result.json, norm_pred.json, criteria.json, evaluation.log, 집계 CSV(result/evaluation_result.csv)

## 확장 가이드
- 스키마 추가: extraction_module/schema/schema_xxx.py에 `ExtractInfo` 정의 후 `--schema schema_xxx`
- 프레임워크/호스트 추가: extraction_module/frameworks/* 구현 → extraction_module/__init__.py 등록 → framework_compatibility.yaml 매핑 추가
- API 확장: api_server/routers/* 추가 후 api_server/main.py 등록

## API 서버 설정(.env)
```ini
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760  # 10MB
TASK_TIMEOUT=3600       # 1시간
```

## 트러블슈팅
- 포트 충돌 시 --port 변경
- 키/엔드포인트 누락 시 요청 실패 → .env 확인
- vLLM/Ollama는 OpenAI 호환 서버가 실행 중이어야 함(…/v1 경로)
- 파일 업로드는 .txt/.json/.pdf/.docx/.md만 허용
- 최초 실행 시 임베딩/모델 다운로드로 시간이 소요될 수 있음

## 빠른 시작 예시

### API 서버
```bash
python main.py

curl -X POST "http://localhost:8000/api/v1/extraction/run" \
	-H "Content-Type: application/json" \
	-d '{
		"input_text": "안녕하세요. 저는 김철수이고 서울에 거주하며 개발자로 일하고 있습니다.",
		"schema_name": "schema_han",
		"host_choice": 1
	}'
```

### CLI
```bash
python main.py --cli run --input "안녕하세요. 저는 김철수입니다." --schema schema_han
python main.py --cli eval --pred-json result/extraction/.../result.json --gt-json sample_gt/리멤버-s1.json
```

## 라이선스
현재 저장소에 라이선스 파일이 없으므로, 사용 전 조직 정책에 따라 라이선스를 지정하세요.

