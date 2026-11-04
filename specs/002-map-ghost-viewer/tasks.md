# Tasks: 갈래2 지도·고스트 뷰어

**Input**: `specs/002-map-ghost-viewer/` (spec.md, plan.md, research.md R-1~R-8, data-model.md, contracts/viewer.md, quickstart.md V-1~V-6, implementation-notes.md)
**Prerequisites**: plan.md (필수), spec.md (사용자 스토리). 테스트 러너 신규 도입 없음 — 검증은 `tsc` + Playwright MCP 화면 확인 + 갈래1 게이트.
**수동 전제 (사람, Muse 밖 터미널, 1회)**: `implementation-notes.md` §4 — `viewer/vendor/three.cjs`·`viewer/node_modules` 심볼링크, Playwright MCP 등록. Muse는 `npm`·`pip install`·셸 Chrome·`check_page.py`·커밋을 실행하지 않는다.

**분할 준수 (AGENTS.md)**: spec US 1개 = plan 슬라이스 1개 = tasks 페이즈 1개. 항목 1개 = 한 파일·한 모듈. `viewer/` 신규이므로 스토리별 페이즈로 분할하고 코드 작성 전 본 문서로 승인받는다.

**변경 사유 (2026-11-04)**: 검증 분리·결정 A 후속·범위 한정·순서 변경을 반영. T006에 `embed.py` 원본 검증 + 로그 헤더 필드 + `failed` 한정 `answer`·`next_instruction`을 명시하고(차단 1·2, 권장 8), T008에 내장/파일 선택 검증 분리를 명시하며(차단 1), T036 범위를 스키마 통과 요구 로그 표본으로 한정하고 `persona`·`space`·`npc` `$ref`를 포함시키며(차단 3), T035·T036을 구현 항목보다 먼저 실행하도록 Phase 2 순서를 바꾸고(차단 4), T009에 `puzzle.json` 파일 입력을 맡기며(차단 5), T017·T022를 한 항목 = 한 파일·한 모듈 규칙에 맞게 나누고 코드 연결 항목에서 `[P]`를 뺀다(권장 9). `next_instruction` 전면 금지를 `failed` 직후 1회 표시로 교체한다(차단 2).
**변경 사유 (2026-11-04)**: 검증 규칙 3건을 반영. 재생 거부 표본은 `embed.py` 스키마 검증·`data.js` 미생성 규칙에서 제외하고 `data.js`에 포함하며 브라우저 거부 표시는 V-2에서 확인한다(항목 1). T008 자필 검증은 재생 필요 항목으로 한정하고 파일 선택 "전체 검증"을 이 범위로 고친다(항목 2). `embed.py`는 표준 라이브러리 + `jsonschema`만 허용하고 `.venv/bin/python`으로 실행한다(항목 3).
**변경 사유 (2026-11-04)**: 표본 구조·검증 게이트를 확정. FR-001·TRD에 `failed` 퍼즐의 `next_instruction` 허용을 추가하고(차단 1), `failed.json`·`multilayer.json` 스키마 수정(persona 값 포함)을 T042·T043으로 T036 뒤·T037 앞에 둔다(차단 2). 재생 거부 표본은 결함 유지·`data.js` 규칙 동일 적용으로 고치고 T035 감사에 포함한다(차단 3). 표본 구조를 바로 아래 `*.json`·`refusal/`·`sets/<puzzle_set_id>/`로 정한다(차단 4). T040·T041을 정적 데이터(T040·T041)와 코드 연결(T044·T045, `dataload.ts` 명시)로 나눈다(권장 5).
**변경 사유 (2026-11-04)**: 표본 실물 대조 반영. `failed.json`·`multilayer.json`·`stuck-action-limit.json`이 이미 있어 T017·T022·T012를 생성에서 사용·검증으로 바꾸고 스키마 수정은 T042·T043에만 둔다. `persona.thinking` enum 위반 1건씩을 T042·T043에서 허용값으로 맞춘다. 사용자 승인(2026-11-04): failed.json thinking=연상을 따라감, puzzle_set_id=viewer-failed / multilayer.json thinking=문자 그대로 읽음, puzzle_set_id=viewer-multilayer.
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. T042·T043은 thinking만 맡기고 puzzle_set_id 변경은 T046·T047로 옮기며 수정 뒤 embed.py·T036 재실행을 명시한다. 세트 탐색 규칙(sets→data, 중복·없음이면 미생성)을 T006에 넣고 T044·T045는 RT_DATA 내장 표본 사용으로 고친다. 허용 필드(퍼즐 number 등 7종, 대화문 text만)를 T006·T007에 넣고 실패 시 글자 붉은색은 '퍼즐 N 결과: failed' 줄에 둠(지도 궤적·고리 표시는 유지)을 T011·T019에 명시한다. T037에 T035·T036 실행·통과를 넣고 Phase 3~5 체크포인트에 V-1 재빌드를 추가한다. T040·T041에 [P]를 넣어 병렬 설명과 맞추고 T040·T044·T045·T018·T020 체크를 실제 상태에 맞춘다.
**변경 사유 (2026-11-04)**: T040 퍼즐 2개 명시(1번 failed 값·2번 failed null)·[ ]로, T041 two-floors 맞춤 명시·[ ]로 되돌린다. 새 요구 미반영 코드 항목(T006·T007·T015·T019·T029·T031·T032)을 [ ]로 되돌리고 Dependencies에 T046·T047 순서를 명시한다.
**변경 사유 (2026-11-04)**: 결정 E 키 규칙을 반영. T006·T019를 reveals 기준으로 고친다(세트 공용 puzzle 무정답, 정답은 연결된 세트의 reveals에서 읽음). reveals 키는 실로그 상대 경로·`testdata/<이름>`·`refusal/<이름>`, 퍼즐 번호 키는 문자열.
**변경 사유 (2026-11-04)**: 결정 E 반영. T007 puzzle 타입에서 `answer`·`next_instruction`을 빼고 `reveals` 타입(퍼즐 번호 문자열 키, `next_instruction` null 생략)을 넣는다.
**변경 사유 (2026-11-04)**: 결정 B 파일 입력 경로 누락 보완. T007에 파일 입력 원본 `puzzle.json`용 타입(`FilePuzzleEntry`, 실패 퍼즐 `answer`·`next_instruction` 포함, `next_instruction` null 허용)을 내장 payload용 `PuzzleEntry`(정답 없음)와 구분해 둔다.
**변경 사유 (2026-11-04)**: T018 완료 반영. `ghost.ts` 재생 상태 모델 계약 맞춤(end 필드, 퍼즐 번호, 전환 초기화, seek) 후 `tsc --noEmit` 0·`app.js` 빌드·`unittest` 83 통과 확인.
**변경 사유 (2026-11-04)**: T020 완료 반영. `main.ts` Ghost 단일 원천 교체(거부 초기화·소진 기준 정지·층 보존) 후 `tsc --noEmit` 0·`unittest` 83 통과·화면 4종 확인.
**변경 사유 (2026-11-05)**: T029 완료 반영. `.venv/bin/python viewer/tools/embed.py`로 `viewer/dist/data.js` 재생성 후 `viewer/node_modules/.bin/tsc -p viewer`로 `viewer/dist/app.js` 빌드(exit 0, 36,637바이트, 첫 줄 `"use strict";`)하고 Playwright MCP에서 콘솔 확인(앱 코드 메시지 0건. 경고 5건은 헤드리스 SwiftShader의 `CONTEXT_LOST_WEBGL`·`GPU stall due to ReadPixels`로 앱 원인 아님. 이후 재실행에서는 0건).
**변경 사유 (2026-11-05)**: T032 완료 반영. `viewer/dist/data.js`에서 `next_object_id`·`sha256`·`reason`·`"hints"` 0건, `panels.ts`·`main.ts` DOM 삽입점 전수 감사 및 `reveals` 노출 규칙(`failed` 직후 1회·`solved_*` 무표시·`null` 무문구·파일 경로 양쪽 선택 시만) 코드 대조, `testdata/failed` 화면 증거 fullPage 촬영. 위반 0건.
**변경 사유 (2026-11-05)**: T031 완료 반영. V-1(빌드·콘솔 0건)·V-2(내장 6종 발자국·거부 2종·파일 r02, fullPage 4장)·V-3(oracle 완주·피드 대조·파일 로그만/로그+퍼즐, fullPage 3장)·V-4(1F 3점·2F 1점·위치 유지·단층 UI 숨김, fullPage 3장)·V-5(랜딩 3요소·연출 `INTRO_MS` 2600ms·진입 버튼·api-error 완주 아님·배포 묶음, fullPage 2장) 전 항목 PASS 및 V-6 `unittest` 83 통과. V-5 랜딩 증거는 영어 전용 전환 뒤 재촬영한 `.shots/t031-v5-landing-v3.png`·`.shots/t031-v5-entered-v3.png`로 대체한다.
**변경 사유 (2026-11-05)**: 사용자 결정 3건 반영. (1) 로그는 추가 실행 없이 5회로 확정(`requirement.md` 결정 줄). (2) 랜딩 화면 영어 전용 — `viewer/index.html`의 여는 주문 `Don't Panic`, 진입 버튼 `Enter`, 부제 요소 삭제(PRD OPEN-4 보완, spec FR-009 예외). (3) 닫는 주문은 별도 화면 없이 `end(completed)` 결과 박스 꼬리말로 표시 — `viewer/src/panels.ts`가 `완주` 줄을 유지하고 그 아래 `So long, and thanks for all the fish`를 `closing` 클래스로 덧붙인다(PRD OPEN-4 보완, spec FR-006, contracts Rendering Contract).
**변경 사유 (2026-11-05)**: 뷰어 영어 기본(FR-009) 작업 T048~T055 추가. T030의 "default language Korean"은 당시 기록으로 두고 T048~T055가 대체한다.
**변경 사유 (2026-11-05)**: T048~T055 완료 반영. V-7(en 기대값 일치·`?lang=ko` 화면이 번역 전 HEAD와 동일·`#ghost` 줄 수 동일·한글 잔존은 `i18n.ts`와 `theme.ts` 도장 1줄)과 V-6 `unittest` 83 통과. 게이트 중 발견한 회귀 1건(ko 모드 제출 영어 병기)은 `ansGloss()` en 한정으로 고쳤다. 탭 제목은 `Real-to-Sim Archive`로 통일했다.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 병렬 가능 (다른 파일, 미완료 태스크에 의존 없음)
- **[Story]**: 해당 사용자 스토리 (`[US1]`/`[US2]`/`[US3]`). Setup·Foundational·Slice 4·Polish는 라벨 없음.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: `viewer/` 뼈대와 고정 빌드 계약. 렌더·로딩 방식은 plan에서 확정됨 (R-1 폴더 `viewer/`, R-2 하이브리드 로딩, R-3 `three.cjs`).

- [X] T001 Create `viewer/tsconfig.json` with `target es2020`, `module none`, `moduleResolution node10`, `outFile dist/app.js`, `strict true`, `types ["three"]`, `lib ["es2020","dom"]`, `skipLibCheck true`, `include ["src"]`
- [X] T002 [P] Create `viewer/src/three-global.d.ts` declaring global `THREE` via `export import THREE = _THREE` so sources use `THREE` with no `import`
- [X] T003 Create `viewer/index.html` shell with fixed script order (`var module/exports` shim → `vendor/three.cjs` → `window.THREE = module.exports` → `dist/data.js` → `dist/app.js`), `<input type="file">`, parchment base `#E9DCC0`–`#DCCFAC`, system serif, no webfonts
- [X] T004 Create `viewer/package.json` pinning exact versions `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0` (no `npm` execution; `node_modules` is a human-made symlink)
- [X] T005 Append `node_modules` and `.shots` (no trailing slash) to `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 스토리가 의존하는 로딩·검증·장면 기반. 이 페이즈 완료 전 스토리 작업 금지.

- `viewer/src/*.ts`는 `import`/`export` 없는 전역 스크립트로 한다(`three-global.d.ts`의 ambient 선언 제외).
- `tsc` 통과 기준은 exit 0이 아니라 `viewer/dist/app.js` 생성과 내용 확인이다(T037).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T035 [P] Create `tests/` unittest for `embed.py` exposure (allowed/excluded fields per T006, `data.js` audit including playback-refusal samples; allowed includes `on_correct` and `answer_submitted.value`, banned target limited to `puzzle.json` `answer` field); run before implementation to confirm failure
- [X] T036 [P] Create `tests/` unittest that the top-level `viewer/testdata/*.json` schema-required log samples pass `log.schema.json` with the `persona`·`space`·`npc` `$ref`s resolvable (static data files and playback-refusal samples excluded); run before implementation to confirm failure
- [X] T042 [P] In `viewer/testdata/failed.json`, replace `persona.thinking` with `연상을 따라감` only (one file only; no other schema errors; sample-set static data stays in T040; `puzzle_set_id` change is T046 scope); fix after T036 Red so T036 passes at T037
- [X] T043 [P] In `viewer/testdata/multilayer.json`, replace `persona.thinking` with `문자 그대로 읽음` only (one file only; no other schema errors; sample-set static data stays in T041; `puzzle_set_id` change is T047 scope); fix after T036 Red so T036 passes at T037
- [X] T006 Create `viewer/tools/embed.py` using stdlib plus `jsonschema` only (no new package install; run with `.venv/bin/python`, never bare `python`/`python3`; on environment failure report the original text without installing): inputs `logs/drunkard-set/` + `data/drunkard-set/` + `viewer/testdata/` (top-level `*.json` schema-required logs, `refusal/` playback-refusal samples, `sets/<puzzle_set_id>/` sample-set static data), output `viewer/dist/data.js` as single `window.RT_DATA = {...}` statement; first validate each schema-required log original (before `reason` removal) against `log.schema.json` and create no `data.js` on failure; playback-refusal samples are excluded from this gate but included in `data.js` with the same allow/exclude rules as other logs including `reason` removal (their `t` discontinuity and non-`end` last defects stay; browser refusal + reason display verified in V-2); embed photo paths only, never binaries; allowed log header fields: `run_id`, `persona`, `puzzle_set_id`, `model`, `seed` (optional), `events[]` (without `reason`); allowed fields otherwise: space geometry/rooms/objects, puzzle `number`/`start_instruction`/`question`/`object_id`/`image.path`/`answer_letter_count`/`max_attempts`/dialogue(`text` only, `contains_hint` excluded)/`on_wrong`/`on_correct`/`start_cell` (shared set `puzzle` carries no `answer`/`next_instruction`), `reveals/<log key> = {<number string>: {answer, next_instruction}}` for puzzles `failed` in that log only (`next_instruction` `null` omitted; keys: real logs relative path, samples `testdata/<name>`, refusal `refusal/<name>`), npc name/image, photo paths; excluded: `sha256`, hints, `next_object_id` (full ban), `answer`/`next_instruction` of non-`failed` puzzles, `tone`, `reason`, dialogue `contains_hint`; set lookup: resolve each log's `puzzle_set_id` against `sets/<id>` then `data/<id>`; if the same id exists in both or in neither, create no `data.js`; audit target includes `viewer/dist/data.js`; `referencing` is a `jsonschema` dependency, not a new package
- [X] T007 Create `viewer/src/types.ts` with log event types (`move.value`, `view.value`, `npc_dialogue.npc`, `answer_submitted.value/attempt/correct` (no `reason`), `hint_revealed.level` (level only), `puzzle_ended.result/attempts_used`, `rejected.attempted_action/error`, `end.outcome`) and static-data types (`space.json` top-level floors/rooms/cells plus rooms and objects(`id`, `cells`, `photos`, `label`), `puzzle.json` `number`/`start_instruction`/`question`/`object_id`/`image.path`/`answer_letter_count`/`max_attempts`/dialogue(`text` only, `contains_hint` excluded)/`on_wrong`/`on_correct`/`start_cell` (no `answer`/`next_instruction`, no `next_object_id`), `reveals` (`{<number string>: {answer[, next_instruction]}}`, `next_instruction` null omitted), `npc.json` name/image; 파일 입력 원본 `puzzle.json`용 `FilePuzzleEntry`는 `PuzzleEntry`와 별도로 실패 퍼즐의 `answer`·`next_instruction`을 포함한다(`next_instruction` `null` 허용))
- [X] T008 [P] Create `viewer/src/logparse.ts` with handwritten TS validation limited to playback needs (no library, runs in browser): log top-level required fields, event kinds and per-kind required fields, value types and enums, cell/object notation format, `t` order, last `end`; schema details unrelated to playback (e.g. `persona` content rules) are not checked. Built-in `window.RT_DATA` logs get `t` starting at 1 increasing by 1 with only the last event `end` only (`embed.py` already fully schema-validated the original except refusal samples); file-select logs get this limited scope (not full-schema) but `reason` is never displayed; otherwise refuse playback with a reason (spec Edge Cases)
- [X] T009 [P] Create `viewer/src/dataload.ts` reading built-in `window.RT_DATA` and ad-hoc logs plus `puzzle.json` via `<input type="file">` + `FileReader` only (no `fetch`/XHR local reads, decision B)
- [X] T010 Create `viewer/src/scene.ts` with `requestAnimationFrame` repeat rendering plus `webglcontextlost` → `preventDefault()` and `webglcontextrestored` → scene rebuild (no one-shot `render()` pages)
- [X] T011 [P] Create `viewer/src/theme.ts` with tokens Base `#E9DCC0`–`#DCCFAC`, Ink `#2A2118`, Seal Red `#A0322B` (끊김·실패 segments only: `puzzle_ended(failed)`, `end(action_limit)`, `end(api_error)`; landing screen excepted; on failure the red goes on the `퍼즐 N 결과: failed` line, the `정답: …` line stays default ink), code-generated `CanvasTexture` parchment; photos render via `<img>`, never WebGL textures
- [X] T033 Create `viewer/src/main.ts` as the global-script entry starting after `DOMContentLoaded`; no cross-file top-level initialization depending on concatenation order
- [X] T034 [P] Create `viewer/testdata/refusal/` playback-refusal samples (`t` discontinuity, last event not `end`) for logparse verification; excluded from the schema-sample requirement and from top-level `*.json` scope (spec Edge Cases); verified only in V-2 (refusal + reason display)
- [X] T037 Run T035·T036 (`.venv/bin/python -m unittest tests.test_viewer_embed tests.test_viewer_testdata -v`) then `.venv/bin/python viewer/tools/embed.py` (never bare `python`/`python3`; no package install — on environment failure report the original text) then `viewer/node_modules/.bin/tsc -p viewer`; pass = T035·T036 pass plus `viewer/dist/app.js` created plus content check (not exit 0 alone)

**Checkpoint**: Foundation ready — `embed.py` + `main.ts` + scene/loading/validation modules + refusal samples + tests exist, `failed.json`·`multilayer.json` schema fixed (T042·T043) with T036 passing at T037, and `embed.py`/`tsc` outputs verified (T037); story implementation can now begin.

---

## Phase 3: User Story 1 - 평면도 위 발자국 확인 (Priority: P1) 🎯 MVP

**Goal**: `start_cell` 시작·`move.value` 순서 발자국 궤적을 평면도 위에 표시. 끊김 로그는 끊긴 지점에서 멈추고 표시.

**Independent Test**: `logs/drunkard-set/` 로그 1개로 전체 궤적을 순서대로 재생하고, 궤적 점 개수 = 해당 로그의 `move` 이벤트 수 + 1이면 통과 (quickstart V-2).

- [X] T012 [P] [US1] Use the existing `viewer/testdata/stuck-action-limit.json`: verify it ends in `end(action_limit)`. Keep it out of `logs/<set>/` (FR-008)
- [X] T038 [P] [US1] Create `viewer/testdata/api-error.json` as a `log.schema.json`-passing sample ending in `end(api_error)` (kept out of `logs/<set>/`, FR-008)
- [X] T039 [P] [US1] Create `viewer/testdata/multi-move.json` as a `log.schema.json`-passing multi-move sample (kept out of `logs/<set>/`, FR-008)
- [X] T013 [US1] Create `viewer/src/plane.ts` rendering floors from `space.json` as `PlaneGeometry` on the `columns`×`rows` grid (1 cell = 1m, `cellRef` pattern, `2F-C4`-style prefixes, prefix-less cells attach to the single floor, `walls`/`doors`/`origin_px`/`meters_per_pixel`); unexplored rooms blurred/desaturated, explored rooms sharp
- [X] T014 [US1] Create `viewer/src/trail.ts` drawing trajectory as `Line` plus footprints as `Points` with point count = `move` count + 1 (`start_cell` first), 끊김·실패 segments (`puzzle_ended(failed)`, `end(action_limit)`, `end(api_error)`) in Seal Red `#A0322B` (landing screen excepted); `puzzle_ended` results marked on the trajectory (FR-004)
- [X] T015 [US1] Extend `viewer/src/main.ts` with US1 wiring loading built-in `RT_DATA` or a file-input log and driving `plane.ts` + `trail.ts` in `t` order with 끊김-stop display
- [X] T016 [US1] Extend `viewer/index.html` with US1 playback controls and missing-photo empty-frame slots (trajectory/dialogue keep playing when photos are absent)

**Checkpoint**: US1 fully functional and testable independently (V-2: both embedded-sample and file-input paths, 끊김·실패 display; refusal and missing-photo cases per quickstart). Phase checkpoints run V-1 rebuild plus V-2, V-3, V-4 each time (applicable scope).

---

## Phase 4: User Story 2 - 고스트 재생으로 끊김·실패 지점 확인 (Priority: P2)

**Goal**: 1회 실행의 시간순 고스트 재생 — `view` 사진·`npc_dialogue`, 맞은 답·틀린 답, 화면 전용 반응, 퍼즐 종료 결과, `failed` 직후 정답·`next_instruction` 1회(`null`이면 다음 장소 문구 없음).

**Independent Test**: `logs/drunkard-set/oracle/r0.json` 재생이 전 퍼즐 `solved_by_dialogue`와 `end(completed)`까지 끊김 없이 보이면 통과 (quickstart V-3).

- [X] T017 [P] [US2] Use the existing `viewer/testdata/failed.json` (schema fixed in T042): verify it contains `puzzle_ended(failed)`; edit only the log's cells/objects if needed to match T040 data. No schema fixes; keep it out of `logs/<set>/` (FR-008)
- [X] T040 [P] [US2] Create the `failed.json` matching sample-set static data in `viewer/testdata/sets/<puzzle_set_id>/` (linked by the log's `puzzle_set_id`); put 2 puzzles in `sets/viewer-failed/puzzle.json` (no. 1 `failed` with non-`null` `next_instruction`, no. 2 `failed` with `null` `next_instruction`); the sample log's cells and objects must match that set's static data
- [X] T046 [US2] Fix `viewer/testdata/failed.json` only: set `puzzle_set_id` to `viewer-failed` and add puzzle 2 events; after the fix re-run `embed.py` and T036
- [X] T044 [US2] Wire `viewer/src/dataload.ts` to use the `failed.json` sample-set static data embedded in `window.RT_DATA` (근거: main.ts staticFor·setLog가 내장 sample_sets에서 정적 데이터·reveals를 읽음)
- [X] T018 [US2] Create `viewer/src/ghost.ts` implementing ordered playback state (current `t`, puzzle number, cell, opened-object set, submission result, end result) over start → `move` → `view` → `npc_dialogue` → `answer_submitted` → (`hint_revealed` | `puzzle_ended`) → next puzzle or `end`
- [X] T019 [US2] Create `viewer/src/panels.ts` showing at each `view` point the object photo (`<img>`) and `npc_dialogue`, per-puzzle `puzzle_ended.result`, `on_wrong` in order and `on_correct` right after a correct submission (next place and answer strings in the line shown verbatim), `answer_submitted.value` as submitted verbatim, `hint_revealed` level only (no hint body), and the matching `reveals` entry (`{answer, next_instruction}` read from the linked set's `reveals`) exactly once right after `puzzle_ended(failed)` (`null` shows no next-place phrase; solved puzzles show no `next_instruction`, their next place comes via `on_correct`); file-input `failed` answers and `next_instruction` only when the log and `puzzle.json` are both selected, else "정답 데이터 없음" only with no next-place phrase; never showing `next_object_id` (full ban), photo paths/hashes, unreleased hints, `reason`, or answers of non-`failed` puzzles (FR-005, decision A/B); Seal Red goes on the `퍼즐 N 결과: failed` line, the `정답: …` line stays default ink
- [X] T020 [US2] Extend `viewer/src/main.ts` with US2 ghost wiring driving `ghost.ts` + `panels.ts` over the US1 trajectory
- [X] T021 [US2] Extend `viewer/index.html` with US2 ghost controls (log + `puzzle.json` file selectors, decision B) and result display regions

**Checkpoint**: US1 AND US2 both work independently (V-3: oracle uninterrupted, `failed` answer (`puzzle.json` `answer` field) shown once with `next_instruction` (`null` shows nothing), non-`failed` answers absent from screen and outputs; `on_correct` after correct submission and `answer_submitted.value` allowed; file-input rule per quickstart). Phase checkpoints run V-1 rebuild plus V-2, V-3, V-4 each time (applicable scope).

---

## Phase 5: User Story 3 - 층 전환 (Priority: P3)

**Goal**: 다층 로그에서 층별 평면 전환. 단층 로그에서는 층 UI 없음.

**Independent Test**: 2층 표본 재생 시 층별 궤적이 각 층 평면에 표시되고 단층 로그에서는 층 UI가 없으면 통과 (quickstart V-4).

- [X] T022 [P] [US3] Use the existing `viewer/testdata/multilayer.json` (schema fixed in T043): verify `2F-`-style prefixed cells; edit only the log's cells/objects if needed to match T041 data. No schema fixes; keep it out of `logs/<set>/` (FR-008)
- [X] T041 [P] [US3] Create the `multilayer.json` matching sample-set static data in `viewer/testdata/sets/<puzzle_set_id>/` (linked by the log's `puzzle_set_id`); align `sets/viewer-multilayer/space.json` to the space in `docs/schemas/examples/valid/space.two-floors.json`; the sample log's cells and objects must match that set's static data
- [X] T047 [US3] Fix `viewer/testdata/multilayer.json` only: set `puzzle_set_id` to `viewer-multilayer` and align cells/objects to `space.two-floors`; after the fix re-run `embed.py` and T036
- [X] T045 [US3] Wire `viewer/src/dataload.ts` to use the `multilayer.json` sample-set static data embedded in `window.RT_DATA` (근거: main.ts staticFor·setLog가 내장 sample_sets에서 정적 데이터·reveals를 읽음)
- [X] T023 [US3] Create `viewer/src/floors.ts` grouping floor planes by cell prefix (prefix-less cells attach to the single floor) with group-visibility switching so only the active floor's moves and observations show
- [X] T024 [US3] Extend `viewer/src/main.ts` with US3 floor-switching wiring over ghost playback
- [X] T025 [US3] Extend `viewer/index.html` with a floor selector that is hidden entirely for single-floor logs

**Checkpoint**: All user stories independently functional (V-4: per-floor display, no floor UI on single-floor logs). Phase checkpoints run V-1 rebuild plus V-2, V-3, V-4 each time (applicable scope).

---

## Phase 6: Slice 4 - 주문·잉크 연출 + 배포 (FR-006 + FR-007)

**Purpose**: 진입 전 랜딩 화면의 주문·잉크 연출과 컴파일-JS-커밋 배포 (R-5, R-6). 사용자 결정(2026-11-04): 주체 = 실행자 본인이 외우는 듯한 연출(극 중 시전 인물 없음), 범위 = 진입 전 랜딩 화면. 진입 방식(버튼/자동)은 착수 시 정한다.

**Independent Test**: 랜딩 화면에서 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적이 5초 이내 끊김 없이 재생; 실패·끊김 로그도 완주 아님 표시와 함께 끝까지 재생 (quickstart V-5).

- [X] T026 Create `viewer/src/order.ts` rendering the pre-entry landing intro (spell text + red seal overlay + SVG `stroke-dashoffset` ink trail, executor-self framing, no in-fiction caster) playing without stutter within 5 seconds
- [X] T027 Extend `viewer/src/main.ts` with landing-to-program entry wiring (button vs auto decided at slice start)
- [X] T028 Extend `viewer/index.html` with the landing intro screen (red subtitle + edge vignette) placed before program entry
- [X] T029 Regenerate `viewer/dist/data.js` via `.venv/bin/python viewer/tools/embed.py` and build `viewer/dist/app.js` via `viewer/node_modules/.bin/tsc -p viewer` only, then verify console error/warning-free at `file://$PWD/viewer/index.html`; deploy set is `index.html` + `dist/app.js` + `dist/data.js` + `vendor/three.cjs` + `data/<set>/` photos with `node_modules`/`.shots` excluded (Muse does not commit; a human commits)

**Checkpoint**: Order/ink + offline deploy verified (V-5).

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: 언어·노출 감사·전체 회귀. 영어 UI는 T048~T055 (FR-009, V-7).

- [X] T030 Polish Korean copy in `viewer/index.html` and `viewer/src/*.ts` strings (default language Korean; no webfonts)
- [X] T032 Audit exposure compliance in viewer screens and outputs including `viewer/dist/data.js`: photo paths banned on screen, hashes (`sha256`) banned in artifacts; `failed` answers (`puzzle.json` `answer` field) appear only once right after `puzzle_ended(failed)` together with that puzzle's `next_instruction` (`null` shows no next-place phrase; solved puzzles show none, next place via `on_correct`) (exception per decision A: `on_correct` right after correct submission and `answer_submitted.value` display allowed, `reason` excluded from display and `data.js`); no `next_object_id` (full ban), unreleased hints, hint bodies, or non-`failed` puzzle answers (FR-005, data-model Display Exposure)
- [X] T031 Run quickstart validation V-1 through V-5 via Playwright MCP only (console collection → real-UI operation → before/after screenshots in `.shots/` opened with `read_file` → PASS/FAIL per item) plus V-6 regression gate `.venv/bin/python -m unittest discover tests -v` (never bare `python`/`python3`)
- [X] T048 Create `viewer/src/i18n.ts`: `lang` from `?lang=ko` (default en), `t()` UI dictionary, `td()` data source-text → English map (FR-009)
- [X] T049 Replace Korean literals in `viewer/index.html` with English and add one EN/KO toggle link; keep all existing ids/classes
- [X] T050 Route `viewer/src/panels.ts` strings through `t()`/`td()`; keep `answer_submitted.value` original with optional English gloss
- [X] T051 Route `viewer/src/logparse.ts` refusal reasons through `t()`
- [X] T052 Route `viewer/src/main.ts` strings through `t()` and apply ko overlay to static `index.html` text
- [X] T053 Route `viewer/src/dataload.ts` strings through `t()`
- [X] T054 Route `viewer/src/floors.ts` strings through `t()`
- [X] T055 Run quickstart V-7 plus V-6 gate; rebuild `viewer/dist/app.js` once before validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately. Human env prep (`implementation-notes.md` §4) runs outside Muse in parallel.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all stories and Slice 4. T035·T036 run before the implementation items (T006 and later); T042·T043 fix the two sample logs after T036 Red so T036 passes at T037.
- **US1 (Phase 3)**: After Foundational. MVP.
- **US2 (Phase 4)**: After Foundational; builds on US1 trajectory but independently testable via V-3.
- **US3 (Phase 5)**: After Foundational; builds on US1/US2 but independently testable via V-4.
- **Slice 4 (Phase 6)**: After US1–US3 (order intro frames the working viewer).
- **Polish (Final)**: After all desired slices.

### Within Each Story

- Test-data sample first (top-level `testdata/*.json` only must pass `log.schema.json`; `refusal/` and `sets/` excluded), then model/scene modules, then `main.ts`/`index.html` wiring.
- T046은 T040 뒤, T047은 T041 뒤에 실행한다.
- `main.ts` and `index.html` extensions are sequential per slice (same files, no `[P]`).

### Parallel Opportunities

- T035·T036 `[P]` run first within Foundational (before T006 and later implementation items); then T008/T009/T011 `[P]` (different files, no interdependency); T002 `[P]` alongside T001 (different files).
- `viewer/testdata/*.json` top-level log samples (T012, T017, T022, T038, T039) `[P]` — independent files. `refusal/` samples (T034) are `[P]` but outside top-level scope. T042·T043 run after T036 Red (different files, `[P]` between them). Sample-set static-data items (T040, T041) `[P]` — independent set dirs. Code-wiring items (T044, T045) carry no `[P]` (`viewer/src/dataload.ts` shared file, wired in order).
- After Foundational, US phases can parallelize only if editors coordinate `main.ts`/`index.html` (shared files — prefer sequential).

---

## Parallel Example: Foundational

```bash
# Launch independent Foundational modules together (different files):
Task: "Create viewer/src/logparse.ts validating t-order and end-last"
Task: "Create viewer/src/dataload.ts reading RT_DATA and FileReader"
Task: "Create viewer/src/theme.ts with parchment/ink/seal tokens"
```

## Parallel Example: Test Data

```bash
# Launch independent schema-required log samples together (different files):
Task: "Create viewer/testdata/stuck-action-limit.json (US1)"
Task: "Create viewer/testdata/failed.json (US2)"
Task: "Create viewer/testdata/multilayer.json (US3)"
Task: "Create viewer/testdata/api-error.json + multi-move.json (US1)"
Task: "Create viewer/testdata/refusal/ playback-refusal samples (logparse, V-2 only; excluded from top-level schema-sample requirement)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (+ human env prep outside Muse).
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: US1 footprint trajectory.
4. **STOP and VALIDATE**: V-2 independently (point count = `move` + 1, 끊김·실패 display, both load paths) + V-6 gate.
5. Demo if ready (`file://` open, no server).

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → V-2 → demo (MVP).
3. Add US2 → V-3 (oracle uninterrupted) → demo.
4. Add US3 → V-4 (floor switching) → demo.
5. Add Slice 4 → V-5 (order/ink + deploy set) → demo.
6. Polish → V-1..V-6 full pass + exposure audit.

---

## Notes

- `[X]`는 동작을 실제로 검증한 뒤에만 표시한다. 현재 `viewer/`는 검증되지 않은 초안이며, 다음 작업에서 삭제하지 않고 수정한다.
- T001~T005는 완료 상태로 둔다. `viewer/package.json`(T004)은 implementation-notes §4에서 사람이 복사한 파일이므로 변경하지 않는다.
- `[P]` = different files, no dependencies. `[USn]` maps the task to its story for traceability.
- Each story is independently completable and testable via its quickstart scenario.
- `file://` prohibitions hold everywhere: no ES modules, importmap, CDN, external URLs, local server, `fetch`/XHR local reads, or photo WebGL textures.
- Exact versions everywhere: `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0` (0.186+ `three.cjs` is an empty 631-byte file; TS 7 drops `outFile` + `module: none`).
- Script order in `viewer/index.html` never changes (contracts Loading Contract).
- Stop at any checkpoint to validate the slice independently.
- Per `/speckit-implement` rule: before implementing, compare this scope against the request; if the request excludes a slice or defers it, ask whether to regenerate tasks first.
