# Feature Specification: 갈래2 지도·고스트 뷰어

**Feature Branch**: `002-map-ghost-viewer`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "갈래2(지도, 연출, 뷰어) specify. 갈래1 로그만 읽고 갈래1을 바꾸지 않는다."

**변경 사유 (2026-11-04)**: 문서 충돌 점검 반영. 로그에 없는 표시 데이터의 출처(FR-001), 노출 규칙(FR-005, US2), 검증 표본(FR-008), 궤적 점 개수(US1), 주문 장면 미결(Design Direction), 결정된 스택(Assumptions)을 정리. 입력 원문은 기록으로 유지.
**변경 사유 (2026-11-04)**: 사용자 결정 A~D 반영. 정답 금지 대상은 `puzzle.json`의 `answer` 필드이며 `on_correct`·제출 원문은 표시 허용(A), 파일 선택 로그의 `failed` 정답은 로그+`puzzle.json` 동시 선택 시에만 표시(B), 지도 궤적 `Line`+`Points`·잉크 효과 랜딩 한정(C), Seal Red 끊김·실패 구간 한정·랜딩 예외(D). FR-003·FR-005·FR-008·Design Direction에 반영.
**변경 사유 (2026-11-04)**: 검증 분리·결정 A 후속·용어 통일을 반영. 내장 로그는 `embed.py`가 `reason` 제거 전 원본을 `log.schema.json`으로 검증하고 실패 시 `data.js`를 생성하지 않으며, 브라우저는 내장 로그의 `t` 순서와 마지막 `end`만 검증하고 파일 선택 로그는 브라우저에서 전체 검증하되 `reason`은 표시하지 않는다(차단 1). `next_instruction` 전면 금지를 `puzzle_ended(failed)` 직후 1회 표시 규칙으로 교체하고 `next_object_id` 전면 금지는 유지한다(차단 2). "막힘/stuck" 표현을 "끊김·실패"로 통일한다(권장 6).
**변경 사유 (2026-11-04)**: 파일 선택 로그의 "전체 검증"은 재생 필요 항목 검증으로 대체됐고, 재생 거부 표본은 `embed.py` 검증에서 제외하며, `embed.py`는 표준 라이브러리 + `jsonschema`만 허용한다.
**변경 사유 (2026-11-04)**: 사용자 결정으로 FR-001 허용 항목에 `failed` 퍼즐의 `next_instruction`을 추가한다. 스키마와 로그 형식은 바꾸지 않는다.
**변경 사유 (2026-11-04)**: 지시 1~15 문서 수정 반영. US2 제목을 끊김·실패 지점으로 고치고 수용 시나리오에 next_instruction 표시를 추가한다.
**변경 사유 (2026-11-05)**: 사용자 결정 3건 반영. 로그 표본은 추가 실행 없이 5회로 확정(FR-008 전제 유지), 랜딩 화면 영어 전용(FR-009 예외), 닫는 주문은 별도 화면 없이 결과 박스 꼬리말로 표시(FR-006).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 평면도 위 발자국 확인 (Priority: P1)

창작자가 평면도 위에서 에이전트가 어디를 맴돌았는지 발자국 궤적으로 확인한다. 시작점(`start_cell`)과 이동(`move.value`) 순서가 보인다.

**Why this priority**: 창작자의 핵심 질문("어디서 맴돌았나, 어떤 사물을 못 봤나")에 답하는 최소 기능이다. API 키 없이 저장된 파일만으로 검증 가능하다.

**Independent Test**: `logs/drunkard-set/` 로그 1개로 전체 궤적을 순서대로 재생하고, 궤적 점 개수가 해당 로그의 `move` 이벤트 수 + 1(`start_cell`)과 일치하면 통과.

**Acceptance Scenarios**:

1. **Given** 스키마 통과 로그 1개, **When** 궤적 재생을 요청, **Then** `start_cell`에서 시작해 `move.value` 순서대로 점이 이어진다.
2. **Given** `end(action_limit)`·`end(api_error)`로 끝난 로그, **When** 궤적 재생을 요청, **Then** 끊긴 지점에서 재생이 멈추고 끊김 표시가 보인다.

---

### User Story 2 - 고스트 재생으로 끊김·실패 지점 확인 (Priority: P2)

보고서 독자가 특정 실행을 처음부터 끝까지 재생하며, 각 지점에서 본 것(`view` 사진·`npc_dialogue`), 맞은 답·틀린 답(`puzzle_ended.result`), 화면 전용 반응(`on_wrong`/`on_correct`)을 확인한다.

**Why this priority**: 난이도 보고서의 오답·갈림 판정을 사례로 뒷받침한다. US1 궤적 위에 얹히는 두 번째 층이다.

**Independent Test**: 오라클 로그(`logs/drunkard-set/oracle/r0.json`)를 재생하면 전 퍼즐 `solved_by_dialogue`와 `end(completed)`까지 끊김 없이 보이면 통과.

**Acceptance Scenarios**:

1. **Given** 완료 로그, **When** 처음부터 재생, **Then** `view` 지점마다 해당 사물 사진과 `npc_dialogue`가 나타나고, 퍼즐 종료마다 결과가 표시된다.
2. **Given** 실패(`failed`) 포함 로그, **When** 해당 퍼즐 구간 재생, **Then** `puzzle_ended(failed)` 직후 `puzzle.json`의 정답과 `next_instruction`이 1회 표시된다(`null`이면 다음 장소 문구 없음).

---

### User Story 3 - 층 전환 (Priority: P3)

2개 이상 층 로그에서 층별 평면도를 오가며 궤적을 본다. 단층 로그에서는 층 선택이 나타나지 않는다.

**Why this priority**: 다층 공간이 생기기 전까지 필요 없다. 단층에서 추가 UI 없이 동작해야 한다.

**Independent Test**: 2층 표본 로그 재생 시 층별 궤적이 각 층 평면에 표시되고, 단층 로그에서는 층 UI가 없으면 통과.

**Acceptance Scenarios**:

1. **Given** 다층 공간 로그, **When** 층을 전환, **Then** 해당 층의 이동·관측만 보인다.

---

### Edge Cases

- 로그 `t`가 1씩 증가하지 않거나 마지막이 `end`가 아니면 재생을 거부하고 이유를 보인다.
- 사진 파일이 없어도 궤적·대화 재생은 된다. 사진 자리는 빈틀로 표시한다.
- `action_limit`·`api_error` 로그도 끝까지 재생하되, 완주 아님을 표시한다.
- 갈래1 로그 형식이 바뀌면 뷰어는 구 로그를 그대로 읽는다. 뷰어 때문에 엔진·로그 형식을 바꾸지 않는다(TRD §9).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 뷰어는 실행 기록을 갈래1 로그(`logs/<set>/`)에서만 읽는다. 표시용 정적 데이터(평면도, 사물 사진, `start_cell`, 대화문, NPC 이름·이미지, `on_wrong`/`on_correct`, `failed` 퍼즐의 정답, `failed` 퍼즐의 `next_instruction`)는 `data/<set>/`에서 읽기 전용으로 가져온다. 엔진·로그·데이터 형식 변경을 요구하지 않는다.
- **FR-002**: 사용자는 실행별 발자국 궤적(`start_cell` 시작, `move.value` 순서)을 볼 수 있다.
- **FR-003**: 사용자는 `view` 지점의 사물 사진과 `npc_dialogue`, `on_wrong`/`on_correct` 반응을 순서대로 볼 수 있다. `hint_revealed`는 레벨만 표시하고 본문은 표시하지 않는다.
- **FR-004**: 사용자는 퍼즐별 종료 결과(`puzzle_ended.result`)를 궤적 위에서 확인할 수 있다.
- **FR-005**: TRD §4 노출 금지는 에이전트 관측 계약이며 뷰어 때문에 바꾸지 않는다. 뷰어 화면은 로그 이벤트로 확인된 시점에 FR-001 항목만 표시한다. 정답 금지 대상은 `puzzle.json`의 `answer` 필드다. `answer`는 `puzzle_ended(failed)` 직후 해당 퍼즐만 1회 표시하고, 불러온 로그에서 `failed`가 아닌 퍼즐의 정답은 뷰어 산출물에 넣지 않는다. `on_correct`는 맞힌 제출 뒤에 표시하며, 대사에 포함된 다음 장소와 정답 문자열도 그대로 표시한다. `answer_submitted.value`는 제출 원문 표시를 허용한다. `reason`은 표시하지 않고 `data.js`에서 제외한다. `next_instruction`은 `puzzle_ended(failed)` 직후 해당 퍼즐의 `answer`와 함께 1회 표시한다. 맞힌 퍼즐에는 표시하지 않으며, 맞힌 퍼즐의 다음 장소는 `on_correct`로 전달한다. 값이 `null`이면(마지막 퍼즐) 다음 장소 문구를 표시하지 않는다. `data.js`에는 해당 로그에서 `failed`인 퍼즐의 `next_instruction`만 넣는다(`answer`와 같은 로그별 규칙). 파일 선택 로그는 `puzzle.json`을 함께 선택했을 때만 `failed` 정답·`next_instruction`을 표시하고, 없으면 "정답 데이터 없음"만 표시하고 다음 장소 문구는 표시하지 않는다. `next_object_id`는 전면 금지다(종료 전후 불문). 사진 경로는 화면 금지, 해시(`sha256`)는 산출물 금지다.
- **FR-006**: 스코프는 지도+고스트+층 전환에 주문·잉크 연출을 포함한다. 주문 연출은 기본 동작 완성 후 필수(동영상용). 주문·잉크의 수용 시나리오는 TRD 계약이 없어 plan 단계에서 구체화한다. 여는 주문은 랜딩 화면에, 닫는 주문은 `end(completed)` 재생 완료 시 결과 박스 꼬리말 한 줄에 표시한다(PRD OPEN-4 보완 2026-11-05). 닫는 주문은 완주 표시를 대체하지 않고 그 아래에 덧붙인다.
- **FR-007**: 3D는 three.js, 언어는 TS로 한다. 번들러 없이 `tsc` 단일 출력만 사용한다. three.js 벤더 파일을 동봉하고 CDN·외부 URL·로컬 서버 없이 `file://`로 연 페이지에서 동작한다. ES 모듈 스크립트·importmap, `fetch`·XHR 로컬 파일 읽기, 로컬 사진의 WebGL 텍스처에 의존하지 않으며(헌법 원칙 II), 구체 로딩 방식은 plan에서 정한다. Pages 배포 방식(컴파일 JS 커밋 vs Action 빌드)은 plan에서 결정. 서버 방식은 헌법 개정 없이 선택하지 않는다.
- **FR-008**: 입력 로그는 현 5회 미달 표본(`logs/drunkard-set/`)으로 진행한다. 발자국·재생 검증이 제한적임을 전제한다. 실제 로그에 없는 실패·끊김·다층·다중 이동 경우는 `log.schema.json`을 통과하는 뷰어 테스트용 표본으로 검증하고, 표본을 `logs/<set>/`에 섞지 않는다. 재생 거부용(`t` 불연속·마지막 비-`end`) 표본은 스키마 표본 요건에서 제외한다. 표본 위치와 작성 방식은 plan에서 정한다.
- **FR-009**: 뷰어 UI 기본 언어는 한국어다. 시간 여유 시 영어 전체 번역을 추가 작업으로 한다. 생성 보고서 구조의 영어화는 생성 코드 변경이 필요하므로 plan 이후에 판단한다. 예외(2026-11-05): 랜딩 화면은 영어 전용이고, 주문 문구 2종은 번역하지 않고 영어 원문으로 표시한다.

### Key Entities

- **재생 로그**: `log.schema.json` 통과 로그 1개. 궤적·대화 시점·결과의 원천. 대화문과 시작 칸은 `puzzle.json`에 있다.
- **발자국**: `move.value` 순서열 + `start_cell`. 지도 위 궤적.
- **고스트**: 1회 실행의 시간순 재생. 관측·반응·종료를 순서대로 보여준다.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 창작자가 로그 1개를 열어 전체 궤적을 3분 안에 확인한다.
- **SC-002**: 오라클 로그 재생이 끊김 없이 끝까지 보인다.
- **SC-003**: 미달·끊김·실패 로그도 끝까지 재생되고, 완주가 아님을 알 수 있다.
- **SC-004**: 갈래1 테스트 게이트(`python -m unittest discover tests -v`)가 뷰어 작업 후에도 통과한다.

## Design Direction

- Base `#E9DCC0`–`#DCCFAC` parchment. No white background.
- Ink `#2A2118` for room outlines and text.
- Seal red `#A0322B` only for interrupted·failed (끊김·실패) segments: `puzzle_ended(failed)`, `end(action_limit)`, `end(api_error)`. Landing screen is the only exception (red seal overlay). 결정 D (2026-11-04).
- Unexplored rooms blurred and desaturated. Explored rooms sharp.
- System serif typeface. No webfonts (offline demo priority).
- Map trails drawn as `Line` + `Points`. SVG stroke-dashoffset ink effect only on the landing screen. 결정 C (2026-11-04).
- Order scene: separate landing intro screen before entering the program. The order is framed as if cast by the person running the program. No in-fiction caster. Red subtitle with edge vignette on the landing screen. 변경 사유(2026-11-04): 사용자 결정으로 주체·범위 확정. 기존 draft(별도 화면 없음·미결)를 교체. PRD OPEN-4 해소.

## Three.js Beginner Notes

- three.js는 브라우저 3D 라이브러리다. 무대·배우·카메라 3요소로 이해한다.
- Scene(장면): 무대. 모든 물체를 올리는 공간.
- Camera(카메라): 관객 시점. 지도 위를 오르내리며 줌·팬한다.
- Renderer(렌더러): 무대를 화면에 그리는 붓. `WebGLRenderer` 사용.
- Mesh(물체): 모양(Geometry) + 재질(Material) 조합. 평면 지도는 얇은 상자다.
- 우리 매핑: 평면 = `PlaneGeometry`, 궤적 = `Line`, 발자국 = `Points`, 층 = 그룹 표시 전환.
- 재질은 코드로 만든다. 이미지 파일 없음. 양피지 질감은 `CanvasTexture`로 그림.
- 조명 1개. 그림자는 물체가 닿는 곳만.
- 실행 방식: TS 작성 → `tsc` 1회 → JS 1개. 번들러 없음.
- 브라우저 연결: `three`는 동봉 벤더 파일로 제공한다. ES 모듈·importmap은 쓰지 않고, 구체 로딩 방식은 plan에서 정한다. CDN 없음.
- 버전 고정: `three`(벤더 파일), `typescript`, `@types/three` 모두 정확한 버전. 어긋나면 타입과 동작이 갈림.
- 오프라인 보장: 외부 URL 0개. `file://`로 열어도 동작한다.
- 변경 사유(2026-11-04): FR-007과 이 절의 연결·버전 문구를 헌법 v1.2.0 원칙 II에 맞춤. importmap은 서버 없는 `file://` 실행과 양립하기 어렵다.

## Assumptions

- 갈래1 로그 형식은 바뀌지 않는다(TRD §9).
- 공간 평면도 데이터는 `space.json`(층·방·칸 범위)에서 가져온다.
- 사람 플레이 브라우저 공개는 범위 밖이다(PRD Non-goals).
- 주문·잉크 연출은 이번 범위에 포함된다. 마우스 평면도 빌더, SAM 제안, `prediction.json`, `revise`는 여유 항목으로 범위 밖이다(TRD §9).
- 현 입력 로그는 5회 미달 표본이다(`reports/drunkard-set/report.md`에 명기).
- 프론트 스택은 three.js + TS로 결정됐다(FR-007). 구체 로딩 방식과 배포 방식은 plan에서 결정한다.
