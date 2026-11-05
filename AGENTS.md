# AGENTS.md — Real-to-Sim 공간 퍼즐 스튜디오

## 읽을 문서 (헌법 금지 조항 우선. 그 외 충돌은 `requirement.md` > 스키마 순)

(2026-11-05 변경 사유: 제출 정리. `docs/PRD.md`·`docs/TRD.md`는 2026-11-05 삭제했고 `backup/pre-docs-cleanup` 브랜치에 보존한다. 아래 PRD·TRD 절 언급은 그 브랜치의 문서를 가리킨다.)

- `docs/schemas/*.schema.json` — 데이터 형식 기준.
- `requirement.md` — speckit-specify 입력.
- `.specify/memory/constitution.md` (v1.3.1) — 테스트·스택·보안 원칙.
- `specs/002-map-ghost-viewer/implementation-notes.md` — 002 plan과 구현 세션 시작 시 읽는다. 시험 근거, 빌드 후보, 시작 지시문. 위 문서와 다르면 위 문서가 우선한다.
- TRD §11 미결 사항은 결정하지 않는다. 예외: 문서가 plan에 위임한 배포 방식(TRD §9·§11, spec FR-007)과 주문·잉크 수용 시나리오(TRD §9, spec FR-006)는 002 plan에서 정한다. 주문 주체와 화면 범위는 PRD OPEN-4 결정(2026-11-04: 실행자 본인이 외우는 듯한 연출, 진입 전 랜딩 화면)으로 확정됐다. (2026-11-04 변경 사유: PRD OPEN-4 결정 반영. OPEN-4 반영에 한해 docs/TRD.md는 수정하지 않는다.)

## 디렉토리 규약

- 구현: 갈래 1은 `realtosim/` 패키지 (`python -m realtosim.<모듈>`). 갈래 2 뷰어는 `realtosim/` 밖 별도 폴더에 두고, 이름은 002 plan에서 확정한다.
- 데이터·로그·보고서: `data/<set>/`, `logs/<set>/`, `reports/<set>/`. 별도 서버 없음.
- 테스트: `tests/`.

## 테스트 게이트

- `python -m unittest discover tests -v` 통과 없이 완료 선언 금지.
- TRD §4 거절 문구 12종은 문자열 정확 일치.

## 작업 분할

- 판단 시점: `/speckit-plan`에서 슬라이스 단위로 나누고, `/speckit-tasks`에서 의존 순서의 체크리스트로 쪼갠다. 구현은 체크리스트 순서대로 한 항목씩 수행한다.
- 분할 기준: 새 파일 3개 이상, 수정 500줄 이상, 또는 실행 10분 이상이면 분할 대상이다.
- 쪼개는 단위: spec 사용자 스토리 1개 = plan 슬라이스 1개 = tasks 페이즈 1개. tasks 항목 1개는 한 파일·한 모듈에 둔다.
- 기준에 걸리면 코드 작성 전 분할안을 보고하고 승인 후 착수한다.

## 금지 사항

(2026-11-05 변경 사유: 헌법 v1.3.0 반영. 제출물 실행 편의를 위해 `httpx`를 `requirements.txt`에 넣는다.)


- 헌법 원칙 II 허용 목록 외 새 패키지 추가 금지. Python은 `jsonschema`와 `httpx`만(`httpx`는 `requirements.txt`에 고정하되 `model_api`에서 지연 import 유지), 뷰어는 `three`, `typescript`, `@types/three`만 정확한 버전으로 허용한다.
- 스키마 수정 금지. docs는 변경 사유를 함께 기록할 때만 허용.
- API 키 등 비밀을 코드·로그·보고서에 기록 금지.
- 커밋 금지.

## 모순·불분명 시

- 추측하지 말고 멈춰서 질문한다.
- `/speckit-implement` 전 tasks.md 범위를 요청과 대조하고, 요청이 제외·다음 슬라이스로 적혀 있으면 tasks 재생성 여부를 먼저 묻는다.
