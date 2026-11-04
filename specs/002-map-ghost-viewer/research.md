# Research: 갈래2 지도·고스트 뷰어

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Notes**: [implementation-notes.md](implementation-notes.md)

**변경 사유 (2026-11-04)**: 결정 C·D 표현 정리와 배포 묶음 일치를 반영. R-5 배포 묶음을 T029와 일치시키고(`index.html`·`data/<set>/` 사진 포함)(권장 7), R-8의 "막힘/stuck" 표현을 "끊김·실패"로 통일하고 Seal Red 적용 대상을 `puzzle_ended(failed)`·`end(action_limit)`·`end(api_error)` 세 가지로 한정한다(권장 6).
**변경 사유 (2026-11-04)**: R-2 생성 스크립트 규칙을 반영. `embed.py`는 표준 라이브러리 + `jsonschema`만 허용하고(새 패키지 설치 없음) `.venv/bin/python`으로 실행한다(항목 3).

## R-1: 뷰어 폴더 이름

- **Decision**: `viewer/`를 쓴다.
- **Rationale**: `implementation-notes.md` §2~§3의 시험 구성이 전부 `viewer/tsconfig.json`, `viewer/index.html`, `viewer/vendor/`, `viewer/src/`, `viewer/dist/app.js` 경로로 기록됐다. 새 이름을 지으면 시험 근거·시작 지시문·환경 준비 절차의 경로를 전부 고쳐야 한다. TRD §2도 "별도 폴더, 이름은 002 plan에서 확정"이라 위임했으므로 여기서 확정한다.
- **Alternatives considered**: 별도 이름 — 이득 없이 문서 churn만 발생해 기각.

## R-2: 로그·데이터 읽기 방식 (FR-001, 헌법 II)

- **Decision**: 하이브리드. (a) 기본 표본은 빌드 시 생성한 `viewer/dist/data.js`를 일반 `<script src>`로 로드해 `window.RT_DATA`로 읽는다. 생성 스크립트 `viewer/tools/embed.py`는 표준 라이브러리 + `jsonschema`만 허용하고(새 패키지 설치 없음) `.venv/bin/python`으로 실행하며, tasks에서 구현한다. (b) 임의 로그는 `<input type="file">` + `FileReader`로 추가 로드한다. `fetch`·XHR 로컬 파일 읽기는 쓰지 않는다.
- **Rationale**: Chrome 146 `file://` 시험(`implementation-notes.md` §1)에서 `fetch` 로컬 JSON 읽기는 CORS 차단, `<img>` 표시와 일반 `<script src>`는 동작이 확인됐다. 생성 JS는 열자마자 오라클 재생이 보여 데모·심사(PRD SC-4)에 유리하고, 파일 선택은 5회 미달 표본 밖의 임의 로그(US1 독립 테스트)에 필요하다. 둘 다 ES 모듈·importmap 없이 동작한다.
- **Alternatives considered**: 파일 선택만 — 매번 여러 파일(로그+공간+퍼즐)을 골라야 해 US1 3분 확인(SC-001)에 불리해 기각. 생성 JS만 — 임의 로그 확인이 막혀 US1 독립 테스트가 어려워 기각. `fetch` — 시험에서 차단이 확인돼 기각.

## R-3: three.js 로딩 방식 (FR-007)

- **Decision**: `viewer/vendor/three.cjs`(고정 `three 0.185.0`)를 `implementation-notes.md` §2 순서 그대로 일반 스크립트로 로드한다. `three`·`typescript 5.9.3`·`@types/three 0.185.0`은 정확한 버전으로 고정한다. ES 모듈 스크립트·importmap·CDN·외부 URL을 쓰지 않는다.
- **Rationale**: 시험에서 `<script type="module">` + importmap은 CORS 차단, 일반 `<script src>` + `three.cjs`는 동작이 확인됐다. three 0.186 이상은 `three.cjs`가 631바이트 빈 파일이라 `file://`에서 못 쓴다. TS 7.0.2는 `outFile` + `module: none`이 제거돼 단일 출력이 실패한다. 버전 고정은 FR-007·헌법 II의 요구다.
- **Alternatives considered**: importmap·CDN·로컬 서버 — `file://` 오프라인(FR-007)과 충돌해 기각. three 0.186+ — 빈 `three.cjs` 문제로 기각.

## R-4: 렌더링 루프와 컨텍스트 끊김

- **Decision**: `requestAnimationFrame` 반복 렌더링 + `webglcontextlost`에서 `preventDefault()` 호출 + `webglcontextrestored`에서 장면 재구성. 1회성 `render()` 호출 페이지는 쓰지 않는다.
- **Rationale**: 시험에서 1회 호출 페이지는 5번 중 1번 빈 화면, 반복 페이지는 5번 모두 정상이었다. 재시험에서 반복 페이지도 24번 중 2번 끊겼고, `preventDefault()` 호출 1건은 복구·미호출 1건은 미복구였다. 반복만으로 부족하므로 복구 경로를 포함한 세트다. three.js 자체 복구 범위는 시험하지 않았으므로 plan은 재구성까지만 계약한다.
- **Alternatives considered**: 1회 렌더 — 끊김 실측으로 기각. 반복만 — 재시험 끊김 2건으로 부족해 기각.

## R-5: 배포 방식 (FR-007 위임 결정)

- **Decision**: 컴파일 JS 커밋. 배포 묶음은 `viewer/index.html` + `viewer/dist/app.js` + `viewer/dist/data.js` + `viewer/vendor/three.cjs` + `data/<set>/` 사진(T029)이며 이를 git에 넣고, `viewer/node_modules`와 `.shots`는 커밋하지 않는다. GitHub Action 빌드는 쓰지 않는다.
- **Rationale**: PRD SC-4(API 키 없이 저장된 파일로 결과 재열람)와 `file://` 오프라인 요구에 가장 단순히 부합한다. Action 빌드는 추가 인프라·마감 리스크만 늘린다. TS 원본도 함께 커밋해 재현 가능성을 유지한다.
- **Alternatives considered**: Action 빌드 — 심사·데모 환경에서 빌드 대기·실패 경로가 늘어 기각. 서버 방식 — 헌법 개정 없이는 선택 불가해 제외.

## R-6: 주문·잉크 수용 시나리오 (FR-006 위임 결정)

- **Decision**: 수용 시나리오는 동작·타이밍 기준으로 정한다. 프로그램 진입 전 랜딩 인트로 화면에서 주문문 + 붉은 봉인 오버레이와 먹 잉크 궤적 효과가 5초 이내에 끊김 없이 재생되면 통과. 주문 주체·화면 범위는 2026-11-04 사용자 결정으로 확정: 주체 = 프로그램을 실행하는 실행자 본인이 외우는 것처럼 보임(극 중 시전 인물 없음), 범위 = 진입 전 랜딩 화면(별도 화면). 진입 방식(버튼 vs 자동)은 Slice 4 착수 시 정한다.
- **Rationale**: TRD §9·spec FR-006이 수용 시나리오만 plan에 위임했고, 주체·범위는 2026-11-04 사용자 결정으로 확정했다.
- **Alternatives considered**: 해당 없음. 사용자 결정(2026-11-04)으로 주체·범위 확정.

## R-7: 검증용 표본 위치 (FR-008)

- **Decision**: 실제 로그에 없는 실패·끊김·다층·다중 이동 표본은 `log.schema.json`을 통과하는 형태로 `viewer/testdata/`에 두고, `logs/<set>/`에는 섞지 않는다. 생성 스크립트는 `logs/drunkard-set/` 실표본과 `viewer/testdata/`를 합쳐 `dist/data.js`를 만든다.
- **Rationale**: FR-008이 "표본을 `logs/<set>/`에 섞지 않는다, 위치·작성 방식은 plan에서 정한다"고 위임했다. 갈래1 집계 오염을 막으면서 뷰어 테스트는 가능해진다.
- **Alternatives considered**: `logs/` 혼합 — 보고서 집계 오염 위험으로 기각.

## R-8: 디자인 토큰 적용

- **Decision**: spec Design Direction 토큰을 그대로 쓴다. Base `#E9DCC0`–`#DCCFAC`, Ink `#2A2118`, Seal Red `#A0322B`(끊김·실패 구간만 — `puzzle_ended(failed)`·`end(action_limit)`·`end(api_error)`, 랜딩 화면 예외), 시스템 세리프, 웹폰트 없음, 지도 궤적 `Line`+`Points`, SVG `stroke-dashoffset` 먹 궤적은 랜딩 화면에만(라이브러리 없음), 미탐험 흐림·탐험 선명, 양피지 질감은 코드 생성 `CanvasTexture`.
- **Rationale**: spec이 확정했고 오프라인(외부 폰트·이미지 없음) 요구와 일치한다.
- **Alternatives considered**: 없음. spec 확정 사항이다.
