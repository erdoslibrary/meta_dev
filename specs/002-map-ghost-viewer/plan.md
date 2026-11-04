# Implementation Plan: 갈래2 지도·고스트 뷰어

**Branch**: `002-map-ghost-viewer` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-map-ghost-viewer/spec.md`

## Summary

저장된 갈래1 로그(`logs/<set>/`)와 읽기 전용 정적 데이터(`data/<set>/`)만으로 평면도 위 발자국 궤적(US1) → 고스트 재생(US2) → 층 전환(US3) → 주문·잉크 연출+배포(Slice 4) 순서로 뷰어를 만든다. 엔진·로그·데이터 형식 변경 없음. `three.js` + TS, `tsc` 단일 출력, 벤더 동봉, `file://` 오프라인. 로딩은 생성 JS(`dist/data.js`) + 파일 선택 하이브리드, 렌더링은 반복 루프 + 컨텍스트 복구다. plan에서 위임받은 2건(배포 방식=컴파일 JS 커밋, 주문·잉크 수용 시나리오=동작·타이밍 기준)을 결정하고, 사용자 결정(2026-11-04)으로 주문 주체(실행자 본인인 듯한 연출, 극 중 시전 인물 없음)·화면 범위(진입 전 랜딩 화면)도 확정한다.

## Technical Context

**Language/Version**: TypeScript 5.9.3 (정확 고정), 빌드 `viewer/node_modules/.bin/tsc -p viewer`만. Node 24.13.1 필요.

**Primary Dependencies**: `three 0.185.0`(벤더 `viewer/vendor/three.cjs` 동봉), `@types/three 0.185.0`. 정확한 버전 고정. 번들러·CDN·외부 URL 없음.

**Storage**: 파일만. 입력 로그 `logs/<set>/`, 정적 데이터 `data/<set>/`, 테스트 표본 `viewer/testdata/`(`log.schema.json` 통과, `logs/`에 섞지 않음). 생성물 `viewer/dist/data.js`(`window.RT_DATA`)·`viewer/dist/app.js` 커밋. 별도 서버 없음.

**Testing**: 갈래1 게이트 `.venv/bin/python -m unittest discover tests -v` 유지(SC-004). 뷰어 검증은 Playwright MCP 화면 확인(`implementation-notes.md` §5: 콘솔 수집→실UI 조작→전후 스크린샷→`read_file` 비교→PASS/FAIL). `check_page.py`·Playwright 설치·셸 Chrome 실행 금지.

**Target Platform**: `file://`로 연 오프라인 페이지(Chrome 146 시험). 로컬 서버 없음.

**Project Type**: frontend static viewer (`viewer/`: `index.html`, `src/*.ts` → `dist/app.js`, `vendor/`, `tools/embed.py`, `testdata/`).

**Performance Goals**: US1 3분 확인(SC-001). 오라클 재생 끊김 없음(SC-002). 주문 연출 5초 이내 재생(Slice 4).

**Constraints**: ES 모듈·importmap·`fetch`/XHR 로컬 읽기·사진 WebGL 텍스처 금지(헌법 II). 사진은 `<img>`. 스크립트 순서 고정(contracts 참조). `npm`·`pip install` 금지(환경 문제는 원문 보고). 커밋 금지. TRD §4 노출 금지 준수(FR-005).

**Scale/Scope**: 신규 `viewer/` 1 폴더. 슬라이스 4개(US1→US2→US3→주문+배포). 각 슬라이스 = spec 사용자 스토리 1개 = tasks 페이즈 1개(AGENTS.md).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. 테스트 게이트: `.venv/bin/python -m unittest discover tests -v` 통과 없이 완료 선언 금지 → quickstart V-6 회귀로 고정.
- [x] I. JS Vitest 등 신규 러너 도입 금지 → 검증은 Playwright MCP 화면 확인만, 러너 추가 없음.
- [x] I. TRD §4 거절 문구·`to_log` 규칙 → 뷰어가 로그를 생성하지 않고 읽기만 하므로 위반 경로 없음.
- [x] II. 갈래2 TS+three.js+`tsc` 단일 출력, 허용 3종 정확한 버전, 번들러·CDN·외부 URL 없음 → R-3·contracts에 고정.
- [x] II. `file://` 동작, ES 모듈·importmap·`fetch`/XHR·사진 WebGL 텍스처 의존 금지 → R-2·R-3·contracts에 고정.
- [x] II. 데이터·로그·보고서 파일만, 별도 서버 없음 → Technical Context·contracts에 고정.
- [x] II. 엔진 순수 상태 머신·계약 기준(스키마+TRD §3~§6) → 형식 변경 없음 선언.
- [x] II. TRD §11 미결은 결정 금지. 단 plan 위임 2건(배포 방식, 주문·잉크 수용 시나리오)은 결정 → R-5·R-6에 결정 기록. 주문 주체·화면 범위는 사용자 결정(2026-11-04)으로 확정 → spec·R-6·contracts에 기록.
- [x] III. 비밀 기록 금지 → contracts에 사진 경로·해시 표시 금지 포함.
- [x] III. TRD §4 노출 금지 → data-model·contracts Display Exposure에 고정(`failed` 직후 1회 예외만).
- [x] IV. spec→plan→tasks→implement 순서, `requirement.md` SSOT → 본 plan이 그 순서대로 생성. tasks는 `/speckit-tasks`에서 별도 생성(본 plan에서 만들지 않음).

위반 없음. Complexity Tracking 불필요.

## Project Structure

### Documentation (this feature)

```text
specs/002-map-ghost-viewer/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── viewer.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
viewer/
├── index.html           # 스크립트 순서 고정 (contracts 참조)
├── tsconfig.json        # target es2020, module none, outFile dist/app.js
├── src/
│   ├── three-global.d.ts
│   ├── main.ts          # 진입점 (슬라이스별 확장)
│   └── ...
├── vendor/
│   └── three.cjs        # three 0.185.0 동봉 (커밋)
├── dist/
│   ├── app.js           # tsc 단일 출력 (커밋)
│   └── data.js          # embed.py 생성물 window.RT_DATA (커밋)
├── tools/
│   └── embed.py         # stdlib only 생성 스크립트 (Slice 1)
└── testdata/            # log.schema.json 통과 표본 (logs/에 섞지 않음)

tests/                   # 기존 유지, 뷰어가 깨뜨리지 않음을 V-6으로 확인
```

**Structure Decision**: TRD §2 위임에 따라 별도 폴더 `viewer/`로 확정(R-1). 갈래1 `realtosim/` 패키지는 손대지 않는다.

## Slices (plan 슬라이스 = spec US 1개 = tasks 페이즈 1개)

- **Slice 1 (US1, P1)**: 평면 + 발자국 궤적 + 로딩 기반(`embed.py`, `data.js`, 파일 선택). 수용: 궤적 점 = `move` 수 + 1, 끊김 표시. 디자인: 평면·격자·먹 궤적.
- **Slice 2 (US2, P2)**: 고스트 재생(`view` 사진·`npc_dialogue`·`on_wrong`/`on_correct`·`puzzle_ended`, `failed` 정답 1회). 수용: 오라클 끊김 없음.
- **Slice 3 (US3, P3)**: 층 전환(다층 표본 `testdata/`, 단층 무UI).
- **Slice 4 (FR-006+FR-007)**: 주문·잉크 연출(수용 R-6: 진입 전 랜딩 화면, 실행자 본인인 듯한 연출) + 배포(컴파일 JS 커밋, R-5). 진입 방식(버튼/자동)은 착수 시 정한다.

## Complexity Tracking

해당 없음 (Constitution Check 위반 없음).
