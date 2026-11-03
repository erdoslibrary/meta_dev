# Quickstart: 엔진 슬라이스 검증 가이드

**Date**: 2026-11-03 | **Spec**: [spec.md](spec.md) | **Contracts**: [contracts/game-engine.md](contracts/game-engine.md)

구현 코드 없이 검증만 기술한다. 전체 흐름의 실행 가이드는 tasks·구현 단계에서 확장한다.

## Prerequisites

- Python 3.11, 의존성은 `requirements.txt`의 `jsonschema`만.
- 테스트 입력: `docs/schemas/examples/valid/` 표본 (모델·키·네트워크 불필요).

## Validation Scenarios

### V-1: 스키마 게이트 (기존)

```console
$ python -m unittest discover tests -v
```

- 기대: `tests/test_schemas.py` 전원 통과. 유효 표본 통과, 무효 표본은 오류 정확히 1개.

### V-2: 엔진 계약 테스트 (신규)

```console
$ python -m unittest tests.test_game_engine -v
```

- 기대: TRD §10 #1~#16·#18~#23·#28~#29 시나리오, 노출 검사, 로그 검사 전부 통과.
- 핵심 증거:
  - 거절 12종이 TRD §4 문장과 정확 일치.
  - 정답 `" Apple "` 입력 시 `attempt 1, correct true`, 로그 원문 유지, `solved_by_dialogue`.
  - 오답 1회 → `hint_revealed(level 1)`, 5회 소진 → `puzzle_ended(failed)` 후 다음 지시·정답 1회 노출, 6번째 시도 없음.
  - 비JSON 50번 → `rejected` 50개 뒤 `t: 51`에 `end(action_limit)`.
  - 모든 `to_log()`이 `log.schema.json` 통과, `t` 1씩 증가, 마지막만 `end`.

### V-3: 노출 검사

- 기대: `brief`·관측 직렬화에 금지 필드(`next_object_id`, `next_instruction`, `object_id`, `photos`, `path`, `sha256`, `contains_hint`, `after_wrong`, NPC 전체, `on_wrong`, `on_correct`) 없음. `answer`는 `failed` 직후만.

## Out of Scope (이번 슬라이스 제외)

- 모델 API 시나리오(#17·#24~#27), 오라클·페르소나·보고서 실행, 뷰어. `tasks.md`는 `/speckit-tasks` 단계에서 생성한다.
