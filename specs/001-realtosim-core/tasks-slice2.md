# Tasks: 다음 슬라이스 — 검증·오라클·에이전트·보고서 (갈래 1 완성)

**Input**: `docs/TRD.md` §2~§8·§10, `docs/schemas/*.schema.json`, `data/drunkard-set/` 실데이터.
**Prerequisites**: 엔진 슬라이스 완료 (`realtosim/game_engine.py`, 게이트 34/34). 본 파일은 `tasks.md`(엔진, 전체 [X])의 다음 단계다.
**실행 순서**: US1 → US2 → US3 → US4. US3이 장시간이므로 먼저 돌리고 US4를 붙인다.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

- Library: `realtosim/`, `python -m realtosim.<모듈>` (TRD §2).
- Data/logs/reports: `data/<set>/`, `logs/<set>/`, `reports/<set>/`.
- Tests: `tests/test_<모듈>.py`, 게이트 `.venv/bin/python -m unittest discover tests -v`.
- 금지: `docs/schemas/`·`docs/` 수정 없음, `jsonschema` 외 의존성 없음 (httpx는 시스템에만 있어 `model_api`에서 지연 import), 비밀 기록 없음, 커밋 없음.

## Phase 1: US1 — 검증기와 재연 보고서 (P1)

**Goal**: `data/drunkard-set/` 실데이터를 스키마+M1~M9·M25로 검사하고 `reports/drunkard-set/replica.md` 남기기.
**Independent Test**: `python -m realtosim.validate drunkard-set` 종료코드 0 + replica.md에 통과/수정/확인 항목.

- [X] T201 [US1] `realtosim/settings.py`에 `model()`, `sam_model()`, `base_url()`, `api_key()` (환경 변수 `MODEL_API_MODEL` 기본 `muse-spark-1.3`, `SAM_MODEL` 기본 `sam-3.1`, `MODEL_API_BASE_URL` 기본 `https://api.meta.ai/v1`, `MODEL_API_KEY` 없을 때 None)
- [X] T202 [US1] `realtosim/validate.py` 구현: 4종 JSON 로드 + 스키마 검사(M1·M2), 연결 검사(M4: object/next 존재·사슬, 마지막만 null), 격자/겹침/사진 검사(M5), 정답 정규화·글자수(M6), 대화문 정답 노출(M7), 그림 SHA-256(M8), 지시문 좌표/방 이름 포함(M25). 실패 이유 리스트 반환, `GameSetupError`/`GameStateError` 사용 안 함
- [X] T203 [US1] `realtosim/validate.py` CLI (`python -m realtosim.validate <set>`): `reports/<set>/replica.md`에 통과/수정/확인 항목 기록(M9), 통과 0/실패 1 종료코드
- [X] T204 [US1] `tests/test_validate.py`: drunkard-set 통과, 깨진 사본(글자수 불일치·연결 끊김) 실패 사유 확인

## Phase 2: US2 — 오라클 완주 증명 (P1)

**Goal**: 정답 주행으로 전 퍼즐 `solved_by_dialogue` + `end(completed)` 증명 (M12).
**Independent Test**: `python -m realtosim.oracle drunkard-set` 후 로그의 전 `puzzle_ended`가 `solved_by_dialogue`.

- [X] T205 [US2] `realtosim/oracle.py` 구현: 퍼즐 순서대로 사물 인접 칸 이동 → `view` → 정답 `answer` 제출, `logs/<set>/oracle/r0.json` (`run_id` r0, `model` oracle) 저장
- [X] T206 [US2] `tests/test_oracle.py`: drunkard-set 오라클 로그가 `log.schema.json` 통과 + 완주 단언

## Phase 3: US3 — 모델 API·페르소나·15회 실행 (P2, 장시간)

**Goal**: 15회 로그 + 사고방식 3값 각 5회 이상, 전부 `log.schema.json` (M13~M17).
**Independent Test**: `logs/drunkard-set/r*.json` 15개, `puzzle_ended` 10개 이상, 스키마 통과.

- [X] T207 [US3] `realtosim/model_api.py` 구현 (httpx 지연 import): `MissingKeyError`·`ModelAPIError`, `make_client()`, `respond()` (`output[type=message]/content[type=output_text]` 수집, 없으면 `""`), `upload_file()` (multipart `file`+`purpose=user_data` → `id`), 재시도(연결/타임아웃/408·409·429·5xx만, `MAX_RETRIES=4`, `TIMEOUT_SECONDS=180`, `Retry-After` 0초 초과 120초 이하 우선 아니면 `min(0.5*2^n,8)`초), 그 외 4xx 즉시 실패. `sleep` 주입 가능
- [X] T208 [US3] `tests/test_model_api.py` (FakeClient, 네트워크 없음): #17 400 즉시 실패 1요청, #24 503 5요청 대기 `[0.5,1,2,4]`, #25 429+Retry-After:3 대기 `[3]` 후 성공, #26 빈 output → `""`, 키 없음 → `MissingKeyError`
- [X] T209 [US3] `realtosim/personas.py` 구현: `random.Random(seed)` 앞에서 15명 확정, `thinking` 3값×5 섞음, `age` 10~79, 10대 학생 고정·나머지 직업 목록 균등, `vocab` 상/중/하 균등, `name` 없음, `persona.schema.json` 검증
- [X] T210 [US3] `tests/test_personas.py`: 분포(3값 각 5)·스키마·10대 규칙·시드 재현
- [X] T211 [US3] `realtosim/run_agents.py` 구현: TRD §4 시스템 프롬프트 원문, 매 차례 `observe` → `json.dumps(ensure_ascii=False)` + 마지막 메시지에 퍼즐그림/직전사진 file_id, `submit` 반복, `ModelAPIError` 즉시 `abort` (`end(api_error)`), 이미지 사전 준비(SHA 불일치·파일 없음 시작 금지)·`workspace/cache/files.json` 캐시(동일 sha 재사용 1회 업로드), 새 `run_id` (`r01`…; 끊김 잇지 않음), `logs/<set>/` 저장. 핵심 루프는 `respond_fn` 주입으로 테스트 가능
- [X] T212 [US3] `tests/test_run_agents.py` (FakeModel, 네트워크 없음): 완주 로그 `log.schema.json` 통과, API 실패 시 `abort` → `end(api_error)`, 동일 sha 1회 업로드(#27)
- [X] T213 [US3] 실실행: `python -m realtosim.run_agents drunkard-set --runs 15 --seed <S>` → `logs/drunkard-set/r*.json` 5개 (2026-11-03 목표 15→5회 하향. r01~r03 보존 + `--runs 2 --start 3 --seed 0` append)

## Phase 4: US4 — 난이도 보고서 (P2)

**Goal**: `reports/drunkard-set/report.md` (+`report.json`)에 난이도 표·갈리는 문제·오답·오프라인·한계 (M18~M24).
**Independent Test**: 보고서에 5종 항목 존재, 수치가 로그 재계산과 일치.

- [X] T214 [US4] `realtosim/report.py` 구현: 퍼즐별 점수(해결 오답수 0~4/실패 5)·평균·실패율·힌트사용률, 끊김 제외+건수, 갈리는 문제(첫시도 해결·실패 모두 30% 이상, 분모 `puzzle_ended`), 상위 오답+대표 reason, 베이스라인 나란히(비교·일치판정 없음), 한계 문구(표본수·프롬프트·사진오인)+재연통과 문구, Muse 실패 시 수치 유지+`분석 없음` 표시. CLI `python -m realtosim.report <set>`
- [X] T215 [US4] `tests/test_report.py`: 고정 로그 픽스처로 집계 수치·갈림 판정 단언

## Phase 5: Polish

- [X] T216 게이트 `.venv/bin/python -m unittest discover tests -v` 초록 + `git status`로 변경 범위(`realtosim/`·`tests/`·`logs/`·`reports/`·`specs/`·`workspace/cache/` 제외 확인: 캐시는 git 제외 대상) 확인
- [X] T217 `docs/schemas/`·`docs/` 무변경, 비밀·노출금지 필드 없음 확인

## Dependencies

- T202→T203→T204, T205→T206, T207→T208, T209→T210, T207+T209→T211→T212→T213, T213→T214→T215 (보고서는 실로그 필요; 키 없으면 T212 Fake 로그가 아니라 중단·보고서에 `분석 없음`이 아니라 실행 자체를 미완으로 기록)
- US1·US2는 모델 없이 먼저, US3 실실행(T213)이 최장 → 먼저 착수
