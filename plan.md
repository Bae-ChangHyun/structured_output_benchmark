# StructuredOutputKit 리팩토링 계획서

작성일: 2025-08-23  
대상 브랜치: refactor  
작성 목적: 도메인 중심 구조 정비, API/CLI 통합 코어 확립, 유지보수성/일관성 향상

## 목표 및 범위
- API 서버와 CLI가 동일한 도메인 Core 함수를 사용하도록 설계 유지/강화
- 중복/혼재된 폴더 구조 정리: extraction/evaluation 중심으로 통합, core는 횡단 관심사만 유지
- 유틸 함수의 도메인 분리 및 중복 제거(특히 convert_schema)
- 로깅/결과물 경로 일원화(core.logging 단일 진입)
- 리소스 경로 표준화(prompt/compatibility/criteria)
- Import 경로/문서 일치화, 최소 단위/통합 테스트 추가

## 아키텍처 결정(ADRs 요약)
1) 실행 모드: FastAPI(서버) / Typer(CLI) 공존, 둘 다 도메인 Core 호출  
2) 도메인 중심 구조: extraction, evaluation 하위에 각 Core 포함  
3) core 폴더는 공통 타입/로깅/트레이싱만 보유  
4) CLI 상호작용(프로바이더/프레임워크 선택)은 CLI 레이어로 한정  
5) Backward-compat: 경로 이동 시 임시 re-export shim 제공 후 Deprecate  

## 제안 폴더 구조(최종)
```
structured_output_kit/
  main.py
  cli.py
  server/
    main.py, config.py
    routers/
    services/
  core/
    types.py
    logging.py
    tracing.py
  extraction/
    core.py                  # run_extraction_core (현 core/extraction.py 이동)
    frameworks/
    schema/
    utils.py                 # load_prompt, convert_schema, 호환성조회 등
    compatibility.yaml       # (현 framework_compatibility.yaml)
  evaluation/
    core.py                  # run_evaluation_core (현 core/evaluation.py 이동)
    metrics.py               # (현 evaluation_module/metric.py)
    utils.py                 # normalize/criteria/convert_np/record_evaluation
    criteria/criteria.json
    visualizer.py
  resources/
    prompts/prompt.yaml
  result/
```

## 파일/기능 이동 매핑
- Core 이동
  - core/extraction.py → extraction/core.py (함수명 유지: run_extraction_core)
  - core/evaluation.py → evaluation/core.py (함수명 유지: run_evaluation_core)
  - core/visualization.py → evaluation/core.py 내부 유지(또는 visualization/core.py 분리 옵션)
- 유틸 분해
  - utils.py →
    - CLI 전용: select_llm/select_embed/select_framework → cli_helpers.py(또는 cli.py 내부)
    - 추출 유틸: load_prompt, convert_schema, get_compatible_frameworks → extraction/utils.py
    - 평가 유틸: load_field_eval_criteria, generate_default_criteria, convert_np, record_evaluation → evaluation/utils.py
  - convert_schema 단일 출처: extraction/utils.py로 통일(기존 중복 제거)
- 리소스/설정 경로
  - prompt.yaml → resources/prompts/prompt.yaml
  - extraction_module/framework_compatibility.yaml → extraction/compatibility.yaml
  - evaluation_module/criteria.json → evaluation/criteria/criteria.json
- Import 수정(대표)
  - cli.py: extraction_module.utils → extraction.utils
  - services/routers: core.* → extraction.core / evaluation.core 로 경로 보정
- 로깅
  - services/*의 logger 초기화 제거, core.logging.setup_logger 단일 사용

## 단계별 작업 계획(체크리스트)

### 0) 베이스라인/안전망
- [x] 현재 폴더/파일 구조 및 역할 분석
- [x] 핵심 호출 흐름/의존성 분석
- [x] 문제점/리스크 도출 및 계획 수립

### 1) 리소스 경로 표준화(저위험)
- [x] prompt.yaml → resources/prompts/prompt.yaml 이동 및 로더 경로 보정
- [x] framework_compatibility.yaml → extraction/compatibility.yaml 이동 및 로더 보정(레거시 fallback 포함)
- [x] criteria 기본 경로를 evaluation/criteria/criteria.json로 통일(코드 기준, 레거시 fallback 포함)
- 검증: 다음 단계에서 스모크 테스트 시 함께 확인

### 2) 유틸 함수 분리/중복 제거
- [x] CLI 전용 상호작용 유틸 분리: cli_helpers.py 생성
- [x] utils.py 기능 분해(추출/평가 유틸로 이동)
- [x] convert_schema 단일 출처 정리 및 전역 import 경로 교정
- [x] 기록 함수(record_extraction/evaluation) 도메인별 유틸로 이동
- 검증: grep 전수 확인, 타입/런타임 임포트 정상

### 3) 도메인 Core 이동 + 호환 shim
- [x] core/extraction.py → extraction/core.py, core/evaluation.py → evaluation/core.py 이동
- [x] 기존 경로에 re-export shim 추가 및 Deprecation 경고
- [x] services/routers/cli import 경로 업데이트
- 검증: CLI 3커맨드 + API 3엔드포인트 스모크

### 4) 로깅/출력 경로 일원화
- [ ] services/* 로깅 초기화 제거, core.logging만 사용
- [ ] 결과 디렉터리 정책: result/{task}/{timestamp} 통일 확인
- 검증: 로그 파일/CSV 누적/경로 일관성 점검

### 5) 문서/패키징 정리
- [ ] README의 경로/예시 업데이트(새 구조 반영)
- [x] pyproject.toml의 package/package-data 경로 갱신
- 검증: 로컬 패키징 드라이런(선택), 런타임 import 정상

### 6) 테스트/검증 자동화(최소)
- [ ] 단위: convert_schema(schema_han), normalize_prediction_json, eval_json(exact/embedding)
- [ ] 시각화: run_visualization_core HTML 생성 스모크
- [ ] 통합: FastAPI TestClient로 /v1/extraction, /v1/evaluation, /v1/visualization/generate 200 확인
- [ ] CLI: extract/eval/viz happy path

## 품질 게이트
- Build: PASS
- Lint/Typecheck(선택): PASS
- Unit: 핵심 케이스 PASS
- Integration/Smoke: API/CLI PASS

## 리스크와 대응
- 대량 경로 변경으로 인한 import 붕괴 → 단계별 적용 + shim + grep 전수 교정
- 패키지 데이터 누락 → pyproject package-data 갱신 및 로컬 검증
- CLI 상호작용 의존 → CLI 레이어로 한정, core/API는 비상호작용 보장

## 마이그레이션/롤백 전략
- 각 단계 소규모 커밋/PR, shim 제공, 문제 시 직전 단계로 롤백
- 완료 후 shim 제거 계획 수립(후속 이슈로 분리)

## 결정 로그(업데이트 예정)
- 2025-08-23: 도메인 중심 구조/단계적 마이그레이션 채택

## 다음 단계(착수 제안)
- 1단계 리소스 경로 표준화부터 수행, 완료 시 본 문서 체크박스 업데이트 및 간단 결과 보고
