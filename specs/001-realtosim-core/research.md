# Research: Real-to-Sim 핵심 검증 흐름 (엔진 슬라이스)

**Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

## R-1: 엔진 상태 표현 방식

- **Decision**: 단일 `Game` 객체가 위치, 사물별 `locked`/`open`, 현재 퍼즐 번호, 퍼즐별 오답 수·개방 여부·공개 힌트, 행동 수, `t` 카운터 포함 이벤트 목록을 들고, `new_game`에서 입력을 깊은 복사한다.
- **Rationale**: TRD §3이 엔진을 순수 상태 머신(무작위성 없음)으로 못 박고, §10 #18이 입력 불변을 요구한다. 복사 한 번이면 두 조건을 동시에 만족한다.
- **Alternatives considered**: 불변(immutable) 스냅샷 체인 — 거절 포함 매 행동 복사 비용이 들고 TRD가 요구하지 않아 기각.

## R-2: 칸·인접 판정

- **Decision**: 스키마 `cellRef`/`cellRange` 패턴으로 파싱·검증한다. 1층 묶음은 접두어 없는 칸만, 복층 묶음은 접두어 있는 칸만 유효하다. 인접은 같은 층 체비셰프 `max(|열차이|,|행차이|) <= 1`, 한 행동에 격자 안 어디든 이동 가능(벽·거리 검사 없음).
- **Rationale**: TRD §4 "이동과 도착"과 §10 #2~#4·#19의 그대로 옮김이다.
- **Alternatives considered**: 없음. TRD가-closed form으로 정의한다.

## R-3: 개방·도착 순서

- **Decision**: `move`로 맞닿은 사물은 로그 없이 전부 `open`(사용자 확정). 현재 퍼즐 사물에 맞닿아 `view`하면(도착) `view` + `npc_dialogue`를 남기고 퍼즐이 열린다. 도착 중복 `view`는 `view`만 기록하고 `npc_dialogue`는 반복하지 않는다(사용자 확정). 현재 퍼즐이 아닌 열린 사물의 `view`는 `view`만 남기고 대화·퍼즐 개방 없음(#7).
- **Rationale**: TRD §3 핵심 처리 순서 + §4 도착 정의 + 사용자 확정 2건.
- **Alternatives considered**: 중복 `view`마다 대화 반복 — #29 취지(미반복)에 어긋나 기각.

## R-4: 제출 파이프라인과 종료

- **Decision**: 거절 1~12번을 순서대로 검사하고 문구를 그대로 쓴다. 정답 판정은 양쪽 `strip().lower()` 비교, 로그에는 원문 유지. 오답5 = `puzzle_ended(failed)` 후 다음 퍼즐(정답 1회 노출). 상한 도달 = `end(action_limit)`, 단 상한 칸 완주는 `completed`. `abort`는 `end(api_error)`만 추가.
- **Rationale**: TRD §3~§4와 §10 #8~#16의 그대로 옮김이다.
- **Alternatives considered**: 없음.

## R-5: 관측 노출 위생

- **Decision**: `brief`·`observe`의 허용 필드만 반환하고, 금지 필드(TRD §4 목록)는 절대 포함하지 않는다. `answer`는 `failed` 직후 `last_result.answer`로만 1회 노출. 둘 다 `json.dumps(..., ensure_ascii=False)` 직렬화.
- **Rationale**: 헌법 III(노출 금지)과 TRD §4의 그대로 옮김이다.
- **Alternatives considered**: 없음.

## R-6: #20~#23 범위 (미해소 → 표본 재생 확인에 그침)

- **Decision**: #20~#23은 별도 단언을 추가하지 않고, 유효 표본을 불러 끝까지 재생되는지만 확인한다.
- **Rationale**: TRD 문구가 "표본으로 확인"에 그치고, 제안 단언에 대한 사용자 답변이 "None of the above"였다. 추측 단언을 넣지 않는다(AGENTS.md).
- **Alternatives considered**: 제안 단언 채택 — 사용자가 기각했으므로 제외. 사용자 별도 정의 — 제공되지 않았으므로 tasks 단계로 이월.

## R-7: #28 기본값 (사용자 확정)

- **Decision**: `rooms` 생략 → 빈 목록, `start_instruction` 생략 → 없음, `max_attempts` 기본값 5.
- **Rationale**: 사용자 확정 답변 + 스키마 선택 필드 정의.
- **Alternatives considered**: 없음.
