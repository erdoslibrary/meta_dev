# Implementation Plan: 갈래2 지도·고스트 뷰어

**Branch**: `002-map-ghost-viewer` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-map-ghost-viewer/spec.md`

**변경 사유 (2026-11-04)**: 결정 C·D 표현 정리와 배포 묶음 일치를 반영. Constitution Check의 노출 금지 항목을 사진 경로(화면 금지)와 해시(산출물 금지)로 분리하고(권장 6), 슬라이스 서술을 결정 C(지도 궤적 `Line`+`Points`·잉크 효과 랜딩 한정)·결정 D(Seal Red 끊김·실패 세 가지 한정·랜딩 예외)에 맞추며, 배포 묶음을 T029와 일치시킨다(`index.html`·`data/<set>/` 사진 포함)(권장 7).
**변경 사유 (2026-11-04)**: `embed.py` 실행 규칙을 반영. 표준 라이브러리 + `jsonschema`만 허용하고(새 패키지 설치 없음) `.venv/bin/python`으로 실행하며, 환경 문제로 실패하면 원문과 함께 보고한다(항목 3).
**변경 사유 (2026-11-04)**: 표본 구조를 바로 아래 `*.json`·`refusal/`·`sets/<puzzle_set_id>/`로 정한다(차단 4, 권장 6).
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. Constitution Check·구조에 T035·T036 unittest 추가를 반영한다(새 러너 없음).
**변경 사유 (2026-11-05)**: PRD OPEN-4 보완 반영. Slice 4에 랜딩 영어 전용과 닫는 주문 결과 박스 꼬리말 표시를 적는다.

## Summary

저장된 갈래1 로그(`logs/<set>/`)와 읽기 전용 정적 데이터(`data/<set>/`)만으로 평면도 위 발자국 궤적(US1) → 고스트 재생(US2) → 층 전환(US3) → 주문·잉크 연출+배포(Slice 4) 순서로 뷰어를 만든다. 엔진·로그·데이터 형식 변경 없음. `three.js` + TS, `tsc` 단일 출력, 벤더 동봉, `file://` 오프라인. 로딩은 생성 JS(`dist/data.js`) + 파일 선택 하이브리드, 렌더링은 반복 루프 + 컨텍스트 복구다. plan에서 위임받은 2건(배포 방식=컴파일 JS 커밋, 주문·잉크 수용 시나리오=동작·타이밍 기준)을 결정하고, 사용자 결정(2026-11-04)으로 주문 주체(실행자 본인인 듯한 연출, 극 중 시전 인물 없음)·화면 범위(진입 전 랜딩 화면)도 확정한다.

## Technical Context

**Language/Version**: TypeScript 5.9.3 (정확 고정), 빌드 `viewer/node_modules/.bin/tsc -p viewer`만. Node 24.13.1 필요.

**Primary Dependencies**: `three 0.185.0`(벤더 `viewer/vendor/three.cjs` 동봉), `@types/three 0.185.0`. 정확한 버전 고정. 번들러·CDN·외부 URL 없음.

**Storage**: 파일만. 입력 로그 `logs/<set>/`, 정적 데이터 `data/<set>/`, 테스트 표본 `viewer/testdata/`(스키마 통과 요구 로그는 바로 아래 `*.json`만, 재생 거부 표본은 `refusal/`, 표본 세트 정적 데이터는 `sets/<puzzle_set_id>/`; `logs/`에 섞지 않음). 생성물 `viewer/dist/data.js`(`window.RT_DATA`)·`viewer/dist/app.js` 커밋. 별도 서버 없음.

**Testing**: 갈래1 게이트 `.venv/bin/python -m unittest discover tests -v` 유지(SC-004). 뷰어 검증은 Playwright MCP 화면 확인(`implementation-notes.md` §5: 콘솔 수집→실UI 조작→전후 스크린샷→`read_file` 비교→PASS/FAIL). `check_page.py`·Playwright 설치·셸 Chrome 실행 금지.

**Target Platform**: `file://`로 연 오프라인 페이지(Chrome 146 시험). 로컬 서버 없음.

**Project Type**: frontend static viewer (`viewer/`: `index.html`, `src/*.ts` → `dist/app.js`, `vendor/`, `tools/embed.py`, `testdata/`).

**Performance Goals**: US1 3분 확인(SC-001). 오라클 재생 끊김 없음(SC-002). 주문 연출 5초 이내 재생(Slice 4).

**Constraints**: ES 모듈·importmap·`fetch`/XHR 로컬 읽기·사진 WebGL 텍스처 금지(헌법 II). 사진은 `<img>`. 스크립트 순서 고정(contracts 참조). `npm`·`pip install` 금지(환경 문제는 원문 보고). 커밋 금지. TRD §4 노출 금지 준수(FR-005).

**Scale/Scope**: 신규 `viewer/` 1 폴더. 슬라이스 4개(US1→US2→US3→주문+배포). 각 슬라이스 = spec 사용자 스토리 1개 = tasks 페이즈 1개(AGENTS.md).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. 테스트 게이트: `.venv/bin/python -m unittest discover tests -v` 통과 없이 완료 선언 금지 → quickstart V-6 회귀로 고정(T035·T036 unittest 추가, 새 테스트 러너 도입 없음).
- [x] I. JS Vitest 등 신규 러너 도입 금지 → 검증은 Playwright MCP 화면 확인만, 러너 추가 없음.
- [x] I. TRD §4 거절 문구·`to_log` 규칙 → 뷰어가 로그를 생성하지 않고 읽기만 하므로 위반 경로 없음.
- [x] II. 갈래2 TS+three.js+`tsc` 단일 출력, 허용 3종 정확한 버전, 번들러·CDN·외부 URL 없음 → R-3·contracts에 고정.
- [x] II. `file://` 동작, ES 모듈·importmap·`fetch`/XHR·사진 WebGL 텍스처 의존 금지 → R-2·R-3·contracts에 고정.
- [x] II. 데이터·로그·보고서 파일만, 별도 서버 없음 → Technical Context·contracts에 고정.
- [x] II. 엔진 순수 상태 머신·계약 기준(스키마+TRD §3~§6) → 형식 변경 없음 선언.
- [x] II. TRD §11 미결은 결정 금지. 단 plan 위임 2건(배포 방식, 주문·잉크 수용 시나리오)은 결정 → R-5·R-6에 결정 기록. 주문 주체·화면 범위는 사용자 결정(2026-11-04)으로 확정 → spec·R-6·contracts에 기록.
- [x] III. 비밀 기록 금지 → contracts에 사진 경로·해시 표시 금지 포함.
- [x] III. TRD §4 노출 금지 → data-model·contracts Display Exposure에 고정(`failed` 직후 1회 예외만). 사진 경로(화면 금지)와 해시(산출물 금지)는 분리 표기.
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
│   ├── app.js           # tsc 단일 출력 (커밋, T029 배포 묶음)
│   └── data.js          # embed.py 생성물 window.RT_DATA (커밋, T029 배포 묶음)
├── tools/
│   └── embed.py         # stdlib + jsonschema만 허용, .venv/bin/python 실행 (Slice 1)
└── testdata/            # 바로 아래 *.json=스키마 통과 요구 로그, refusal/=재생 거부, sets/<id>/=표본 세트 (logs/에 섞지 않음)

tests/                   # 기존 유지 + T035·T036 unittest(새 러너 없음), 뷰어가 깨뜨리지 않음을 V-6으로 확인
```

**Structure Decision**: TRD §2 위임에 따라 별도 폴더 `viewer/`로 확정(R-1). 갈래1 `realtosim/` 패키지는 손대지 않는다. 배포 묶음은 `viewer/index.html` + `viewer/dist/app.js` + `viewer/dist/data.js` + `viewer/vendor/three.cjs` + `data/<set>/` 사진(T029, R-5).

## Slices (plan 슬라이스 = spec US 1개 = tasks 페이즈 1개)

- **Slice 1 (US1, P1)**: 평면 + 발자국 궤적(`Line`+`Points`) + 로딩 기반(`embed.py`, `data.js`, 파일 선택). 수용: 궤적 점 = `move` 수 + 1, 끊김·실패 표시(Seal Red는 `puzzle_ended(failed)`·`end(action_limit)`·`end(api_error)`에만, 랜딩 화면 예외). 잉크 효과는 랜딩 화면에만.
- **Slice 2 (US2, P2)**: 고스트 재생(`view` 사진·`npc_dialogue`·`on_wrong`/`on_correct`·`puzzle_ended`, `failed` 정답·`next_instruction` 1회). 수용: 오라클 끊김 없음.
- **Slice 3 (US3, P3)**: 층 전환(다층 표본 `testdata/`, 단층 무UI).
- **Slice 4 (FR-006+FR-007)**: 주문·잉크 연출(수용 R-6: 진입 전 랜딩 화면, 실행자 본인인 듯한 연출) + 배포(컴파일 JS 커밋, R-5). 진입 방식(버튼/자동)은 착수 시 정한다. 보완(2026-11-05): 랜딩은 영어 전용(여는 주문 + `Enter`), 닫는 주문은 별도 화면 없이 `end(completed)` 결과 박스 꼬리말 한 줄로 표시하며 완주 표시는 그대로 둔다.

## Complexity Tracking

해당 없음 (Constitution Check 위반 없음).
