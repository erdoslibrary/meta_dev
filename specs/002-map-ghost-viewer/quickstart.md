# Quickstart: 뷰어 슬라이스 검증 가이드

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Contracts**: [contracts/viewer.md](contracts/viewer.md)

**변경 사유 (2026-11-04)**: `tsc` 통과 기준 명확화(`app.js` 생성+내용 확인), 재생 거부·사진 누락 검증 추가, 파일 선택 로그 `failed` 정답 조건(결정 B) 추가.
**변경 사유 (2026-11-04)**: 검증 분리·결정 A 후속·배포 묶음을 반영. 내장 로그는 `embed.py` 원본 검증 + 브라우저 `t`·마지막 `end` 검증, 파일 선택 로그는 브라우저 전체 검증(`reason` 표시 제외)(차단 1). `on_correct` 맞힌 제출 뒤 표시·정답은 `answer` 필드 한정·`next_instruction`은 `failed` 직후 1회(맞힌 퍼즐 제외·`null` 제외·파일 선택 동시 선택 조건)(차단 2). V-2에 다중 이동 표본 검증을 추가한다(권장 10). 배포 묶음을 T029와 일치시킨다(`index.html`·`data/<set>/` 사진 포함)(권장 7).
**변경 사유 (2026-11-04)**: 검증 규칙 3건을 반영. 재생 거부 표본은 `embed.py` 게이트에서 제외하고 `data.js`에 포함하며 V-2에서 거부·이유 표시만 확인한다(항목 1). 파일 선택 검증은 재생 필요 항목 범위로 한정한다(항목 2).
**변경 사유 (2026-11-04)**: `embed.py`는 표준 라이브러리 + `jsonschema`만 허용하고(새 패키지 설치 없음) `.venv/bin/python`으로 실행한다(항목 3).
**변경 사유 (2026-11-04)**: V-1을 T037과 맞춰 `.venv/bin/python viewer/tools/embed.py`를 먼저 실행하도록 고친다(권장 7).
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. V-3 next_instruction 표시·null 확인은 3번 표본으로 한다고 명시한다.

구현 코드 없이 검증만 기술한다. 전체 실행 가이드는 tasks·구현 단계에서 확장한다. 화면 확인은 Playwright MCP로만 하고, 셸에서 Chrome을 실행하지 않는다(`implementation-notes.md` §3·§5).

## Prerequisites

- Node 24.13.1 (`node -v` 확인. 시스템 Node 12에서는 `tsc`가 `SyntaxError: Unexpected token '?'`로 실패).
- 고정 버전: `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0`.
- 환경 준비(`implementation-notes.md` §4, Muse 밖 터미널에서 1회): `viewer/vendor/three.cjs`·`viewer/node_modules` 심볼링크, Playwright MCP 등록.
- 테스트 게이트: `.venv/bin/python -m unittest discover tests -v` (뷰어 작업 후에도 통과, SC-004).

## Validation Scenarios

### V-1: 빌드 (슬라이스 공통)

```zsh
.venv/bin/python viewer/tools/embed.py
viewer/node_modules/.bin/tsc -p viewer
```

- 기대: `embed.py`를 `.venv/bin/python`으로 먼저 실행해 `viewer/dist/data.js`를 생성한다(bare `python`/`python3`·패키지 설치 금지, T037). `viewer/dist/app.js` 단일 출력. 통과 기준은 exit 0이 아니라 `viewer/dist/app.js` 생성과 내용 확인이다. `npm` 명령 실행 없음.
- 기대: `file://$PWD/viewer/index.html`을 열면 콘솔 error·warning 없음.

### V-2: US1 발자국 (Slice 1)

- 입력 (a) 내장 표본: `viewer/dist/data.js`. 입력 (b) 파일 선택: `logs/drunkard-set/` 로그 1개를 `<input type="file">`로 로드.
- 기대: 생성물-원본 일치 — (a)의 표본 로그가 원본 파일과 이벤트 수·`t` 순서가 같다.
- 기대: 두 경로 모두 `start_cell`에서 시작해 `move.value` 순서대로 궤적이 이어진다.
- 기대: 궤적 점 개수 = 해당 로그의 `move` 이벤트 수 + 1.
- 기대: `end(action_limit)`·`end(api_error)` 로그는 끊긴 지점에서 멈추고 끊김 표시.
- 기대: `t` 불연속·마지막 비-`end` 표본은 `data.js`에 포함하되 재생을 거부하고 이유를 표시한다. 내장 표본 중 스키마 통과 요구 로그는 `embed.py`가 원본(`reason` 제거 전)을 `log.schema.json`으로 검증하고 실패 시 `data.js`를 생성하지 않으며, 브라우저는 내장 로그의 `t` 순서와 마지막 `end`만 검증한다. 파일 선택 로그는 브라우저에서 재생 필요 항목(최상위 필수 필드·종류별 필수 필드·값 타입과 enum·칸·사물 표기·`t`·마지막 `end`)만 검증하되 `reason`은 표시하지 않는다.
- 기대: 다중 이동 표본(`viewer/testdata/` 다중 이동)은 궤적 점 개수 = `move` 수 + 1을 만족하며 순서대로 재생된다.
- 기대: 사진 누락 시 빈틀로 표시하고 궤적·대화 재생은 계속된다.

### V-3: US2 고스트 (Slice 2)

- 입력: `logs/drunkard-set/oracle/r0.json`.
- 기대: 전 퍼즐 `solved_by_dialogue`와 `end(completed)`까지 끊김 없이 재생.
- 기대: `view` 지점에서 사물 사진(`<img>`)과 `npc_dialogue` 표시, 퍼즐 종료마다 결과 표시. `on_correct`는 맞힌 제출 뒤에 표시하며 대사에 포함된 다음 장소와 정답 문자열도 그대로 표시한다. `answer_submitted.value`는 제출 원문 표시를 허용한다.
- 기대: `failed` 포함 표본(`viewer/testdata/`)에서는 `puzzle_ended(failed)` 직후 해당 퍼즐 정답(`puzzle.json`의 `answer` 필드)과 `next_instruction` 1회 표시. `failed`가 아닌 퍼즐 정답은 화면·산출물에 없음. 맞힌 퍼즐에는 `next_instruction`을 표시하지 않으며, 맞힌 퍼즐의 다음 장소는 `on_correct`로 전달한다. `next_instruction`이 `null`이면(마지막 퍼즐) 다음 장소 문구를 표시하지 않는다. `next_instruction` 표시와 `null` 확인은 3번 표본(퍼즐 2개: 1번 `failed` 값 있음·2번 `failed` `null`)으로 한다.
- 기대: 파일 선택 로그의 `failed` 정답·`next_instruction`은 로그와 `puzzle.json`을 함께 선택했을 때만 표시하고, 없으면 "정답 데이터 없음"만 표시하고 다음 장소 문구는 표시하지 않는다. 정답 금지 대상은 `puzzle.json`의 `answer` 필드로 한정한다.

### V-4: US3 층 전환 (Slice 3)

- 입력: `viewer/testdata/` 다층 표본(`log.schema.json` 통과).
- 기대: 층별 평면에 해당 층 이동·관측만 표시. 단층 로그에서는 층 UI 없음.

### V-5: 주문·잉크 + 배포 (Slice 4)

- 기대: 진입 전 랜딩 화면에서 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적이 5초 이내 끊김 없이 재생. 실행자 본인이 외우는 듯한 연출, 극 중 시전 인물 없음.
- 기대: 실패·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.
- 기대: 배포 묶음은 `index.html` + `dist/app.js` + `dist/data.js` + `vendor/three.cjs` + `data/<set>/` 사진 포함(T029). `node_modules`·`.shots` 미커밋. `file://`로 서버 없이 동작.

### V-6: 회귀 게이트

```zsh
.venv/bin/python -m unittest discover tests -v
```

- 기대: 전원 통과. `python`·`python3` 직접 사용 없음.

## Out of Scope (plan 이후·구현 단계)

- 영어 전체 번역(뷰어 UI·보고서·퍼즐 데이터, 잔여 시간 있을 때).
- 003 마우스 평면도 빌더.
- 주문 진입 방식(버튼/자동)은 Slice 4 착수 시 정한다.
