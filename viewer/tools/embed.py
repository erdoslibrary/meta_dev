"""Bundle real logs + static data into viewer/dist/data.js (stdlib only).

Reads:
  logs/<set>/            real run logs (log.schema.json)
  data/<set>/            space.json, puzzle.json, npc.json
  viewer/testdata/       schema-passing viewer samples (never mixed into logs/)

Writes:
  viewer/dist/data.js    single statement: window.RT_DATA = {...};

Photo binaries are never embedded; only relative paths are stored and the
page shows them with <img>.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "viewer"


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_set(set_name: str):
    log_dir = ROOT / "logs" / set_name
    data_dir = ROOT / "data" / set_name
    logs = {}
    for path in sorted(log_dir.rglob("*.json")):
        key = str(path.relative_to(log_dir))[:-len(".json")]
        logs[key] = load_json(path)
    return {
        "space": load_json(data_dir / "space.json"),
        "puzzle": load_json(data_dir / "puzzle.json"),
        "npc": load_json(data_dir / "npc.json"),
        "logs": logs,
    }


def collect_testdata():
    samples = {}
    test_dir = VIEWER / "testdata"
    if test_dir.is_dir():
        for path in sorted(test_dir.glob("*.json")):
            samples[path.stem] = load_json(path)
    return samples


def main() -> int:
    sets = {}
    logs_root = ROOT / "logs"
    if logs_root.is_dir():
        for child in sorted(logs_root.iterdir()):
            if child.is_dir() and (child / "..").exists():
                try:
                    sets[child.name] = collect_set(child.name)
                except FileNotFoundError as exc:
                    print(f"skip set {child.name}: {exc}", file=sys.stderr)
    payload = {"sets": sets, "testdata": collect_testdata()}
    out_dir = VIEWER / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "window.RT_DATA = " + json.dumps(payload, ensure_ascii=False) + ";"
    with open(out_dir / "data.js", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {out_dir / 'data.js'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
