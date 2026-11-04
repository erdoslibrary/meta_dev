"""Difficulty report from run logs (TRD §8, M18-M24).

Usage: python -m realtosim.report <set> [--data data --logs logs --reports reports]
Always writes reports/<set>/report.md + report.json. Code owns every number;
free prose from the model is marked 분석 없음 when unavailable (FR-12).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from realtosim import model_api, settings
from realtosim.validate import load_json


def load_logs(logs_dir):
    logs = []
    for path in sorted(Path(logs_dir).glob("r[0-9]*.json")):
        logs.append(load_json(path))
    return logs


def aggregate(logs, puzzle_set):
    """Per-puzzle numbers. Interrupted runs contribute no puzzle_ended."""
    numbers = [p["number"] for p in puzzle_set.get("puzzles", [])]
    ended = {n: [] for n in numbers}
    wrongs = {n: [] for n in numbers}
    for log in logs:
        for e in log.get("events", []):
            if e.get("type") == "puzzle_ended" and e.get("puzzle") in ended:
                ended[e["puzzle"]].append(e)
            if e.get("type") == "answer_submitted" and not e.get("correct") \
                    and e.get("puzzle") in wrongs:
                wrongs[e["puzzle"]].append(e)
    rows = {}
    for n in numbers:
        evs = ended[n]
        if not evs:
            rows[n] = {"ended": 0}
            continue
        scores = [(e["attempts_used"] - 1
                   if e["result"] != "failed" else 5)
                  for e in evs]
        failed = sum(1 for e in evs if e["result"] == "failed")
        hinted = sum(1 for e in evs if e["result"] == "solved_with_hint")
        first = sum(1 for e in evs if e["result"] != "failed"
                    and e["attempts_used"] == 1)
        top = Counter((e.get("value", ""), e.get("reason", ""))
                      for e in wrongs[n]).most_common(3)
        rows[n] = {
            "ended": len(evs),
            "avg_score": sum(scores) / len(scores),
            "fail_rate": failed / len(evs),
            "hint_rate": hinted / len(evs),
            "first_try_rate": first / len(evs),
            "controversial": (first / len(evs) >= 0.3
                              and failed / len(evs) >= 0.3),
            "top_wrongs": [{"value": v, "reason": r, "count": c}
                           for (v, r), c in top],
        }
    interrupted = sum(1 for log in logs
                      if not log.get("events")
                      or log["events"][-1].get("outcome") != "completed")
    return {"runs": len(logs), "interrupted": interrupted, "puzzles": rows}


def analyze_with_model(client, wrongs):
    """One-line reason summaries. Returns None when unavailable (FR-12)."""
    if client is None:
        return None
    try:
        lines = [f"{w['value']} :: {w.get('reason', '')}" for w in wrongs]
        text = model_api.respond(
            client, settings.model(),
            "오답과 이유를 보고 퍼즐별 상위 오답 한 줄 요약을 번호별로 돌려준다. "
            "원문을 그대로 인용한다.",
            [{"text": "\n".join(lines), "images": []}])
    except model_api.ModelAPIError:
        return None
    for w in wrongs:
        if w["value"] and w["value"] not in text:
            return None
    return text if text else None


def replica_verdict(reports_dir):
    replica = Path(reports_dir) / "replica.md"
    if not replica.is_file():
        return "재연 보고서 없음"
    for line in replica.read_text(encoding="utf-8").splitlines():
        if line.startswith("판정:"):
            return line.strip()
    return "판정不明"


def render(set_id, puzzle_set, baseline, agg, verdict, analysis):
    puzzles = {p["number"]: p for p in puzzle_set.get("puzzles", [])}
    obs = {o["puzzle"]: o for o in baseline.get("observations", [])}
    lines = [f"# 난이도 보고서 — {set_id}", "",
             f"- 실행 {agg['runs']}회 (끊김 {agg['interrupted']}회)",
             f"- 재연 검증: {verdict}", "",
             "## 난이도 표", "",
             "| 퍼즐 | 종료 | 평균 점수 | 실패율 | 힌트 사용률 | 첫시도 해결율 |",
             "|---|---|---|---|---|---|"]
    for n in sorted(agg["puzzles"]):
        r = agg["puzzles"][n]
        if not r["ended"]:
            lines.append(f"| {n} | 0 | 표본 없음 | - | - | - |")
            continue
        lines.append(
            f"| {n} | {r['ended']} | {r['avg_score']:.2f} | "
            f"{r['fail_rate']:.0%} | {r['hint_rate']:.0%} | "
            f"{r['first_try_rate']:.0%} |")
    lines += ["", "## 갈리는 문제", ""]
    hot = [n for n, r in agg["puzzles"].items()
           if r.get("ended") and r["controversial"]]
    lines.append("없음" if not hot else "")
    for n in hot:
        lines.append(f"- {n}번: 첫시도 해결과 실패가 모두 30% 이상")
    lines += ["", "## 상위 오답과 이유", ""]
    any_wrong = False
    for n in sorted(agg["puzzles"]):
        r = agg["puzzles"][n]
        for w in r.get("top_wrongs", []):
            any_wrong = True
            lines.append(f"- {n}번 {w['value']!r} {w['count']}회: {w['reason']}")
    if not any_wrong:
        lines.append("오답 없음" if agg["runs"] else "실행 로그 없음")
    lines += ["", "## 모델 분석", "",
              analysis if analysis else "분석 없음 (모델 호출 실패 또는 키 없음)", "",
              "## 오프라인 관찰과 나란히", ""]
    for n in sorted(agg["puzzles"]):
        o = obs.get(n, {})
        r = agg["puzzles"][n]
        agent = (f"평균 {r['avg_score']:.2f}, 실패율 {r['fail_rate']:.0%}"
                 if r.get("ended") else "표본 없음")
        lines.append(f"- {n}번: 오프라인 {o.get('observed', '기록 없음')} "
                     f"({o.get('note', '')}) / 에이전트 {agent}")
    sample_note = (
        f"- 표본 수: 실행 {agg['runs']}회 (TRD §5·§7 기준 15회 충족)."
        if agg["runs"] >= 15
        else f"- 표본 수: 실행 {agg['runs']}회 (목표 5회, "
             "2026-11-03 15회에서 하향. spec/TRD 기준과 다름)."
    )
    lines += ["", "## 한계", "",
              sample_note,
              "- 프롬프트 한계: 시스템 프롬프트는 고정 문구이며 5회 소진 규칙·"
              "상한을 모델에 알리지 않는다.",
              "- 사진 오인 가능: view 사진·퍼즐 그림 해석은 모델에 의존한다.",
              "- 수치 비교·일치 판정은 하지 않는다.", ""]
    return "\n".join(lines)


def build(set_id, data_dir="data", logs_dir="logs", reports_dir="reports",
          client=None):
    data_dir, logs_dir = Path(data_dir), Path(logs_dir)
    reports = Path(reports_dir) / set_id
    puzzle_set = load_json(data_dir / set_id / "puzzle.json")
    baseline = load_json(data_dir / set_id / "baseline.json")
    logs = load_logs(logs_dir / set_id)
    agg = aggregate(logs, puzzle_set)
    wrongs = [{"value": w["value"], "reason": w.get("reason", "")}
              for log in logs for e in log.get("events", [])
              for w in [e] if e.get("type") == "answer_submitted"
              and not e.get("correct")]
    analysis = analyze_with_model(client, wrongs[:20])
    verdict = replica_verdict(reports)
    text = render(set_id, puzzle_set, baseline, agg, verdict, analysis)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "report.md").write_text(text, encoding="utf-8")
    (reports / "report.json").write_text(
        json.dumps({"puzzle_set_id": set_id, "verdict": verdict,
                    "aggregation": agg}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return text, agg


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build difficulty report.")
    parser.add_argument("set", help="puzzle_set_id, equals directory name")
    parser.add_argument("--data", default="data")
    parser.add_argument("--logs", default="logs")
    parser.add_argument("--reports", default="reports")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args(argv)
    client = None
    if not args.no_llm:
        try:
            client = model_api.make_client()
        except (model_api.MissingKeyError, model_api.ModelAPIError):
            client = None
    text, agg = build(args.set, args.data, args.logs, args.reports,
                      client=client)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
