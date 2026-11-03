# Data Model: Real-to-Sim 핵심 검증 흐름 (엔진 슬라이스)

**Date**: 2026-11-03 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

엔티티 형상(필드 이름·제약)은 `docs/schemas/*.schema.json`이 기준이다. 아래는 관계와 엔진이 맡는 검증·전이만 적는다.

## Entities

### Space (공간)

- 층(`floors`: 격자 크기·원점·벽·문), 방(`rooms`: 이름·칸 범위, 선택), 사물(`objects`: id·라벨·칸·사진·설명).
- 엔진이 무시하는 입력: 사물 `state` 값(전부 `locked`로 강제), `photos`, `path` 성격 필드.
- 관계: `PuzzleSet.space_id`가 `Space.space_id`를 가리킨다.

### PuzzleSet (퍼즐 묶음)

- `puzzle_set_id`, `space_id`, `start_cell`, `start_instruction`(선택), 선형 `puzzles[]`.
- 관계: `puzzles[i].number`는 1부터 연속. `object_id`·`next_object_id`는 공간에 존재해야 한다(검증기 몫, 엔진은 존재를 전제하고 `GameSetupError`로 방어).

### Puzzle (퍼즐)

- 장소 사물(`object_id`), NPC id, 대화(`dialogue[]`: `text`+`contains_hint`), 그림(`image.path`+`sha256`), 문제(`question`), 정답(`answer`), 글자 수(`answer_letter_count`), 힌트 1개(`level`+`after_wrong` 1~4+`text`), `next_instruction`·`next_object_id`(마지막은 null).
- 엔진 규칙: `max_attempts`는 5 고정(없으면 5).

### Persona (페르소나)

- `age` 10~79, `job`, `vocab` 상/중/하, `thinking` 3값 고정. 실행마다 전체를 로그에 기록. 엔진은 값을 해석하지 않고 보관만 한다.

### Game (엔진 내부 상태, 로그에 직접 노출 없음)

- `position`(현재 칸), `object_state`(사물별 locked/open), `current_puzzle`(진행 중 번호), 퍼즐별 `wrong_count`·`opened`·`revealed_hints`, `action_count`, `events[]`(t 포함), `over`·`outcome`.
- 불변식: `action_count` == 기록된 행동 수(거절 포함). `t`는 1부터 1씩 증가.

### Run Log (실행 로그)

- `run_id`(`r0`, `r07`…), `persona`, `puzzle_set_id`, `model`, `seed`(선택), `events[]`.
- 이벤트 종류: `move`·`view`·`npc_dialogue`·`answer_submitted`·`hint_revealed`·`puzzle_ended`·`rejected`·`end`. 마지막만 `end`. 끊긴 퍼즐에는 `puzzle_ended` 없음.

## Validation Rules (엔진 몫)

- 칸 형식·격자 포함·사물 존재·개방 여부·도착 전 `answer`·빈 답·`reason` 조건을 거절 1~12번 순서로 검사한다.
- 정답 비교는 양쪽 `strip().lower()`. 퍼즐당 시도 5회, 거절은 시도 아님, 6번째 시도 없음.

## State Transitions

퍼즐: 잠김 → (앞 퍼즐 종료·시작) 잠금 해제 → (맞닿아 `view`) 풀이 중 → (정답) 해결 / (오답 5 미만) 풀이 중 / (오답 5) 실패. 거절은 상태 불변.

실행: 시작 전 → `new_game` 성공 시 진행 중 (설정 오류·키 없음·SHA 불일치·사진 없음은 시작 안 함, 로그 없음) → `submit` 반복 → 마지막 퍼즐 종료 시 완주 `completed`, 상한 도달 시 `action_limit`, `abort` 시 `api_error`. 종료 후 `observe`·`submit`·`abort`는 `GameStateError`.
