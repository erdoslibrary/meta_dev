"""Agent runner: personas x engine x model into logs/<set>/rNN.json (TRD §7).

Usage: python -m realtosim.run_agents <set> [--runs 15 --seed 0
       --data data --logs logs --max-actions 50]
Interrupting a run is not resumed; rerun with a new seed (TRD §6.1).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from realtosim import game_engine, model_api, personas
from realtosim import settings
from realtosim.validate import load_json

CACHE_PATH = Path("workspace/cache/files.json")

SYSTEM_PROMPT = """당신은 공간 퍼즐 게임의 참가자입니다. 아래 사람처럼 생각하고 행동하세요.
나이: {age}
직업: {job}
어휘 수준: {vocab}
사고 방식: {thinking}

지시를 따라 이동하세요. 처음 받는 정보의 rooms는 방 이름과 칸 범위입니다. 지시받은 사물 근처로 가서 view로 찍으면 사물 사진을 볼 수 있습니다. 반응하는 사물이면 puzzle에 인물의 대화, 문제, 정답 글자 수, 열린 힌트, 남은 시도 횟수가 나타나고 퍼즐 그림이 함께 주어집니다.
대화에도 단서가 들어 있을 수 있습니다. 대화와 그림을 보고 답하세요.
매 차례 JSON 객체 하나만 출력하세요. 형식: {{"action": "...", "value": "...", "reason": "..."}}
- move: value는 이동할 칸입니다. cell_prefix_required가 true이면 2F-C4처럼 층을 붙입니다.
- view: value는 opened_object_ids에 있는 사물 id입니다. 사물의 설명과 사진을 돌려줍니다.
- answer: value는 답입니다. reason에 그렇게 답한 이유를 반드시 적으세요.
행동이 거절되면 last_result.error를 읽고 고치세요."""


class ImageError(Exception):
    """Images are missing or hashed wrong: the run must not start."""


def build_system(persona):
    return SYSTEM_PROMPT.format(age=persona["age"], job=persona["job"],
                                vocab=persona["vocab"],
                                thinking=persona["thinking"])


def _resolve(data_dir, rel):
    direct = Path(data_dir) / rel
    if direct.is_file():
        return direct
    return Path(data_dir) / "photos" / rel


def prepare_images(data_dir, puzzle_set, space, client,
                   cache_path=CACHE_PATH):
    """Verify every image, upload unknowns, return {observe_path: file_id}."""
    needed = {}
    for puzzle in puzzle_set.get("puzzles", []):
        img = puzzle.get("image", {})
        needed[img.get("path", "")] = ("sha", img.get("sha256"))
    for obj in space.get("objects", []):
        photos = obj.get("photos", [])
        if photos:
            needed.setdefault(photos[0], ("exists", None))
    for rel, (kind, sha) in needed.items():
        abs_path = _resolve(data_dir, rel)
        if not abs_path.is_file():
            raise ImageError(f"이미지 없음: {rel}")
        if kind == "sha" and hashlib.sha256(abs_path.read_bytes()).hexdigest() != sha:
            raise ImageError(f"SHA-256 불일치: {rel}")
    cache_path = Path(cache_path)
    cache = {}
    if cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    image_ids = {}
    for rel in needed:
        digest = hashlib.sha256(_resolve(data_dir, rel).read_bytes()).hexdigest()
        if digest not in cache:
            cache[digest] = model_api.upload_file(client, _resolve(data_dir, rel))
        image_ids[rel] = cache[digest]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return image_ids


def run_once(space, puzzle_set, persona, *, run_id, model_name, seed,
             respond_fn, image_ids, max_actions=50):
    """One full run. respond_fn(system, turns) -> str; ModelAPIError aborts."""
    game = game_engine.new_game(space, puzzle_set, persona, run_id=run_id,
                                model=model_name, seed=seed,
                                max_actions=max_actions)
    system = build_system(persona)
    turns = []
    first = True
    while not game.over:
        viewed = game_engine.observe(game)
        payload = {"observation": viewed["observation"]}
        if first:
            payload = {"brief": game_engine.brief(game),
                       "observation": viewed["observation"]}
            first = False
        turns.append({
            "text": json.dumps(payload, ensure_ascii=False),
            "images": [image_ids[p] for p in viewed["images"]
                       if p in image_ids],
        })
        try:
            raw = respond_fn(system, turns)
        except model_api.ModelAPIError:
            game_engine.abort(game)
            break
        game_engine.submit(game, raw if isinstance(raw, str) else "")
    return game_engine.to_log(game)


def run_set(set_id, runs, seed, data_dir="data", logs_dir="logs",
            max_actions=50, client=None, cache_path=CACHE_PATH):
    """Personas up front (TRD §7), then each run to logs/<set>/rNN.json."""
    data_dir, logs_dir = Path(data_dir), Path(logs_dir)
    space = load_json(data_dir / set_id / "space.json")
    puzzle_set = load_json(data_dir / set_id / "puzzle.json")
    own_client = client if client is not None else model_api.make_client()

    def respond_fn(system, turns):
        return model_api.respond(own_client, settings.model(), system, turns)

    image_ids = prepare_images(data_dir / set_id, puzzle_set, space,
                               own_client, cache_path)
    group = personas.generate(runs, seed=seed)
    out_dir = logs_dir / set_id
    out_dir.mkdir(parents=True, exist_ok=True)
    logs = []
    for i, persona in enumerate(group):
        log = run_once(space, puzzle_set, persona,
                       run_id=f"r{i + 1:02d}", model_name=settings.model(),
                       seed=seed, respond_fn=respond_fn, image_ids=image_ids,
                       max_actions=max_actions)
        path = out_dir / f"r{i + 1:02d}.json"
        path.write_text(json.dumps(log, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        logs.append(log)
        last = log["events"][-1]
        print(f"{path}: {last.get('type')}/{last.get('outcome')}",
              flush=True)
    return logs


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run agent episodes (TRD §7).")
    parser.add_argument("set", help="puzzle_set_id, equals directory name")
    parser.add_argument("--runs", type=int, default=15)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--data", default="data")
    parser.add_argument("--logs", default="logs")
    parser.add_argument("--max-actions", type=int, default=50)
    args = parser.parse_args(argv)
    try:
        run_set(args.set, args.runs, args.seed, args.data, args.logs,
                args.max_actions)
    except (model_api.MissingKeyError, ImageError) as e:
        print(f"run_agents: {e}", file=sys.stderr)
        return 2
    except model_api.ModelAPIError as e:
        print(f"run_agents: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
