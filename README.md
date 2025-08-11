## Structured Output Benchmark

LLM 프레임워크별 구조화 출력(Structured Output) 추출 성능을 빠르게 비교하고, 정답(JSON)과의 유사도를 정량/시각화로 평가하는 경량 툴킷입니다. 
`OpenAI`/`Anthropic`/`Google`/`Ollama`/`vLLM` 등 다양한 호스트와 `Instructor`, `LangChain`, `LlamaIndex`, `Marvin`, `Mirascope`, `LM Format Enforcer` 등 여러 프레임워크를 통일된 인터페이스로 실험할 수 있습니다.

### 주요 기능
- 인터랙티브로 Host·Framework 선택 후 JSON 스키마 기반 추출 실행
- 예측 결과(JSON) vs 정답(JSON) 평가: 구조 정규화 + 의미 유사도(임베딩)/완전일치 혼합
- Streamlit 기반 평가 결과 시각화 대시보드 제공


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
CLI는 Typer 기반이며 세 가지 하위 명령을 제공합니다.

### 1) Structured output 추출
프롬프트 문자열 또는 텍스트 파일 경로를 입력해 구조화 추출을 수행합니다. 실행 중 Host/Framework를 터미널에서 인터랙티브로 선택합니다.

```bash
# 프롬프트 문자열로 실행
python main.py run --prompt "안녕하세요. 제 이력은 ..." \
	--schema schema_han \
	--retries 1 \
	--temperature 0.1 \
	--timeout 900

# 프롬프트 파일로 실행
python main.py run --prompt ./sample.txt --schema schema
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


### 2) 평가(eval)
예측 JSON과 정답 JSON을 비교해 점수와 상세 리포트를 생성합니다.

```bash
python main.py eval \
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


### 3) 시각화(viz)
평가 결과(JSON)를 Streamlit 대시보드로 시각화합니다.

```bash
python main.py viz --eval-result result/evaluation/20250808_1757/eval_result.json
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
- 새 스키마 추가: `schema_xxx.py`에 `ExtractInfo` 모델 정의 후 `--schema schema_xxx`로 사용
- 프레임워크/호스트 확장: `extraction_module/frameworks/`에 구현 추가 → `extraction_module/__init__.py`의 `frameworks` 맵에 등록 → `framework_compatibility.yaml`에 호스트 매핑 추가


## 트러블슈팅
- Host 선택 시 키가 없거나 Base URL이 올바르지 않으면 요청 실패가 발생할 수 있습니다. `.env`를 확인하세요.
- vLLM/Ollama는 OpenAI 호환 서버가 실행 중이어야 합니다(`.../v1` 경로).
- 처음 실행 시 임베딩/모델 다운로드로 시간이 걸릴 수 있습니다.


## 라이선스
프로젝트 루트에 라이선스 파일이 없으므로, 사용 전에 조직 정책에 따라 라이선스를 지정하세요.

