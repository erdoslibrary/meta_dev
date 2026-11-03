# Implementation Plan: Real-to-Sim 핵심 검증 흐름

**Branch**: `001-realtosim-core` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-realtosim-core/spec.md`

## Summary

창작자가 제출한 공간·선형 퍼즐 묶음을 검증기·오라클·페르소나 에이전트 실행·로그·난이도 보고서로 검증하는 핵심 흐름 중, 첫 슬라이스로 순수 상태 머신 게임 엔진(`realtosim/game_engine.py`, TRD §3~§4)과 그 계약 테스트(`tests/test_game_engine.py`, TRD §10 #1~#16·#18~#23·#28~#29)를 구현한다. 표본 데이터(`docs/schemas/examples/valid/`)로 모델 없이 검증한다.

## Technical Context

**Language/Version**: Python 3.11 (저장소 기존 `test.py` 기준)

**Primary Dependencies**: `jsonschema` (requirements.txt 고정, 신규 패키지 추가 금지)

**Storage**: 파일만 (`data/<set>/`, `logs/<set>/`, `reports/<set>/`). 엔진은 저장소 접근 없음. 별도 서버 없음.

**Testing**: `python -m unittest discover tests -v` (유일한 게이트)

**Target Platform**: Linux, 서버 없음 (CLI 모듈 실행)

**Project Type**: library (`realtosim` 패키지, `python -m realtosim.<모듈>` 실행)

**Performance Goals**: 해당 없음. 엔진 연산은 인 메모리 1회성 전이이며 측정 대상이 아니다.

**Constraints**: 엔진은 순수 상태 머신 (모델·파일·네트워크 접근 없음, 무작위성 없음). 거절 문구 12종은 TRD §4와 문자열 정확 일치. 모든 `to_log()` 출력은 `log.schema.json` 통과, `t` 1부터 1씩 증가, 마지막만 `end`. API 키 등 비밀을 코드·로그·보고서에 기록 금지. TRD §4 노출 금지 필드를 관측에 노출 금지.

**Scale/Scope**: 신규 2개 파일 (`realtosim/game_engine.py`, `tests/test_game_engine.py`). 기존 `tests/test_schemas.py` 유지. TRD §10 시나리오 #1~#16·#18~#23·#28~#29와 노출·로그 검사.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. 테스트 게이트: `python -m unittest discover tests -v` 통과 없이 완료 선언 금지 → Validation은 이 명령뿐.
- [x] I. 엔진 검사는 모델 없이 `docs/schemas/examples/valid/` 표본으로만 → Phase 0/1과 quickstart가 표본 기반으로 고정.
- [x] I. TRD §4 거절 문구 12종 문자열 정확 일치 → 테스트가 원문 비교.
- [x] I. `to_log()` 출력의 스키마·`t`·마지막 `end` 규칙 → 로그 검사 테스트에 명시.
- [x] II. `realtosim` 패키지 + `python -m` 실행 규약 준수 → Source Code 구조 참조.
- [x] II. `jsonschema` 외 의존성 추가 금지 → Technical Context에 고정.
- [x] II. 엔진 순수 상태 머신 → data-model이 상태 전이만 기술, I/O 없음.
- [x] II. TRD §11 미결 사항(뷰어·프론트·SAM 경로·가구 크기·주문 연출·사람 플레이·마감/제출물) 결정 금지 → 범위 밖으로 명시.
- [x] III. 비밀·노출 금지 필드 없음 → contracts가 허용/금지 필드를 명시.
- [x] III. 권리·출처 고지는 코드·TRD가 아니라 README·보고서에 → 본 슬라이스에서 다루지 않음.

위반 없음. Complexity Tracking 불필요.

## Project Structure

### Documentation (this feature)

```text
specs/001-realtosim-core/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
realtosim/
├── __init__.py
└── game_engine.py      # 순수 상태 머신 (TRD §3~§4)

tests/
├── test_schemas.py         # 기존 유지
└── test_game_engine.py     # 신규 (TRD §10)

docs/schemas/examples/valid/  # 테스트 입력 (space/puzzle/persona/log 표본)
```

**Structure Decision**: 단일 라이브러리 패키지 구조. TRD §2가 `realtosim` 패키지와 `python -m realtosim.<모듈>` 실행을 못 박았으므로 그대로 따른다. 뷰어·서버 디렉터리 없음.

## Complexity Tracking

해당 없음 (Constitution Check 위반 없음).
