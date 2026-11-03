<!-- Sync Impact Report
- Version change: 1.0.0 → 1.1.0 (MINOR: 원칙 확장 + 원칙 1개 추가)
- Modified principles: I. 테스트 게이트 → I. 테스트 게이트 (TDD Red-Green 명시화로 확장)
- Added sections: IV. Spec-Driven Development 워크플로우 (4단계 루프, SSOT, tasks 범위 대조)
- Removed sections: (none)
- Deferred TODOs: (none). TRD §11 미결 TODO는 계속 미결 유지, 본 헌법에서 결정하지 않음.
- Note: this report is temporary review material; remove before commit.
-->

# Real-to-Sim 공간 퍼즐 스튜디오 Constitution

## Core Principles

### I. 테스트 게이트 (NON-NEGOTIABLE)

- `python -m unittest discover tests -v` 통과 없이 갈래 1 완료를 선언 MUST NOT.
- 핵심 도메인 로직은 `tests/`에 실패 테스트를 먼저 작성(Red)하고 구현(Green)하는 Red-Green 순서 MUST. JS Vitest 등 신규 러너 도입 MUST NOT.
- 엔진 검사는 모델 없이 `docs/schemas/examples/valid/` 표본으로; `model_api` 검사는 `MockTransport`로만 MUST.
- TRD §4 거절 문구 12종은 테스트에서 문자열 정확 일치 MUST.
- 모든 `to_log()` 출력은 `log.schema.json`을 통과하고, `t`는 1부터 1씩 증가하며 마지막 이벤트만 `end` MUST.

### II. 기술 스택 고정

- Python `realtosim` 패키지로만 구현; 저장소 루트에서 `from realtosim import ...`, `python -m realtosim.<모듈>` MUST.
- 의존성은 `requirements.txt`의 `jsonschema` 외 추가 MUST NOT (TRD §10).
- Muse Spark 호출은 `realtosim/model_api.py`에서 `httpx`로만; 모델명·키는 환경 변수(`MODEL_API_*`, `SAM_MODEL`)로만 MUST.
- 데이터·로그·보고서는 파일로만(`data/<set>/`, `logs/<set>/`, `reports/<set>/`); 별도 서버 MUST NOT (PRD AS-5).
- 계약 기준은 스키마 `docs/schemas/*.schema.json`와 TRD §3~§6; 엔진은 순수 상태 머신(모델·파일·네트워크·무작위성 없음) MUST.
- TRD §11 미결 사항(뷰어/프론트 스택, SAM 경로, 가구 크기, 주문 연출, 사람 플레이, 마감·제출물)은 본 헌법에서 결정 MUST NOT.

### III. 보안 및 비밀 관리

- API 키·Base URL은 환경 변수로만; 코드·로그·보고서·스키마 예제에 비밀 기록 MUST NOT.
- `workspace/cache/files.json`(sha256→file_id)은 git 제외; `logs/`·`reports/`는 API 키 없이 열람용으로 git 포함하되 비밀 포함 MUST NOT.
- TRD §4 노출 금지 필드(정답, 다음 장소, 사진 경로·해시, 미공개 힌트, NPC 전체 등)를 관측·로그·보고서에 노출 MUST NOT; `answer`는 `failed` 직후 1회만 예외.
- 권리·출처 고지는 README·보고서에만; 코드·TRD에 법률 판단 기록 MUST NOT (PRD §12).

### IV. Spec-Driven Development 워크플로우

- 새 Phase·기능 요청 시 바로 코드 작성 MUST NOT. `specs/<id>/`에 spec.md → plan.md → tasks.md → implement 순서 MUST.
- 범위 기준(SSOT)은 저장소 루트 `requirement.md` 최우선, 원본은 `docs/PRD.md`·`docs/TRD.md` MUST. 워크플로우 세부 동작은 `.specify/workflows/speckit/`을 따른다.
- `/speckit-implement` 전 `tasks.md` 범위를 요청과 대조하고, 요청이 제외·다음 슬라이스로 적혀 있으면 `tasks` 재생성 여부를 먼저 묻 MUST.
- 본 헌법 개정 없이 `docs/`·스키마 수정 MUST NOT.

## Governance

- 본 헌법의 금지 조항이 다른 관행보다 우선한다. 그 외 충돌 시 PRD(WHAT/WHY) > TRD §3~§10(HOW) > 스키마 예시 순으로 따른다.
- 개정은 본 파일 수정 + 버전 증가 + 날짜 갱신으로만 한다. 개정 제안은 이유와 영향 범위를 함께 기록한다.
- 버전 규칙: MAJOR는 원칙 삭제·재정의 등 호환 불가 변경, MINOR은 원칙·섹션 추가나 실질 확장, PATCH는 문구·오탈자 등 비의미 정정.
- 모든 변경은 준수 확인을 거친다: 테스트 게이트 통과, 신규 의존성 없음, 비밀·노출 금지 필드 없음.

**Version**: 1.1.0 | **Ratified**: 2026-11-03 | **Last Amended**: 2026-11-03
