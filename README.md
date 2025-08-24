# 📊 Structured Output Kit

<div align="center">

**🚀 LLM 구조화 출력 성능을 빠르고 정확하게 비교·평가하는 올인원 벤치마크 툴킷**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.48+-ff4b4b.svg)](https://streamlit.io)

</div>

다양한 LLM 호스트(OpenAI, Anthropic, Google, Ollama 등)와 여러 추출 프레임워크(Instructor, LangChain, LlamaIndex, Marvin 등)를 통일된 인터페이스로 실험하고, 정답 JSON과의 유사도를 정량화하여 시각화할 수 있는 벤치마크 도구입니다.

## ✨ 주요 특징

🔄 **다중 프레임워크 지원**  
- OpenAI, Anthropic, Google, Ollama, OpenAI-Compatible 등 호스트
- Instructor, LangChain, LlamaIndex, Marvin, Mirascope, LM Format Enforcer 등 프레임워크

🎯 **정량적 평가 시스템**  
- 임베딩 유사도와 완전일치 기반 하이브리드 스코어링
- 필드별 세부 평가 리포트 제공

📊 **실시간 시각화**  
- Streamlit 기반 인터랙티브 대시보드
- 정적 HTML 리포트 생성

🚀 **API & CLI 인터페이스**  
- RESTful API 서버 (FastAPI)
- 명령줄 인터페이스 (Typer)

🔧 **확장성**  
- 커스텀 스키마 추가 가능
- 평가 기준 커스터마이징 지원

## 🚀 Quick Start

### 1️⃣ 설치

```bash
# uv 설치 (권장)
curl -fsSL https://astral.sh/uv/install.sh | sh

# 프로젝트 클론 및 의존성 설치
git clone https://github.com/Bae-ChangHyun/StructuredOutputKit.git
cd StructuredOutputKit
uv venv
source .venv/bin/activate
uv sync
```

### 2️⃣ 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일에 API 키 설정
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

### 3️⃣ 30초 테스트

```bash
# API 서버 시작
python main.py

# 새 터미널에서 테스트 실행
curl -X POST http://localhost:8000/v1/extraction \
  -H 'Content-Type: application/json' \
  -d '{
    "input_text": "안녕하세요. 저는 홍길동입니다. 컴퓨터공학과를 졸업했고 Python 개발자로 3년간 근무했습니다.",
    "schema_name": "schema_han",
    "framework": "OpenAIFramework",
    "host_info": {
      "provider": "openai",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4o-mini"
    }
  }'
```

### 4️⃣ CLI로 시작하기

```bash
# 추출 실행
python main.py --cli extract --input "안녕하세요. 김철수입니다. 서울대학교 졸업 후 삼성에서 5년간 근무했습니다."

# 평가 실행 (샘플 데이터 사용)
python main.py --cli eval \
  --pred result/extraction/$(ls result/extraction | tail -1)/result.json \
  --gt data/리멤버-s1.json

# 시각화 실행
python main.py --cli viz --eval-result result/evaluation/$(ls result/evaluation | tail -1)/eval_result.json
```

## 📋 목차

<details>
<summary>📋 목차</summary>

- [설치 가이드](#-설치-가이드)
- [환경 설정](#-환경-설정)
- [사용법](#-사용법)
  - [API 사용법](#api-사용법)
  - [CLI 사용법](#cli-사용법)
- [프로젝트 구조](#-프로젝트-구조)
- [지원 프레임워크](#-지원-프레임워크)
- [스키마와 평가](#-스키마와-평가)
- [시각화](#-시각화)
- [개발 가이드](#-개발-가이드)
- [트러블슈팅](#-트러블슈팅)
- [라이선스](#-라이선스)

</details>

## 📦 설치 가이드

### 시스템 요구사항
- Python 3.12 이상
- Linux/macOS/Windows
- 최소 4GB RAM

### 설치 방법

<details>
<summary><b>방법 1: uv 사용 (권장)</b></summary>

```bash
# uv 설치
curl -fsSL https://astral.sh/uv/install.sh | sh

# 프로젝트 설정
git clone https://github.com/Bae-ChangHyun/StructuredOutputKit.git
cd StructuredOutputKit
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync
```

</details>

<details>
<summary><b>방법 2: pip 사용</b></summary>

```bash
git clone https://github.com/Bae-ChangHyun/StructuredOutputKit.git
cd StructuredOutputKit
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

</details>

<details>
<summary><b>방법 3: Docker (실험적)</b></summary>

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev
COPY . .
ENV API_HOST=0.0.0.0 API_PORT=8000
EXPOSE 8000
CMD ["python", "main.py"]
```

```bash
docker build -t structured-output-kit .
docker run -p 8000:8000 --env-file .env structured-output-kit
```

</details>

## ⚙️ 환경 설정

### 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 필요한 API 키를 설정하세요.

<details>
<summary><b>환경 변수 상세 설정</b></summary>

```ini
# 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# OpenAI
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODELS=gpt-4o-mini
OPENAI_EMBED_MODELS=text-embedding-3-small

# Anthropic
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_MODELS=claude-3-5-sonnet-latest

# Google
GOOGLE_API_KEY=your-api-key
GOOGLE_MODELS=gemini-1.5-flash

# OpenAI-Compatible (vLLM, Together AI 등)
OPENAI_COMPATIBLE_BASEURL=http://localhost:8000/v1
OPENAI_COMPATIBLE_MODELS=your-model-name
OPENAI_COMPATIBLE_API_KEY=dummy

# Ollama
OLLAMA_BASEURL=http://localhost:11434/v1
OLLAMA_MODELS=llama3.1:8b

# HuggingFace (로컬 임베딩)
HUGGINGFACE_EMBED_MODELS=jhgan/ko-sroberta-multitask

# Langfuse (선택사항)
LANGFUSE_HOST=your-langfuse-host
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key

# 제한 설정
MAX_FILE_SIZE=10485760
TASK_TIMEOUT=3600
```

</details>

## 💻 사용법

### API 사용법

#### 서버 시작

```bash
# 기본 실행
python main.py

# 커스텀 포트로 실행
python main.py --port 8080

# 개발 모드 (자동 리로드)
python main.py --reload
```

API 문서: http://localhost:8000/docs

#### 주요 엔드포인트

<details>
<summary><b>🔄 추출 API - POST /v1/extraction</b></summary>

**기본 사용법:**
```bash
curl -X POST http://localhost:8000/v1/extraction \
  -H 'Content-Type: application/json' \
  -d '{
    "input_text": "안녕하세요. 제 이름은 홍길동입니다.",
    "schema_name": "schema_han",
    "framework": "OpenAIFramework",
    "host_info": {
      "provider": "openai",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4o-mini"
    }
  }'
```

**Python 사용법:**
```python
import requests

response = requests.post("http://localhost:8000/v1/extraction", json={
    "input_text": "김철수입니다. 서울대학교 컴퓨터공학과 졸업 후 네이버에서 5년간 근무했습니다.",
    "schema_name": "schema_han",
    "framework": "OpenAIFramework",
    "extra_kwargs": {"temperature": 0.1, "timeout": 900},
    "host_info": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1", 
        "model": "gpt-4o-mini"
    }
})

result = response.json()
print(f"추출 결과: {result['data']['result']}")
print(f"성공률: {result['success_rate']}")
print(f"응답 시간: {result['latency']}초")
```

</details>

<details>
<summary><b>📊 평가 API - POST /v1/evaluation</b></summary>

```bash
curl -X POST http://localhost:8000/v1/evaluation \
  -H 'Content-Type: application/json' \
  -d '{
    "pred_json_path": "result/extraction/20250812_0850/result.json",
    "gt_json_path": "data/리멤버-s1.json",
    "schema_name": "schema_han",
    "host_info": {
      "provider": "huggingface",
      "base_url": "",
      "model": "jhgan/ko-sroberta-multitask"
    }
  }'
```

</details>

<details>
<summary><b>🎨 시각화 API - POST /v1/visualization/generate</b></summary>

```bash
curl -X POST http://localhost:8000/v1/visualization/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "eval_result_path": "result/evaluation/20250812_0854/eval_result.json"
  }'
```

</details>

<details>
<summary><b>🔧 유틸리티 API</b></summary>

```bash
# 지원 호스트 목록
curl http://localhost:8000/v1/utils/providers

# 호스트별 프레임워크 목록  
curl http://localhost:8000/v1/utils/frameworks?provider=openai

# 사용 가능한 스키마 목록
curl http://localhost:8000/v1/utils/schemas
```

</details>

### CLI 사용법

#### 추출 (Extract)

```bash
# 기본 추출
python main.py --cli extract --input "홍길동입니다. 서울대 졸업 후 카카오에서 3년 근무했습니다."

# 파일에서 추출
python main.py --cli extract --input ./sample.txt --schema schema_han

# 고급 옵션
python main.py --cli extract \
  --input "텍스트 내용" \
  --schema schema_han \
  --retries 3 \
  --kwargs '{"temperature":0.1,"timeout":900}' \
  --save
```

#### 평가 (Evaluation)

```bash
# 기본 평가
python main.py --cli eval \
  --pred result/extraction/latest/result.json \
  --gt data/리멤버-s1.json

# 커스텀 평가 기준 사용
python main.py --cli eval \
  --pred result/extraction/latest/result.json \
  --gt data/리멤버-s1.json \
  --criteria evaluation/criteria/custom_criteria.json \
  --save
```

#### 시각화 (Visualization)

```bash
# Streamlit 대시보드 실행
python main.py --cli viz --eval-result result/evaluation/latest/eval_result.json

# 정적 HTML 생성
python main.py --cli viz \
  --eval-result result/evaluation/latest/eval_result.json \
  --html \
  --out result/visualization/custom_dir
```

## 🏗️ 프로젝트 구조
```
structured_output_kit/
├── 📁 main.py                    # 🚀 메인 진입점 (API 서버/CLI 실행)
├── 📁 cli.py                     # 💻 Typer 기반 CLI 인터페이스
├── 📁 server/                    # 🌐 FastAPI 서버
│   ├── main.py                   # FastAPI 앱 설정 및 라우터 등록
│   ├── config.py                 # 서버 설정 관리
│   ├── routers/                  # API 엔드포인트
│   │   ├── extraction.py         # 추출 API
│   │   ├── evaluation.py         # 평가 API
│   │   ├── visualization.py      # 시각화 API
│   │   └── utils.py              # 유틸리티 API
│   └── services/                 # 비즈니스 로직 서비스
├── 📁 extraction/                # 🔧 추출 모듈
│   ├── core.py                   # 추출 핵심 로직
│   ├── utils.py                  # 추출 유틸리티
│   ├── factory.py                # 프레임워크 팩토리
│   ├── compatibility.yaml        # 프레임워크-호스트 호환성 매핑
│   ├── frameworks/               # 프레임워크 구현체
│   │   ├── openai_framework.py
│   │   ├── anthropic_framework.py
│   │   ├── google_framework.py
│   │   ├── instructor_framework.py
│   │   ├── langchain_*.py
│   │   └── ...
│   └── schema/                   # 데이터 스키마
│       └── schema_han.py         # 한국어 이력서 스키마
├── 📁 evaluation/                # 📊 평가 모듈  
│   ├── core.py                   # 평가 핵심 로직
│   ├── metrics.py                # 평가 메트릭
│   ├── utils.py                  # 평가 유틸리티
│   ├── visualizer.py             # Streamlit 시각화
│   └── criteria/                 # 평가 기준
├── 📁 utils/                     # 🛠️ 공통 유틸리티
│   ├── types.py                  # 타입 정의
│   ├── logging.py                # 로깅 설정
│   ├── tracing.py                # 추적 설정
│   ├── cli_helpers.py            # CLI 헬퍼
│   └── visualization.py          # 시각화 헬퍼
├── 📁 data/                      # 📄 샘플 데이터
│   ├── 리멤버-s1.json
│   ├── 국문이력서(그림포함)-s1.json
│   └── ...
└── 📁 result/                    # 📈 결과 저장소
    ├── extraction/               # 추출 결과
    ├── evaluation/               # 평가 결과
    └── visualization/            # 시각화 결과
```

### 실행 모드

- **🌐 API 서버 모드**: `python main.py` (기본값)
- **💻 CLI 모드**: `python main.py --cli [command]`

## 🔧 지원 프레임워크

### 호스트별 지원 프레임워크

<details>
<summary><b>🤖 OpenAI</b></summary>

- ✅ OpenAIFramework
- ✅ InstructorFramework  
- ✅ LangchainToolFramework
- ✅ LangchainParserFramework
- ✅ LlamaIndexFramework
- ✅ MarvinFramework
- ✅ MirascopeFramework

</details>

<details>
<summary><b>🎭 Anthropic</b></summary>

- ✅ AnthropicFramework
- ✅ InstructorFramework
- ✅ LangchainToolFramework  
- ✅ LangchainParserFramework
- ✅ MarvinFramework

</details>

<details>
<summary><b>🔍 Google</b></summary>

- ✅ GoogleFramework
- ✅ InstructorFramework
- ✅ LangchainToolFramework
- ✅ LangchainParserFramework
- ✅ LlamaIndexFramework
- ✅ MarvinFramework
- ✅ MirascopeFramework

</details>

<details>
<summary><b>🦙 Ollama</b></summary>

- ✅ OllamaFramework
- ✅ OpenAIFramework (OpenAI 호환)
- ✅ InstructorFramework
- ✅ LangchainToolFramework
- ✅ LangchainParserFramework
- ✅ LlamaIndexFramework
- ✅ MarvinFramework
- ✅ MirascopeFramework

</details>

<details>
<summary><b>🔗 OpenAI-Compatible</b></summary>

- ✅ OpenAIFramework
- ✅ InstructorFramework
- ✅ LangchainToolFramework
- ✅ LangchainParserFramework
- ✅ LlamaIndexFramework
- ✅ MarvinFramework
- ✅ MirascopeFramework

</details>

## 📋 스키마와 평가

### 기본 스키마 (schema_han)

한국어 이력서 정보 추출을 위한 구조화된 스키마를 제공합니다.

<details>
<summary><b>📝 스키마 구조</b></summary>

```python
class ExtractInfo(BaseModel):
    personal_info: Optional[PersonalInfo]           # 개인정보
    summary_info: Optional[SummaryInfo]             # 요약정보  
    educations: List[Education]                     # 학력사항
    careers: List[Career]                           # 경력
    education_programs: List[EducationProgram]      # 교육
    overseas_experiences: List[OverseasExperience]  # 해외연수
    certificates: List[Certificate]                 # 자격증
    awards: List[Award]                             # 수상/공모전
    employment_preference: Optional[EmploymentPreference] # 취업우대
    military_service: Optional[MilitaryService]     # 병역
    cover_letter: Optional[CoverLetter]             # 자기소개서
    etc_info: Optional[EtcInfo]                     # 기타
```

</details>

### 평가 시스템

**하이브리드 평가 방식**을 사용하여 정확도와 의미적 유사성을 모두 측정합니다.

- **🎯 완전일치 (Exact Match)**: 정확한 값 일치 여부
- **🧠 임베딩 유사도**: 의미적 유사성 측정 (코사인 유사도)
- **📊 종합 점수**: 가중 평균으로 최종 점수 산출

<details>
<summary><b>📊 평가 메트릭 상세</b></summary>

```python
# 필드별 평가 방식
evaluation_criteria = {
    "personal_info.name": {"method": "exact"},        # 이름은 정확해야 함
    "personal_info.email": {"method": "exact"},       # 이메일도 정확해야 함  
    "summary_info.brief_introduction": {"method": "embedding"}, # 소개글은 의미적 유사성
    "careers": {"method": "hybrid", "exact_weight": 0.3, "embedding_weight": 0.7}
}
```

</details>

## 🎨 시각화

### Streamlit 대시보드

인터랙티브 대시보드로 평가 결과를 실시간으로 탐색할 수 있습니다.

**주요 기능:**
- 📊 전체 성능 개요
- 📈 필드별 상세 분석  
- 🔍 예측 vs 정답 비교
- 📉 성능 분포 차트

### 정적 HTML 리포트

간단한 HTML 리포트로 결과를 공유할 수 있습니다.

**생성 방법:**
```bash
# CLI로 생성
python main.py --cli viz --eval-result path/to/eval_result.json --html

# API로 생성  
curl -X POST http://localhost:8000/v1/visualization/generate \
  -H 'Content-Type: application/json' \
  -d '{"eval_result_path": "path/to/eval_result.json"}'
```

## 🛠️ 개발 가이드

### 로컬 개발 환경

```bash
# 개발 모드로 서버 실행
python main.py --reload

# 테스트 실행 (구현 예정)
pytest tests/

# 코드 포맷팅 (권장)
black .
ruff check .
```

### 커스텀 스키마 추가

1. `extraction/schema/` 디렉토리에 새 스키마 파일 생성
2. Pydantic v2 BaseModel을 상속받는 `ExtractInfo` 클래스 정의
3. 스키마 이름으로 파일에 접근 가능

<details>
<summary><b>📝 커스텀 스키마 예시</b></summary>

```python
# extraction/schema/custom_schema.py
from pydantic import BaseModel, Field
from typing import Optional

class PersonInfo(BaseModel):
    name: Optional[str] = Field(description="이름", default=None)
    age: Optional[int] = Field(description="나이", default=None)

class ExtractInfo(BaseModel):
    person: Optional[PersonInfo] = Field(description="인물정보", default=None)
```

</details>

### 커스텀 프레임워크 추가

1. `extraction/frameworks/` 디렉토리에 새 프레임워크 파일 생성
2. `BaseFramework`를 상속받는 클래스 구현
3. `compatibility.yaml`에 호스트 호환성 정보 추가

### 기여 방법

1. 🍴 Fork the repository
2. 🌟 Create a feature branch: `git checkout -b feature/amazing-feature`
3. 💾 Commit your changes: `git commit -m 'Add amazing feature'`
4. 📤 Push to the branch: `git push origin feature/amazing-feature`
5. 🎯 Open a Pull Request

## 🔍 트러블슈팅

<details>
<summary><b>🚨 자주 발생하는 문제들</b></summary>

**🔌 포트 충돌**
```bash
# 다른 포트 사용
python main.py --port 8080
```

**🔑 API 키 오류**
```bash
# .env 파일 확인
cat .env | grep API_KEY

# 환경 변수 직접 설정
export OPENAI_API_KEY=your-key-here
```

**📦 의존성 문제**
```bash
# 가상환경 재생성
rm -rf .venv
uv venv
source .venv/bin/activate
uv sync
```

**🐌 느린 첫 실행**
- HuggingFace 모델 다운로드로 인한 지연
- 네트워크 연결 상태 확인

**💾 대용량 파일 처리**
```bash
# MAX_FILE_SIZE 조정 (.env)
MAX_FILE_SIZE=52428800  # 50MB
```

</details>

## 🔄 결과물 구조

```
result/
├── 📁 extraction/                # 추출 결과
│   └── 20250823_1430/           # 타임스탬프 폴더
│       ├── result.json          # 추출된 JSON 결과
│       ├── extraction.log       # 추출 로그
│       └── metadata.json        # 실행 메타데이터
├── 📁 evaluation/               # 평가 결과  
│   └── 20250823_1435/
│       ├── eval_result.json     # 평가 결과
│       ├── pred.json           # 예측 JSON (정규화됨)
│       ├── gt.json             # 정답 JSON
│       ├── criteria.json       # 사용된 평가 기준
│       └── evaluation.log      # 평가 로그
└── 📁 visualization/            # 시각화 결과
    └── 20250823_1440/
        └── visualization.html   # HTML 리포트
```

## 📈 성능 벤치마크

<details>
<summary><b>📊 샘플 벤치마크 결과</b></summary>

| 프레임워크 | 호스트 | 모델 | 정확도 | 응답시간 | 안정성 |
|-----------|-------|------|--------|----------|--------|
| OpenAIFramework | OpenAI | gpt-4o-mini | 94.2% | 1.2s | ⭐⭐⭐⭐⭐ |
| InstructorFramework | OpenAI | gpt-4o-mini | 93.8% | 1.4s | ⭐⭐⭐⭐⭐ |
| AnthropicFramework | Anthropic | claude-3-5-sonnet | 95.1% | 2.1s | ⭐⭐⭐⭐⭐ |
| LangchainToolFramework | OpenAI | gpt-4o-mini | 92.5% | 1.8s | ⭐⭐⭐⭐ |

*결과는 한국어 이력서 데이터셋 기준이며, 실제 성능은 데이터에 따라 달라질 수 있습니다.

</details>

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 영향을 받았습니다:

- [Instructor](https://github.com/jxnl/instructor) - OpenAI 구조화 출력
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 애플리케이션 프레임워크  
- [LlamaIndex](https://github.com/run-llama/llama_index) - 데이터 프레임워크
- [Marvin](https://github.com/prefecthq/marvin) - AI 엔지니어링 툴킷
- [Mirascope](https://github.com/Mirascope/mirascope) - LLM 라이브러리

## 📞 연락처

- **작성자**: Bae ChangHyun
- **GitHub**: [@Bae-ChangHyun](https://github.com/Bae-ChangHyun)
- **이슈 리포트**: [GitHub Issues](https://github.com/Bae-ChangHyun/StructuredOutputKit/issues)

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요! ⭐**

</div>

