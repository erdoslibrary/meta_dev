# Contracts: 뷰어 입출력·로딩·렌더링

**Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

**변경 사유 (2026-11-04)**: 사용자 결정 A~D 반영. 정답 금지 대상 `answer` 필드 한정·`on_correct`/제출 원문 허용·`reason` 제외(A), 파일 선택 로그 `failed` 정답 동시 선택 조건(B), 지도 궤적 `Line`+`Points`·잉크 효과 랜딩 한정(C), Seal Red 끊김·실패 한정·랜딩 예외(D). Rendering·Display Exposure 계약 수정.
**변경 사유 (2026-11-04)**: 검증 분리·결정 A 후속·용어 통일을 반영. `embed.py`는 `reason` 제거 전 원본을 `log.schema.json`으로 검증하고 실패 시 `data.js`를 생성하지 않으며, 브라우저는 내장 로그의 `t` 순서와 마지막 `end`만 검증하고 파일 선택 로그는 전체 검증하되 `reason`은 표시하지 않는다(차단 1). `next_instruction` 전면 금지를 `failed` 직후 1회 표시로 교체하고 `next_object_id` 전면 금지는 유지한다(차단 2). T036 범위를 스키마 통과 요구 로그 표본으로 한정한다(차단 3). `puzzle.json` 파일 입력을 명시한다(차단 5). "막힘/stuck"을 "끊김·실패"로 통일하고(권장 6), Data Generation 절에 허용·제외 필드를 명시한다(권장 8).
**변경 사유 (2026-11-04)**: 검증 규칙 3건을 반영. 재생 거부 표본은 `embed.py` 검증 게이트에서 제외하고 `data.js`에 그대로 포함한다(항목 1). 파일 선택 "전체 검증"을 재생 필요 항목 범위로 고친다(항목 2). `embed.py`는 표준 라이브러리 + `jsonschema`만 허용하고 `.venv/bin/python`으로 실행한다(항목 3).
**변경 사유 (2026-11-04)**: 재생 거부 표본은 결함 유지·`data.js` 규칙 동일 적용으로 고치고(차단 3), 표본 구조를 바로 아래 `*.json`·`refusal/`·`sets/<puzzle_set_id>/`로 정한다(차단 4).
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. 세트 탐색 규칙(sets→data, 중복·없음이면 미생성), 허용 필드(퍼즐 7종·대화문 text만, contains_hint 제외), Seal Red 결과 줄 한정을 명시한다.
**변경 사유 (2026-11-04)**: 결정 E 페이로드 분리를 반영. 세트 공용 `puzzle`에는 `answer`·`next_instruction`을 넣지 않고, 로그별 정답은 `reveals/<로그 키>`에 그 로그에서 `failed`인 퍼즐만 둔다(`next_instruction`이 `null`이면 생략). `sets/<id>/reveals`와 `sample_sets/<id>/reveals` 모두 같은 규칙을 따른다.
**변경 사유 (2026-11-05)**: PRD OPEN-4 보완 반영. Rendering Contract에 주문 문구 배치(랜딩 영어 전용·닫는 주문 결과 박스 꼬리말)를 추가한다.
**변경 사유 (2026-11-04)**: 결정 E 키 규칙을 통일. 정답은 로그가 연결된 세트(세트 조회 결과 `sets/<id>` 또는 `sample_sets/<id>`)의 `reveals`에 둔다. 키는 실로그 상대 경로(`r01`, `oracle/r0`)·표본 로그 `testdata/<이름>`·재생 거부 표본 `refusal/<이름>`, 퍼즐 번호 키는 문자열(`"1"`)이다.
**변경 사유 (2026-11-05)**: 뷰어 영어 기본(FR-009) 반영. 인용 표시 문구는 `?lang=ko` 기준임을 명시한다.
**변경 사유 (2026-11-05)**: "실패 로그" 표현이 FR-006(`end(completed)` 기준)과 다르게 읽힐 수 있어 끊김 로그로 한정한다. 동작 변경 없음.

## Input Contract (읽기 전용, 형식 변경 없음)

- 로그: `logs/<set>/`의 `log.schema.json` 통과 파일 1개. `run_id`, `events[]` 사용.
- 정적 데이터: `data/<set>/`의 `space.json`, `puzzle.json`, `npc.json`, 사진 파일. 엔진·로그·데이터 형식 변경을 요구하지 않는다(FR-001).
- 테스트 표본: `viewer/testdata/` 바로 아래 `*.json`의 스키마 통과 요구 로그 표본(`log.schema.json` 통과, `persona`·`space`·`npc` `$ref` 해결). `logs/<set>/`에 섞지 않는다(FR-008). `refusal/`(재생 거부 표본, `t` 불연속·마지막 비-`end`)·`sets/`(표본 세트 정적 데이터)는 스키마 표본 요건에서 제외한다. 재생 거부 표본은 `refusal/` 아래에, 표본 세트 정적 데이터는 `sets/<puzzle_set_id>/` 아래에 두고 로그의 `puzzle_set_id`로 연결한다. 재생 거부 표본은 V-2에서 재생 거부와 이유 표시만 확인한다.
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
- 임의 로그 추가 로드는 `<input type="file">` + `FileReader`로만 한다. `puzzle.json` 파일 입력도 `<input type="file">` + `FileReader`로 받는다(결정 B, T009). 파일 선택 로그는 브라우저에서 재생 필요 항목만 검증(로그 최상위 필수 필드, 이벤트 종류와 종류별 필수 필드, 값 타입과 enum, 칸·사물 표기 형식, `t` 순서, 마지막 `end`)하되 `reason`은 표시하지 않는다. 재생과 무관한 스키마 세부 규칙(`persona` 내용 규칙 등)은 검사하지 않는다. 내장 로그(`window.RT_DATA`)는 브라우저에서 `t` 순서와 마지막 `end`만 검증한다(`embed.py`가 재생 거부 표본 제외 원본 전체 스키마 검증을 마쳤으므로).

## Data Generation Contract (`viewer/tools/embed.py`, stdlib + `jsonschema` only)

- 입력: `logs/drunkard-set/` 실표본 + `data/drunkard-set/` + `viewer/testdata/`(바로 아래 `*.json`, `refusal/`, `sets/<puzzle_set_id>/`). 각 로그의 `puzzle_set_id`는 `sets/<id>`에서 먼저 찾고 없으면 `data/<id>`에서 찾으며, 같은 ID가 둘 다 있거나 어디에도 없으면 `data.js`를 생성하지 않는다. 실행은 `.venv/bin/python`으로만 하며(bare `python`/`python3` 금지), 새 패키지를 설치하지 않고(`referencing`은 `jsonschema` 의존 패키지) 환경 문제로 실패하면 원문과 함께 보고한다.
- 검증: 내장 전 스키마 통과 요구 로그 원본(`reason` 제거 전)을 `log.schema.json`으로 검증하고, 실패 시 `data.js`를 생성하지 않는다. `answer_submitted`의 `reason`은 스키마 필수 필드이므로 제거 전 원본으로 검증한다. 재생 거부 표본(`t` 불연속·마지막 비-`end`)은 이 검증 게이트에서 제외하되, `t` 불연속과 마지막 비-`end` 결함은 유지한 채 `reason` 제거를 포함한 `data.js` 허용·제외 규칙은 다른 로그와 똑같이 적용해 포함한다(브라우저 재생 거부·이유 표시는 V-2에서 확인).
- 출력: `viewer/dist/data.js` — `window.RT_DATA = {...}` 한 문장. 커밋한다.
- 사진 바이너리는 내장하지 않는다. 경로만 싣고 `<img>`가 상대 경로로 읽는다.
- 허용: 로그 헤더 `run_id`·`persona`·`puzzle_set_id`·`model`·`seed`(선택)·`events[]`, 공간 기하/방/사물, 퍼즐 `number`·`start_instruction`·`question`·`object_id`·`image.path`·`answer_letter_count`·`max_attempts`·대화문(`text`만)·`on_wrong`·`on_correct`·`start_cell`, `reveals/<로그 키> = {퍼즐 number 문자열: {answer, next_instruction}}`(로그가 연결된 세트의 `reveals`에, 그 로그에서 `failed`인 퍼즐만, `next_instruction`이 `null`이면 생략), NPC 이름·이미지, 사진 경로, 로그 이벤트(`reason` 제외).
- 분리(결정 E): 세트 공용 `puzzle`에는 `answer`·`next_instruction`을 넣지 않는다. 정답은 로그가 연결된 세트(세트 조회 결과 `sets/<id>` 또는 `sample_sets/<id>`)의 `reveals`에만 두며, `sets/<id>/reveals`와 `sample_sets/<id>/reveals` 모두 같은 규칙을 따른다. 로그 키는 실로그 상대 경로(`r01`, `oracle/r0`), 표본 로그 `testdata/<이름>`, 재생 거부 표본 `refusal/<이름>`이다. 퍼즐 번호 키는 문자열(`"1"`)이다.
- 제외: `sha256`, 힌트(미공개·본문), `next_object_id`(전면 금지), `failed`가 아닌 퍼즐의 `answer`·`next_instruction`, `tone`, `reason`, 대화문 `contains_hint`.

## Rendering Contract

- `requestAnimationFrame` 반복 렌더. 1회성 `render()` 페이지는 쓰지 않는다.
- `webglcontextlost`에서 `preventDefault()` 호출, `webglcontextrestored`에서 장면 재구성.
- 평면 = `PlaneGeometry`, 지도 궤적 = `Line`, 발자국 = `Points`, 층 = 그룹 표시 전환.
- 주문 문구: 여는 주문은 랜딩 화면에만, 닫는 주문은 `end(completed)` 결과 박스 꼬리말 한 줄에만 둔다. 완주 표시(`완주`)는 유지하고 그 아래에 덧붙인다. 끊김 로그(`end(action_limit)`·`end(api_error)`)에는 닫는 주문을 쓰지 않는다. 퍼즐이 `failed`여도 실행이 `end(completed)`로 끝났으면 닫는 주문을 표시한다(FR-006). 랜딩 화면은 영어 전용이다. 완주 표시 문구 `완주`는 `?lang=ko` 기준이며 영어 화면은 i18n 사전의 대응 문구를 쓴다.
- 색·서체: Base `#E9DCC0`–`#DCCFAC`, Ink `#2A2118`, Seal Red `#A0322B`(끊김·실패 구간만 — `puzzle_ended(failed)`·`end(action_limit)`·`end(api_error)`, 랜딩 화면 예외; 실패 시 붉은색은 `퍼즐 N 결과: failed` 줄에 쓰고 `정답: …` 문구는 기본 먹색으로 표시), 시스템 세리프, 웹폰트 없음. SVG `stroke-dashoffset` 잉크 효과는 랜딩 화면에만 쓴다. 미탐험 흐림·탐험 선명.

## Display Exposure Contract (FR-005, 결정 A/B)

- 표시 가능: 로그 확인 시점의 FR-001 항목만. `on_correct`는 맞힌 제출 뒤에 표시하며 대사에 포함된 다음 장소와 정답 문자열도 그대로 표시한다. `answer_submitted.value`는 제출 원문 표시를 허용한다.
- 정답 금지 대상은 `puzzle.json`의 `answer` 필드다. `puzzle_ended(failed)` 직후 해당 퍼즐만 1회 표시. `failed`가 아닌 퍼즐 정답은 산출물에 넣지 않는다.
- `next_instruction`은 `puzzle_ended(failed)` 직후 해당 퍼즐의 `answer`와 함께 1회 표시한다. 맞힌 퍼즐에는 표시하지 않으며, 맞힌 퍼즐의 다음 장소는 `on_correct`로 전달한다. 값이 `null`이면(마지막 퍼즐) 다음 장소 문구를 표시하지 않는다.
- 파일 선택 로그의 `failed` 정답·`next_instruction`은 로그와 `puzzle.json`을 함께 선택했을 때만 표시. 없으면 "정답 데이터 없음"만 표시하고 다음 장소 문구는 표시하지 않는다. "정답 데이터 없음"은 `?lang=ko` 기준 문구다.
- `hint_revealed`는 레벨만 표시(본문 제외).
- 표시 금지: `next_object_id`(전면 금지), 사진 경로(화면), 해시(산출물), `reason`(표시·`data.js` 제외), 미공개 힌트.

## Order/Spell Contract (FR-006, 수용만)

- 프로그램 진입 전 랜딩 화면에서 주문문 + 붉은 봉인 오버레이 + 먹 잉크 궤적 효과가 5초 이내 끊김 없이 재생. 주문은 실행자 본인이 외우는 것처럼 연출하고, 극 중 시전 인물은 두지 않는다.
- `failed`·끊김 로그에서도 완주 아님 표시와 함께 끝까지 재생.
- 주체·범위(2026-11-04 확정): 실행자 본인인 듯한 연출 + 진입 전 랜딩 화면. 진입 방식(버튼/자동)은 Slice 4 착수 시 정한다.
