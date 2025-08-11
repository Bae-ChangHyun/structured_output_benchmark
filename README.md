## Structured Output Benchmark

LLM 프레임워크별 구조화 출력(Structured Output) 추출 성능을 빠르게 비교하고, 정답(JSON)과의 유사도를 정량/시각화로 평가하는 경량 툴킷입니다. 
`OpenAI`/`Anthropic`/`Google`/`Ollama`/`vLLM` 등 다양한 호스트와 `Instructor`, `LangChain`, `LlamaIndex`, `Marvin`, `Mirascope`, `LM Format Enforcer` 등 여러 프레임워크를 통일된 인터페이스로 실험할 수 있습니다.

## 목차
- [주요 기능](#주요-기능)
- [설치](#설치)
- [환경 변수](#환경-변수env)
- [사용법](#사용법)
  - [프로젝트 구조](#프로젝트-구조)
  - [실행 모드](#실행-모드)
- [API 사용법](#api-사용법)
- [CLI 사용법](#cli-사용법-기존-방식)
- [빠른 시작 예시](#빠른-시작-예시)
- [데이터 스키마](#데이터-스키마)
- [결과물 구조 요약](#결과물-구조-요약)
- [확장 가이드](#확장-가이드)
- [트러블슈팅](#트러블슈팅)

### 주요 기능
- **CLI 모드**: 인터랙티브로 Host·Framework 선택 후 JSON 스키마 기반 추출 실행
- **API 서버 모드**: FastAPI 기반 REST API 서버로 웹/앱에서 활용 가능
- **파일 업로드 지원**: CLI와 API 모두에서 텍스트 파일 업로드를 통한 추출 지원
- 예측 결과(JSON) vs 정답(JSON) 평가: 구조 정규화 + 의미 유사도(임베딩)/완전일치 혼합
- Streamlit 기반 평가 결과 시각화 대시보드 제공

### 새로운 기능 ✨
- **FastAPI REST API**: 웹 애플리케이션이나 다른 서비스에서 HTTP API를 통해 기능 사용 가능
- **비동기 작업 지원**: 긴 작업을 백그라운드에서 실행하고 상태 추적 가능
- **파일 업로드 API**: 웹을 통해 텍스트 파일을 업로드하여 추출/평가 실행


## 설치

요구 사항
- Python 3.12 이상

```bash
curl -fsSL https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync
```

## 환경 변수(.env)
프로젝트 루트에 `.env` 파일을 만들고 필요한 키를 설정하세요. 선택한 Host에 따라 일부만 필요합니다.

예시
```ini
# 공통(선택)
MODE=INFO

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODELS=gpt-4.1-nano

# Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODELS=claude-3-7-sonnet-20250219 # 코드 기본값: claude-sonnet-4-20250514

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
├── main.py                    # 메인 진입점 (API 서버 시작 또는 CLI 실행)
├── cli.py                     # CLI 명령어 (기존 main.py)
├── api_server/                # FastAPI 서버
│   ├── main.py               # FastAPI 애플리케이션
│   ├── config.py             # 서버 설정
│   ├── models/               # Pydantic 모델들
│   ├── routers/              # API 라우터들
│   └── services/             # 비즈니스 로직
├── extraction_module/         # 추출 모듈
├── evaluation_module/         # 평가 모듈
└── result/                   # 결과 저장소
```

### 실행 모드

#### 1) API 서버 모드 (기본값)
FastAPI 서버를 시작하여 REST API로 기능을 제공합니다.

```bash
# 기본 설정으로 API 서버 시작
python main.py

# 커스텀 호스트/포트로 시작
python main.py --host 127.0.0.1 --port 8080

# 개발 모드 (자동 리로드)
python main.py --reload
```

서버가 시작되면:
- API 서버: `http://localhost:8000`
- API 문서: `http://localhost:8000/docs` (Swagger UI)
- ReDoc 문서: `http://localhost:8000/redoc`

#### 2) CLI 모드
기존과 동일한 터미널 기반 인터페이스를 사용합니다.

```bash
# CLI 모드로 추출 실행
python main.py --cli run --input "안녕하세요. 제 이력은 ..." \
    --schema schema_han \
    --retries 1 \
    --temperature 0.1 \
    --timeout 900

# CLI 모드로 평가 실행
python main.py --cli eval \
    --pred-json result/extraction/20250808_1755/result_20250808_1755.json \
    --gt-json sample_gt/리멤버-s1.json \
    --schema schema_han

# CLI 모드로 시각화 실행
python main.py --cli viz --eval-result result/evaluation/20250808_1757/eval_result.json
```

## API 사용법

### 1) 추출 API

**동기 추출 (즉시 결과 반환)**
```bash
curl -X POST "http://localhost:8000/api/v1/extraction/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "안녕하세요. 제 이름은 김철수입니다...",
    "schema": "schema_han",
    "temperature": 0.1,
    "retries": 1,
    "host_choice": 1,
    "framework_choice": 1
  }'
```

**비동기 추출 (백그라운드 실행)**
```bash
# 작업 시작
curl -X POST "http://localhost:8000/api/v1/extraction/run-async" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "긴 텍스트...",
    "schema": "schema_han"
  }'

# 작업 상태 확인
curl "http://localhost:8000/api/v1/extraction/status/{task_id}"
```

**파일 업로드를 통한 추출**
```bash
curl -X POST "http://localhost:8000/api/v1/extraction/upload" \
  -F "file=@document.txt" \
  -F "schema=schema_han" \
  -F "temperature=0.1" \
  -F "retries=1"
```

### 2) 평가 API

**JSON 파일 경로를 통한 평가**
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

**파일 업로드를 통한 평가**
```bash
curl -X POST "http://localhost:8000/api/v1/evaluation/upload" \
  -F "pred_file=@prediction.json" \
  -F "gt_file=@ground_truth.json" \
  -F "schema_name=schema_han" \
  -F "embed_backend=openai"
```

### 3) 유틸리티 API

```bash
# 사용 가능한 호스트 목록
curl "http://localhost:8000/api/v1/utils/hosts"

# 호스트별 호환 프레임워크 목록
curl "http://localhost:8000/api/v1/utils/frameworks?host=openai"

# 사용 가능한 스키마 목록
curl "http://localhost:8000/api/v1/utils/schemas"

# 환경 설정 정보
curl "http://localhost:8000/api/v1/utils/config"
```

### 4) 시각화 API

```bash
# Streamlit URL 생성
curl "http://localhost:8000/api/v1/visualization/streamlit/{result_path}"

# HTML 시각화 생성
curl -X POST "http://localhost:8000/api/v1/visualization/generate" \
  -H "Content-Type: application/json" \
  -d '{"eval_result_path": "result/evaluation/.../eval_result.json"}'
```

## CLI 사용법 (기존 방식)

CLI는 Typer 기반이며 세 가지 하위 명령을 제공합니다.

### 1) Structured output 추출 (CLI)
프롬프트 문자열 또는 텍스트 파일 경로를 입력해 구조화 추출을 수행합니다. 실행 중 Host/Framework를 터미널에서 인터랙티브로 선택합니다.

```bash
# 프롬프트 문자열로 실행
python main.py --cli run --input "안녕하세요. 제 이력은 ..." \
	--schema schema_han \
	--retries 1 \
	--temperature 0.1 \
	--timeout 900

# 프롬프트 파일로 실행
python main.py --cli run --input ./sample.txt --schema schema_han
```

- 스키마: 기본 제공 `schema`(Pydantic BaseModel: `ExtractInfo`) <br>
	**반드시 스키마의 최종 클래스명은 ExtractInfo여야 하며, extraction_module/schema 폴더에 들어있어야 합니다.**
	<details>
	<summary>스키마 파일 구조</summary>

	```python
	from pydantic import BaseModel, Field
	from typing import List, Optional

	# 개인정보
	class PersonalInfo(BaseModel):
		name: Optional[str] = Field(description="이름", default=None)
		gender: Optional[str] = Field(description="성별(남자/여자)", default=None)
		nationality_type: Optional[str] = Field(description="외국인/내국인", default=None)
		nationality: Optional[str] = Field(description="국가명", default=None)
		birth: Optional[str] = Field(description="생년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
		contacts: List[str] = Field(description="연락처(전화번호)", default_factory=list)
		email: Optional[str] = Field(description="이메일", default=None)
		address: Optional[str] = Field(description="주소", default=None)
		available_date: Optional[str] = Field(description="입사가능시기", default=None)
		sns_links: List[str] = Field(description="SNS 링크(깃헙/링크드인/블로그 등)", default_factory=list)
		desired_job: Optional[str] = Field(description="희망직무", default=None)
		desired_location: Optional[str] = Field(description="희망 근무지", default=None)
		desired_position: Optional[str] = Field(description="희망 직급", default=None)
		desired_salary: Optional[str] = Field(description="희망 급여", default=None)

	class MilitaryService(BaseModel):
		military_status: Optional[str] = Field(description="병역대상(군필, 미필, 면제, 복무중, 해당없음)", default=None)
		service_start_date: Optional[str] = Field(description="입대년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
		service_end_date: Optional[str] = Field(description="제대년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
		military_branch: Optional[str] = Field(description="군별(육군,해군,공군,해병 등)", default=None)
		rank: Optional[str] = Field(description="제대계급(이병, 일병, 상병, 병장)", default=None)

	class ExtractInfo(BaseModel):
		personal_info: Optional[PersonalInfo] = Field(description="개인정보", default=None)
		military_service: Optional[MilitaryService] = Field(description="병역", default=None)
	```
	</details>

- 결과물: `result/extraction/<YYYYMMDD_HHMM>/result_<ts>.json` 및 로그 저장
- 실험 요약/추적 링크는 Langfuse 설정 시 기록됩니다

지원 프레임워크
- [OpenAIFramework](https://platform.openai.com/docs/guides/structured-outputs)
- [GoogleFramework](https://ai.google.dev/gemini-api/docs/structured-output?lang=python&authuser=1&hl=ko)
- [AnthropicFramework](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview#json-mode)
- [InstructorFramework](https://python.useinstructor.com/)
- [LangchainToolFramework](https://python.langchain.com/docs/how_to/structured_output/#the-with_structured_output-method)
- [LangchainParserFramework](https://python.langchain.com/docs/how_to/structured_output/#prompting-and-parsing-model-outputs-directly)
- [MirascopeFramework](https://mirascope.com/docs/mirascope/learn/output_parsers)
- [LlamaIndexFramework](https://docs.llamaindex.ai/en/stable/examples/output_parsing/llm_program/)
- [MarvinFramework](https://github.com/PrefectHQ/marvin)
- [OllamaFramework](https://ollama.com/blog/structured-outputs)
- [LMFormatEnforcerFramework](https://github.com/noamgat/lm-format-enforcer)


Host별 호환성은 [extraction_module/framework_compatibility.yaml](extraction_module/framework_compatibility.yaml)를 참고하세요. <br>
해당 파일을 기반으로 호환되는 프레임워크를 사용가능하도록 구현해놨으니, 파일은 수정하면 안됩니다.


### 2) 평가(eval) (CLI)
예측 JSON과 정답 JSON을 비교해 점수와 상세 리포트를 생성합니다.

```bash
python main.py --cli eval \
	--pred-json result/extraction/20250808_1755/result_20250808_1755.json \
	--gt-json sample_gt/리멤버-s1.json \
	--schema schema_han \
	--embed-backend huggingface \
	--model-name jhgan/ko-sroberta-multitask
```

임베딩 백엔드
- huggingface: 기본값(모델 미지정 시 `jhgan/ko-sroberta-multitask`)
- openai: OpenAI Embeddings 사용(예: `text-embedding-3-large`)
- vllm/ollama: OpenAI 호환 임베딩 엔드포인트 필요(`--api-base http://host:port`)

옵션
- `--api-key`, `--api-base`: openai/vllm/ollama 백엔드 사용 시 필요할 수 있음
- `--run-folder`: 외부 경로에 결과를 함께 보관하고 싶을 때 사용

출력물
- `result/evaluation/<YYYYMMDD_HHMM>/`
	- `pred.json`, `gt.json`: 입력 복사본
	- `criteria.json`: 필드별 평가 기준(exact/embedding) 자동 생성 또는 기존 파일 로드
	- `norm_pred.json`: 정답 구조로 정규화된 예측 결과
	- `eval_result.json`: 전체/필드별 점수 리포트
	- `evaluation.log`: 로그
- 집계 CSV: `result/evaluation_result.csv`


### 3) 시각화(viz) (CLI)
평가 결과(JSON)를 Streamlit 대시보드로 시각화합니다.

```bash
python main.py --cli viz --eval-result result/evaluation/20250808_1757/eval_result.json
```

명령 실행 후 기본 브라우저에서 `http://localhost:8501`로 접속합니다.


## 데이터 스키마
스키마는 Pydantic v2 기반이며, 파일명은 인자로 사용됩니다.
- 기본 스키마: `schema_han.py` 내 `ExtractInfo` 모델
- 평가 기준(criteria): 최초 평가 시 자동 생성되어 `criteria.json`으로 저장됩니다.


## 결과물 구조 요약
- 추출 로그/결과: `result/extraction/<timestamp>/`
- 평가 로그/리포트: `result/evaluation/<timestamp>/`
- 집계 CSV: `result/extraction_result.csv`, `result/evaluation_result.csv`


## 확장 가이드
- 새 스키마 추가: `extraction_module/schema/schema_xxx.py`에 `ExtractInfo` 모델 정의 후 `--schema schema_xxx`로 사용
- 프레임워크/호스트 확장: `extraction_module/frameworks/`에 구현 추가 → `extraction_module/__init__.py`의 `frameworks` 맵에 등록 → `framework_compatibility.yaml`에 호스트 매핑 추가
- API 엔드포인트 확장: `api_server/routers/`에 새 라우터 추가 후 `api_server/main.py`에 등록


## API 서버 설정
환경변수를 통해 API 서버를 설정할 수 있습니다:

```ini
# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# 파일 업로드 설정
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760  # 10MB
TASK_TIMEOUT=3600       # 1시간
```


## 트러블슈팅
- **API 서버**: 서버가 시작되지 않으면 포트 충돌을 확인하세요 (`--port` 옵션 사용)
- **Host 선택**: 키가 없거나 Base URL이 올바르지 않으면 요청 실패가 발생할 수 있습니다. `.env`를 확인하세요.
- **vLLM/Ollama**: OpenAI 호환 서버가 실행 중이어야 합니다(`.../v1` 경로).
- **파일 업로드**: 허용된 파일 형식(.txt, .json, .pdf, .docx, .md)인지 확인하세요.
- **처음 실행**: 임베딩/모델 다운로드로 시간이 걸릴 수 있습니다.


## 빠른 시작 예시

### API 서버 모드
```bash
# 1. 서버 시작
python main.py

# 2. 다른 터미널에서 API 테스트
curl -X POST "http://localhost:8000/api/v1/extraction/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "안녕하세요. 저는 김철수이고 서울에 거주하며 개발자로 일하고 있습니다.",
    "schema": "schema_han",
    "host_choice": 1
  }'
```

### CLI 모드
```bash
# 추출 실행
python main.py --cli run --input "안녕하세요. 저는 김철수입니다." --schema schema_han

# 평가 실행 (추출 결과와 정답 JSON 필요)
python main.py --cli eval --pred-json result/extraction/.../result.json --gt-json sample_gt/리멤버-s1.json
```

## 라이선스
프로젝트 루트에 라이선스 파일이 없으므로, 사용 전에 조직 정책에 따라 라이선스를 지정하세요.

