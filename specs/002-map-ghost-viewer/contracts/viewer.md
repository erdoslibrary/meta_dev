# Contracts: 뷰어 입출력·로딩·렌더링

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Input Contract (읽기 전용, 형식 변경 없음)

- 로그: `logs/<set>/`의 `log.schema.json` 통과 파일 1개. `run_id`, `events[]` 사용.
- 정적 데이터: `data/<set>/`의 `space.json`, `puzzle.json`, `npc.json`, 사진 파일. 엔진·로그·데이터 형식 변경을 요구하지 않는다(FR-001).
- 테스트 표본: `viewer/testdata/`의 `log.schema.json` 통과 파일. `logs/<set>/`에 섞지 않는다(FR-008).
- 빌드 입력: `viewer/src/*.ts`, `viewer/vendor/three.cjs`(`three 0.185.0`), `viewer/dist/data.js`(생성물, `window.RT_DATA`).

## Loading Contract (`file://`, classic script only)

- `viewer/index.html` 스크립트 순서(`implementation-notes.md` §2, 순서 변경 금지):
  1. `<script>var module = { exports: {} }, exports = module.exports;</script>`
  2. `<script src="vendor/three.cjs"></script>`
  3. `<script>window.THREE = module.exports;</script>`
  4. `<script src="dist/data.js"></script>` (`window.RT_DATA`)
  5. `<script src="dist/app.js"></script>` (`tsc` 단일 출력)
- 금지: ES 모듈 스크립트·importmap·CDN·외부 URL·로컬 서버·`fetch`/XHR 로컬 읽기·사진의 WebGL 텍스처(TextureLoader 포함)(헌법 II, FR-007).
- 사진은 `<img>` 상대 경로로 표시. `CanvasTexture`는 코드 생성 질감에만 쓴다.
- 임의 로그 추가 로드는 `<input type="file">` + `FileReader`로만 한다.

## Data Generation Contract (`viewer/tools/embed.py`, stdlib only)

- 입력: `logs/drunkard-set/` 실표본 + `data/drunkard-set/` + `viewer/testdata/`.
- 출력: `viewer/dist/data.js` — `window.RT_DATA = {...}` 한 문장. 커밋한다.
- 사진 바이너리는 내장하지 않는다. 경로만 싣고 `<img>`가 상대 경로로 읽는다.

## Rendering Contract

- `requestAnimationFrame` 반복 렌더. 1회성 `render()` 페이지는 쓰지 않는다.
- `webglcontextlost`에서 `preventDefault()` 호출, `webglcontextrestored`에서 장면 재구성.
- 평면 = `PlaneGeometry`, 궤적 = `Line`, 발자국 = `Points`, 층 = 그룹 표시 전환.
- 색·서체: Base `#E9DCC0`–`#DCCFAC`, Ink `#2A2118`, Seal Red `#A0322B`(막힘·실패 구간만), 시스템 세리프, 웹폰트 없음. 궤적은 SVG `stroke-dashoffset` 잉크 효과. 미탐험 흐림·탐험 선명.

## Display Exposure Contract (FR-005)

- 표시 가능: 로그 확인 시점의 FR-001 항목만. `answer_submitted.value`는 제출 원문 표시 가능.
- `puzzle.json` 정답은 `puzzle_ended(failed)` 직후 해당 퍼즐만 1회 표시. `failed`가 아닌 퍼즐 정답은 산출물에 넣지 않는다.
- 표시 금지: 다음 장소 지시, 사진 경로·해시.

## Order/Spell Contract (FR-006, 수용만)

- 트리거 이후 붉은 봉인 오버레이 + 먹 잉크 궤적 효과가 5초 이내 끊김 없이 재생.
- `failed`·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.
- 주문 주체·화면 범위는 미결. 주문 연출 착수 시 묻는다.
