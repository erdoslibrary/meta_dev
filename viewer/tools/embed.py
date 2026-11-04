"""Bundle real logs + static data into viewer/dist/data.js.

Uses the standard library plus ``jsonschema`` only (no new package
install; run with ``.venv/bin/python``, never bare ``python``/``python3``).

Reads:
  logs/<set>/            real run logs (log.schema.json)
  data/<set>/            space.json, puzzle.json, npc.json
  viewer/testdata/       schema-passing viewer samples (never mixed into logs/)
  viewer/testdata/refusal/   playback-refusal samples (t gap / last not end)
  viewer/testdata/sets/<puzzle_set_id>/  sample-set static data

Writes:
  viewer/dist/data.js    single statement: window.RT_DATA = {...};

Gate: every schema-required log original (logs/<set>/ plus top-level
viewer/testdata/*.json, BEFORE reason removal) is validated against
log.schema.json first. On failure nothing is written. Refusal samples are
excluded from this gate but included in data.js with the same
allow/exclude rules (their t defect and non-end last event are kept).

Photo binaries are never embedded; only relative paths are stored and the
page shows them with <img>.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "viewer"
SCHEMA_DIR = ROOT / "docs" / "schemas"
SCHEMA_NAMES = ("space", "puzzle", "persona", "log", "baseline", "npc")

LOG_HEADER_FIELDS = ("run_id", "persona", "puzzle_set_id", "model", "seed")

# Dropped everywhere in the payload (data.js audit target).
ALWAYS_BANNED_KEYS = frozenset({"sha256", "next_object_id", "tone", "hints", "reason"})


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _registry():
    schemas = {}
    for name in SCHEMA_NAMES:
        schemas[name] = load_json(SCHEMA_DIR / f"{name}.schema.json")
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values()
    )
    return registry, schemas


def validate_log_doc(doc) -> list:
    """Schema errors in one log original. Empty means valid."""
    registry, schemas = _registry()
    validator = Draft202012Validator(schemas["log"], registry=registry)
    return [e.message for e in validator.iter_errors(doc)]


def failed_numbers(log_doc) -> set:
    """Puzzle numbers ending in failed in this log."""
    failed = set()
    for event in log_doc.get("events", []):
        if event.get("type") == "puzzle_ended" and event.get("result") == "failed":
            failed.add(event.get("puzzle"))
    return failed


def strip_banned(node):
    """Deep copy without ALWAYS_BANNED_KEYS (photo paths stay as paths)."""
    if isinstance(node, dict):
        return {
            key: strip_banned(value)
            for key, value in node.items()
            if key not in ALWAYS_BANNED_KEYS
        }
    if isinstance(node, list):
        return [strip_banned(item) for item in node]
    return node


def filter_event(event: dict) -> dict:
    return {k: v for k, v in event.items() if k != "reason"}


def filter_log(doc: dict) -> dict:
    out = {k: doc[k] for k in LOG_HEADER_FIELDS if k in doc}
    out["events"] = [filter_event(e) for e in doc.get("events", [])]
    return out


def filter_puzzle(doc: dict, failed: set) -> dict:
    """Shared set puzzle: dialogue text only, no answers (reveals holds them)."""
    out = strip_banned(doc)
    entries = out.get("puzzles", [])
    for entry in entries:
        number = entry.get("number")
        if number not in failed:
            entry.pop("answer", None)
            entry.pop("next_instruction", None)
        elif entry.get("next_instruction") is None:
            entry.pop("next_instruction", None)
        if isinstance(entry.get("dialogue"), list):
            entry["dialogue"] = [
                {"text": line.get("text")}
                for line in entry["dialogue"]
                if isinstance(line, dict)
            ]
    return out


def reveals_for(puzzle_doc: dict, failed: set) -> dict:
    """Per-log answers: {<number string>: {answer[, next_instruction]}}.

    Only puzzles failed in that log; null next_instruction omitted.
    """
    out = {}
    for entry in puzzle_doc.get("puzzles", []):
        number = entry.get("number")
        if number in failed and "answer" in entry:
            item = {"answer": entry["answer"]}
            if entry.get("next_instruction") is not None:
                item["next_instruction"] = entry["next_instruction"]
            out[str(number)] = item
    return out


def filter_static_set(space, puzzle, npc, failed: set) -> dict:
    return {
        "space": strip_banned(space),
        "puzzle": filter_puzzle(puzzle, failed),
        "npc": strip_banned(npc),
    }


def collect_set(set_name: str, log_dir: Path, data_dir: Path):
    logs = {}
    for path in sorted(log_dir.rglob("*.json")):
        key = str(path.relative_to(log_dir))[: -len(".json")]
        logs[key] = load_json(path)
    try:
        space = load_json(data_dir / "space.json")
        puzzle = load_json(data_dir / "puzzle.json")
        npc = load_json(data_dir / "npc.json")
    except FileNotFoundError as exc:
        print(f"skip set {set_name}: {exc}", file=sys.stderr)
        return None
    entry = filter_static_set(space, puzzle, npc, set())
    entry["logs"] = {key: filter_log(doc) for key, doc in logs.items()}
    entry["reveals"] = {
        key: reveals_for(puzzle, failed_numbers(doc))
        for key, doc in logs.items()
    }
    return entry


def collect_testdata(test_dir: Path):
    samples = {}
    if test_dir.is_dir():
        for path in sorted(test_dir.glob("*.json")):
            samples[path.stem] = load_json(path)
    return samples


def collect_refusal(test_dir: Path):
    samples = {}
    refusal_dir = test_dir / "refusal"
    if refusal_dir.is_dir():
        for path in sorted(refusal_dir.glob("*.json")):
            samples[path.stem] = load_json(path)
    return samples


def collect_sample_sets(test_dir: Path, samples: dict) -> dict:
    sets_dir = test_dir / "sets"
    out = {}
    if not sets_dir.is_dir():
        return out
    by_set_id: dict = {}
    for stem, doc in samples.items():
        by_set_id.setdefault(doc.get("puzzle_set_id"), []).append((stem, doc))
    for child in sorted(sets_dir.iterdir()):
        if not child.is_dir():
            continue
        parts = {}
        for name in ("space", "puzzle", "npc"):
            path = child / f"{name}.json"
            if path.is_file():
                parts[name] = load_json(path)
        if not parts:
            continue
        if "puzzle" in parts:
            puzzle_orig = parts["puzzle"]
            parts["puzzle"] = filter_puzzle(puzzle_orig, set())
            parts["reveals"] = {
                f"testdata/{stem}": reveals_for(puzzle_orig, failed_numbers(doc))
                for stem, doc in by_set_id.get(child.name, [])
            }
        if "space" in parts:
            parts["space"] = strip_banned(parts["space"])
        if "npc" in parts:
            parts["npc"] = strip_banned(parts["npc"])
        out[child.name] = parts
    return out


def gate_errors(root: Path = ROOT) -> dict:
    """Validate every schema-required log original. {} means pass."""
    registry, schemas = _registry()
    validator = Draft202012Validator(schemas["log"], registry=registry)
    errors = {}
    targets = []
    logs_root = root / "logs"
    if logs_root.is_dir():
        targets += sorted(logs_root.rglob("*.json"))
    test_dir = root / "viewer" / "testdata"
    if test_dir.is_dir():
        targets += sorted(test_dir.glob("*.json"))
    for path in targets:
        try:
            doc = load_json(path)
        except (OSError, ValueError) as exc:
            errors[str(path)] = [f"unreadable: {exc}"]
            continue
        msgs = [e.message for e in validator.iter_errors(doc)]
        if msgs:
            errors[str(path)] = msgs
    return errors


def _link_cross_set_reveals(root, sets, sample_sets, samples, refusal):
    """Reveals for sample/refusal logs linked to data/ sets.

    Real logs land in collect_set; sample_sets entries already carry
    their own testdata/* reveals. Every other embedded log lands in
    its linked set (sets/<id> or sample_sets/<id>) under testdata/<name>
    or refusal/<name> with the same per-log rule.
    """
    labeled = [(f"testdata/{stem}", doc) for stem, doc in samples.items()]
    labeled += [(f"refusal/{name}", doc) for name, doc in refusal.items()]
    by_set: dict = {}
    for key, doc in labeled:
        by_set.setdefault(doc.get("puzzle_set_id"), []).append((key, doc))
    for psid, items in by_set.items():
        if psid in sample_sets:
            target = sample_sets[psid]
            puzzle_orig = load_json(
                root / "viewer" / "testdata" / "sets" / psid / "puzzle.json"
            )
        else:
            data_dir = root / "data" / psid if psid else None
            if data_dir is None or not data_dir.is_dir():
                continue
            target = sets.get(psid)
            if target is None:
                try:
                    space = load_json(data_dir / "space.json")
                    puzzle_orig = load_json(data_dir / "puzzle.json")
                    npc = load_json(data_dir / "npc.json")
                except (OSError, ValueError):
                    continue
                target = filter_static_set(space, puzzle_orig, npc, set())
                target["logs"] = {}
                target["reveals"] = {}
                sets[psid] = target
            else:
                puzzle_orig = load_json(data_dir / "puzzle.json")
        reveals = target.setdefault("reveals", {})
        for key, doc in items:
            reveals.setdefault(
                key, reveals_for(puzzle_orig, failed_numbers(doc))
            )


def build_payload(root: Path = ROOT) -> dict:
    logs_root = root / "logs"
    sets = {}
    if logs_root.is_dir():
        for child in sorted(logs_root.iterdir()):
            if child.is_dir():
                entry = collect_set(
                    child.name, child, root / "data" / child.name
                )
                if entry is not None:
                    sets[child.name] = entry
    test_dir = root / "viewer" / "testdata"
    samples = collect_testdata(test_dir)
    refusal = collect_refusal(test_dir)
    sample_sets = collect_sample_sets(test_dir, samples)
    _link_cross_set_reveals(root, sets, sample_sets, samples, refusal)
    return {
        "sets": sets,
        "testdata": {k: filter_log(v) for k, v in samples.items()},
        "refusal": {k: filter_log(v) for k, v in refusal.items()},
        "sample_sets": sample_sets,
    }


def _lookup_targets(root: Path = ROOT) -> list:
    """Every embedded log: logs/ plus top-level testdata plus refusal/."""
    targets = []
    logs_root = root / "logs"
    if logs_root.is_dir():
        targets += sorted(logs_root.rglob("*.json"))
    test_dir = root / "viewer" / "testdata"
    if test_dir.is_dir():
        targets += sorted(test_dir.glob("*.json"))
        refusal_dir = test_dir / "refusal"
        if refusal_dir.is_dir():
            targets += sorted(refusal_dir.glob("*.json"))
    return targets


def set_lookup_errors(root: Path = ROOT) -> dict:
    """puzzle_set_id values with no unique set source.

    Each log resolves against sets/<id> first, then data/<id>; an id
    found in both or in neither is a violation (no data.js).
    Returns {puzzle_set_id: [log paths]}; {} means all resolve.
    """
    errors: dict = {}
    for path in _lookup_targets(root):
        try:
            doc = load_json(path)
        except (OSError, ValueError):
            continue  # unreadable files are reported by gate_errors
        psid = doc.get("puzzle_set_id")
        in_sets = bool(psid) and (root / "viewer" / "testdata" / "sets" / psid).is_dir()
        in_data = bool(psid) and (root / "data" / psid).is_dir()
        if in_sets == in_data:
            errors.setdefault(psid or str(path), []).append(str(path))
    return errors


def main(root: Path = ROOT) -> int:
    try:
        errors = gate_errors(root)
    except Exception as exc:  # environment failure: report, never install
        print(f"embed gate failed to run: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("embed gate: schema-required logs invalid, data.js not written:",
              file=sys.stderr)
        for path, msgs in errors.items():
            for msg in msgs:
                print(f"  {path}: {msg}", file=sys.stderr)
        return 1
    try:
        lookup = set_lookup_errors(root)
    except Exception as exc:
        print(f"embed lookup failed to run: {exc}", file=sys.stderr)
        return 2
    if lookup:
        print("embed gate: set lookup violations, data.js not written:",
              file=sys.stderr)
        for psid, paths in lookup.items():
            for path in paths:
                print(f"  {psid}: {path}", file=sys.stderr)
        return 1
    try:
        payload = build_payload(root)
    except Exception as exc:
        print(f"embed failed: {exc}", file=sys.stderr)
        return 2
    out_dir = root / "viewer" / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "window.RT_DATA = " + json.dumps(payload, ensure_ascii=False) + ";"
    with open(out_dir / "data.js", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {out_dir / 'data.js'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
