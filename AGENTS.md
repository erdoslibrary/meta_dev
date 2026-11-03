# AGENTS.md — Real-to-Sim 공간 퍼즐 스튜디오

## 읽을 문서 (위에서 아래 순으로 우선)

- `docs/PRD.md` — WHAT/WHY, 제품 기준.
- `docs/TRD.md` §3~§10 — HOW, 동작 계약 기준.
- `docs/schemas/*.schema.json` — 데이터 형식 기준.
- `requirement.md` — speckit-specify 입력.
- `.specify/memory/constitution.md` (v1.0.0) — 테스트·스택·보안 원칙.
- TRD §11 미결 사항은 결정하지 않는다.

## 디렉토리 규약

- 구현: `realtosim/` 패키지 (`python -m realtosim.<모듈>`).
- 데이터·로그·보고서: `data/<set>/`, `logs/<set>/`, `reports/<set>/`. 별도 서버 없음.
- 테스트: `tests/`.

## 테스트 게이트

- `python -m unittest discover tests -v` 통과 없이 완료 선언 금지.
- TRD §4 거절 문구 12종은 문자열 정확 일치.

## 금지 사항

- `jsonschema` 외 새 패키지 추가 금지.
- 스키마·docs 수정 금지.
- API 키 등 비밀을 코드·로그·보고서에 기록 금지.
- 커밋 금지.

## 모순·불분명 시

- 추측하지 말고 멈춰서 질문한다.
- `/speckit-implement` 전 tasks.md 범위를 요청과 대조하고, 요청이 제외·다음 슬라이스로 적혀 있으면 tasks 재생성 여부를 먼저 묻는다.
