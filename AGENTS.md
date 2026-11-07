# AGENTS.md — Real-to-Sim 공간 퍼즐 스튜디오

## 문서 SSOT (단일 진실 공급원)

(2026-11-05 변경 사유: 제출 정리. `docs/PRD.md`·`docs/TRD.md`는 2026-11-05 삭제했고 `backup/pre-docs-cleanup` 브랜치에 보존한다. 아래 PRD·TRD 절 언급은 그 브랜치의 문서를 가리킨다.)
(2026-11-06 변경 사유: SSOT·워크플로우 절 신설. speckit 강제 문장 복원.)
(2026-11-06 변경 사유: 워크플로우 0번 단계 추가. 신규 저장소는 `muse init` 먼저 검증.)

| 문서 | 역할 | 최종 권위를 갖는 영역 |
| :--- | :--- | :--- |
| `.specify/memory/constitution.md` (v1.3.1) | 원칙·금지 | 전역 최우선. 금지 조항은 모든 문서보다 우선한다 |
| `requirement.md` | speckit-specify 입력 | 범위·요구·완료 기준 |
| `docs/schemas/*.schema.json` | 데이터 형식 | 필드·형식 판정 기준 |
| `specs/<id>/spec.md` | 기능 명세 | WHAT (사용자 가치·인수 시나리오) |
| `specs/<id>/plan.md` + `research.md`, `data-model.md`, `contracts/`, `quickstart.md` | 설계 | HOW (기술 선택·구조·검증 절차) |
| `specs/<id>/tasks.md` | 실행 순서 | 작업 범위·의존 순서 |
| `specs/002-map-ghost-viewer/implementation-notes.md` | 002 참고 | 시험 근거·빌드 후보·시작 지시문. 002 한정 참고이며 위 문서와 다르면 위 문서가 우선한다 |

충돌 우선순위: 헌법 금지 조항 > `requirement.md` > 스키마(형식 판정) > spec(WHAT) > plan(HOW) > tasks. 충돌을 발견하면 임의로 한쪽을 따르지 말고 문서를 먼저 고친다.

- TRD §11 미결 사항은 결정하지 않는다. 예외: 문서가 plan에 위임한 배포 방식(TRD §9·§11, spec FR-007)과 주문·잉크 수용 시나리오(TRD §9, spec FR-006)는 002 plan에서 정한다. 주문 주체와 화면 범위는 PRD OPEN-4 결정(2026-11-04: 실행자 본인이 외우는 듯한 연출, 진입 전 랜딩 화면)으로 확정됐다. (2026-11-04 변경 사유: PRD OPEN-4 결정 반영. OPEN-4 반영에 한해 docs/TRD.md는 수정하지 않는다.)

## 개발 워크플로우 (speckit SDD)

0. `muse init` — 신규 저장소면 맨 먼저 실행해 `AGENTS.md`를 만든다. 기존 파일이 있으면 `--dry-run`으로만 확인하고 `--force`로 덮어쓰지 않는다.

사용자가 `speckit`을 언급하지 않아도("구현해줘") 직결 구현을 하지 않고 4단계 루프를 순서대로 적용한다.

1. `speckit-specify` — `requirement.md`를 붙여 넣어 `specs/<id>/spec.md` 작성. HOW 금지.
2. `speckit-plan` — spec + 헌법을 읽고 `research.md`로 미정을 해소한 뒤 `data-model.md`, `contracts/`, `quickstart.md` 작성.
3. `speckit-tasks` — `plan.md` + `spec.md`를 사용자 스토리별 페이즈(`Setup` → `Foundational` → 스토리별 → `Polish`)의 `tasks.md`로 생성.
4. `speckit-implement` — `tasks.md` 순서대로 한 항목씩 TDD(Red-Green)로 구현.

새 Phase·기능 요청 시 바로 코드 작성 금지. plan 없이 tasks를, tasks 없이 implement를 시작하지 않는다.

## 최소 변경·검증 규율

(2026-11-06 변경 사유: 스킬 없이 AGENTS.md만으로 과잉설계 방지.)

- 필요 없으면 만들지 않는다. 기존 코드·표준 기능 재사용이 우선이다.
- 검증·에러 처리는 생략 금지. 작게 쓰되 증명은 남긴다.
- 완료 주장은 실행 결과로만 한다. 테스트·빌드 출력을 인용한다.

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
(2026-11-07 변경 사유: 해커톤 마감 이후 정리 및 문서 업데이트를 위해 커밋 허용.)


- 헌법 원칙 II 허용 목록 외 새 패키지 추가 금지. Python은 `jsonschema`와 `httpx`만(`httpx`는 `requirements.txt`에 고정하되 `model_api`에서 지연 import 유지), 뷰어는 `three`, `typescript`, `@types/three`만 정확한 버전으로 허용한다.
- 스키마 수정 금지. docs는 변경 사유를 함께 기록할 때만 허용.
- API 키 등 비밀을 코드·로그·보고서에 기록 금지.

## 모순·불분명 시

- 추측하지 말고 멈춰서 질문한다.
- `/speckit-implement` 전 tasks.md 범위를 요청과 대조하고, 요청이 제외·다음 슬라이스로 적혀 있으면 tasks 재생성 여부를 먼저 묻는다.
