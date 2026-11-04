# Tasks: 갈래2 지도·고스트 뷰어

**Input**: `specs/002-map-ghost-viewer/` (spec.md, plan.md, research.md R-1~R-8, data-model.md, contracts/viewer.md, quickstart.md V-1~V-6, implementation-notes.md)
**Prerequisites**: plan.md (필수), spec.md (사용자 스토리). 테스트 러너 신규 도입 없음 — 검증은 `tsc` + Playwright MCP 화면 확인 + 갈래1 게이트.
**수동 전제 (사람, Muse 밖 터미널, 1회)**: `implementation-notes.md` §4 — `viewer/vendor/three.cjs`·`viewer/node_modules` 심볼링크, Playwright MCP 등록. Muse는 `npm`·`pip install`·셸 Chrome·`check_page.py`·커밋을 실행하지 않는다.

**분할 준수 (AGENTS.md)**: spec US 1개 = plan 슬라이스 1개 = tasks 페이즈 1개. 항목 1개 = 한 파일·한 모듈. `viewer/` 신규이므로 스토리별 페이즈로 분할하고 코드 작성 전 본 문서로 승인받는다.

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

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create `viewer/tools/embed.py` using stdlib only: inputs `logs/drunkard-set/` + `data/drunkard-set/` + `viewer/testdata/`, output `viewer/dist/data.js` as single `window.RT_DATA = {...}` statement; embed photo paths only, never binaries
- [X] T007 Create `viewer/src/types.ts` with log event types (`move.value`, `view.value`, `npc_dialogue.npc`, `answer_submitted.value/attempt/correct/reason`, `hint_revealed.level`, `puzzle_ended.result/attempts_used`, `rejected.attempted_action/error`, `end.outcome`) and static-data types (`space.json` floors/rooms/cells, `puzzle.json` dialogue/`on_wrong`/`on_correct`/`answer`/`start_cell`, `npc.json` name/image)
- [X] T008 [P] Create `viewer/src/logparse.ts` validating schema pass plus `t` starting at 1 increasing by 1 with only the last event `end`; otherwise refuse playback with a reason (spec Edge Cases)
- [X] T009 [P] Create `viewer/src/dataload.ts` reading built-in `window.RT_DATA` and ad-hoc logs via `<input type="file">` + `FileReader` only (no `fetch`/XHR local reads)
- [X] T010 Create `viewer/src/scene.ts` with `requestAnimationFrame` repeat rendering plus `webglcontextlost` → `preventDefault()` and `webglcontextrestored` → scene rebuild (no one-shot `render()` pages)
- [X] T011 [P] Create `viewer/src/theme.ts` with tokens Base `#E9DCC0`–`#DCCFAC`, Ink `#2A2118`, Seal Red `#A0322B` (stuck/failed segments only), code-generated `CanvasTexture` parchment; photos render via `<img>`, never WebGL textures

**Checkpoint**: Foundation ready — `embed.py` + scene/loading/validation modules exist; story implementation can now begin.

---

## Phase 3: User Story 1 - 평면도 위 발자국 확인 (Priority: P1) 🎯 MVP

**Goal**: `start_cell` 시작·`move.value` 순서 발자국 궤적을 평면도 위에 표시. 끊김 로그는 끊긴 지점에서 멈추고 표시.

**Independent Test**: `logs/drunkard-set/` 로그 1개로 전체 궤적을 순서대로 재생하고, 궤적 점 개수 = 해당 로그의 `move` 이벤트 수 + 1이면 통과 (quickstart V-2).

- [X] T012 [P] [US1] Create `viewer/testdata/stuck-action-limit.json` as a `log.schema.json`-passing sample ending in `end(action_limit)` (kept out of `logs/<set>/`, FR-008)
- [X] T013 [US1] Create `viewer/src/plane.ts` rendering floors from `space.json` as `PlaneGeometry` on the `columns`×`rows` grid (1 cell = 1m, `cellRef` pattern, `2F-C4`-style prefixes, `walls`/`doors`/`origin_px`/`meters_per_pixel`)
- [X] T014 [US1] Create `viewer/src/trail.ts` drawing trajectory as `Line` plus footprints as `Points` with point count = `move` count + 1 (`start_cell` first), stuck segments in Seal Red `#A0322B`
- [X] T015 [US1] Extend `viewer/src/main.ts` with US1 wiring loading built-in `RT_DATA` or a file-input log and driving `plane.ts` + `trail.ts` in `t` order with stuck-stop display
- [X] T016 [US1] Extend `viewer/index.html` with US1 playback controls and missing-photo empty-frame slots (trajectory/dialogue keep playing when photos are absent)

**Checkpoint**: US1 fully functional and testable independently (V-2: both embedded-sample and file-input paths, stuck display).

---

## Phase 4: User Story 2 - 고스트 재생으로 막힌 지점 확인 (Priority: P2)

**Goal**: 1회 실행의 시간순 고스트 재생 — `view` 사진·`npc_dialogue`, 맞은 답·틀린 답, 화면 전용 반응, 퍼즐 종료 결과, `failed` 직후 정답 1회.

**Independent Test**: `logs/drunkard-set/oracle/r0.json` 재생이 전 퍼즐 `solved_by_dialogue`와 `end(completed)`까지 끊김 없이 보이면 통과 (quickstart V-3).

- [X] T017 [P] [US2] Create `viewer/testdata/failed.json` as a `log.schema.json`-passing sample containing `puzzle_ended(failed)` (kept out of `logs/<set>/`, FR-008)
- [X] T018 [US2] Create `viewer/src/ghost.ts` implementing ordered playback state (current `t`, puzzle number, cell, opened-object set, submission result, end result) over start → `move` → `view` → `npc_dialogue` → `answer_submitted` → (`hint_revealed` | `puzzle_ended`) → next puzzle or `end`
- [X] T019 [US2] Create `viewer/src/panels.ts` showing at each `view` point the object photo (`<img>`) and `npc_dialogue`, per-puzzle `puzzle_ended.result`, `on_wrong`/`on_correct` in order, `answer_submitted.value` as submitted verbatim, and the matching `puzzle.json answer` exactly once right after `puzzle_ended(failed)`; never showing `next_object_id`, pre-completion `next_instruction`, photo paths/hashes, unreleased hints, or answers of non-`failed` puzzles (FR-005)
- [X] T020 [US2] Extend `viewer/src/main.ts` with US2 ghost wiring driving `ghost.ts` + `panels.ts` over the US1 trajectory
- [X] T021 [US2] Extend `viewer/index.html` with US2 ghost controls and result display regions

**Checkpoint**: US1 AND US2 both work independently (V-3: oracle uninterrupted, `failed` answer shown once, non-`failed` answers absent from screen and outputs).

---

## Phase 5: User Story 3 - 층 전환 (Priority: P3)

**Goal**: 다층 로그에서 층별 평면 전환. 단층 로그에서는 층 UI 없음.

**Independent Test**: 2층 표본 재생 시 층별 궤적이 각 층 평면에 표시되고 단층 로그에서는 층 UI가 없으면 통과 (quickstart V-4).

- [X] T022 [P] [US3] Create `viewer/testdata/multilayer.json` as a `log.schema.json`-passing 2-floor sample with `2F-` style prefixed cells (kept out of `logs/<set>/`, FR-008)
- [X] T023 [US3] Create `viewer/src/floors.ts` grouping floor planes by cell prefix with group-visibility switching so only the active floor's moves and observations show
- [X] T024 [US3] Extend `viewer/src/main.ts` with US3 floor-switching wiring over ghost playback
- [X] T025 [US3] Extend `viewer/index.html` with a floor selector that is hidden entirely for single-floor logs

**Checkpoint**: All user stories independently functional (V-4: per-floor display, no floor UI on single-floor logs).

---

## Phase 6: Slice 4 - 주문·잉크 연출 + 배포 (FR-006 + FR-007)

**Purpose**: 진입 전 랜딩 화면의 주문·잉크 연출과 컴파일-JS-커밋 배포 (R-5, R-6). 사용자 결정(2026-11-04): 주체 = 실행자 본인이 외우는 듯한 연출(극 중 시전 인물 없음), 범위 = 진입 전 랜딩 화면. 진입 방식(버튼/자동)은 착수 시 정한다.

**Independent Test**: 랜딩 화면에서 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적이 5초 이내 끊김 없이 재생; 실패·끊김 로그도 완주 아님 표시와 함께 끝까지 재생 (quickstart V-5).

- [X] T026 Create `viewer/src/order.ts` rendering the pre-entry landing intro (spell text + red seal overlay + SVG `stroke-dashoffset` ink trail, executor-self framing, no in-fiction caster) playing without stutter within 5 seconds
- [X] T027 Extend `viewer/src/main.ts` with landing-to-program entry wiring (button vs auto decided at slice start)
- [X] T028 Extend `viewer/index.html` with the landing intro screen (red subtitle + edge vignette) placed before program entry
- [ ] T029 Regenerate `viewer/dist/data.js` via `viewer/tools/embed.py` and build `viewer/dist/app.js` via `viewer/node_modules/.bin/tsc -p viewer` only, then verify console error/warning-free at `file://$PWD/viewer/index.html`; deploy set is `dist/app.js` + `dist/data.js` + `vendor/three.cjs` with `node_modules`/`.shots` excluded (Muse does not commit; a human commits)

**Checkpoint**: Order/ink + offline deploy verified (V-5).

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: 언어·노출 감사·전체 회귀. 영어 전체 번역은 시간 여유 시 별도 작업 (FR-009, Out of Scope).

- [X] T030 Polish Korean copy in `viewer/index.html` and `viewer/src/*.ts` strings (default language Korean; no webfonts)
- [ ] T031 Run quickstart validation V-1 through V-5 via Playwright MCP only (console collection → real-UI operation → before/after screenshots in `.shots/` opened with `read_file` → PASS/FAIL per item) plus V-6 regression gate `.venv/bin/python -m unittest discover tests -v` (never bare `python`/`python3`)
- [X] T032 Audit exposure compliance in viewer screens and outputs: no `next_object_id`, `next_instruction`, photo paths/hashes, unreleased hints, or non-`failed` puzzle answers; `failed` answers appear only once right after `puzzle_ended(failed)` (FR-005, data-model Display Exposure)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately. Human env prep (`implementation-notes.md` §4) runs outside Muse in parallel.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all stories and Slice 4.
- **US1 (Phase 3)**: After Foundational. MVP.
- **US2 (Phase 4)**: After Foundational; builds on US1 trajectory but independently testable via V-3.
- **US3 (Phase 5)**: After Foundational; builds on US1/US2 but independently testable via V-4.
- **Slice 4 (Phase 6)**: After US1–US3 (order intro frames the working viewer).
- **Polish (Final)**: After all desired slices.

### Within Each Story

- Test-data sample first (`testdata/*.json` must pass `log.schema.json`), then model/scene modules, then `main.ts`/`index.html` wiring.
- `main.ts` and `index.html` extensions are sequential per slice (same files, no `[P]`).

### Parallel Opportunities

- T002 `[P]` alongside T001 (different files); T008/T009/T011 `[P]` within Foundational (different files, no interdependency).
- `viewer/testdata/*.json` samples (T012, T017, T022) `[P]` — independent files.
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
# Launch independent schema-passing samples together (different files):
Task: "Create viewer/testdata/stuck-action-limit.json (US1)"
Task: "Create viewer/testdata/failed.json (US2)"
Task: "Create viewer/testdata/multilayer.json (US3)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (+ human env prep outside Muse).
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: US1 footprint trajectory.
4. **STOP and VALIDATE**: V-2 independently (point count = `move` + 1, stuck display, both load paths) + V-6 gate.
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

- `[P]` = different files, no dependencies. `[USn]` maps the task to its story for traceability.
- Each story is independently completable and testable via its quickstart scenario.
- `file://` prohibitions hold everywhere: no ES modules, importmap, CDN, external URLs, local server, `fetch`/XHR local reads, or photo WebGL textures.
- Exact versions everywhere: `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0` (0.186+ `three.cjs` is an empty 631-byte file; TS 7 drops `outFile` + `module: none`).
- Script order in `viewer/index.html` never changes (contracts Loading Contract).
- Stop at any checkpoint to validate the slice independently.
- Per `/speckit-implement` rule: before implementing, compare this scope against the request; if the request excludes a slice or defers it, ask whether to regenerate tasks first.
