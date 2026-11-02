# 워크숍에서 해커톤으로 가져갈 것

Nov 2, 2026 · @수목원

## 개요

마감(11/4)이 가까우니 모델 연결 코드, SAM 3.1 사용법, 문서 캐시 세 가지를 먼저 가져가고 나머지는 시간이 남을 때 넣는 것을 권합니다. 기준은 "현실 공간의 사진과 대략적인 평면도로 플레이 가능한 시뮬레이션을 만들어, 공간형 퍼즐을 설치 전에 테스트하는 도구"라는 기획입니다. 가져올 대상은 `meta-models/legal-agent-workshop` 저장소의 `agent/` 폴더입니다.

## 바로 가져다 쓸 것

아래 세 가지는 코드를 거의 그대로 복사해 쓸 수 있습니다.

| 가져올 것 | 위치 (`agent/` 기준) | 해커톤에서의 쓰임 |
| --- | --- | --- |
| 모델 연결 코드 | `agent_kit/client.py`, `settings.py` | OpenAI SDK의 주소만 `https://api.meta.ai/v1`로 바꾼 약 30줄. 모델은 `muse-spark-1.3`, 호출은 `client.responses.create(...)`. `.env` 패턴과 `.gitignore`의 `.env` 항목도 함께 가져가면 키가 깃에 올라가지 않음 |
| SAM 3.1 사용 노하우 | `agent_kit/tools/check_signatures.py` 아래쪽 주석 | 방 사진에서 문, 가구, 벽의 위치(박스)를 뽑아 시뮬레이션 물체로 변환 |
| 이미지/PDF 읽기와 캐시 | `agent_kit/document_text.py` | Files API로 올려 모델이 읽게 하고, 결과를 파일의 SHA-256 해시로 저장해 같은 사진을 다시 처리하지 않음. 크레딧 절약 |

SAM을 쓸 때 알아둘 점입니다.

- 결과가 `<|box;x1=..;y1=..;x2=..;y2=..|>` 같은 특수 토큰 텍스트로 나오며, 이를 파싱하는 정규식(`BOX`)이 이미 있습니다.
- 글자 검색어에 따라 결과가 갈립니다. "signature"는 스캔 페이지에서 잡히지 않고 "ink scribble"이 잡혔으므로, "door", "chair", "table" 같은 검색어도 실제 사진으로 직접 시험해야 합니다.
- 이 파일의 호출 부분은 아직 플레이스홀더입니다. 완성된 호출 코드는 `solutions/02_session2/`에 있을 수 있으니 확인이 필요합니다.

## 아이디어로 가져갈 것

가장 큰 가치는 코드가 아니라 "AI가 만든 결과를 AI 밖의 코드로 검증한다"는 설계입니다. 심사에서 강점이 될 부분입니다.

1. **코드 밖 검증 구조.** 워크숍에서는 모델이 인용한 문장이 실제 문서에 없으면 코드가 거절하고, 이유를 알려 최대 3번 다시 시도시킵니다. 기획에 옮기면 생성된 시뮬레이션이 평면도 치수 안에 들어오는지, 물체가 겹치지 않는지, 문까지 이동할 수 있는지를 코드가 검사하고, 실패하면 이유를 모델에 돌려주어 다시 만들게 합니다. "설치 전에 믿고 테스트할 수 있다"는 메시지에 근거가 생깁니다.
2. **모를 때 사람에게 묻고 이어가기** (`agent_kit/progress.py`, `ESCALATION_RULES.md`). 치수가 불분명하거나 사진에서 가려진 곳은 추측하지 않고 멈춰서 사용자에게 묻고, 같은 작업을 이어갑니다. 시간이 남을 때 넣을 만합니다.
3. **에이전트 루프** (`legal_agent/loop.py`, 92줄). 모델이 도구 하나를 고르고, 실행하고, 결과를 돌려주고, 저장하는 반복입니다. 도구를 `analyze_photo`, `segment_objects`, `build_scene`, `validate_scene`처럼 바꿔 끼우면 됩니다. 다만 순서가 고정된 "사진 → 분석 → 생성" 파이프라인이라면 에이전트 루프 없이 함수를 이어 붙이는 쪽이 더 빠릅니다.

## 개발 편의

개발 중 크레딧을 아끼고 데모를 만드는 데 쓸 수 있는 도구가 두 가지 있습니다.

- **가짜 모델 API** (`tests/fake_model.py`). 실제 API를 부르지 않고 테스트할 수 있어 크레딧을 쓰지 않습니다.
- **Agent Console** (`ui/`, `python3 ui/ui.py` 후 http://127.0.0.1:8765). 실행 과정을 실시간으로 보여 줍니다. 법률 데이터 형식에 맞춰져 있어 그대로 쓰기는 어렵지만, 데모 영상 구성의 참고가 됩니다.

## 주의사항

복사해 쓰기 전에 확인해야 할 것이 세 가지 있습니다.

- **법률 사건 자료는 가져갈 필요가 없습니다.** `cases/`, `ground_truth/`, `world/`는 해커톤 기획과 무관합니다.
- **저장소 루트에 LICENSE 파일이 보이지 않습니다.** 코드를 그대로 복사한다면 해커톤 규정에서 기존 코드 사용 조건을 확인하세요.
- **출처를 밝혀 두는 것이 안전합니다.** README에 워크숍 저장소(`meta-models/legal-agent-workshop`)에서 가져온 부분을 적어 두세요.

## 가져올 파일 목록

- [x] agent/.env.example
- [x] agent/.gitignore
- [x] agent/agent_kit/__init__.py
- [x] agent/agent_kit/client.py
- [x] agent/agent_kit/settings.py
- [x] agent/agent_kit/tools/check_signatures.py
- [x] agent/agent_kit/document_text.py
- [x] agent/agent_kit/progress.py
- [x] agent/ESCALATION_RULES.md
- [x] agent/legal_agent/loop.py
- [x] agent/tests/fake_model.py

