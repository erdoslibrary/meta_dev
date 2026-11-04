# Data Model: 갈래2 지도·고스트 뷰어

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

엔진·로그·데이터 형식을 바꾸지 않는다(TRD §9, FR-001). 아래는 뷰어가 읽는 기존 형식의 뷰어 관점 투영이다.

## Entities

### 재생 로그 (원천: `logs/<set>/` 1개 파일, `log.schema.json`)

- 필드: `run_id`, `persona`, `puzzle_set_id`, `model`, `seed`(선택), `events[]`.
- 뷰어가 쓰는 이벤트: `move.value`(발자국 순서), `view.value`(사물 사진 지점), `npc_dialogue.npc`(도착 대화), `answer_submitted.value/attempt/correct/reason`(제출 원문 표시), `hint_revealed.level`, `puzzle_ended.result/attempts_used`, `rejected.attempted_action/error`(거부 표시), `end.outcome`.
- 검증: `t` 1부터 1씩 증가·마지막만 `end`가 아니면 재생 거부 + 이유 표시(Edge Cases). `log.schema.json` 미통과는 재생 거부.
- 상태 전이(재생 위치): 시작(`start_cell`) → `move` 이동 → `view` 관측 → `npc_dialogue` 도착 → `answer_submitted` 제출 → (`hint_revealed` | `puzzle_ended`) → 다음 퍼즐 또는 `end`. `action_limit`·`api_error`는 끊긴 지점에서 멈추고 끊김 표시.

### 발자국 (파생: `start_cell` + `move.value` 순서열)

- 시작점: `puzzle.json`의 `start_cell`. 궤적 점 개수 = `move` 이벤트 수 + 1(US1 독립 테스트).
- 좌표계: `space.json` 층의 `columns`×`rows` 격자, 1칸=1m. 칸 문자열은 `space.schema.json` `cellRef` 패턴. 다층이면 `2F-C4`형 접두어.
- 층 귀속: 접두어로 층을 구분. 단층 로그에서는 층 UI 없음(US3).

### 표시용 정적 데이터 (원천: `data/<set>/`, 읽기 전용)

- `space.json`: 층·방·사물·격자 범위. 평면도 기하(`walls`, `doors`, `origin_px`, `meters_per_pixel`)와 사물 `cells`.
- `puzzle.json`: 퍼즐별 `dialogue`(대화문), `on_wrong`/`on_correct`(화면 전용 반응), `failed` 퍼즐의 `answer`(종료 직후 1회만), `start_cell`.
- `npc.json`: NPC 이름·이미지. 로그 `npc_dialogue.npc`와 조인.
- 사진: `photos/`·`puzzles/`·`npcs/` 경로. `<img>`로 표시, WebGL 텍스처로 쓰지 않는다.
- 표시 금지(TRD §4·FR-005): `next_object_id`, 종료 전 `next_instruction`, 사진 경로·해시, 미공개 힌트, `failed`가 아닌 퍼즐의 정답. `answer_submitted.value`는 제출 원문으로 표시 가능.

### 고스트 (파생: 1회 실행의 시간순 재생 상태)

- 필드: 현재 `t`, 현재 퍼즐 번호, 현재 위치 칸, 열린 사물 집합, 제출 결과(`last_result` 상당), 종료 결과.
- 동작: 처음부터 끝까지 순서대로 재생. `view` 지점에서 사물 사진+`npc_dialogue`, 퍼즐 종료마다 `puzzle_ended.result`, `failed` 직후에만 해당 퍼즐 정답 1회 표시.

### 주문 연출 상태 (FR-006)

- 트리거: 기본 동작 완성 후의 주문 지점(주체·범위 미결). 효과: 붉은 봉인 오버레이 + 먹 잉크 궤적(화면 범위 미결).
- 수용: 5초 이내 끊김 없이 재생, 실패·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.

## Relationships

- 로그 1개 → 퍼즐 묶음 1개(`puzzle_set_id`) → 공간 1개(`space_id`).
- `view.value`(사물 id) → `space.json` 사물의 `cells`·사진.
- `npc_dialogue.npc` → `npc.json` 이름·이미지 + `puzzle.json` `dialogue` 본문.
- `puzzle_ended(failed)` → 해당 퍼즐 `answer` 1회 표시. 그 외 퍼즐 정답은 산출물에 없음.

## Validation Rules

- 재생 전: 스키마 통과 + `t` 단조 증가 + 마지막 `end` 확인.
- 사진 파일 없어도 궤적·대화 재생 계속, 빈틀로 표시.
- `logs/<set>/`에 테스트 표본을 섞지 않는다. 표본은 `viewer/testdata/`(`log.schema.json` 통과).
