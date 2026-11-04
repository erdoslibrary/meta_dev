# Quickstart: 뷰어 슬라이스 검증 가이드

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Contracts**: [contracts/viewer.md](contracts/viewer.md)

구현 코드 없이 검증만 기술한다. 전체 실행 가이드는 tasks·구현 단계에서 확장한다. 화면 확인은 Playwright MCP로만 하고, 셸에서 Chrome을 실행하지 않는다(`implementation-notes.md` §3·§5).

## Prerequisites

- Node 24.13.1 (`node -v` 확인. 시스템 Node 12에서는 `tsc`가 `SyntaxError: Unexpected token '?'`로 실패).
- 고정 버전: `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0`.
- 환경 준비(`implementation-notes.md` §4, Muse 밖 터미널에서 1회): `viewer/vendor/three.cjs`·`viewer/node_modules` 심볼링크, Playwright MCP 등록.
- 테스트 게이트: `.venv/bin/python -m unittest discover tests -v` (뷰어 작업 후에도 통과, SC-004).

## Validation Scenarios

### V-1: 빌드 (슬라이스 공통)

```zsh
viewer/node_modules/.bin/tsc -p viewer
```

- 기대: `viewer/dist/app.js` 단일 출력. `npm` 명령 실행 없음.
- 기대: `file://$PWD/viewer/index.html`을 열면 콘솔 error·warning 없음.

### V-2: US1 발자국 (Slice 1)

- 입력 (a) 내장 표본: `viewer/dist/data.js`. 입력 (b) 파일 선택: `logs/drunkard-set/` 로그 1개를 `<input type="file">`로 로드.
- 기대: 생성물-원본 일치 — (a)의 표본 로그가 원본 파일과 이벤트 수·`t` 순서가 같다.
- 기대: 두 경로 모두 `start_cell`에서 시작해 `move.value` 순서대로 궤적이 이어진다.
- 기대: 궤적 점 개수 = 해당 로그의 `move` 이벤트 수 + 1.
- 기대: `end(action_limit)`·`end(api_error)` 로그는 끊긴 지점에서 멈추고 끊김 표시.

### V-3: US2 고스트 (Slice 2)

- 입력: `logs/drunkard-set/oracle/r0.json`.
- 기대: 전 퍼즐 `solved_by_dialogue`와 `end(completed)`까지 끊김 없이 재생.
- 기대: `view` 지점에서 사물 사진(`<img>`)과 `npc_dialogue` 표시, 퍼즐 종료마다 결과 표시.
- 기대: `failed` 포함 표본(`viewer/testdata/`)에서는 `puzzle_ended(failed)` 직후 해당 퍼즐 정답 1회 표시. `failed`가 아닌 퍼즐 정답은 화면·산출물에 없음.

### V-4: US3 층 전환 (Slice 3)

- 입력: `viewer/testdata/` 다층 표본(`log.schema.json` 통과).
- 기대: 층별 평면에 해당 층 이동·관측만 표시. 단층 로그에서는 층 UI 없음.

### V-5: 주문·잉크 + 배포 (Slice 4)

- 기대: 진입 전 랜딩 화면에서 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적이 5초 이내 끊김 없이 재생. 실행자 본인이 외우는 듯한 연출, 극 중 시전 인물 없음.
- 기대: 실패·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.
- 기대: `viewer/dist/app.js`·`dist/data.js`·`vendor/three.cjs` 커밋, `node_modules`·`.shots` 미커밋. `file://`로 서버 없이 동작.

### V-6: 회귀 게이트

```zsh
.venv/bin/python -m unittest discover tests -v
```

- 기대: 전원 통과. `python`·`python3` 직접 사용 없음.

## Out of Scope (plan 이후·구현 단계)

- 영어 전체 번역(뷰어 UI·보고서·퍼즐 데이터, 잔여 시간 있을 때).
- 003 마우스 평면도 빌더.
- 주문 진입 방식(버튼/자동)은 Slice 4 착수 시 정한다.
