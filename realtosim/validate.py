"""Validator for a puzzle set: schemas + replay rules M1-M9/M25 (TRD §5).

Usage: python -m realtosim.validate <set> [--data data --reports reports]
Exit 0 when every check passes, 1 otherwise. Always writes replica.md (M9).
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from realtosim import settings

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "docs" / "schemas"
SCHEMA_NAMES = ("space", "puzzle", "persona", "log", "baseline", "npc")

CELL_RE = re.compile(r"^(?:([1-9][0-9]*)F-)?([A-Z]+)([1-9][0-9]*)$")
RANGE_RE = re.compile(
    r"^(?:([1-9][0-9]*)F-)?([A-Z]+)([1-9][0-9]*)(?::([A-Z]+)([1-9][0-9]*))?$"
)


def _col_to_num(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _registry():
    schemas = {}
    for name in SCHEMA_NAMES:
        schemas[name] = load_json(SCHEMA_DIR / f"{name}.schema.json")
    return Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values()
    ), schemas


def _schema_errors(schemas, registry, name, doc):
    validator = Draft202012Validator(schemas[name], registry=registry)
    return [e.message for e in validator.iter_errors(doc)]


def _expand_range(text, floor_prefix):
    """Cell range to {(prefix, col, row)}. Raises ValueError on bad shape."""
    m = RANGE_RE.match(text)
    if not m:
        raise ValueError(f"bad range {text!r}")
    prefix = f"{m.group(1)}F" if m.group(1) else None
    if floor_prefix is not None and prefix != floor_prefix:
        raise ValueError(f"prefix {prefix!r} not on floor {floor_prefix!r}")
    if floor_prefix is None and prefix is not None:
        raise ValueError(f"prefixed {text!r} on single-floor space")
    c1, r1 = _col_to_num(m.group(2)), int(m.group(3))
    c2, r2 = c1, r1
    if m.group(4):
        c2, r2 = _col_to_num(m.group(4)), int(m.group(5))
    if c2 < c1 or r2 < r1:
        raise ValueError(f"reversed range {text!r}")
    lo, hi = (c1, c2) if c1 <= c2 else (c2, c1)
    return {(prefix, c, r) for c in range(lo, hi + 1) for r in range(r1, r2 + 1)}


def _canon_cell(prefix, col, row):
    num = ""
    n = col
    while n:
        n, rem = divmod(n - 1, 26)
        num = chr(65 + rem) + num
    return f"{prefix}-{num}{row}" if prefix else f"{num}{row}"


def check(data_dir):
    """Run every check. Returns (passed: bool, results: list of dicts)."""
    data_dir = Path(data_dir)
    results = []

    def record(check_id, ok, detail):
        results.append({"check": check_id, "ok": bool(ok), "detail": detail})
        return ok

    try:
        space = load_json(data_dir / "space.json")
        puzzle_set = load_json(data_dir / "puzzle.json")
        npc = load_json(data_dir / "npc.json")
        baseline = load_json(data_dir / "baseline.json")
    except (OSError, json.JSONDecodeError) as e:
        record("load", False, f"파일 읽기 실패: {e}")
        return False, results

    registry, schemas = _registry()
    ok_all = True

    # M1/M2: schema conformance.
    for name, doc in (("puzzle", puzzle_set), ("space", space),
                      ("npc", npc), ("baseline", baseline)):
        errs = _schema_errors(schemas, registry, name, doc)
        ok_all &= record(f"M1-{name}" if name == "puzzle" else f"M2-{name}",
                         not errs, "통과" if not errs else f"스키마 오류: {errs[0]}")

    # Cross-id sanity (needed by every rule below).
    ids_ok = True
    if puzzle_set.get("space_id") != space.get("space_id"):
        ids_ok = False
    if baseline.get("puzzle_set_id") != puzzle_set.get("puzzle_set_id"):
        ids_ok = False
    ok_all &= record("ids", ids_ok, "통과" if ids_ok else "space_id/puzzle_set_id 불일치")
    if not ids_ok:
        return False, results

    puzzles = puzzle_set.get("puzzles", [])
    numbers = [p.get("number") for p in puzzles]
    ok_all &= record("numbers", numbers == list(range(1, len(puzzles) + 1)),
                     "통과" if numbers == list(range(1, len(puzzles) + 1))
                     else f"number가 1..N이 아님: {numbers}")

    objects = {o.get("id"): o for o in space.get("objects", [])}

    # M4: object/next linkage and chain.
    m4_problems = []
    for i, p in enumerate(puzzles):
        if p.get("object_id") not in objects:
            m4_problems.append(f"{p.get('number')}번 object_id {p.get('object_id')} 없음")
        nxt, nxt_ins = p.get("next_object_id"), p.get("next_instruction")
        last = i == len(puzzles) - 1
        if last:
            if nxt is not None or nxt_ins is not None:
                m4_problems.append(f"{p.get('number')}번: 마지막인데 next가 null 아님")
        else:
            if nxt is None or nxt_ins is None:
                m4_problems.append(f"{p.get('number')}번: next null")
            elif nxt not in objects:
                m4_problems.append(f"{p.get('number')}번 next_object_id {nxt} 없음")
        if i > 0 and p.get("object_id") != puzzles[i - 1].get("next_object_id"):
            m4_problems.append(
                f"{p.get('number')}번 object_id가 앞 퍼즐 next_object_id와 다름")
    ok_all &= record("M4", not m4_problems, "통과" if not m4_problems else "; ".join(m4_problems))

    # M5: grid bounds, overlap, photos.
    floors = {f.get("id"): f for f in space.get("floors", [])}
    single = len(floors) == 1
    only_prefix = next(iter(floors)) if not single else None
    m5_problems = []

    def cells_of(text):
        if single:
            if CELL_RE.match(text) and CELL_RE.match(text).group(1):
                raise ValueError(f"single-floor prefixed {text!r}")
            return _expand_range(text, None)
        m = RANGE_RE.match(text)
        if not m or not m.group(1):
            raise ValueError(f"multi-floor bare {text!r}")
        prefix = f"{m.group(1)}F"
        if prefix not in floors:
            raise ValueError(f"unknown floor {prefix!r}")
        return _expand_range(text, prefix)

    seen_objects, seen_rooms = set(), set()
    for o in space.get("objects", []):
        try:
            cells = cells_of(o.get("cells", ""))
        except ValueError as e:
            m5_problems.append(f"사물 {o.get('id')}: {e}")
            continue
        fl = next(iter(cells))[0] if cells else None
        grid = floors.get(fl) if fl else next(iter(floors.values()))
        if grid is None or any(
                c < 1 or c > grid["columns"] or r < 1 or r > grid["rows"]
                for _, c, r in cells):
            m5_problems.append(f"사물 {o.get('id')}: 격자 밖")
        if cells & seen_objects:
            m5_problems.append(f"사물 {o.get('id')}: 겹침")
        seen_objects |= cells
        photos = o.get("photos", [])
        if not photos:
            m5_problems.append(f"사물 {o.get('id')}: 사진 없음")
        elif not (data_dir / "photos" / photos[0]).is_file():
            m5_problems.append(f"사물 {o.get('id')}: 첫 사진 {photos[0]} 없음")
    for room in space.get("rooms", []):
        try:
            cells = cells_of(room.get("cells", ""))
        except ValueError as e:
            m5_problems.append(f"방 {room.get('name')}: {e}")
            continue
        fl = next(iter(cells))[0] if cells else None
        grid = floors.get(fl) if fl else next(iter(floors.values()))
        if grid is None or any(
                c < 1 or c > grid["columns"] or r < 1 or r > grid["rows"]
                for _, c, r in cells):
            m5_problems.append(f"방 {room.get('name')}: 격자 밖")
        if cells & seen_rooms:
            m5_problems.append(f"방 {room.get('name')}: 겹침")
        seen_rooms |= cells
    ok_all &= record("M5", not m5_problems, "통과" if not m5_problems else "; ".join(m5_problems))

    # M6: answer normalization and letter count (len in characters).
    m6_problems = []
    for p in puzzles:
        ans = p.get("answer", "")
        if ans != ans.strip() or ans != ans.lower():
            m6_problems.append(f"{p.get('number')}번: 소문자·공백 위반 {ans!r}")
        if p.get("answer_letter_count") != len(ans):
            m6_problems.append(
                f"{p.get('number')}번: 글자수 {p.get('answer_letter_count')} != {len(ans)}")
    ok_all &= record("M6", not m6_problems, "통과" if not m6_problems else "; ".join(m6_problems))

    # M7: answer must not appear in dialogue.
    m7_problems = []
    for p in puzzles:
        ans = p.get("answer", "").strip().lower()
        if ans and any(ans in line.get("text", "").lower()
                       for line in p.get("dialogue", [])):
            m7_problems.append(f"{p.get('number')}번: 대화문에 정답 노출")
    ok_all &= record("M7", not m7_problems, "통과" if not m7_problems else "; ".join(m7_problems))

    # M8: puzzle image sha256 matches file bytes.
    m8_problems = []
    for p in puzzles:
        img = p.get("image", {})
        path = data_dir / img.get("path", "")
        if not path.is_file():
            m8_problems.append(f"{p.get('number')}번: 그림 {img.get('path')} 없음")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != img.get("sha256"):
            m8_problems.append(f"{p.get('number')}번: SHA-256 불일치")
    ok_all &= record("M8", not m8_problems, "통과" if not m8_problems else "; ".join(m8_problems))

    # M25: next_instruction names the next object's cell or a room.
    m25_problems = []
    room_names = [r.get("name", "") for r in space.get("rooms", [])]
    for i, p in enumerate(puzzles):
        if i == len(puzzles) - 1:
            continue
        ins = p.get("next_instruction") or ""
        obj = objects.get(p.get("next_object_id"), {})
        cands = [obj.get("cells", "")]
        try:
            cells = cells_of(obj.get("cells", "C4"))
            first = sorted(cells)[0]
            cands.append(_canon_cell(first[0], first[1], first[2]))
        except ValueError:
            pass
        cands.extend(room_names)
        if not any(c and c in ins for c in cands):
            m25_problems.append(f"{p.get('number')}번: 지시문에 좌표·방 이름 없음")
    ok_all &= record("M25", not m25_problems, "통과" if not m25_problems else "; ".join(m25_problems))

    return all(r["ok"] for r in results), results


def write_replica(report_path, set_id, passed, results):
    lines = [f"# 재연 보고서 — {set_id}", "",
             f"판정: {'통과' if passed else '수정 필요'}", "",
             "## 통과 항목", ""]
    for r in results:
        if r["ok"]:
            lines.append(f"- {r['check']}: {r['detail']}")
    lines += ["", "## 수정 항목", ""]
    bad = [r for r in results if not r["ok"]]
    lines.append("없음" if not bad else "")
    for r in bad:
        lines.append(f"- {r['check']}: {r['detail']}")
    lines += ["", "## 확인 항목", "",
              "- M6 글자수는 파이썬 문자 수 기준이다.",
              "- 사물-방 겹침은 허용한다(방 안에 사물이 있다).",
              f"- 모델: {settings.model()} (검증은 모델 없이 수행).", ""]
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a puzzle set (TRD §5).")
    parser.add_argument("set", help="puzzle_set_id, equals directory name")
    parser.add_argument("--data", default="data")
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args(argv)
    passed, results = check(Path(args.data) / args.set)
    write_replica(Path(args.reports) / args.set / "replica.md",
                  args.set, passed, results)
    for r in results:
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {r['check']}: {r['detail']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
