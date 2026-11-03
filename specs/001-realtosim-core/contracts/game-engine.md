# Contracts: 게임 엔진 (라이브러리 API)

**Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

외부 인터페이스는 `realtosim.game_engine` 모듈의 여섯 함수다. 모델·파일·네트워크 접근 없음, 무작위성 없음.

## Functions

- `new_game(space, puzzle_set, persona, *, run_id, model, seed=None, max_actions=50) -> Game`
  - 모든 사물 `state`를 `locked`로 둔다(입력값 무시). 현재 퍼즐 1번, 행동 수 0, 위치 `start_cell`.
  - 실패 시 `GameSetupError`. 입력 dict는 복사되어 호출자 값이 변하지 않는다(#18).
- `brief(game) -> dict`
  - 실행 중 변하지 않는 공간 정보만: `floors`, `cell_prefix_required`, `rooms`, `objects(id,label,cells,description)`.
- `observe(game) -> {"observation": dict, "images": [...]}` 
  - `position`, `opened_object_ids`, `instruction`, `puzzle`, `last_result`.
  - 실패 시 `GameStateError`.
- `submit(game, raw_output) -> {"events": [...], "over": bool, "outcome": str|null}`
  - 호출 1번 = 행동 1회(거절 포함). 거절은 예외가 아니라 `rejected` 이벤트.
- `abort(game)` → `end(api_error)`만 남긴다. 행동 수 증가 없음.
- `to_log(game) -> dict`
  - 끝난 게임에만 호출. `log.schema.json` 만족 dict(`run_id`, `persona`, `puzzle_set_id`, `model`, `seed` 있을 때만, `events`).

## Rejections (순서·문장 고정, TRD §4)

1. JSON이 아님(빈 문자열 포함) → `출력이 JSON 형식이 아닙니다` (`attempted_action: null`)
2. JSON 객체가 아님 → `출력은 JSON 객체여야 합니다` (`attempted_action: null`)
3. `action`이 없거나 문자열이 아님 → `action은 문자열이어야 합니다`
4. `action`이 `move`/`view`/`answer`가 아님 → `알 수 없는 행동입니다. move, view, answer 중 하나를 쓰세요`
5. `value`가 없거나 문자열이 아님 → `value는 문자열이어야 합니다`
6. `move`가 칸 형식에 맞지 않음 → `칸 좌표 형식이 아닙니다`
7. `move`가 격자 밖 → `지도에 없는 칸입니다`
8. `view` 사물이 공간에 없음 → `존재하지 않는 사물입니다`
9. `view` 사물이 `locked` → `아직 가까이 가지 않은 사물입니다`
10. 도착 전 `answer` → `아직 퍼즐이 열리지 않았습니다`
11. `answer`가 빈 문자열 → `답이 비어 있습니다`
12. `answer`의 `reason` 조건 불충족 → `answer에는 이유(reason)가 필요합니다`

테스트는 위 문장과 문자열 정확 일치를 단언한다.

## Observation Exposure (허용/금지)

- 허용(`brief`): `floors`, `cell_prefix_required`, `rooms`, `objects(id,label,cells,description)`.
- 허용(`observe`): `position`, `opened_object_ids`, `instruction`, `puzzle`, `last_result`.
- 금지(어디에도 노출 없음): `next_object_id`, 종료 전 `next_instruction`, `object_id` 필드, `photos`, `path`, `sha256`, `contains_hint`, `after_wrong`, NPC 전체, `on_wrong`, `on_correct`, 안 열린 힌트 text, 다른 퍼즐 dialogue.
- 예외: `answer`는 `failed` 직후 `last_result.answer`로 1회만 노출.
- 관측은 `json.dumps(값, ensure_ascii=False)` 직렬화해 텍스트로 전달한다.

## Engine Outcomes

- `puzzle_ended.result`: `solved_by_dialogue` (힌트 없이 해결) | `solved_with_hint` (힌트 공개 후 해결) | `failed` (5회 소진).
- `end.outcome`: `completed` | `action_limit` | `api_error`.
