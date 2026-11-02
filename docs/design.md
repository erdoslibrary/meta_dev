# 설계

## 아키텍처

갈래 1(퍼즐 데이터 → 실행 → 로그 → 보고서)을 먼저 완성한다. 갈래 2(지도, 연출)는 로그만 읽으므로 나중에 합류해도 갈래 1을 바꾸지 않는다. 어디까지가 필수인지는 `docs/acceptance.md`가 정한다.

```text
사진, 평면도 ─▶ 공간 빌더 ─▶ space.json ─┐
저작 퍼즐 ─▶ 옮기기 ─▶ puzzle.json ──────┼─▶ 검증기 ─▶ 재연 보고서
                                         │     │ 통과
                                         │     ▼
                                         │   오라클 실행 ─┐
                                         ▼                │
페르소나 생성기 ─▶ 에이전트 실행기 ◀─▶ 게임 엔진          │
                      │ ▲                 │               │
                      ▼ │                 ▼               ▼
          Muse Spark API, Files API      로그 저장소 (logs/)
                                          │        │
                                          ▼        ▼
                        Muse ◀─▶ 보고서 생성기    뷰어 (지도, 고스트)
```

| 구성 요소 | 입력 | 출력 | 모델 | 위치 |
|---|---|---|---|---|
| 공간 빌더 | 사진, 평면도 | `space.json` | SAM 3.1, Muse Spark | `realtosim/space_builder.py` |
| 검증기 | 데이터, 로그 | 합격 여부, 재연 보고서 | 없음 | `realtosim/validate.py` |
| 오라클 실행 | 데이터 | 정답을 아는 플레이어의 로그 | 없음 | `realtosim/oracle.py` |
| 게임 엔진 | 데이터, 페르소나, 모델 출력 원문 | 관측, 이벤트, 로그 dict | 없음 (순수 상태 머신) | `realtosim/game_engine.py` |
| 페르소나 생성기 | 시드, 실행 수 | 페르소나 목록 | 없음 | `realtosim/personas.py` |
| 에이전트 실행기 | 데이터, 페르소나 | 실행별 로그 파일 | Muse Spark | `realtosim/run_agents.py` |
| 모델 API 클라이언트 | Responses API 입력, 파일 경로 | 출력 텍스트, `file_id` | 호출만 담당 | `realtosim/model_api.py` |
| 로그 저장소 | 스키마를 통과한 로그 dict | `logs/` 아래 JSON 파일. 별도 서버는 없다 | 없음 | 파일 |
| 보고서 생성기 | 로그, 퍼즐, 오프라인 기록 | `report.md`, `report.json` | 일부 Muse Spark (보고서 분담 절) | `realtosim/report.py` |
| 뷰어 | `space.json`, 로그, `report.json`, NPC 데이터 | 지도, 고스트, 연출 화면 | 없음 | `viewer/` |

공간 빌더의 마우스 그리기와 SAM 제안은 여유 항목이다. 빌더 없이 진행할 때는 `space.json`을 손으로 쓴다. 스키마가 벽과 문을 1개 이상 요구하므로 바깥 사각형 벽과 문 1개를 적고, 축척은 문 폭 0.9m로 계산한다.

**외부 의존**

| 대상 | 쓰임 | 실패 처리 |
|---|---|---|
| Muse Spark API | 에이전트 행동, 보고서의 `reason` 분석, 사물 이름 제안, 퍼즐 수정안과 초안 (여유 항목) | §6.1, §7. 보고서에서는 해당 분석만 비우고 수치는 생성한다 |
| Files API | 퍼즐 그림 업로드. `sha256` 캐시로 재사용 | §6.2, §7 |
| Modal 위 SAM 3.1 | 사진에서 사물 박스 추출 (여유 항목). 게임과 보고서는 이것 없이 돌아간다 | 창작자가 사물을 직접 배치 |

**SAM 출력.** 결과는 `<0f>0<|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|><|mask;...|>,1<|box;...|>` 형식의 텍스트다. 박스만 쓰며, 정규식은 `(\d+)<\|box;x1=(\d+);y1=(\d+);x2=(\d+);y2=(\d+);w=(\d+);h=(\d+)\|>`이다. 빈 출력은 찾은 것이 없다는 뜻이다. 검색어에 따라 결과가 갈리므로 `door`, `chair`, `table` 같은 검색어는 실제 사진으로 시험한다.

**데이터 흐름**

1. 공간과 퍼즐을 `data/<puzzle_set_id>/`에 JSON으로 둔다.
2. 검증기가 스키마와 재연 규칙을 검사한다. 실패하면 이유를 돌려주고 고쳐서 다시 검사한다.
3. 오라클 실행이 모델 없이 끝까지 진행한다. 막히면 퍼즐이 아니라 재연의 문제다.
4. 페르소나 생성기가 실행 수만큼 페르소나를 뽑고, 실행기가 페르소나마다 게임 1개를 독립적으로 돌린다. 호출 흐름은 §1이다.
5. `to_log` 결과를 `log.schema.json`으로 검증해 `logs/`에 저장한다.
6. 보고서 생성기와 뷰어는 저장된 파일만 읽는다. 모델을 다시 돌리지 않으며, 고스트는 기록의 재생이다.

## 폴더 구조

`game_engine`과 `model_api`는 `realtosim` 패키지 안에 둔다. 저장소 루트에서 `from realtosim import game_engine`으로 가져오고 `python -m realtosim.<모듈>`로 실행한다.

```text
meta/
├── AGENTS.md                 Muse Code 지침 (미결 TODO의 계획 참고)
├── README.md                 다음 단계에서 작성
├── requirements.txt          구현할 때 httpx 추가
├── .env                      MODEL_API_KEY 등. git에서 제외
├── docs/                     spec, design, acceptance, schemas/
├── realtosim/
│   ├── game_engine.py        §2, §3, §4, §8
│   ├── model_api.py          §6.1
│   ├── settings.py           model(), sam_model()
│   ├── personas.py
│   ├── run_agents.py         실행기. 시스템 프롬프트(§5), 이미지 입력(§6.2) 포함
│   ├── oracle.py
│   ├── validate.py
│   ├── report.py
│   ├── revise.py             여유 항목
│   └── space_builder.py      여유 항목
├── viewer/                   뷰어. 스택은 미결
├── data/
│   ├── npcs/<npc_id>.json    NPC 1명당 파일 1개. 이미지 경로는 image 필드
│   └── <puzzle_set_id>/
│       ├── space.json
│       ├── puzzle.json
│       ├── baseline.json
│       ├── prediction.json   제작자의 예상 점수. 여유 항목
│       ├── puzzles/          퍼즐 그림. image.path의 기준 폴더는 puzzle.json 위치
│       └── photos/           사물 사진. photos 경로의 기준 폴더
├── logs/<puzzle_set_id>/
│   ├── r01.json ...          에이전트 실행. 파일 이름은 run_id
│   └── oracle/r0.json        오라클 실행. 집계와 15회 기준에서 제외
├── reports/<puzzle_set_id>/
│   ├── replica.md            재연 보고서
│   ├── report.md             최종 보고서
│   └── report.json           뷰어가 읽는 집계 값
├── workspace/cache/files.json  sha256 → file_id. git에서 제외
├── tests/                    test_schemas.py, 구현할 때 §9의 테스트 추가
└── test.py                   Modal GPU 동작 확인
```

- 폴더 이름 `<puzzle_set_id>`는 데이터의 `puzzle_set_id`와 같다. 뷰어는 로그의 `puzzle_set_id`로 이 폴더를 찾는다.
- `logs/`와 `reports/`는 git에 넣는다. API 키 없이도 보고서와 고스트를 볼 수 있게 하기 위해서다. `.gitignore`의 `runs/`, `cache/` 패턴에 걸리지 않는 경로다.
- 오라클 로그는 `run_id: "r0"`, `model: "oracle"`이다. 스키마와 `new_game`이 페르소나를 요구하므로 고정 값을 넣는다.

## 인터페이스 계약

갈래 1(에이전트, 로그, 보고서), 갈래 2(지도, 연출), 테스트가 모두 이 절을 기준으로 삼는다. 데이터 형식의 기준은 `docs/schemas/*.schema.json`이다.

예시의 입력은 `docs/schemas/examples/valid/`의 가상 표본 `space.sample.json`, `puzzle.sample.json`, `persona.sample.json`이다. 표본의 힌트는 두 퍼즐 모두 `after_wrong`이 1이다.

### 1. 구성과 실행 흐름

게임 엔진은 순수 상태 머신이다. 모델, 파일, 네트워크에 접근하지 않고, 무작위성도 없다. 모델 호출과 이미지 업로드는 에이전트 실행기가 맡는다.

```python
game = new_game(space, puzzle_set, persona, run_id=run_id, model=model_name)
instructions = system_prompt(persona)
history = [user_text(to_json(brief(game)))]

while not game.over:
    view = observe(game)
    history.append(user_text(to_json(view["observation"])))
    request = history[:-1] + [with_images(history[-1], view["images"])]  # images가 비면 그대로
    try:
        raw = client.respond(model=model_name, instructions=instructions, input=request)
    except ModelAPIError as error:
        print(run_id, error, file=sys.stderr)
        abort(game)
        break
    if raw:
        history.append(assistant_text(raw))
    submit(game, raw)

log = to_log(game)  # log.schema.json으로 검증한 뒤 저장한다
```

- 호출 1번은 `submit` 1번이며 행동 1회다.
- 에이전트는 한 실행 안에서 이전 관측과 자기 출력을 텍스트로 모두 기억한다. 실행 사이에는 아무것도 공유하지 않는다.
- 이미지는 현재 퍼즐의 그림과 방금 `view`한 사물의 사진만, 마지막 메시지에만 붙인다. `history`에는 이미지를 넣지 않는다.

### 2. 게임 엔진 함수

모듈 이름은 `game_engine`이다. 위치는 폴더 구조 절에서 정한다.

| 함수 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `new_game(space, puzzle_set, persona, *, run_id, model, seed=None, max_actions=50)` | 스키마 검증을 마친 dict. 입력을 복사해 쓰고 바꾸지 않는다 | `Game` | `GameSetupError` |
| `brief(game)` | `Game` | 실행 중 변하지 않는 공간 정보 (§3.1) | 없음 |
| `observe(game)` | 진행 중인 `Game` | `{"observation": dict, "images": [{"path", "sha256"}, ...]}` (§3.2) | `GameStateError` |
| `submit(game, raw_output)` | 진행 중인 `Game`, 모델 출력 원문 `str` | `{"events": list, "over": bool, "outcome": str 또는 null}` | `GameStateError` |
| `abort(game)` | 진행 중인 `Game` | `{"events": list, "over": true, "outcome": "api_error"}` | `GameStateError` |
| `to_log(game)` | 끝난 `Game` | `log.schema.json`을 만족하는 dict | `GameStateError` |

`Game`은 `over: bool`과 `outcome: str | None` 속성을 제공한다. 나머지는 비공개다.

**거절은 데이터로 돌려준다.** 모델의 잘못된 출력이나 불가능한 행동에는 절대 예외를 던지지 않는다. `submit`이 `rejected` 이벤트를 남기고, 이유는 다음 관측의 `last_result.error`로 전달한다. 예외는 호출 코드의 실수에만 쓴다.

- `GameSetupError`: `space_id` 불일치, `number`가 1부터 N까지 순서대로 이어지지 않음, `object_id`가 공간에 없음, `start_cell`이 격자 밖이거나 §4.2의 층 표기와 맞지 않음, `run_id`가 `^r[0-9]+$`에 맞지 않음
- `GameStateError`: 끝난 게임에 `observe`, `submit`, `abort` 호출, 끝나지 않은 게임에 `to_log` 호출

`submit`의 반환값 `events`는 이번 호출로 새로 생긴 이벤트이며, 순서는 로그와 같다.

**`new_game` 처리 순서**
1. 모든 사물의 `state`를 `locked`로 둔다. 입력 파일의 `state`는 읽지 않는다. 파일 값을 그대로 쓰면 `open`인 사물과 `locked`인 사물의 차이로 퍼즐 위치가 드러날 수 있고, 실행마다 시작 상태가 같아야 하기 때문이다.
2. 현재 퍼즐을 1번으로, 행동 수를 0으로 둔다.
3. 위치를 `start_cell`로 두고 §4.3의 트리거를 판정한다. 시작 칸이 1번 사물의 이웃이어도 도착은 `view`해야 일어나므로 이벤트는 남지 않는다.

`npc` 데이터는 입력이 아니다. 엔진은 퍼즐의 `npc` id만 로그에 옮긴다.

**`submit` 처리 순서**
1. 행동 수를 1 늘린다. 거절된 출력도 센다.
2. §4의 규칙으로 검사한다. 실패하면 `rejected` 이벤트를 남기고 5번으로 간다.
3. 행동을 적용하고 `move`, `view`, `answer_submitted` 이벤트를 남긴다. `move`이면 §4.3의 트리거를, `view`이면 도착을 판정한다.
4. `answer`의 결과를 처리한다.
   - 정답이면 `puzzle_ended`를 남기고 다음 퍼즐로 넘어간다. 힌트가 열린 적이 있으면 `result`는 `solved_with_hint`, 없으면 `solved_by_dialogue`다.
   - 오답이면 이번 퍼즐의 오답 수를 1 늘린다. 오답 수가 힌트의 `after_wrong`과 같으면 `hint_revealed`를 남긴다. 오답 수가 5면 `puzzle_ended`(`failed`)를 남기고 다음 퍼즐로 넘어간다.
   - 다음 퍼즐로 넘어가도 도착을 판정하지 않는다. 다음 사물이 이미 이웃 칸에 있어도 `view`해야 `npc_dialogue`가 남는다.
5. 마지막 퍼즐까지 끝났으면 `end`(`completed`)를 남긴다. 아니고 행동 수가 `max_actions`이면 `end`(`action_limit`)를 남긴다.

마지막 행동에서 게임을 끝까지 마쳤다면 상한에 닿았더라도 `completed`다. 마지막 퍼즐이 `failed`로 끝난 경우도 `completed`다.

**`abort`**는 `end`(`api_error`)만 남긴다. 행동 수는 늘리지 않는다. `action_limit`이나 `api_error`로 끊긴 퍼즐에는 `puzzle_ended`를 남기지 않는다.

**`to_log`**는 `run_id`, `persona`(입력 그대로, `name` 포함), `puzzle_set_id`, `model`, `events`를 담는다. `seed`는 `None`이 아닐 때만 담는다.

### 3. 에이전트 관측

관측은 `json.dumps(값, ensure_ascii=False)`로 직렬화해 텍스트로 보낸다.

#### 3.1 `brief(game)`: 실행 시작 때 1번

```json
{
  "floors": [{ "id": "1F", "columns": 8, "rows": 6 }],
  "cell_prefix_required": false,
  "rooms": [
    { "name": "가상 방 1", "cells": "A1:D6" },
    { "name": "가상 방 2", "cells": "E1:H6" }
  ],
  "objects": [
    { "id": "desk@C4", "label": "desk", "cells": "C4:D4", "description": "" },
    { "id": "shelf@F2", "label": "shelf", "cells": "F2", "description": "" }
  ]
}
```

`cell_prefix_required`는 층이 2개 이상일 때 `true`다. `rooms`는 공간 데이터의 값을 그대로 주고, 없으면 `[]`다.

#### 3.2 `observe(game)`: 호출마다

첫 관측:

```json
{
  "observation": {
    "position": "A1",
    "opened_object_ids": [],
    "instruction": "C4의 책상으로 가라",
    "puzzle": null,
    "last_result": null
  },
  "images": []
}
```

| 필드 | 값 |
|---|---|
| `position` | 현재 칸 |
| `opened_object_ids` | `open`인 사물 id. `space.objects` 순서 |
| `instruction` | 가장 최근에 받은 장소 지시. `start_instruction`이 없으면 첫 퍼즐을 풀 때까지 `null` |
| `puzzle` | 현재 퍼즐 장소에 도착한 뒤 끝나기 전까지 객체, 그 밖에는 `null` |
| `last_result` | 직전 행동의 결과 (§3.4). 첫 관측은 `null` |

`images`는 실행기만 읽는다. 아래 순서로 담고, 해당하는 것이 없으면 빈 목록이다.

1. 직전 행동이 성공한 `view`이면 그 사물의 첫 번째 사진. `sha256`은 `null`이고 실행기가 파일에서 계산한다 (§6.2). `photos`가 비어 있으면 넣지 않는다.
2. `puzzle`이 객체이면 현재 퍼즐의 그림.

**`path`와 `sha256`은 모델에 보내지 않는다.** 파일 이름에 정답이나 퍼즐 위치가 들어 있을 수 있기 때문이다.

`move` `C4`, `view` `desk@C4`로 도착한 직후의 관측:

```json
{
  "observation": {
    "position": "C4",
    "opened_object_ids": ["desk@C4"],
    "instruction": "C4의 책상으로 가라",
    "puzzle": {
      "number": 1,
      "dialogue": ["가상 대화 1", "가상 단서 1"],
      "question": "그림이 가리키는 단어는?",
      "answer_letter_count": 5,
      "hints": [],
      "attempts_left": 5
    },
    "last_result": {
      "action": "view",
      "ok": true,
      "object": { "id": "desk@C4", "label": "desk", "cells": "C4:D4", "description": "" }
    }
  },
  "images": [
    { "path": "desk_front.jpg", "sha256": null },
    {
      "path": "puzzles/sample_1.jpg",
      "sha256": "0000000000000000000000000000000000000000000000000000000000000001"
    }
  ]
}
```

#### 3.3 필드 노출 시점

| 출처 | 필드 | 에이전트에게 노출되는 시점 |
|---|---|---|
| space | `floors[].id`, `columns`, `rows` | 시작부터 (`brief`) |
| space | `rooms[].name`, `cells` | 시작부터 (`brief`). 모든 방을 함께 보여 주므로 퍼즐 위치가 드러나지 않는다 |
| space | `objects[].id`, `label`, `cells`, `description` | 시작부터 (`brief`). 퍼즐이 있는 사물을 구분하지 않는다 |
| space | `objects[].state` | `opened_object_ids`로 현재 값만 |
| space | `objects[].photos` | 경로는 노출 안 함. 파일 이름이 퍼즐 위치를 흘릴 수 있다. 첫 번째 사진의 이미지만 `view` 직후 1번 |
| space | `walls`, `doors`, `meters_per_pixel`, `origin_px`, `background_image`, `space_id` | 노출 안 함. 이동은 격자만 검사한다 |
| persona | `age`, `job`, `vocab`, `thinking` | 시스템 프롬프트 |
| persona | `name` | 노출 안 함 |
| puzzle set | `start_cell` | 첫 관측의 `position` |
| puzzle set | `start_instruction` | 첫 관측의 `instruction` |
| puzzle | `number`, `question`, `answer_letter_count`, 그림 | 현재 퍼즐 장소에 도착한 때부터 퍼즐이 끝나기 전까지 |
| puzzle | `dialogue[].text` | 위와 같음. 전체 문장을 한 번에 준다 |
| puzzle | `dialogue[].contains_hint` | **노출 안 함.** 어느 문장이 단서인지 드러난다 |
| puzzle | `hints[].level`, `text` | `hint_revealed` 때부터 퍼즐이 끝나기 전까지. 안 열린 힌트는 노출 안 함 |
| puzzle | `hints[].after_wrong` | 노출 안 함 |
| puzzle | `npc`와 NPC 데이터 전체(`name`, `image`, `tone`) | 노출 안 함. 화면 연출용이다 |
| puzzle | `on_wrong`, `on_correct` | 노출 안 함. 화면 전용 대사다 |
| puzzle | `object_id` | 필드로 노출 안 함. 다음 퍼즐의 `object_id`는 이전 퍼즐의 `next_object_id`와 같기 때문이다 |
| puzzle | `answer` | **퍼즐이 끝나기 전에는 노출 안 함.** `failed` 직후 `last_result.answer`로 1번 |
| puzzle | `next_instruction` | **퍼즐이 끝나기 전에는 노출 안 함.** 해결 또는 `failed` 직후부터 `instruction`으로 |
| puzzle | `next_object_id` | **노출 안 함.** 해결 후에도 지시문만 준다 |
| 엔진 | 남은 시도 횟수 | `puzzle.attempts_left` |
| 엔진 | 5회 소진 후 정답 공개 규칙, 행동 수, 행동 상한 | 노출 안 함 |
| 로그 | `run_id`, `puzzle_set_id`, `model`, `seed`, `t` | 노출 안 함 |

오답에는 틀렸다는 사실과 조건에 맞아 열린 힌트만 알린다. 어떤 글자가 맞았는지, 얼마나 가까운지는 알리지 않는다.

#### 3.4 `last_result`

| 상황 | 값 |
|---|---|
| 이동 | `{"action": "move", "ok": true, "position": "C4", "newly_opened": ["desk@C4"]}` |
| 사물 보기 | `{"action": "view", "ok": true, "object": {...}}` |
| 오답 | `{"action": "answer", "ok": true, "correct": false}` |
| 오답 + 힌트 | `{"action": "answer", "ok": true, "correct": false, "hint_revealed": true}` |
| 5번째 오답 | `{"action": "answer", "ok": true, "correct": false, "failed": true, "answer": "apple"}` |
| 정답 | `{"action": "answer", "ok": true, "correct": true}` |
| 거절 | `{"action": "view", "ok": false, "error": "존재하지 않는 사물입니다"}` |

- `object`는 `id`, `label`, `cells`, `description` 4개 필드다.
- `view` 결과는 모든 사물이 같은 형태다. 현재 퍼즐의 사물이면 같은 관측의 `puzzle`이 함께 열린다.
- 힌트 본문은 `puzzle.hints`에, 다음 지시는 `instruction`에 있다.
- 형식 오류로 행동을 알 수 없으면 거절의 `action`은 `null`이다.

### 4. 에이전트 출력

JSON 객체 하나다. `submit`은 모델 출력을 앞뒤 공백만 제거하고 그대로 `json.loads`로 읽는다. 코드 펜스는 벗기지 않으며, 정의되지 않은 필드는 무시한다.

```json
{ "action": "answer", "value": "apple", "reason": "그림에 빨간 과일이 있어서" }
```

| `action` | `value` | `reason` | 로그 이벤트 |
|---|---|---|---|
| `move` | 칸 좌표 문자열 | 선택 | `move` |
| `view` | 사물 id 문자열 | 선택 | `view` |
| `answer` | 답 문자열 | **필수**. 공백 제외 1자 이상 | `answer_submitted` |

`npc_dialogue`, `hint_revealed`, `puzzle_ended`, `end`는 엔진이 남기는 이벤트이며 행동이 아니다. 포기 행동은 없다.

`reason`이 공백 제외 1자 이상의 문자열이면 로그에 원문으로 남긴다. `move`와 `view`에서 그 외의 값이면 해당 필드를 뺀다. 거절 이벤트에도 같은 규칙을 적용한다.

#### 4.1 검사 순서와 거절 메시지

위에서부터 검사해 처음 걸린 것으로 거절한다. `error`는 아래 문장을 정확히 쓴다. 테스트가 이 문자열을 비교하며, 어떤 문장도 정답이나 퍼즐 위치를 드러내지 않는다.

| # | 조건 | `attempted_action` | `error` |
|---|---|---|---|
| 1 | JSON이 아님 (빈 문자열 포함) | `null` | `출력이 JSON 형식이 아닙니다` |
| 2 | JSON 객체가 아님 | `null` | `출력은 JSON 객체여야 합니다` |
| 3 | `action`이 없거나 문자열이 아님 | `null` | `action은 문자열이어야 합니다` |
| 4 | `action`이 `move`, `view`, `answer`가 아님 | 보낸 값 | `알 수 없는 행동입니다. move, view, answer 중 하나를 쓰세요` |
| 5 | `value`가 없거나 문자열이 아님 | 보낸 값 | `value는 문자열이어야 합니다` |
| 6 | `move`: `cellRef` 패턴에 맞지 않음 | `move` | `칸 좌표 형식이 아닙니다` |
| 7 | `move`: 격자에 없는 칸 (§4.2) | `move` | `지도에 없는 칸입니다` |
| 8 | `view`: 공간에 없는 사물 | `view` | `존재하지 않는 사물입니다` |
| 9 | `view`: 사물이 `locked` | `view` | `아직 가까이 가지 않은 사물입니다` |
| 10 | `answer`: 현재 퍼즐에 아직 도착하지 않음 (§4.3) | `answer` | `아직 퍼즐이 열리지 않았습니다` |
| 11 | `answer`: 앞뒤 공백 제거 후 빈 문자열 | `answer` | `답이 비어 있습니다` |
| 12 | `answer`: `reason`이 조건에 맞지 않음 | `answer` | `answer에는 이유(reason)가 필요합니다` |

`rejected.value` 규칙: `value`가 문자열이면 원문, 없거나 `null`이면 `null`, 그 밖의 값이면 `json.dumps(값, ensure_ascii=False)`다. 1, 2번 거절은 `null`이다.

#### 4.2 `move`

- 한 행동으로 격자 안의 어느 칸이든 갈 수 있다. 벽과 거리는 검사하지 않는다 (spec §3). 사물이 있는 칸에도 들어갈 수 있고, 지금 있는 칸으로 가도 행동으로 센다.
- 층이 1개면 접두어 없는 칸만 있는 칸이다. `1F-C4`는 7번으로 거절한다.
- 층이 2개 이상이면 접두어 있는 칸만 있는 칸이다. `C2`는 7번으로 거절한다.
- 열은 A=1, Z=26, AA=27로 읽는다. 열 번호가 `columns` 이하, 행 번호가 `rows` 이하면 격자 안이다.

#### 4.3 트리거, 도착, `view`

"맞닿음"은 위치가 사물의 어느 칸과든 같거나 상하좌우, 대각선으로 붙어 있는 것이다. 조건은 같은 층에서 `max(|열 차이|, |행 차이|) <= 1`이다.

- **트리거:** 맞닿은 사물은 `open`이 된다. `open`은 되돌아가지 않으며, 멀어져도 `view`할 수 있다.
- **도착:** 위치가 현재 퍼즐의 사물과 맞닿은 상태에서 그 사물을 `view`하면 엔진이 `view` 뒤에 `npc_dialogue`를 남기고 퍼즐을 연다. 오프라인에서 사물을 찍으면 AR이 반응하던 순간이다. `open` 상태가 아니라 **현재 위치**로 판정한다. 앞 퍼즐을 푸는 동안 지나가며 `open`된 사물이라도, 차례가 되었을 때 위치가 떨어져 있으면 다시 가서 찍어야 한다. 이미 도착한 퍼즐의 사물을 다시 `view`해도 `npc_dialogue`를 또 남기지 않는다.
- **차례가 아닌 퍼즐의 사물:** 찍어도 NPC와 퍼즐이 나오지 않는다.
- **`view`:** 사물 텍스트와 첫 번째 사진을 돌려주고 행동으로 센다. 찍은 사물이 맞는지는 이미지 인식이 아니라 엔진이 사물 id로 판정한다. 인식 실패가 난이도 점수에 섞이지 않게 하기 위해서다.
- spec §5.4의 트리거는 이 계약에서 `view`할 수 있게 되는 것을 뜻한다.

#### 4.4 `answer`

- 정답 판정은 `value.strip().lower() == puzzle["answer"].strip().lower()`다.
- 퍼즐당 5회 시도한다. 퍼즐의 `max_attempts`가 없으면 5로 본다. `answer_submitted.attempt`는 1부터 늘고, 6번째 시도는 없다.
- 거절된 입력은 시도로 세지 않는다.
- 글자 수가 다른 답도, 같은 오답을 반복한 답도 오답으로 센다. spec §8 예시의 `apple`, `pear`가 글자 수가 달라도 `correct: false`로 기록된 것을 따른다.
- 로그의 `value`에는 입력 원문을 남긴다.
- 도착한 뒤에는 어느 칸에서든 답할 수 있다.

### 5. 시스템 프롬프트

아래 문구에 페르소나 값만 넣는다. 5회 소진 후 정답 공개 규칙과 행동 상한은 넣지 않는다. 답을 얻으려 일부러 틀리거나 상한을 의식하는 행동을 막기 위해서다.

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

### 6. 모델 API와 이미지 입력

#### 6.1 모델 API 클라이언트

Muse Spark API를 `httpx`로 직접 호출한다. 모델 이름은 환경 변수 `MODEL_API_MODEL`(기본 `muse-spark-1.3`)과 `SAM_MODEL`(기본 `sam-3.1`)로 정하며, `realtosim/settings.py`의 `model()`, `sam_model()`이 읽는다.

모듈 이름은 `model_api`다. 위치는 폴더 구조 절에서 정한다.

| 함수 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `make_client(*, transport=None, sleep=time.sleep)` | `MODEL_API_KEY`, `MODEL_API_BASE_URL`(기본 `https://api.meta.ai/v1`) 환경 변수. `transport`와 `sleep`은 테스트용 | `ModelClient` | `MissingKeyError` |
| `client.respond(*, model, instructions=None, input, json_mode=True)` | Responses API의 `input` 목록 | 출력 텍스트 `str`. 없으면 `""` | `ModelAPIError` |
| `client.upload_file(path)` | 파일 경로 | `file_id` `str` | `ModelAPIError` |

**요청**
- 공통 헤더는 `Authorization: Bearer {MODEL_API_KEY}`다.
- `respond`는 `POST {base_url}/responses`에 JSON 본문 `{"model", "instructions", "input", "text": {"format": {"type": "json_object"}}}`를 보낸다. `instructions`가 `None`이면 뺀다. `json_mode=False`면 `text`를 뺀다. SAM 호출이 이 경우다.
- `upload_file`은 `POST {base_url}/files`에 multipart로 `file`과 `purpose=user_data`를 보내고, 응답의 `id`를 돌려준다.

**응답.** 출력 텍스트는 아래와 같이 모은다. 응답의 최상위 `output_text` 필드에 기대지 않는다.

```python
"".join(
    block["text"]
    for item in body["output"] if item["type"] == "message"
    for block in item["content"] if block["type"] == "output_text"
)
```

`output`에 해당 항목이 없으면 `""`을 돌려주며, 엔진이 §4.1의 1번으로 거절한다. HTTP 200인데 본문이 JSON이 아니거나 `output`이 목록이 아니면 재시도 없이 `ModelAPIError`다.

**재시도.** 이 모듈에서 직접 구현한다.

| 항목 | 값 |
|---|---|
| 재시도 횟수 | `MAX_RETRIES = 4` (최초 포함 최대 5번 시도) |
| 호출 제한 | `TIMEOUT_SECONDS = 180` (시도 1번 기준) |
| 재시도 대상 | 연결 실패, 시간 초과, HTTP 408, 409, 429, 500 이상 |
| 재시도 안 함 | 그 밖의 4xx. 바로 `ModelAPIError` |
| 대기 | `Retry-After`가 0초 초과 120초 이하의 숫자면 그 값. 아니면 `min(0.5 × 2^n, 8)`초 (`n`은 0부터) |
| 끝내 실패 | `ModelAPIError`. 메시지에 HTTP 상태와 응답 본문 앞 200자를 담는다. API 키는 담지 않는다 |

#### 6.2 이미지 입력

- 실행기는 첫 모델 호출 전에 모든 퍼즐 그림과 모든 사물의 첫 번째 사진을 준비한다.
- `image.path`는 퍼즐 JSON 파일이 있는 폴더 기준 상대 경로다. `photos`의 경로는 `space.json` 옆 `photos/` 폴더 기준이다.
- 퍼즐 그림 파일의 SHA-256이 `image.sha256`과 다르거나 사물 사진 파일이 없으면 실행을 시작하지 않고 예외를 던진다. 로그는 남기지 않는다. 사물 사진의 SHA-256은 실행기가 파일에서 계산한다.
- `workspace/cache/files.json`에 `sha256`을 키로 `file_id`를 저장한다. 없을 때만 `client.upload_file(path)`로 올린다.
- 입력 형식은 `{"type": "input_file", "file_id": file_id}`이고, `input_text` 뒤에 `images`의 순서대로 붙인다. JPG와 PNG에 쓰는 형식이다.

엔진은 이미지 파일을 읽지 않는다. 그래서 실제 그림 파일이 없는 표본으로도 엔진을 테스트할 수 있다.

### 7. 형식 오류와 API 실패

| 구분 | 형식 오류 | API 실패 |
|---|---|---|
| 해당 | 모델이 응답했으나 §4.1의 1~5번에 걸림. 빈 응답 포함 | `ModelAPIError` (§6.1) |
| 재시도 | 다음 호출이 곧 재시도다. 이유를 `last_result.error`로 전달 | `model_api` 안에서만 한다. 실행기에서 덧붙이지 않는다 |
| 횟수 | 별도 상한 없음. 행동 상한 50회에서 멈춤 | `MAX_RETRIES = 4`, 호출 제한 `TIMEOUT_SECONDS = 180` |
| 대기 | 없음 | §6.1. 호출 1번의 최악은 약 15분(180초 × 5)이고, 서버가 대기를 요청하면 최대 약 23분이다 |
| 로그 | 매번 `rejected`. 행동 수에 포함, 점수에 미포함 | 재시도는 남기지 않음. 최종 실패 시 `end`(`api_error`) |
| 실행 | 계속 | 즉시 끝남. 그때까지의 로그를 저장 |

- 그림 업로드가 끝내 실패해도 같게 처리한다. 첫 호출 전이면 `t: 1`인 `end` 이벤트 하나만 남는다.
- 실패 원인은 표준 오류에 한 줄로 출력한다. `end` 이벤트에는 원인 필드가 없고, `reason`은 에이전트의 이유이므로 쓰지 않는다.
- 끊긴 실행을 이어 가지 않는다. 다시 돌릴 때는 새 `run_id`를 쓴다.
- `MissingKeyError`는 실행 시작 전 설정 오류다. 로그를 남기지 않고 프로그램을 끝낸다.

### 8. 로그

필드 정의는 `log.schema.json`이 기준이다. 스키마가 다루지 않는 규칙은 아래와 같다.

- `t`는 행동 수가 아니라 이벤트 순번이다. `npc_dialogue`, `hint_revealed`, `puzzle_ended`, `end`도 `t`를 쓴다. 상한 판정에 `t`를 쓰지 않는다.
- `puzzle`은 이벤트 시점에 진행 중인 퍼즐이다. `puzzle_ended`는 끝난 퍼즐의 번호다. 그 뒤의 이벤트부터 다음 번호다.
- `completed`의 `end`는 마지막 퍼즐 번호를 쓴다.
- `npc_dialogue`, `hint_revealed`, `puzzle_ended`, `end`에는 `reason`이 없다.

완주 예시다. 1번은 5회 모두 틀려 실패하고, 2번은 첫 시도에 푼다. 행동은 12회, 이벤트는 18개다.

```json
{
  "run_id": "r01",
  "persona": { "age": 54, "job": "약사", "vocab": "중", "thinking": "문자 그대로 읽음" },
  "puzzle_set_id": "sample-set",
  "model": "muse-spark-1.3",
  "events": [
    { "t": 1, "puzzle": 1, "type": "move", "value": "C4", "reason": "지시문의 좌표로 이동" },
    { "t": 2, "puzzle": 1, "type": "view", "value": "desk@C4" },
    { "t": 3, "puzzle": 1, "type": "npc_dialogue", "npc": "librarian" },
    { "t": 4, "puzzle": 1, "type": "rejected", "attempted_action": "view", "value": "shelf@F2",
      "error": "아직 가까이 가지 않은 사물입니다" },
    { "t": 5, "puzzle": 1, "type": "answer_submitted", "value": "pear", "attempt": 1, "correct": false, "reason": "가상 이유 1" },
    { "t": 6, "puzzle": 1, "type": "hint_revealed", "level": 1 },
    { "t": 7, "puzzle": 1, "type": "rejected", "attempted_action": null, "value": null,
      "error": "출력이 JSON 형식이 아닙니다" },
    { "t": 8, "puzzle": 1, "type": "answer_submitted", "value": "plum", "attempt": 2, "correct": false, "reason": "가상 이유 2" },
    { "t": 9, "puzzle": 1, "type": "answer_submitted", "value": "grape", "attempt": 3, "correct": false, "reason": "가상 이유 3" },
    { "t": 10, "puzzle": 1, "type": "answer_submitted", "value": "melon", "attempt": 4, "correct": false, "reason": "가상 이유 4" },
    { "t": 11, "puzzle": 1, "type": "answer_submitted", "value": "peach", "attempt": 5, "correct": false, "reason": "가상 이유 5" },
    { "t": 12, "puzzle": 1, "type": "puzzle_ended", "result": "failed", "attempts_used": 5 },
    { "t": 13, "puzzle": 2, "type": "move", "value": "F2" },
    { "t": 14, "puzzle": 2, "type": "view", "value": "shelf@F2" },
    { "t": 15, "puzzle": 2, "type": "npc_dialogue", "npc": "librarian" },
    { "t": 16, "puzzle": 2, "type": "answer_submitted", "value": " PineApple ", "attempt": 1, "correct": true, "reason": "가상 이유 6" },
    { "t": 17, "puzzle": 2, "type": "puzzle_ended", "result": "solved_by_dialogue", "attempts_used": 1 },
    { "t": 18, "puzzle": 2, "type": "end", "outcome": "completed" }
  ]
}
```

첫 호출부터 API가 실패한 예시다.

```json
{
  "run_id": "r02",
  "persona": { "age": 54, "job": "약사", "vocab": "중", "thinking": "문자 그대로 읽음" },
  "puzzle_set_id": "sample-set",
  "model": "muse-spark-1.3",
  "events": [
    { "t": 1, "puzzle": 1, "type": "end", "outcome": "api_error" }
  ]
}
```

`docs/schemas/examples/valid/log.spec-example.json`은 앞부분을 생략한 형식 표본이다. 2번 퍼즐에서 시작하므로 엔진 동작의 기준으로 쓰지 않는다.

**갈래 2가 로그에서 읽는 것**
- NPC 등장 연출은 `npc_dialogue.npc`로 NPC 데이터를 찾아 보여 준다. NPC 이미지 작업은 후반에 한다.
- `view` 바로 뒤의 `npc_dialogue`가 AR 반응이다. 사물 사진, SAM 윤곽선, NPC 순서로 보여 줄 수 있다.
- NPC 반응 대사는 `answer_submitted.correct`에 따라 퍼즐의 `on_wrong`, `on_correct`를 보여 준다. 화면 전용 대사이며 선택 필드이므로 없으면 표시하지 않는다.
- 퍼즐별 결과는 `puzzle_ended`의 `result`다. 이 이벤트가 없으면 끊긴 퍼즐이다.
- 발자국의 시작은 퍼즐 묶음의 `start_cell`이고, 이후 순서대로 `move.value`다. 층을 건너뛰어도, 벽을 지나도 유효한 기록이다. 칸 사이 경로는 재생 때 보간한다.
- 거절된 이동은 `rejected`이므로 위치가 바뀌지 않는다.
- `t`는 순서일 뿐 시간이 아니다.
- 퍼즐의 장소는 `puzzle_set_id`로 찾은 묶음의 `object_id`로 찾는다.
- 지도의 층과 방 이름은 로그가 아니라 `space.json`의 `floors[].id`, `rooms`로 표시한다.

### 9. 테스트 기준

모델 없이 표본으로 엔진을 검사한다. 실행기와 `model_api`는 `make_client(transport=httpx.MockTransport(handler), sleep=기록용_함수)`로 네트워크와 실제 대기 없이 검사한다.

표의 거절 번호는 §4.1의 번호다. "도착 후"는 맞닿은 칸에서 해당 사물을 `view`까지 마친 상태다.

| # | 입력 (표본) | 기대 결과 |
|---|---|---|
| 1 | 시작 직후 `move` `C4` 후 `view` `desk@C4` | `move` 뒤에는 `npc_dialogue` 없음, `newly_opened`는 `["desk@C4"]`, `puzzle`은 `null`. `view` 뒤에 `npc_dialogue`. `puzzle.attempts_left`는 5, `hints`는 `[]`, `images`는 `desk_front.jpg`, 1번 그림 순서 |
| 2 | `move` `E5` (D4의 대각선) 후 `view` `desk@C4` | `desk@C4` 열림, 도착 |
| 3 | `move` `F4` (D4에서 2칸) | `desk@C4` 열리지 않음, `npc_dialogue` 없음 |
| 4 | `move` `c4` / `I1` / `1F-C4` | 각각 6번 / 7번 / 7번 거절. 위치 그대로 |
| 5 | 시작 직후 `view` `shelf@F2` / `sofa@A1` | 각각 9번 / 8번 거절 |
| 6 | 시작 직후 `answer` `apple` | 10번 거절. 시도로 세지 않음 |
| 7 | `move` `F2` 후 `view` `shelf@F2` (1번 진행 중) | `npc_dialogue` 없음. `puzzle: null`. 사물 텍스트를 반환하고 `images`는 `shelf_front.jpg`만. 다음 관측의 `images`는 `[]` |
| 8 | 도착 후 첫 `answer` 값 `" Apple "` | `attempt: 1`, `correct: true`, 로그 `value`는 `" Apple "`. `puzzle_ended`는 `solved_by_dialogue`, `attempts_used: 1` |
| 9 | 도착 후 `reason` 없는 `answer` | 12번 거절. `attempts_left`는 5 그대로 |
| 10 | 도착 후 오답 1번 | `answer_submitted` 뒤 `hint_revealed`(`level: 1`). `hints`는 `[{"level": 1, "text": "가상 힌트 1"}]`, `attempts_left`는 4 |
| 11 | 오답 1번 후 정답 | `puzzle_ended`는 `solved_with_hint`, `attempts_used: 2` |
| 12 | 1번 퍼즐 오답 5번 | 마지막 `attempt: 5` 뒤 `puzzle_ended`(`failed`, `attempts_used: 5`). 다음 관측의 `last_result.answer`는 `"apple"`, `instruction`은 `"F2의 선반으로 가라"`, `puzzle`은 `null`. 6번째 시도 없음 |
| 13 | 2번 퍼즐 오답 5번 (`max_attempts` 없는 표본) | `puzzle_ended`(`failed`) 뒤 `end`(`completed`) |
| 14 | §8의 완주 예시 그대로 재생 | `to_log`의 `events`가 §8 예시와 같음 |
| 15 | `"not json"` 50번 | `rejected` 50개 뒤 `t: 51`의 `end`(`action_limit`). `puzzle_ended` 없음 |
| 16 | `max_actions=6`으로 `move`, `view`, `answer`, `move`, `view`, `answer` 모두 성공 | 마지막이 6번째 행동이어도 `end`(`completed`) |
| 17 | 첫 호출에 HTTP 400 | 재시도 없음. `end`(`api_error`), `t: 1`, 예외가 실행기 밖으로 나가지 않음 |
| 18 | 입력 dict를 복사해 둔 뒤 완주 | 입력이 바뀌지 않음. 파일의 `shelf@F2`가 `open`이어도 시작 때 `opened_object_ids`는 `[]` |
| 19 | 두 층 표본에서 `move` `C2` / `2F-AA3` | 7번 거절 / 성공 |
| 20 | `move` `E3` (D4와 F2 모두의 대각선), `view` `desk@C4` 후 정답 | 두 사물 열림. `puzzle_ended` 뒤에 `npc_dialogue` 없음, 다음 관측의 `puzzle`은 `null`. 이어서 이동 없이 `view` `shelf@F2`하면 `npc_dialogue`, `puzzle.number`는 2 |
| 21 | `start_cell`을 `B3`으로 바꾼 묶음 | 시작부터 `desk@C4`가 `open`, 이벤트 없음, 첫 관측의 `puzzle`은 `null`. `view` `desk@C4`하면 `t: 1`이 `view`, `t: 2`가 `npc_dialogue` |
| 22 | 힌트를 `level: 7`, `after_wrong: 2`로 바꾼 묶음 | 오답 1번에는 안 열림. 오답 2번 뒤 `hint_revealed`(`level: 7`) |
| 23 | 1번 진행 중 `move` `F2`로 2번 사물 `open` 후 `move` `C4`, `view` `desk@C4`, 정답. 이어서 `view` `shelf@F2` | 정답 뒤의 `view`는 위치가 떨어져 있어 사진만 반환하고 `npc_dialogue` 없음. 다시 `move` `F2` 후 `view` `shelf@F2`하면 남음 |
| 24 | `respond`에 HTTP 503 계속 | 요청 5번, 대기 `0.5, 1, 2, 4`초, 이후 `ModelAPIError` |
| 25 | 첫 응답 HTTP 429 + `Retry-After: 3`, 다음 응답 정상 | 요청 2번, 대기 `3`초, 출력 텍스트 반환 |
| 26 | `output`이 빈 목록인 HTTP 200 | `respond`는 `""` 반환. `submit`은 1번 거절 |
| 27 | 같은 `sha256`의 그림을 두 실행에서 사용 | `upload_file` 요청 1번 |
| 28 | 표본의 `brief` / `rooms`를 뺀 공간의 `brief` | `rooms`가 표본 값과 같음 / `rooms`는 `[]` |
| 29 | 도착 후 `view` `desk@C4`를 다시 실행 | `view`만 남고 `npc_dialogue`는 또 남지 않음. `images`는 `desk_front.jpg`, 1번 그림 순서 |

**노출 검사.** 위 모든 시나리오에서 `brief`와 `observe(...)["observation"]`을 직렬화해 다음을 확인한다.
- 키 `next_object_id`, `next_instruction`, `object_id`, `photos`, `path`, `sha256`, `contains_hint`, `after_wrong`, `npc`, `tone`, `on_wrong`, `on_correct`가 어디에도 없다.
- 키 `answer`는 `failed` 직후의 `last_result`에만 있다.
- 현재 퍼즐과 그 뒤 퍼즐의 `answer` 값과 `next_instruction` 값이, 퍼즐이 끝나기 전에는 문자열로 나타나지 않는다.
- 안 열린 힌트의 `text`와 현재 퍼즐이 아닌 퍼즐의 `dialogue` 문장이 나타나지 않는다.

**로그 검사.** 모든 `to_log` 결과가 `log.schema.json`을 통과하고, `t`가 1부터 1씩 늘며, 마지막 이벤트만 `end`다.

## 상태 전이표

퍼즐 상태:

| 현재 | 사건 | 다음 | 로그 이벤트 |
|---|---|---|---|
| 잠김 | 실행 시작(1번 퍼즐), 또는 앞 퍼즐이 해결이나 실패로 끝남 | 잠금 해제 | 없음 |
| 잠금 해제 | 사물과 맞닿은 위치에서 `view` (도착) | 풀이 중 | `view`, `npc_dialogue` |
| 풀이 중 | 정답 | 해결 | `answer_submitted`, `puzzle_ended` |
| 풀이 중 | 오답, 시도 < 5 | 풀이 중 (조건에 맞으면 힌트 열림) | `answer_submitted`, 조건에 맞으면 `hint_revealed` |
| 풀이 중 | 오답, 시도 = 5 | 실패 (정답 공개) | `answer_submitted`, `puzzle_ended`(`failed`) |

거절된 행동은 어느 상태에서든 상태를 바꾸지 않고 `rejected`만 남긴다.

실행 상태:

| 현재 | 사건 | 다음 | 로그 이벤트 |
|---|---|---|---|
| 시작 전 | `new_game` 성공 | 진행 중 | 없음 |
| 시작 전 | `GameSetupError`, `MissingKeyError`, 그림 SHA-256 불일치, 사물 사진 파일 없음 | 시작 안 함 | 로그 파일 없음 |
| 진행 중 | `submit`, 남은 퍼즐 있음, 행동 수 < `max_actions` | 진행 중 | 행동 이벤트 또는 `rejected` |
| 진행 중 | `submit`, 마지막 퍼즐이 끝남 (행동 수와 무관) | 완주 | `answer_submitted`, `puzzle_ended`, `end`(`completed`) |
| 진행 중 | `submit`, 남은 퍼즐 있음, 행동 수 = `max_actions` | 상한 종료 | 행동 이벤트 또는 `rejected`, `end`(`action_limit`) |
| 진행 중 | `abort` (`ModelAPIError`) | API 실패 종료 | `end`(`api_error`) |
| 완주, 상한 종료, API 실패 종료 | `to_log` | 그대로 | 없음. 로그를 저장한다 |
| 완주, 상한 종료, API 실패 종료 | `observe`, `submit`, `abort` | 그대로 | 없음. `GameStateError` |

상한 종료와 API 실패 종료 때 풀이 중이던 퍼즐은 `puzzle_ended` 없이 끊긴 퍼즐이 된다. 끊긴 실행을 이어 가지 않는다 (§7).

## 규칙

### 정답 판정, 힌트, 시도

인터페이스 계약을 따르며 여기서 다시 정의하지 않는다. 정답 판정과 시도는 §4.4, 힌트와 퍼즐 종료는 §2의 `submit` 처리 순서, 도착은 §4.3이 기준이다.

### 페르소나 생성

코드가 `random.Random(seed)`로 만든다. 게임 엔진에는 무작위성이 없으므로 생성은 실행기 앞에서 끝낸다.

| 속성 | 규칙 |
|---|---|
| `thinking` | 스키마의 3개 값을 5회씩 넣은 15칸을 섞어 배정한다 |
| `age` | 10~79의 정수를 균등하게 뽑는다 |
| `job` | `personas.py`의 목록에서 균등하게 뽑는다. 초기 목록은 학생, 개발 공부 중인 학생, 약사, 개발자, 교사, 간호사, 요리사, 회사원, 농부, 은퇴자다. 10대는 학생으로 고정한다 |
| `vocab` | `상`, `중`, `하`를 균등하게 뽑는다 |
| `name` | 넣지 않는다. 대표 페르소나 고정은 여유 항목이다 |

- 생성 결과는 `persona.schema.json`으로 검증한다.
- 실행마다 페르소나 전체와 `seed`를 로그에 남긴다. 같은 시드면 같은 목록이 나온다.
- 15회 기준은 `end.outcome`과 관계없이 모든 실행을 센다. 퍼즐별 집계 표본이 10개에 못 미치면 실행을 더 돌린다. 15회를 넘겨 더 돌릴 때는 3개 값을 1회씩 묶어 추가해 값별 표본을 맞춘다. 다시 돌릴 때도 새 `run_id`를 쓴다 (§7).
- 어휘 제한 등은 프롬프트로만 걸리므로 모델이 어길 수 있다. 보고서의 한계에 적는다 (spec §7.2).

### 점수

퍼즐별 점수는 그 퍼즐의 오답 수와 같다.

| `result` | 점수 |
|---|---|
| `solved_by_dialogue`, `solved_with_hint` | `attempts_used - 1` (0~4) |
| `failed` | 5 |

- 대화 속 단서는 문제의 일부이므로 점수에 반영하지 않는다.
- `contains_hint`는 보고서에서 "에이전트가 `reason`에서 대화의 단서를 언급했는지" 분석하는 용도로만 쓴다.
- `puzzle_ended`가 없는 끊긴 퍼즐은 점수와 비율 집계에서 빼고, 건수만 보고서에 표시한다.

### 보고서 해석 기준

| 결과 | 해석 |
|---|---|
| 대화만으로 해결 (`solved_by_dialogue`) | 단서가 충분히 전달됨 |
| 힌트 후 해결 (`solved_with_hint`) | 대화만으로는 부족했음 |
| 실패 (`failed`) | 지식의 저주가 가장 강하게 의심됨 |

### 재연 검증

코드가 대화문에 정답이 그대로 들어 있지 않은지 검사한다. 대소문자를 무시하고, 정답 앞뒤에 영문자가 없을 때만 일치로 본다. `appear` 안의 `pear`는 잡지 않고 `pear를`은 잡는다. 정규식은 `(?<![a-z])` + 이스케이프한 정답 + `(?![a-z])`이며, 정답과 대화문을 모두 소문자로 바꿔 비교한다.

코드가 지시문에 사물의 위치가 적혀 있는지 검사한다 (M25). 아래 둘 중 하나가 지시문에 있으면 통과다.

- **칸 좌표:** 사물의 어느 칸이든 된다. 앞뒤에 영문자나 숫자가 없을 때만 일치로 본다. `C4의 책상`은 잡고 `AC4`, `C41` 안의 `C4`는 잡지 않는다. 정규식은 `(?<![A-Za-z0-9])` + 칸 좌표 + `(?![A-Za-z0-9])`다. 층이 2개 이상이면 `2F-C4`처럼 접두어까지 포함해 찾는다.
- **방 이름:** 사물의 칸이 범위 안에 있는 방의 `name`을 문자열 그대로 찾는다.

### 실제 퍼즐 데이터 옮기기

저작 형태가 스키마와 다르면 아래처럼 옮긴다.

| 저작 형태 | 스키마 |
|---|---|
| `puzzle_id`, `type` | 쓰지 않음. `number`, `object_id`로 표현 |
| `assets.npc_image` | 퍼즐에는 `npc` id, 이미지는 NPC 파일의 `image` |
| `assets.puzzle_image` | `image: { path, sha256 }` |
| `dialogue.intro` | `dialogue: [{ text, contains_hint }]` |
| `dialogue.stage_direction` | 쓰지 않음 |
| `dialogue.on_wrong`, `on_correct` | `on_wrong`, `on_correct` (화면 전용) |
| `nodes`, `decoys`, `chain_rule` | **쓰지 않음.** 정답 풀이가 드러나므로 데이터에 넣지 않음 |
| `answer: { value, normalize, accept }` | `answer`(소문자 문자열), `answer_letter_count` |
| `hints[].trigger` | `after_wrong` 정수 |
| `reward.next_location` | `next_instruction`, `next_object_id` |

- `question`은 오프라인 원문을 그대로 쓴다. 저작 데이터에 없으면 지어내지 않고 창작자에게 묻는다.
- `contains_hint`는 스키마의 필수 필드다. 저작 데이터로 알 수 없으면 추측하지 않고 창작자에게 묻는다.
- 계약의 정답은 1개다 (§4.4). `accept`에 다른 답이 있으면 옮기기 전에 창작자에게 묻는다.
- `on_correct`의 `{NEXT_LOCATION}`은 치환하지 않는다. 옮길 때 실제 방 이름으로 바꿔 대사에 직접 쓴다.

## 보고서 분담

원칙은 수치와 판정은 코드, 자유 문장의 해석만 Muse다. 코드 결과만으로도 보고서가 성립해야 하므로, Muse 호출이 실패하면 해당 칸을 "분석 없음"으로 표시하고 나머지를 생성한다.

**코드가 맡는다 (같은 로그면 같은 결과)**

| spec §10 항목 | 내용 |
|---|---|
| 1. 난이도 표 | 퍼즐별 점수(규칙 절), 평균 점수, 실패율, 힌트 사용률, 집계 표본 수, 끊긴 건수 |
| 2. 갈리는 문제 | 판정과 속성 비교. 첫 시도 해결(`attempts_used`가 1이고 `failed`가 아님) 비율과 `failed` 비율이 모두 30% 이상이면 표시한다. 분모는 그 퍼즐의 `puzzle_ended` 수다. 두 무리의 나이대, 어휘, 사고 방식별 건수를 표로 만든다 |
| 3. 오답과 이유 | 오답 집계. `strip().lower()` 기준 상위 오답과 빈도, 해당 `reason` 원문 수집 |
| 4. 오프라인 사례 | `baseline`의 `observed`, `note`와 에이전트 수치를 퍼즐별로 나란히 표시. 수치 비교와 일치 판정은 하지 않는다 |
| 5. 지도 화면 | 뷰어가 읽을 `report.json` (여유 항목) |
| 6. 한계 | 고정 문구와 실제 표본 수 |

**Muse가 맡는다 (점수와 비율에 넣지 않는다)**

| 작업 | 입력 | 출력 | 코드 검증 |
|---|---|---|---|
| 오답 이유 요약 | 퍼즐별 상위 오답과 `reason` 원문 | 오답별 한 줄 요약, 대표 `reason` | 대표 `reason`이 입력 원문과 정확히 일치하는지 확인. 어긋나면 이유를 돌려주고 다시 요청하며, 끝내 어긋나면 "분석 없음" |
| `reason`의 단서 언급 판정 | `contains_hint`가 `true`인 문장과 `reason` 원문 | `reason`별 언급 여부 | 출력이 입력과 같은 수의 참/거짓인지 확인 |

Muse 출력에는 모델 판단임을 표시한다. Muse에는 위 입력만 보내며 페르소나 속성은 보내지 않는다.

## 여유 기능

게임 엔진과 로그 형식을 바꾸지 않는다. 범위는 `docs/acceptance.md`의 여유 항목이 정한다.

**저주 지수.** 제작자가 첫 실행 전에 `data/<set>/prediction.json`에 퍼즐별 예상 점수(0~5)를 적는다. 예: `{ "1": 1, "2": 3 }`. 보고서가 퍼즐별로 예상 점수, 실제 평균 점수, 그 차이(실제 − 예상)를 코드로 계산해 표시한다. 파일이 없으면 이 항목을 뺀다.

**수정과 재검증.** `python -m realtosim.revise <set> <number>`로 실행한다.

1. Muse가 퍼즐의 대화, 힌트, 상위 오답과 `reason`을 읽고 대화나 힌트의 수정안을 제안한다.
2. 제작자가 고른 수정안으로, 그 퍼즐 1개만 담은 새 묶음 `data/<set>-v2-<number>/`를 만든다. `number`는 1, `next_instruction`과 `next_object_id`는 `null`이다. `baseline.json`은 두지 않으며 `validate`의 M13, M14, 오프라인 사례 항목을 적용하지 않는다.
3. `validate`와 오라클 실행을 통과하면 새 시드로 실행하고, 원래 결과와 전후를 나란히 보여 준다. 실행 횟수는 크레딧에 맞춰 정하고 표본 수를 함께 표시한다.

- 기준은 쉬워졌는지가 아니라 예상 점수에 가까워졌는지다. 쉬워지는 것을 기준으로 삼으면 답을 대놓고 알려 주는 퍼즐로 수렴한다.
- 재실행에는 앞 퍼즐의 기억이 없고 표본도 적다. "개선을 증명했다"가 아니라 "이 사례에서 이렇게 달라졌다"로 보고한다.

**사진에서 퍼즐 초안.** `space_builder.py`에 둔다. SAM과 Muse가 사진 1장에서 찾은 사물(O4)로 Muse가 퍼즐 초안 1개를 만들고, 그 사물 사진을 퍼즐 그림으로 쓴다. 제작자가 승인한 초안만 `data/`에 저장하며, 이후에는 일반 퍼즐과 똑같이 `validate`, 오라클, 에이전트 실행을 거친다. 초안의 품질은 아직 확인하지 않았으므로 실제 사진으로 먼저 시험한다.

## 미결 TODO

| 항목 | 상태 | 정할 때 |
|---|---|---|
| 프론트 스택 | 지도 렌더링(SVG/캔버스), 프레임워크 여부. Pannellum은 불필요할 수 있음 | 뷰어 착수 시 |
| 가구 크기 추정 방식 | SAM 박스 비율 vs Muse 추정. 둘 다 시도 후 결정 | SAM 제안 착수 시 (여유 항목) |
| 주문 의식의 주체 | 사람 플레이가 범위 밖이므로 누가 주문을 하는지 정리 필요. Babel fish 역할도 함께 재정의 | 주문 연출 착수 시 (여유 항목) |
| 마감과 제출물 | 2026-11-04의 정확한 시각, 데모 영상, 배포 여부. 창작자가 해커톤 규정을 확인한 뒤 알려 줌 | 구현을 마친 뒤 |
| SAM 호출 경로 | 가능하면 Modal 위 SAM 3.1을 쓴다. §6.1의 Model API `sam-3.1` 호출을 대안으로 남길지 함께 정한다 | SAM 제안 착수 시 (여유 항목) |

**Muse Code 지침 파일 (계획).** Muse Code 문서(`dev.meta.ai/docs/muse-code/configuration`)에 따르면 시작할 때 작업 폴더에서 가장 가까운 `.git`까지 올라가며 `AGENTS.md`를 자동으로 읽는다. 구현을 시작할 때 저장소 루트에 `AGENTS.md`를 두고 아래 내용을 적는다.

- 읽을 문서: `docs/spec.md`, `docs/design.md`, `docs/acceptance.md`, `docs/schemas/`
- 지켜야 할 규칙: 모델 호출은 `model_api`로만 한다, 인터페이스 계약과 스키마가 기준
- Muse Code는 저장소 루트에서 시작한다. 프로젝트 지침은 작업 폴더를 신뢰한 뒤에만 적용되므로 처음 실행할 때 신뢰를 허용한다.
