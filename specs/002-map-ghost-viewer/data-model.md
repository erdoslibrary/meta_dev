# Data Model: 갈래2 지도·고스트 뷰어

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

**변경 사유 (2026-11-04)**: 사용자 결정 A·B 반영(`answer` 필드 한정·`on_correct`/제출 원문 허용·`reason` 제외, 파일 선택 로그 동시 선택 조건)과 `next_instruction` 전면 금지(T019 일치). 표시 금지·고스트 절 수정.
**변경 사유 (2026-11-04)**: 검증 분리·결정 A 후속을 반영. `embed.py`는 `reason` 제거 전 원본을 `log.schema.json`으로 검증하고 실패 시 `data.js`를 생성하지 않으며, 브라우저는 내장 로그의 `t` 순서와 마지막 `end`만 검증하고 파일 선택 로그는 전체 검증하되 `reason`은 표시하지 않는다(차단 1). `next_instruction` 전면 금지를 `puzzle_ended(failed)` 직후 `answer`와 함께 1회 표시로 교체하고 `next_object_id` 전면 금지는 유지한다(차단 2). 정답 금지 대상을 `puzzle.json`의 `answer` 필드로 한정한다(차단 2). T036 범위를 스키마 통과 요구 로그 표본으로 한정한다(차단 3). 접두어 없는 칸 귀속 규칙을 명시한다(권장 10).
**변경 사유 (2026-11-04)**: 검증 규칙 3건을 반영. 재생 거부 표본은 `embed.py` 검증 게이트에서 제외하고 `data.js`에 그대로 포함한다(항목 1). 브라우저 검증은 재생 필요 항목(최상위 필수 필드·이벤트 종류별 필수 필드·값 타입과 enum·칸·사물 표기·`t` 순서·마지막 `end`)으로 한정하고 `persona` 내용 등 재생 무관 규칙은 검사하지 않으며, 내장 로그의 스키마 전체 검증은 `embed.py`가 맡는다(항목 2).
**변경 사유 (2026-11-04)**: 재생 거부 표본은 결함 유지·`data.js` 규칙 동일 적용으로 고치고(차단 3), 표본 구조를 바로 아래 `*.json`·`refusal/`·`sets/<puzzle_set_id>/`(로그 `puzzle_set_id` 연결)로 정한다(차단 4).
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. 재생 전 검증을 t가 1부터 1씩 증가로 정확히 적는다.
**변경 사유 (2026-11-04)**: 결정 E 페이로드 분리를 반영. 세트 공용 `puzzle`은 `answer`·`next_instruction`을 싣지 않고, 로그별 정답은 `reveals/<로그 키>`에 그 로그에서 `failed`인 퍼즐만 둔다(`next_instruction`이 `null`이면 생략). `sets/<id>/reveals`와 `sample_sets/<id>/reveals` 모두 같은 규칙을 따른다.
**변경 사유 (2026-11-04)**: 결정 E 키 규칙을 통일. 정답은 로그가 연결된 세트의 `reveals`에 둔다. 키는 실로그 상대 경로·`testdata/<이름>`·`refusal/<이름>`, 퍼즐 번호 키는 문자열이다.

엔진·로그·데이터 형식을 바꾸지 않는다(TRD §9, FR-001). 아래는 뷰어가 읽는 기존 형식의 뷰어 관점 투영이다.

## Entities

### 재생 로그 (원천: `logs/<set>/` 1개 파일, `log.schema.json`)

- 필드: `run_id`, `persona`, `puzzle_set_id`, `model`, `seed`(선택), `events[]`.
- 뷰어가 쓰는 이벤트: `move.value`(발자국 순서), `view.value`(사물 사진 지점), `npc_dialogue.npc`(도착 대화), `answer_submitted.value/attempt/correct`(제출 원문 표시, `reason` 제외), `hint_revealed.level`(레벨만), `puzzle_ended.result/attempts_used`, `rejected.attempted_action/error`(거부 표시), `end.outcome`.
- 검증: 내장 로그(`window.RT_DATA`)는 브라우저에서 `t` 1부터 1씩 증가·마지막만 `end`가 아니면 재생 거부 + 이유 표시(Edge Cases). `embed.py`(stdlib + `jsonschema`, `.venv/bin/python`)는 내장 전 스키마 통과 요구 로그 원본(`reason` 제거 전)을 `log.schema.json`으로 검증하고 실패 시 `data.js`를 생성하지 않는다. 재생 거부 표본은 이 게이트에서 제외하되, `t` 불연속과 마지막 비-`end` 결함은 유지한 채 `reason` 제거를 포함한 `data.js` 허용·제외 규칙은 다른 로그와 똑같이 적용해 포함한다. 브라우저 검증은 재생 필요 항목(로그 최상위 필수 필드, 이벤트 종류와 종류별 필수 필드, 값 타입과 enum, 칸·사물 표기 형식, `t` 순서, 마지막 `end`)으로 한정하고 `reason`은 표시하지 않으며, `persona` 내용 등 재생 무관 규칙은 검사하지 않는다.
- 상태 전이(재생 위치): 시작(`start_cell`) → `move` 이동 → `view` 관측 → `npc_dialogue` 도착 → `answer_submitted` 제출 → (`hint_revealed` | `puzzle_ended`) → 다음 퍼즐 또는 `end`. `action_limit`·`api_error`는 끊긴 지점에서 멈추고 끊김 표시.

### 발자국 (파생: `start_cell` + `move.value` 순서열)

- 시작점: `puzzle.json`의 `start_cell`. 궤적 점 개수 = `move` 이벤트 수 + 1(US1 독립 테스트).
- 좌표계: `space.json` 층의 `columns`×`rows` 격자, 1칸=1m. 칸 문자열은 `space.schema.json` `cellRef` 패턴. 다층이면 `2F-C4`형 접두어.
- 층 귀속: 접두어로 층을 구분. 접두어 없는 칸은 단일 층에 귀속한다. 단층 로그에서는 층 UI 없음(US3).

### 표시용 정적 데이터 (원천: `data/<set>/`, 읽기 전용)

- `space.json`: 층·방·사물·격자 범위. 평면도 기하(`walls`, `doors`, `origin_px`, `meters_per_pixel`)와 사물 `cells`.
- `puzzle.json`: 퍼즐별 `dialogue`(대화문), `on_wrong`/`on_correct`(화면 전용 반응, `on_correct`는 맞힌 제출 뒤 표시하며 대사의 다음 장소·정답 문자열 그대로), `failed` 퍼즐의 `answer`(종료 직후 1회만), `failed` 퍼즐의 `next_instruction`(`answer`와 함께 종료 직후 1회만, `null`이면 다음 장소 문구 없음), `start_cell`. 단 `data.js` 페이로드의 세트 공용 `puzzle`에는 `answer`·`next_instruction`을 싣지 않으며, 로그별 정답은 아래 `reveals`에 둔다(결정 E).
- `reveals`: `data.js` 페이로드의 로그별 정답. 정답은 로그가 연결된 세트(세트 조회 결과 `sets/<id>` 또는 `sample_sets/<id>`)의 `reveals`에 둔다. `reveals/<로그 키> = {퍼즐 number 문자열: {answer, next_instruction}}`이며, 그 로그에서 `failed`인 퍼즐만 포함하고 `next_instruction`이 `null`이면 생략한다. 로그 키는 실로그 상대 경로(`r01`, `oracle/r0`), 표본 로그 `testdata/<이름>`, 재생 거부 표본 `refusal/<이름>`이다.
- `npc.json`: NPC 이름·이미지. 로그 `npc_dialogue.npc`와 조인.
- 사진: `photos/`·`puzzles/`·`npcs/` 경로. `<img>`로 표시, WebGL 텍스처로 쓰지 않는다.
- 표시 금지(TRD §4·FR-005, 결정 A): `next_object_id`(전면 금지), 사진 경로(화면), 해시(산출물), `reason`(표시·`data.js` 제외), 미공개 힌트와 힌트 본문, `failed`가 아닌 퍼즐의 정답(`puzzle.json`의 `answer` 필드). `on_correct`(맞힌 제출 뒤, 다음 장소·정답 문자열 그대로)와 `answer_submitted.value`는 제출 원문으로 표시 가능. `next_instruction`은 `failed` 직후 1회만 허용하고 맞힌 퍼즐에는 표시하지 않는다.

### 고스트 (파생: 1회 실행의 시간순 재생 상태)

- 필드: 현재 `t`, 현재 퍼즐 번호, 현재 위치 칸, 열린 사물 집합, 제출 결과(`last_result` 상당), 종료 결과.
- 동작: 처음부터 끝까지 순서대로 재생. `view` 지점에서 사물 사진+`npc_dialogue`, 퍼즐 종료마다 `puzzle_ended.result`, `failed` 직후에만 해당 퍼즐 정답(`puzzle.json`의 `answer` 필드, 페이로드에서는 `reveals`에서 읽는다)과 `next_instruction` 1회 표시(`null`이면 다음 장소 문구 없음). 맞힌 퍼즐의 다음 장소는 `on_correct`(맞힌 제출 뒤 표시)로 전달한다. 파일 선택 로그의 `failed` 정답·`next_instruction`은 로그와 `puzzle.json`을 함께 선택했을 때만 표시하고, 없으면 "정답 데이터 없음"만 표시하고 다음 장소 문구는 표시하지 않는다(결정 B).

### 주문 연출 상태 (FR-006)

- 트리거: 프로그램 진입 전 랜딩 화면. 효과: 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적. 주체는 실행자 본인인 듯한 연출(극 중 시전 인물 없음). 진입 방식(버튼/자동)은 Slice 4 착수 시.
- 수용: 5초 이내 끊김 없이 재생, 실패·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.

## Relationships

- 로그 1개 → 퍼즐 묶음 1개(`puzzle_set_id`) → 공간 1개(`space_id`).
- `view.value`(사물 id) → `space.json` 사물의 `cells`·사진.
- `npc_dialogue.npc` → `npc.json` 이름·이미지 + `puzzle.json` `dialogue` 본문.
- `puzzle_ended(failed)` → 해당 퍼즐 `answer`(`puzzle.json`의 `answer` 필드)와 `next_instruction` 1회 표시. 그 외 퍼즐 정답은 산출물에 없음.

## Validation Rules

- 재생 전: 내장 로그는 `embed.py`가 스키마 통과 요구 원본(`reason` 제거 전)을 `log.schema.json`으로 검증(실패 시 `data.js` 미생성; 재생 거부 표본은 게이트 제외·`data.js` 포함) + 브라우저에서 `t`가 1부터 1씩 증가 + 마지막 `end` 확인. 파일 선택 로그는 브라우저에서 재생 필요 항목(최상위 필수 필드·종류별 필수 필드·값 타입과 enum·칸·사물 표기·`t`·마지막 `end`)만 검증하되 `reason`은 표시하지 않는다.
- 사진 파일 없어도 궤적·대화 재생 계속, 빈틀로 표시.
- `logs/<set>/`에 테스트 표본을 섞지 않는다. 스키마 통과 요구 로그 표본은 `viewer/testdata/` 바로 아래 `*.json`으로 한정한다(`log.schema.json` 통과, `persona`·`space`·`npc` `$ref` 해결). 재생 거부 표본은 `viewer/testdata/refusal/` 아래에, 표본 세트 정적 데이터는 `viewer/testdata/sets/<puzzle_set_id>/` 아래에 두고 로그의 `puzzle_set_id`로 연결한다. `refusal/`·`sets/`는 스키마 표본 요건에서 제외한다.
