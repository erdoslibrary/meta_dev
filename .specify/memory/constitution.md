# Real-to-Sim 공간 퍼즐 스튜디오 Constitution

## Core Principles

### I. 테스트 게이트 (NON-NEGOTIABLE)

- `python -m unittest discover tests -v` 통과 없이 갈래 1 완료를 선언 MUST NOT.
- 핵심 도메인 로직은 `tests/`에 실패 테스트를 먼저 작성(Red)하고 구현(Green)하는 Red-Green 순서 MUST. JS Vitest 등 신규 러너 도입 MUST NOT.
- 엔진 검사는 모델 없이 `docs/schemas/examples/valid/` 표본으로; `model_api` 검사는 `MockTransport`로만 MUST.
- TRD §4 거절 문구 12종은 테스트에서 문자열 정확 일치 MUST.
- 모든 `to_log()` 출력은 `log.schema.json`을 통과하고, `t`는 1부터 1씩 증가하며 마지막 이벤트만 `end` MUST.

### II. 기술 스택 고정

- 갈래 1은 Python `realtosim` 패키지로만 구현; 저장소 루트에서 `from realtosim import ...`, `python -m realtosim.<모듈>` MUST.
- Python 의존성은 `requirements.txt`의 `jsonschema`와 `httpx`(`model_api` 전용, 지연 import 유지) 외 추가 MUST NOT (TRD §10).
- 변경 사유(2026-11-05, v1.3.0): 제출물을 `pip install -r requirements.txt` 한 번으로 에이전트 실행까지 할 수 있게 `httpx==0.28.1`을 허용 목록에 넣는다. `model_api`의 지연 import는 그대로 두어 `httpx` 없이도 테스트가 돈다.
- 갈래 2 뷰어는 TS + three.js로 구현하고 `tsc` 단일 출력만 쓴다. 허용 패키지는 `three`(벤더 파일 동봉)와 개발 전용 `typescript`·`@types/three`뿐이며, 모두 정확한 버전으로 고정 MUST. 번들러·CDN·외부 URL 사용 MUST NOT.
- 뷰어는 로컬 서버 없이 `file://`로 연 페이지에서 동작 MUST. ES 모듈 스크립트·importmap, `fetch`·XHR 로컬 파일 읽기, 로컬 사진의 WebGL 텍스처 사용에 의존 MUST NOT. 구체 로딩 방식은 002 plan에서 정한다.
- Muse Spark 호출은 `realtosim/model_api.py`에서 `httpx`로만; 모델명·키는 환경 변수(`MODEL_API_*`, `SAM_MODEL`)로만 MUST.
- 데이터·로그·보고서는 파일로만(`data/<set>/`, `logs/<set>/`, `reports/<set>/`); 별도 서버 MUST NOT (PRD AS-5).
- 계약 기준은 스키마 `docs/schemas/*.schema.json`와 TRD §3~§6; 엔진은 순수 상태 머신(모델·파일·네트워크·무작위성 없음) MUST.
- TRD §11 미결 사항(뷰어 배포 방식, SAM 경로, 가구 크기, 주문 연출, 사람 플레이, 마감·제출물)은 본 헌법에서 결정 MUST NOT.

### III. 보안 및 비밀 관리

- API 키·Base URL은 환경 변수로만; 코드·로그·보고서·스키마 예제에 비밀 기록 MUST NOT.
- `workspace/cache/files.json`(sha256→file_id)은 git 제외; `logs/`·`reports/`는 API 키 없이 열람용으로 git 포함하되 비밀 포함 MUST NOT.
- TRD §4 노출 금지 필드(정답, 다음 장소, 사진 경로·해시, 미공개 힌트, NPC 전체 등)를 관측·로그·보고서에 노출 MUST NOT; `answer`는 `failed` 직후 1회만 예외.
- 권리·출처 고지는 README·보고서에만; 코드·TRD에 법률 판단 기록 MUST NOT (PRD §12).

### IV. Spec-Driven Development 워크플로우

- 새 Phase·기능 요청 시 바로 코드 작성 MUST NOT. `specs/<id>/`에 spec.md → plan.md → tasks.md → implement 순서 MUST.
- 범위 기준(SSOT)은 저장소 루트 `requirement.md` 최우선, 원본은 `docs/PRD.md`·`docs/TRD.md` MUST.
- 변경 사유(2026-11-05, v1.3.1): `docs/PRD.md`·`docs/TRD.md`는 2026-11-05 삭제했고 `backup/pre-docs-cleanup` 브랜치에 보존한다. 위 원본 언급은 그 브랜치의 문서를 가리킨다. 워크플로우 세부 동작은 `.specify/workflows/speckit/`을 따른다.
- `/speckit-implement` 전 `tasks.md` 범위를 요청과 대조하고, 요청이 제외·다음 슬라이스로 적혀 있으면 `tasks` 재생성 여부를 먼저 묻 MUST.
- 본 헌법 개정 없이 `docs/`·스키마 수정 MUST NOT.

## Governance

- 본 헌법의 금지 조항이 다른 관행보다 우선한다. 그 외 충돌 시 PRD(WHAT/WHY) > TRD §3~§10(HOW) > 스키마 예시 순으로 따른다.
- 개정은 본 파일 수정 + 버전 증가 + 날짜 갱신으로만 한다. 개정 제안은 이유와 영향 범위를 함께 기록한다.
- 버전 규칙: MAJOR는 원칙 삭제·재정의 등 호환 불가 변경, MINOR은 원칙·섹션 추가나 실질 확장, PATCH는 문구·오탈자 등 비의미 정정.
- 모든 변경은 준수 확인을 거친다: 테스트 게이트 통과, 원칙 II 허용 목록 외 신규 의존성 없음, 비밀·노출 금지 필드 없음.

**Version**: 1.3.1 | **Ratified**: 2026-11-03 | **Last Amended**: 2026-11-05
