# Tasks: Real-to-Sim 핵심 검증 흐름 (엔진 슬라이스)

**Input**: Design documents from `specs/001-realtosim-core/` (spec.md, plan.md, research.md, data-model.md, contracts/game-engine.md, quickstart.md)

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: plan.md와 quickstart.md V-2가 `tests/test_game_engine.py` 계약 테스트를 명시하므로 테스트 태스크를 포함한다. 각 페이즈의 테스트를 먼저 작성하고 FAIL을 확인한 뒤 구현한다.

**Organization**: 엔진 슬라이스(`realtosim/game_engine.py` + `tests/test_game_engine.py`, plan.md Scale/Scope)만 다룬다. US1·US2(P1)는 같은 엔진 코어를 공유하므로 Phase 3에 합치고, US3·US4(P2)는 로그·보고서 입력 규칙으로 Phase 4·5에 둔다. `validate.py`·`oracle.py`·`personas.py`·`run_agents.py`·`model_api.py`·`report.py`와 모델 API 시나리오(#17·#24~#27)·뷰어는 이번 슬라이스 제외(quickstart.md Out of Scope)이며 태스크를 만들지 않는다.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Library: `realtosim/` 패키지, `python -m realtosim.<모듈>` 실행 (plan.md Structure Decision)
- Tests: `tests/` (`test_schemas.py` 기존 유지, `test_game_engine.py` 신규)
- Test inputs: `docs/schemas/examples/valid/` 표본만 (모델·키·네트워크 불필요)
- 금지: `docs/schemas/`·`docs/` 수정 없음, `jsonschema` 외 의존성 없음, 비밀 없음, 커밋 없음 (AGENTS.md)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 기준선 확정과 패키지 뼈대

- [X] T001 [P] Run baseline gate `python -m unittest discover tests -v` in repo root and record the pass before any code change
- [X] T002 [P] Create package scaffold in `realtosim/__init__.py` exposing game_engine per `specs/001-realtosim-core/plan.md` source structure
- [X] T003 [P] Inventory engine test inputs under `docs/schemas/examples/valid/` (space/puzzle/persona/log samples) read-only, no edits

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 스토리 전에 완성해야 하는 Game 상태·좌표·생성·요약 기반

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define `GameSetupError`, `GameStateError`, and `Game` state (position, object_state locked/open, current_puzzle, per-puzzle wrong_count/opened/revealed_hints, action_count, events with t, over/outcome) with input deep-copy in `realtosim/game_engine.py` (research.md R-1)
- [X] T005 Implement cell parsing/validation and adjacency in `realtosim/game_engine.py` (schema cellRef/cellRange patterns; single-floor bare cells only, multi-floor prefixed only; Chebyshev max(|dcol|,|drow|) <= 1 same floor; one move reaches any in-grid cell, no wall/distance checks; research.md R-2)
- [X] T006 Implement `new_game(space, puzzle_set, persona, *, run_id, model, seed=None, max_actions=50)` in `realtosim/game_engine.py` (force every object state to locked ignoring input; current puzzle 1, action count 0, position at start_cell; defaults rooms to [], missing start_instruction to absent, max_attempts to 5 per research.md R-7; GameSetupError on bad refs)
- [X] T007 Implement `brief(game)` in `realtosim/game_engine.py` returning only floors, cell_prefix_required, rooms, objects(id,label,cells,description) per `specs/001-realtosim-core/contracts/game-engine.md` (research.md R-5)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Stories 1+2 - 검증 통과 묶음의 플레이 가능성 증명 (Priority: P1) 🎯 MVP

**Goal**: 오라클이 1번부터 끝까지 `solved_by_dialogue`로 완주할 수 있는 제출 파이프라인 (TRD §3~§4, 시나리오 #1~#13·#16·#18·#19·#28·#29)

**Independent Test**: `docs/schemas/examples/valid/` 표본으로 정답 스크립트 재생 시 전 퍼즐 해결 후 `end(completed)`; 깨진 설정은 `GameSetupError`이며 로그 없음

- [X] T008 [US1] Add new_game edge tests for #18 (caller dicts unchanged after full walkthrough) and #28 (rooms omitted yields [], start_instruction omitted yields absent, max_attempts defaults to 5) in `tests/test_game_engine.py`
- [X] T009 [US1] Add rejection tests for #4 (move c4/I1/1F-C4 yield rejections 6/7/7), #6 (leading answer yields rejection 10, not an attempt), #9 (reasonless answer yields rejection 12, no attempt consumed) in `tests/test_game_engine.py` asserting TRD §4 sentences verbatim
- [X] T010 [US1] Implement rejection checks 1-12 in order with exact TRD §4 messages in `realtosim/game_engine.py` (attempted_action null for checks 1-2; rejections consume no attempts and leave state unchanged, emitting only a `rejected` event)
- [X] T011 [US2] Add movement/arrival/view tests for #1 (move emits no npc_dialogue, puzzle null), #2 (diagonal arrival opens), #3 (2-away stays closed), #5 (locked/distant views yield rejections 9/8), #7 (off-puzzle open view yields view only), #19 (two-floor move C2 rejected 7, 2F-AA3 succeeds), #29 (duplicate view logs view without repeating npc_dialogue) in `tests/test_game_engine.py`
- [X] T012 [US2] Implement move/open/arrival/view rules in `realtosim/game_engine.py` (action count +1 including rejections; move silently opens every adjacent object; adjacent view on current puzzle object emits view + npc_dialogue and opens the puzzle; view on non-current open object emits view only; repeat view emits view only per research.md R-3)
- [X] T013 [US2] Add answer/hint tests for #8 (" Apple " yields attempt 1 correct true with raw value preserved and solved_by_dialogue), #10 (one wrong yields hint_revealed level 1 with 4 attempts left), #11 (wrong-then-right yields solved_with_hint with 2 attempts) in `tests/test_game_engine.py`
- [X] T014 [US2] Implement answer judging and hints in `realtosim/game_engine.py` (strip().lower() compare both sides with raw value logged; max 5 attempts per puzzle excluding rejections with no 6th attempt; wrong below 5 emits hint_revealed when after_wrong matches; post-arrival answers allowed from any cell)
- [X] T015 [US2] Add fail/advance/completion tests for #12 (5 wrongs yield puzzle_ended failed with single answer reveal plus next instruction), #13 (last-puzzle fail yields end completed), #16 (completing on the 6th action at limit 6 still yields completed) in `tests/test_game_engine.py`
- [X] T016 [US2] Implement fail/next/completion in `realtosim/game_engine.py` (5th wrong emits answer_submitted plus puzzle_ended failed with attempts_used 5, reveals the answer once, unlocks the next puzzle; last-puzzle end emits end(completed); final-action completion beats action_limit per TRD §3)

**Checkpoint**: At this point, User Stories 1 AND 2 engine support should be fully functional and testable independently (oracle walkthrough completes)

---

## Phase 4: User Story 3 - 15회 실행 로그 (Priority: P2)

**Goal**: 끊김·상한·중단까지 순서 있는 로그 이벤트로 남긴다 (TRD §7, 시나리오 #14·#15·#20~#23)

**Independent Test**: 완주 재생이 `to_log` 이벤트와 일치하고(#14); 비JSON 50번 뒤 `t: 51`에 `end(action_limit)`(#15); 유효 표본 재생(#20~#23)이 끝까지 간다

- [X] T017 [US3] Add log-shape tests for #14 (full walkthrough to_log event equality) and #15 (50 non-JSON inputs yield 50 rejected events then end(action_limit) at t 51) in `tests/test_game_engine.py`
- [X] T018 [US3] Implement `to_log(game)` in `realtosim/game_engine.py` (ended games only, else GameStateError; include run_id, persona, puzzle_set_id, model, events, and seed only when given; t starts at 1 incrementing by 1 with only the last event as end; output must pass `docs/schemas/log.schema.json`)
- [X] T019 [US3] Add abort/limit/end-guard tests (abort yields only end(api_error) with no action-count increment; observe/submit/abort after end raise GameStateError; default max_actions 50 bounds #15) in `tests/test_game_engine.py`
- [X] T020 [US3] Implement `abort(game)` and post-end guards in `realtosim/game_engine.py` (abort appends end(api_error) only; observe/submit/abort on an ended game raise GameStateError per data-model.md state transitions)
- [X] T021 [US3] Add sample-replay tests for #20-#23 in `tests/test_game_engine.py` (load valid samples covering two-object-open, start_cell change, hint-condition change, turn-order view; play each to end and assert completion per research.md R-6 with no extra assertions)

**Checkpoint**: At this point, User Stories 1, 2 AND 3 engine support should all work independently (every run ends in a schema-valid log)

---

## Phase 5: User Story 4 - 난이도 보고서 입력 (Priority: P2)

**Goal**: 보고서 집계가 읽는 결과 분류와 노출 위생을 확정한다 (TRD §4 노출 금지, §7 점수·결과, §8 분담)

**Independent Test**: 결과값이 solved_by_dialogue/solved_with_hint/failed 중 하나이며; brief·관측 직렬화에 금지 필드가 없고 answer는 failed 직후에만 보인다

- [X] T022 [US4] Add outcome-taxonomy assertions (solved_by_dialogue means hint-free solve, solved_with_hint means post-hint solve, failed means 5 attempts used; puzzle_ended carries attempts_used; end outcome is only completed/action_limit/api_error) in `tests/test_game_engine.py`
- [X] T023 [US4] Add exposure-hygiene tests in `tests/test_game_engine.py` (brief plus json.dumps-serialized observations contain none of next_object_id, next_instruction, object_id, photos, path, sha256, contains_hint, after_wrong, npc, tone, on_wrong, on_correct; answer appears only right after failed; other-puzzle dialogue and unopened hint text absent)
- [X] T024 [US4] Enforce the observation allow-list in `realtosim/game_engine.py` (observe exposes only position, opened_object_ids, instruction, puzzle, last_result with opened-hint text only; answer exposed once via last_result.answer right after failed; serialize the boundary with json.dumps value ensure_ascii=False per contracts/game-engine.md)

**Checkpoint**: All user stories should now be independently functional at engine level (report aggregation can read outcomes without forbidden fields)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 게이트·금지사항·슬라이스 검증 마무리

- [X] T025 Run the full gate `python -m unittest discover tests -v` in repo root and fix failures until green (constitution I: no completion claim while red)
- [X] T026 Verify the working tree shows changes only under `realtosim/` and `tests/` (no `docs/schemas/` or `docs/` edits) via git status in repo root
- [X] T027 Verify engine purity and secrecy in `realtosim/game_engine.py` (no model/file/network/random access; no API key or Base URL literals; grep MODEL_API_KEY and files.json cache writes absent)
- [X] T028 Run quickstart validations V-1 through V-3 per `specs/001-realtosim-core/quickstart.md` (schema gate, engine contract scenarios, exposure check) and record results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Phase 3 (US1+US2, P1) first - oracle playability is the precondition for every later story (spec.md)
  - Phase 4 (US3, P2) and Phase 5 (US4, P2) proceed sequentially (single-threaded engine file); US4 needs US3 log shape settled
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Stories 1+2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - needs Phase 3 submit pipeline to produce loggable runs; independently testable via to_log
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - needs Phase 3 outcomes and Phase 4 log shape; independently testable via taxonomy/exposure tests

### Within Each User Story

- Tests MUST be written and FAIL before implementation (T008 before T010; T011 before T012; T013 before T014; T015 before T016; T017 before T018; T019 before T020; T022/T023 before T024)
- State before transitions (T004 before T006/T012/T016)
- Core implementation before integration (Phase 2 before Phase 3 before Phase 4 before Phase 5)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001 gate run, T002 `realtosim/__init__.py`, T003 sample inventory - different files, no dependencies)
- No [P] inside Phases 2-5: every task edits either `realtosim/game_engine.py` or `tests/test_game_engine.py`, so same-file tasks run sequentially
- Once Foundational completes, test-writing across stories could parallelize only if split into separate files; as scoped to one test file, keep sequential
- Polish T026/T027 (read-only greps) can run in parallel with each other after T025 is green

---

## Parallel Example: Setup (the only parallel phase)

```bash
# Launch all Setup tasks together (different files, no dependencies):
Task: "Run baseline gate python -m unittest discover tests -v in repo root"
Task: "Create package scaffold in realtosim/__init__.py"
Task: "Inventory engine test inputs under docs/schemas/examples/valid/"
```

---

## Implementation Strategy

### MVP First (User Stories 1+2 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007, CRITICAL - blocks all stories)
3. Complete Phase 3: User Stories 1+2 (T008-T016)
4. **STOP and VALIDATE**: oracle walkthrough on valid samples completes with all solved_by_dialogue and end(completed); `python -m unittest discover tests -v` green
5. Deploy/demo if ready (engine slice only; no report yet)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 3 (US1+US2) → oracle proof → MVP (playability proven)
3. Add Phase 4 (US3) → every run including api_error/action_limit yields a schema-valid log
4. Add Phase 5 (US4) → outcomes and exposure hygiene ready for report aggregation
5. Each story adds value without breaking previous stories (full gate stays green)

### Next Slices (NOT in this tasks.md)

- `realtosim/validate.py` + `reports/<set>/replica.md` (US1 full: M1-M9/M25 checks)
- `realtosim/oracle.py` (US2 runner), `realtosim/personas.py` + `realtosim/run_agents.py` (US3 runners)
- `realtosim/model_api.py` (scenarios #17/#24-#27 with MockTransport), `realtosim/report.py` (US4 aggregation)
- Viewer/갈래 2 (TRD §9·§11: out of scope by constitution II)

---

## Notes

- [P] tasks = different files, no dependencies (only Phase 1 here; engine work is single-file sequential)
- [Story] label maps task to specific user story for traceability (US1+US2 share Phase 3 as one P1 increment)
- Each user story phase is independently testable via its scenario subset in `tests/test_game_engine.py`
- Rejection sentences must match TRD §4 verbatim; tests assert exact strings (constitution I)
- Every `to_log()` output must pass `log.schema.json` with t from 1 by 1 and only the last event as end (constitution I)
- Stop at any checkpoint to validate the story independently; do not commit (AGENTS.md 금지 사항)

