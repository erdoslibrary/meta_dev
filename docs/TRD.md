# TRD — Real-to-Sim 공간 퍼즐 스튜디오 (갈래 1 우선)

- 상태: 재정비 v3 자립형. 이 문서가 HOW 기준이다. 구 `spec.md`/`design.md`/`acceptance.md`는 삭제됨.
- 우선순위: 갈래 1(엔진, 검증, 로그, 보고서) 먼저. 갈래 2(지도, 연출, 뷰어)는 후순위 절로 분리.
- 데이터 형식의 기준은 `docs/schemas/*.schema.json`이다. 계약 문장은 이 문서 §3~§10이 기준이고, §11은 미결 인계다.
- 변경 사유(2026-11-04): 문서 충돌 점검 반영. §1·§7 뷰어 입력 범위를 002 spec FR-001과 맞춤. §2·§9 결정된 스택과 실제 데이터 폴더에 맞춤. §2 테스트 절 번호 정정. §6 `httpx` 설치 상태 명시. 기준 범위를 AGENTS.md·헌법의 §3~§10과 맞춤.

## 1. 아키텍처

갈래 1을 먼저 완성한다. 갈래 2는 실행 기록을 로그에서만 읽고 표시용 정적 데이터는 `data/<set>/`에서 읽기 전용으로 가져오므로, 나중에 합류해도 갈래 1을 바꾸지 않는다.

흐름:

사진, 평면도 → 공간 빌더 → `space.json` →
저작 퍼즐 옮기기 → `puzzle.json` → 검증기 → 재연 보고서 →
오라클 실행 → 페르소나 생성기 → 에이전트 실행기 ↔ 게임 엔진 →
로그 저장소(`logs/`) → 보고서 생성기(`report.md`, `report.json`)

외부 의존:

- Muse Spark API: 에이전트 행동, 보고서 `reason` 분석, 사물 이름 제안, 퍼즐 수정안과 초안.
- Files API: 퍼즐 그림 업로드. `sha256` 캐시로 재사용.
- Modal 위 SAM 3.1: 사진에서 사물 박스 추출. 여유 항목. 없어도 게임과 보고서는 돈다.
- 실패 처리: 모델 실패는 수치 보고서 유지 + 빠진 분석 표시. 상세는 §6을 따른다.

## 2. 폴더 구조

엔진과 모델 클라이언트는 `realtosim` 패키지에 둔다.
저장소 루트에서 `from realtosim import game_engine`으로 가져오고
`python -m realtosim.<모듈>`로 실행한다.

- `realtosim/game_engine.py`: 순수 상태 머신. §3.
- `realtosim/model_api.py`: Muse Spark 호출만. §6.1.
- `realtosim/settings.py`: `model()`, `sam_model()`. 환경 변수 읽기.
- `realtosim/personas.py`: 페르소나 생성. §7.
- `realtosim/run_agents.py`: 실행기. 시스템 프롬프트와 이미지 입력 포함.
- `realtosim/oracle.py`: 정답 플레이어.
- `realtosim/validate.py`: 스키마와 재연 규칙 검사.
- `realtosim/report.py`: 보고서 생성.
- `realtosim/revise.py`: 여유 항목.
- `realtosim/space_builder.py`: 여유 항목.
- `data/<set>/`: `space.json`, `puzzle.json`, `npc.json`, `baseline.json`, `prediction.json`(여유), `puzzles/`, `npcs/`, `photos/`.
- `logs/<set>/`: `r01.json` 등. 오라클은 `logs/<set>/oracle/r0.json`.
- `reports/<set>/`: `replica.md`, `report.md`, `report.json`.
- `workspace/cache/files.json`: sha256 → file_id. git 제외.
- `tests/`: 스키마 테스트 + §10 테스트.
- 갈래 2 뷰어: `realtosim/` 밖 별도 폴더. 이름은 002 plan에서 확정. 기술은 §9.

규칙:

- `<set>`은 `puzzle_set_id`와 같다.
- `logs/`와 `reports/`는 git에 넣는다. API 키 없이도 보고서와 고스트를 보기 위해서다.
- 오라클 로그는 `run_id: "r0"`, `model: "oracle"`이다.
- 공간 빌더 없이 진행할 때는 `space.json`을 손으로 쓴다.

## 3. 게임 엔진 계약

이 절이 기준이다.

- 엔진은 순수 상태 머신이다. 모델, 파일, 네트워크 접근 없음. 무작위성 없음.
- 호출 1번 = `submit` 1번 = 행동 1회다.
- 에이전트는 한 실행 안의 관측과 자기 출력을 텍스트로 모두 기억한다. 실행 사이에는 공유 없음.
- 이미지는 현재 퍼즐 그림과 방금 `view`한 사물 사진만 마지막 메시지에 붙인다.

함수:

- `new_game(space, puzzle_set, persona, *, run_id, model, seed=None, max_actions=50)` → `Game`. `GameSetupError` 가능.
- `brief(game)` → 실행 중 변하지 않는 공간 정보.
- `observe(game)` → `{"observation": dict, "images": [...]}`. `GameStateError` 가능.
- `submit(game, raw_output)` → `{"events": [...], "over": bool, "outcome": str|null}`. 거절은 예외가 아니라 `rejected` 이벤트.
- `abort(game)` → `end(api_error)`만 남긴다. 행동 수 증가 없음.
- `to_log(game)` → `log.schema.json` 만족 dict. 끝난 게임에만 호출.

핵심 처리 순서:

- `new_game`: 모든 사물 `state`를 `locked`로 둔다. 입력 파일 값 무시. 현재 퍼즐 1번, 행동 수 0, 위치 `start_cell`.
- `submit`: 행동 수 +1(거절 포함). §4.1 순서로 검사. 실패면 `rejected`. 성공이면 `move`/`view`/`answer` 적용. 정답이면 `puzzle_ended`. 오답이면 오답 수 +1, 조건 맞으면 `hint_revealed`, 5회면 `puzzle_ended(failed)` 후 다음 퍼즐. 마지막 퍼즐 종료면 `end(completed)`, 상한이면 `end(action_limit)`.
- 마지막 행동으로 완주했으면 상한에 닿아도 `completed`다.
- `to_log`: `run_id`, `persona`, `puzzle_set_id`, `model`, `events` 담기. `seed`는 있을 때만.

## 4. 관측과 출력 계약

이 절이 기준이다.

관측은 `json.dumps(값, ensure_ascii=False)` 직렬화해 텍스트로 보낸다.

- `brief`: `floors`, `cell_prefix_required`, `rooms`, `objects(id,label,cells,description)`만. 위치 드러나는 필드 없음.
- `observe`: `position`, `opened_object_ids`, `instruction`, `puzzle`, `last_result`. 이미지는 실행기만 읽고 모델에는 파일명으로 보내지 않는다.
- 노출 금지: `next_object_id`, `next_instruction`(종료 전), `object_id` 필드, `photos`, `path`, `sha256`, `contains_hint`, `after_wrong`, NPC 전체, `on_wrong`, `on_correct`, 안 열린 힌트 text, 다른 퍼즐 dialogue.
- `answer`는 `failed` 직후 `last_result.answer`로 1번만 노출.

에이전트 출력:

- `{ "action": "answer", "value": "apple", "reason": "..." }` 형태 JSON 객체 하나.
- `move`: value 칸 좌표. `view`: value 사물 id. `answer`: value 답, reason 필수.
- 코드 펜스 벗기지 않음. 정의되지 않은 필드 무시.
- 거절은 아래 1~12번 순서와 `error` 문장 그대로. 테스트가 문자열 비교한다.

거절 검사 순서:

- 1: JSON이 아님(빈 문자열 포함) → `출력이 JSON 형식이 아닙니다`
- 2: JSON 객체가 아님 → `출력은 JSON 객체여야 합니다`
- 3: `action`이 없거나 문자열이 아님 → `action은 문자열이어야 합니다`
- 4: `action`이 `move`/`view`/`answer`가 아님 → `알 수 없는 행동입니다. move, view, answer 중 하나를 쓰세요`
- 5: `value`가 없거나 문자열이 아님 → `value는 문자열이어야 합니다`
- 6: `move`가 칸 형식에 맞지 않음 → `칸 좌표 형식이 아닙니다`
- 7: `move`가 격자 밖 → `지도에 없는 칸입니다`
- 8: `view` 사물이 공간에 없음 → `존재하지 않는 사물입니다`
- 9: `view` 사물이 `locked` → `아직 가까이 가지 않은 사물입니다`
- 10: 도착 전 `answer` → `아직 퍼즐이 열리지 않았습니다`
- 11: `answer`가 빈 문자열 → `답이 비어 있습니다`
- 12: `answer`의 `reason` 조건 불충족 → `answer에는 이유(reason)가 필요합니다`

이동과 도착:

- 한 행동으로 격자 안 어느 칸이든 이동 가능. 벽과 거리 검사 없음.
- 층 1개면 접두어 없는 칸만 유효. 층 2개 이상이면 접두어 있는 칸만 유효.
- 맞닿음 = 같은 층에서 `max(|열 차이|, |행 차이|) <= 1`.
- 트리거: 맞닿은 사물은 `open`. 되돌아가지 않음.
- 도착: 현재 퍼즐 사물과 맞닿은 상태에서 `view`하면 `npc_dialogue` 후 퍼즐 열림.

정답 판정:

- `value.strip().lower() == answer.strip().lower()`.
- 퍼즐당 5회. 거절은 시도로 세지 않음. 6번째 시도 없음.
- 도착 뒤에는 어느 칸에서든 답 가능.

시스템 프롬프트는 아래 원문을 그대로 쓴다. 페르소나 값만 넣는다. 5회 소진 공개 규칙과 상한은 넣지 않는다.

```text
당신은 공간 퍼즐 게임의 참가자입니다. 아래 사람처럼 생각하고 행동하세요.
나이: {age}
직업: {job}
어휘 수준: {vocab}
사고 방식: {thinking}

지시를 따라 이동하세요. 처음 받는 정보의 rooms는 방 이름과 칸 범위입니다. 지시받은 사물 근처로 가서 view로 찍으면 사물 사진을 볼 수 있습니다. 반응하는 사물이면 puzzle에 인물의 대화, 문제, 정답 글자 수, 열린 힌트, 남은 시도 횟수가 나타나고 퍼즐 그림이 함께 주어집니다.
대화에도 단서가 들어 있을 수 있습니다. 대화와 그림을 보고 답하세요.
매 차례 JSON 객체 하나만 출력하세요. 형식: {"action": "...", "value": "...", "reason": "..."}
- move: value는 이동할 칸입니다. cell_prefix_required가 true이면 2F-C4처럼 층을 붙입니다.
- view: value는 opened_object_ids에 있는 사물 id입니다. 사물의 설명과 사진을 돌려줍니다.
- answer: value는 답입니다. reason에 그렇게 답한 이유를 반드시 적으세요.
행동이 거절되면 last_result.error를 읽고 고치세요.
```

## 5. 검증과 오라클

- 검증기: 스키마 + 재연 규칙 검사. 실패 이유를 돌려주고 고쳐서 다시 검사.
- 출력: `reports/<set>/replica.md`에 통과/수정/확인 항목.
- 오라클: 모든 정답을 아는 플레이어로 1번부터 끝까지 진행. 끝까지 가면 플레이 가능. 막히면 재연 문제.

필수 완료기준(구 acceptance M1~M25 중 갈래 1):

- M1: 모든 퍼즐 데이터가 `puzzle` 스키마 만족.
- M2: 공간, NPC, 오프라인 기록이 각각 `space`, `npc`, `baseline` 스키마 만족.
- M3: 스키마 유효. 유효 표본 통과, 무효 표본은 오류 정확히 1개로 거절.
- M4: 퍼즐 `object_id`와 `next_object_id`가 공간에 있고, 각 퍼즐 `object_id`가 앞 퍼즐 `next_object_id`와 같음.
- M5: 모든 사물과 방이 격자 안, 겹침 없음, 모든 사물 사진 1장 이상, 첫 사진 파일 존재.
- M6: 모든 `answer`는 소문자, 앞뒤 공백 없음, `answer_letter_count` 일치.
- M7: 대화문에 정답 그대로 없음.
- M8: 모든 퍼즐 그림 SHA-256이 데이터와 일치.
- M9: `replica.md`에 통과/수정/확인 항목 기록.
- M25: 모든 `next_instruction`에 `next_object_id` 사물의 칸 좌표나 방 이름 포함.
- M12: 오라클 실행이 전부 `solved_by_dialogue`, `end(completed)`.
- M13~M17: 로그 15개 이상, 사고방식 3값 각 5회 이상, `log` 스키마 만족, 6번째 시도 없음, `completed`는 `puzzle_ended` 완결.
- M18~M24: 보고서 항목과 수치 규칙, Muse 실패 시 수치 유지.

상태 전이(퍼즐):

- 잠김 → 실행 시작 또는 앞 퍼즐 종료 → 잠금 해제. 로그 없음.
- 잠금 해제 → 맞닿은 위치에서 `view`(도착) → 풀이 중. `view`, `npc_dialogue`.
- 풀이 중 → 정답 → 해결. `answer_submitted`, `puzzle_ended`.
- 풀이 중 → 오답(시도 5 미만) → 풀이 중. 조건 맞으면 `hint_revealed`.
- 풀이 중 → 오답(시도 5) → 실패. 정답 공개. `puzzle_ended(failed)`.
- 거절된 행동은 상태 불변. `rejected`만 남긴다.

상태 전이(실행):

- 시작 전 → `new_game` 성공 → 진행 중.
- 시작 전 → 설정 오류, 키 없음, SHA 불일치, 사진 없음 → 시작 안 함. 로그 없음.
- 진행 중 → `submit`, 남은 퍼즐 있음, 상한 미만 → 진행 중.
- 진행 중 → 마지막 퍼즐 종료 → 완주. `end(completed)`.
- 진행 중 → 상한 도달 → `end(action_limit)`.
- 진행 중 → `abort` → `end(api_error)`.
- 종료 후 `observe`/`submit`/`abort` → `GameStateError`.

## 6. 모델 API와 이미지

이 절이 기준이다.

- `model_api`만 Muse Spark를 직접 호출한다. `httpx` 사용(`requirements.txt`에 고정, 지연 import 유지).
- 변경 사유(2026-11-05): 헌법 v1.3.0. 제출물을 `requirements.txt` 한 번으로 설치할 수 있게 `httpx`를 넣는다.
- 모델명: `MODEL_API_MODEL`(기본 `muse-spark-1.3`), `SAM_MODEL`(기본 `sam-3.1`).
- `make_client`: `MODEL_API_KEY`, `MODEL_API_BASE_URL`(기본 `https://api.meta.ai/v1`) 필요. 없으면 `MissingKeyError`.
- `respond`: `POST {base}/responses`. 출력 텍스트는 `output[type=message]/content[type=output_text]`에서 모은다. 없으면 `""`.
- `upload_file`: `POST {base}/files`, multipart `file` + `purpose=user_data`. 응답 `id` 반환.
- 재시도: 연결 실패, 타임아웃, HTTP 408/409/429/500 이상만. `MAX_RETRIES=4`, `TIMEOUT_SECONDS=180`. 그 밖 4xx는 즉시 `ModelAPIError`.
- 대기: `Retry-After`(0초 초과 120초 이하) 우선. 아니면 `min(0.5*2^n, 8)`초.
- 이미지: 실행 전 모든 퍼즐 그림과 모든 사물 첫 사진 준비. SHA-256 불일치나 파일 없음이면 실행 시작 안 함.
- 캐시: `workspace/cache/files.json`에 sha256 → file_id.
- 형식 오류(§4.1 1~5번)는 다음 호출이 재시도. API 실패는 실행기에서 덧붙이지 않고 즉시 `end(api_error)`.
- 끊긴 실행은 잇지 않는다. 새 `run_id`로 다시 돈다.

## 7. 페르소나, 점수, 로그

- 생성은 `random.Random(seed)`로 실행기 앞에서 끝낸다. 엔진 무작위성 없음.
- `thinking`: 3개 값을 5회씩 넣은 15칸을 섞어 배정.
- `age`: 10~79 균등. `job`: 목록에서 균등. 10대는 학생 고정. `vocab`: 상/중/하 균등. `name`: 넣지 않음.
- `persona.schema.json`으로 검증. 실행마다 전체와 `seed`를 로그에 남김.
- 15회 기준은 `outcome` 관계없이 전부 센다. 퍼즐별 `puzzle_ended` 10개 미만이면 더 돌린다. 추가는 3개 값 1회씩 묶음.

점수:

- 해결: 오답 수(0~4). 실패: 5.
- 평균 점수 = 난이도. 실패율과 힌트 사용률 함께 표시.
- 끊긴 퍼즐은 집계 제외, 건수만 표시.
- 해석: `solved_by_dialogue` = 단서 충분, `solved_with_hint` = 대화만으로 부족, `failed` = 저주 의심.

로그:

- 기준은 `log.schema.json`. `t`는 이벤트 순번. 1부터 1씩 증가. 마지막만 `end`.
- 갈래 2가 로그에서 읽는 것: `npc_dialogue.npc`, `view` 뒤 `npc_dialogue`(AR 반응), `answer_submitted`, `puzzle_ended.result`, `move.value` 발자국.
- 갈래 2가 `data/<set>/`에서 읽는 것: `start_cell` 시작점, `dialogue`, `on_wrong`/`on_correct`(화면 전용), `failed` 퍼즐의 `answer`·`next_instruction`(`puzzle.json`). 평면도와 사물 사진(`space.json`). NPC 이름과 이미지(`npc.json`).
- 변경 사유(2026-11-04): 사용자 결정으로 갈래 2 읽기 목록에 `failed` 퍼즐의 `next_instruction`을 추가한다. 스키마와 로그 형식은 바꾸지 않는다.

## 8. 보고서 분담

원칙: 수치와 판정은 코드, 자유 문장 해석만 Muse. Muse 실패해도 수치 보고서는 생성.

코드가 맡는다:

- 난이도 표, 갈리는 문제 판정과 속성 비교, 오답 집계, 오프라인 나란히 표시, 한계 문구.
- 갈리는 문제: 첫 시도 해결 비율과 `failed` 비율이 모두 30% 이상. 분모는 `puzzle_ended` 수.

Muse가 맡는다(점수에 영향 없음):

- 오답 이유 한 줄 요약과 대표 `reason`. 원문 일치 검증. 어긋나면 재요청, 끝내 어긋나면 분석 없음.
- `reason`의 단서 언급 판정.

## 9. 갈래 2(진행 중)

게임 엔진과 로그 형식을 바꾸지 않는다.

- 지도 화면, 고스트 재생, 주문 연출, 잉크 연출, 층 전환.
- 002 범위: 위 5종 포함. 주문 연출은 기본 동작 완성 후 필수(동영상용). 수용 기준과 배포 방식은 002 plan에서 결정. §11 미결 유지.
- 뷰어 기술: three.js(`WebGLRenderer`) + TS. `tsc` 단일 출력, 번들러 없음.
- 연결: three.js 벤더 파일 동봉. CDN·외부 URL·번들러·로컬 서버 없이 `file://`로 연 페이지에서 동작. ES 모듈 스크립트·importmap, `fetch`·XHR 로컬 파일 읽기, 로컬 사진의 WebGL 텍스처에 의존하지 않는다. 구체 로딩 방식은 002 plan에서 정한다.
- 버전 고정: `three`(벤더 파일), `typescript`, `@types/three` 모두 정확한 버전.
- 변경 사유(2026-11-04): 헌법 v1.2.0 원칙 II. importmap은 서버 없는 `file://` 실행과 양립하기 어려워 연결 문구를 교체하고, 버전 고정을 정확한 버전으로 맞춤.
- 디자인 톤: 양피지·먹·봉인 붉은색, 시스템 세리프. 상세는 002 spec Design Direction.
- 이후 003 후보: 층수 → 마우스 평면도 → 사물·장소 → 사진·퀴즈 JSON → 풀이 검증 빌더. `space_builder.py` 여유 항목과 연결.
- 마우스 평면도 빌더와 축척(문 폭 0.9m 기준)은 여유 항목.
- SAM 제안(O4)과 사진 초안(O9)은 실제 사진으로 먼저 시험.
- 저주 지수(`prediction.json`)와 수정 재검증(`revise`)은 여유 항목.
- Pannellum 불필요 가능.

## 10. 테스트 기준

- 모델 없이 표본(`docs/schemas/examples/valid/`)으로 엔진 검사. `model_api`는 `MockTransport`로 검사.
- 거절 메시지는 §4 문장과 정확히 일치해야 한다.
- 새 패키지 추가 금지. Python은 `requirements.txt`의 `jsonschema`, `httpx` 외 추가 없음. 뷰어는 `three`, `typescript`, `@types/three`만 정확한 버전으로 허용.
- 변경 사유(2026-11-04): 헌법 v1.2.0 원칙 II의 뷰어 허용 목록 반영.
- 변경 사유(2026-11-05): 헌법 v1.3.0 원칙 II에 `httpx` 추가 반영.
- 확인: `python -m unittest discover tests -v`.

엔진 시나리오(#1~#16, #18~#23, #28, #29):

- #1: 시작 후 `move C4`, `view desk@C4` → `move` 뒤 `npc_dialogue` 없음, `puzzle`은 `null`. `view` 뒤 `npc_dialogue`, 시도 5회 남음.
- #2: `move E5`(대각선) 후 `view` → 열림, 도착.
- #3: `move F4`(2칸) → 열리지 않음.
- #4: `move c4`/`I1`/`1F-C4` → 각각 6번/7번/7번 거절.
- #5: 시작 직후 `view shelf@F2`/`sofa@A1` → 각각 9번/8번 거절.
- #6: 시작 직후 `answer` → 10번 거절. 시도 아님.
- #7: 1번 진행 중 `move F2` 후 `view shelf@F2` → `npc_dialogue` 없음, `puzzle: null`.
- #8: 도착 후 `" Apple "` → `attempt 1`, `correct true`, 로그 원문 유지. `solved_by_dialogue`.
- #9: `reason` 없는 `answer` → 12번 거절. 시도 차감 없음.
- #10: 오답 1번 → `hint_revealed(level 1)`, 시도 4회 남음.
- #11: 오답 후 정답 → `solved_with_hint`, 시도 2회.
- #12: 1번 오답 5번 → `puzzle_ended(failed)`, 다음 지시와 정답 1번 노출. 6번째 시도 없음.
- #13: 2번 오답 5번 → `puzzle_ended(failed)` 뒤 `end(completed)`.
- #14: 완주 예시 재생 → `to_log` 이벤트 일치.
- #15: 비JSON 50번 → `rejected` 50개 뒤 `t: 51`에 `end(action_limit)`.
- #16: 상한 6에서 6행동 완주 → 그래도 `completed`.
- #18: 입력 dict 복사 후 완주 → 입력 불변.
- #19: 두 층 표본 `move C2`/`2F-AA3` → 7번 거절/성공.
- #20~#23: 두 사물 동시 열림, 시작 칸 변경, 힌트 조건 변경, 차례 위반 `view` 처리를 표본으로 확인.
- #28~#29: `brief`/`rooms` 생략 시 기본값, 중복 `view` 시 `npc_dialogue` 미반복.

모델 API(#17, #24~#27):

- #17: 첫 호출 HTTP 400 → 재시도 없음. `end(api_error)`.
- #24: HTTP 503 계속 → 요청 5번, 대기 `0.5, 1, 2, 4`초 후 `ModelAPIError`.
- #25: 429 + `Retry-After: 3` 후 정상 → 대기 3초, 출력 반환.
- #26: 빈 `output` → `respond`는 `""`. `submit`은 1번 거절.
- #27: 같은 sha256 재사용 → `upload_file` 1번.

노출 검사: `brief`와 관측 직렬화에서 `next_object_id`, `next_instruction`, `object_id`, `photos`, `path`, `sha256`, `contains_hint`, `after_wrong`, `npc`, `tone`, `on_wrong`, `on_correct` 없음. `answer`는 `failed` 직후만. 안 열린 힌트와 다른 퍼즐 대화문 노출 금지.

로그 검사: 모든 `to_log`이 `log.schema.json` 통과, `t` 1씩 증가, 마지막만 `end`.

## 11. 미결 TODO 인계

- 프론트 스택: three.js + TS 결정. 배포 방식(컴파일 JS 커밋 vs Action 빌드)은 002 plan에서.
- 가구 크기 추정: SAM 제안 착수 시.
- 주문 주체와 Babel fish 역할: 주문 연출 착수 시.
- 사람 플레이: 해커톤 후.
- 마감과 제출물: 구현 마친 뒤 규정 확인.
- SAM 호출 경로(Modal vs Model API): SAM 제안 착수 시.
- Muse Code 지침 파일: 구현 시작 시 저장소 루트 `AGENTS.md`에 읽을 문서와 규칙 기록.
