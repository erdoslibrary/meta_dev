"""Pure state-machine game engine (TRD §3~§4).

No model, file, or network access. No randomness. One submit call is one
action (rejections included). All inputs are deep-copied at new_game so
caller dicts never change.
"""

import copy
import json
import re

# TRD §4 rejection sentences, in check order 1~12. Tests compare verbatim.
ERR_NOT_JSON = "출력이 JSON 형식이 아닙니다"
ERR_NOT_OBJECT = "출력은 JSON 객체여야 합니다"
ERR_ACTION_TYPE = "action은 문자열이어야 합니다"
ERR_UNKNOWN_ACTION = "알 수 없는 행동입니다. move, view, answer 중 하나를 쓰세요"
ERR_VALUE_TYPE = "value는 문자열이어야 합니다"
ERR_CELL_FORMAT = "칸 좌표 형식이 아닙니다"
ERR_CELL_UNKNOWN = "지도에 없는 칸입니다"
ERR_OBJECT_MISSING = "존재하지 않는 사물입니다"
ERR_OBJECT_LOCKED = "아직 가까이 가지 않은 사물입니다"
ERR_ANSWER_EARLY = "아직 퍼즐이 열리지 않았습니다"
ERR_ANSWER_EMPTY = "답이 비어 있습니다"
ERR_REASON_NEEDED = "answer에는 이유(reason)가 필요합니다"

ACTIONS = ("move", "view", "answer")

CELL_RE = re.compile(r"^(?:([1-9][0-9]*)F-)?([A-Z]+)([1-9][0-9]*)$")


class GameSetupError(Exception):
    """Raised by new_game when the bundle cannot start (no log is written)."""


class GameStateError(Exception):
    """Raised when observing/submitting/aborting/to_log at the wrong time."""


def _col_to_num(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def _parse_cell(text):
    """Parse a cellRef into (floor_prefix|None, col, row); None when malformed."""
    m = CELL_RE.match(text)
    if not m:
        return None
    prefix, letters, row = m.group(1), m.group(2), int(m.group(3))
    return (f"{prefix}F" if prefix else None, _col_to_num(letters), row)


def _canon_cell(prefix, col, row):
    letters = ""
    n = col
    while n:
        n, r = divmod(n - 1, 26)
        letters = chr(ord("A") + r) + letters
    return f"{prefix}-{letters}{row}" if prefix else f"{letters}{row}"


def _parse_range(text):
    """Parse a cellRange into (prefix|None, set of (col,row)); None when malformed."""
    parts = text.split(":")
    if len(parts) > 2:
        return None
    first = _parse_cell(parts[0])
    if first is None:
        return None
    prefix, c1, r1 = first
    if len(parts) == 1:
        return (prefix, {(c1, r1)})
    second = _parse_cell(parts[1])
    if second is None:
        return None
    prefix2, c2, r2 = second
    if prefix2 is not None and prefix2 != prefix:
        return None
    if prefix is None and prefix2 is not None:
        prefix = prefix2
    cells = set()
    for c in range(min(c1, c2), max(c1, c2) + 1):
        for r in range(min(r1, r2), max(r1, r2) + 1):
            cells.add((c, r))
    return (prefix, cells)


class Game:
    """Internal engine state. Never exposed directly (observe/to_log only)."""

    def __init__(self, space, puzzle_set, persona, run_id, model, seed, max_actions):
        self.floors = space["floors"]
        self.floor_ids = [f["id"] for f in self.floors]
        self.multi = len(self.floors) > 1
        self.rooms = copy.deepcopy(space.get("rooms", []))
        self.objects = []
        for o in space["objects"]:
            parsed = _parse_range(o["cells"])
            if parsed is None:
                raise GameSetupError(f"bad object cells: {o.get('id')}")
            prefix, cells = parsed
            floor = self._floor_of(prefix)
            if floor is None:
                raise GameSetupError(f"object outside grid: {o.get('id')}")
            for (c, r) in cells:
                if not (1 <= c <= floor["columns"] and 1 <= r <= floor["rows"]):
                    raise GameSetupError(f"object outside grid: {o.get('id')}")
            self.objects.append({
                "id": o["id"],
                "label": o["label"],
                "cells": cells,
                "floor": prefix,
                "description": o.get("description", ""),
                "photo": o["photos"][0] if o.get("photos") else None,
            })
        self.object_state = {o["id"]: "locked" for o in self.objects}
        self.by_id = {o["id"]: o for o in self.objects}

        self.puzzles = puzzle_set["puzzles"]
        self.start_instruction = puzzle_set.get("start_instruction")
        self.persona = persona
        self.run_id = run_id
        self.model = model
        self.seed = seed
        self.max_actions = max_actions
        self.puzzle_set_id = puzzle_set["puzzle_set_id"]

        pos = _parse_cell(puzzle_set["start_cell"])
        if pos is None or not self._in_grid(pos):
            raise GameSetupError("bad start_cell")
        self.position = pos

        self.current = 0  # 0-based index into self.puzzles
        self.wrong = [0] * len(self.puzzles)
        self.opened = [False] * len(self.puzzles)
        self.revealed = [set() for _ in self.puzzles]
        self.instruction = self.start_instruction
        self.action_count = 0
        self.events = []
        self.over = False
        self.outcome = None
        self.last_result = {}
        self.reveal_answer = None
        self.last_viewed_id = None

    def _floor_of(self, prefix):
        if self.multi:
            if prefix is None:
                return None
            for f in self.floors:
                if f["id"] == prefix:
                    return f
            return None
        if prefix is not None:
            return None
        return self.floors[0]

    def _in_grid(self, pos):
        prefix, c, r = pos
        floor = self._floor_of(prefix)
        return floor is not None and 1 <= c <= floor["columns"] and 1 <= r <= floor["rows"]

    def _adjacent(self, pos, obj):
        if pos[0] != obj["floor"]:
            return False
        for (c, r) in obj["cells"]:
            if max(abs(pos[1] - c), abs(pos[2] - r)) <= 1:
                return True
        return False

    @property
    def current_number(self):
        return min(self.current + 1, len(self.puzzles))

    def attempts_allowed(self, index):
        return self.puzzles[index].get("max_attempts") or 5

    def _advance(self):
        self.current += 1
        if self.current >= len(self.puzzles):
            self.emit("end", outcome="completed")
            self.over = True
            self.outcome = "completed"
            return
        self.instruction = self.puzzles[self.current - 1].get("next_instruction")

    def _maybe_limit(self):
        if self.over:
            return
        if self.action_count >= self.max_actions:
            self.emit("end", outcome="action_limit")
            self.over = True
            self.outcome = "action_limit"

    def emit(self, type_, **fields):
        event = {"t": len(self.events) + 1, "puzzle": self.current_number, "type": type_}
        event.update(fields)
        self.events.append(event)
        return event


def _puzzle_position(puzzle_set, space, persona, run_id, model, seed, max_actions):
    puzzles = puzzle_set["puzzles"]
    numbers = [p.get("number") for p in puzzles]
    if numbers != list(range(1, len(puzzles) + 1)):
        raise GameSetupError("puzzle numbers must run 1..N")
    ids = set()
    for p in puzzles:
        for key in ("number", "object_id", "npc", "dialogue", "image", "question",
                    "answer", "answer_letter_count", "hints", "next_instruction", "next_object_id"):
            if key not in p:
                raise GameSetupError(f"puzzle {p.get('number')} missing {key}")
    return Game(space, puzzle_set, persona, run_id, model, seed, max_actions)


def new_game(space, puzzle_set, persona, *, run_id, model, seed=None, max_actions=50):
    """Start a run. All object states forced to locked; inputs never mutated."""
    try:
        space_c = copy.deepcopy(space)
        pset_c = copy.deepcopy(puzzle_set)
        persona_c = copy.deepcopy(persona)
        if not isinstance(space_c, dict) or not isinstance(pset_c, dict):
            raise GameSetupError("space and puzzle_set must be objects")
        for key in ("space_id", "floors", "objects"):
            if key not in space_c:
                raise GameSetupError(f"space missing {key}")
        for key in ("puzzle_set_id", "space_id", "start_cell", "puzzles"):
            if key not in pset_c:
                raise GameSetupError(f"puzzle_set missing {key}")
        if pset_c["space_id"] != space_c["space_id"]:
            raise GameSetupError("puzzle_set.space_id must match space.space_id")
        if not isinstance(pset_c["puzzles"], list) or not pset_c["puzzles"]:
            raise GameSetupError("puzzles must be a non-empty list")
        seen = set()
        for o in space_c["objects"]:
            if o.get("id") in seen:
                raise GameSetupError(f"duplicate object id: {o.get('id')}")
            seen.add(o.get("id"))
        for p in pset_c["puzzles"]:
            if p.get("object_id") not in seen:
                raise GameSetupError(f"unknown object_id: {p.get('object_id')}")
            nxt = p.get("next_object_id")
            if nxt is not None and nxt not in seen:
                raise GameSetupError(f"unknown next_object_id: {nxt}")
        for prev, cur in zip(pset_c["puzzles"], pset_c["puzzles"][1:]):
            if cur.get("object_id") != prev.get("next_object_id"):
                raise GameSetupError("puzzle chain is broken")
        if not isinstance(persona_c, dict):
            raise GameSetupError("persona must be an object")
        return _puzzle_position(pset_c, space_c, persona_c, run_id, model, seed, max_actions)
    except (KeyError, TypeError, AttributeError) as exc:
        raise GameSetupError(f"unusable bundle: {exc}") from exc


def brief(game):
    """Static bundle info only (TRD §4 allow-list). Callable any time."""
    return {
        "floors": copy.deepcopy(game.floors),
        "cell_prefix_required": game.multi,
        "rooms": copy.deepcopy(game.rooms),
        "objects": [
            {"id": o["id"], "label": o["label"],
             "cells": _cells_text(game, o), "description": o["description"]}
            for o in game.objects
        ],
    }


def _cells_text(game, obj):
    cells = sorted(obj["cells"])
    (c1, r1), (c2, r2) = cells[0], cells[-1]
    lo = _canon_cell(obj["floor"], c1, r1)
    hi = _canon_cell(obj["floor"], c2, r2)
    return lo if lo == hi else f"{lo}:{hi}"


def _puzzle_view(game, index):
    """Current-puzzle observation: dialogue text only, opened hints only."""
    puzzle = game.puzzles[index]
    return {
        "number": puzzle["number"],
        "dialogue": [{"text": line["text"]} for line in puzzle["dialogue"]],
        "question": puzzle["question"],
        "answer_letter_count": puzzle["answer_letter_count"],
        "hints": [
            {"level": h["level"], "text": h["text"]}
            for h in puzzle.get("hints", [])
            if h.get("level") in game.revealed[index]
        ],
        "attempts_left": game.attempts_allowed(index) - game.wrong[index],
    }


def observe(game):
    """Current observation + images (puzzle art, last-viewed photo)."""
    if game.over:
        raise GameStateError("종료된 실행입니다")
    observation = {
        "position": _canon_cell(*game.position),
        "opened_object_ids": [o["id"] for o in game.objects
                              if game.object_state[o["id"]] == "open"],
        "instruction": game.instruction,
        "puzzle": _puzzle_view(game, game.current) if game.opened[game.current] else None,
        "last_result": dict(game.last_result),
    }
    if game.reveal_answer is not None:
        observation["last_result"]["answer"] = game.reveal_answer
        game.reveal_answer = None
    images = []
    if game.opened[game.current]:
        images.append(game.puzzles[game.current]["image"]["path"])
    if game.last_viewed_id is not None:
        photo = game.by_id[game.last_viewed_id]["photo"]
        if photo is not None and photo not in images:
            images.append(photo)
    return {"observation": observation, "images": images}


def _reject(game, attempted_action, value, error):
    game.action_count += 1
    fields = {"attempted_action": attempted_action, "error": error}
    if isinstance(value, str):
        fields["value"] = value
    event = game.emit("rejected", **fields)
    game.last_result = {"action": attempted_action, "error": error}
    game._maybe_limit()
    return event


def submit(game, raw_output):
    """One call is one action (rejections included). Never raises for content."""
    if game.over:
        raise GameStateError("종료된 실행입니다")
    before = len(game.events)
    if not isinstance(raw_output, str):
        _reject(game, None, None, ERR_NOT_JSON)
        return _result(game, before)
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        _reject(game, None, None, ERR_NOT_JSON)
        return _result(game, before)
    if not isinstance(parsed, dict):
        _reject(game, None, None, ERR_NOT_OBJECT)
        return _result(game, before)
    action = parsed.get("action")
    if not isinstance(action, str):
        _reject(game, None, parsed.get("value"), ERR_ACTION_TYPE)
        return _result(game, before)
    if action not in ACTIONS:
        _reject(game, action, parsed.get("value"), ERR_UNKNOWN_ACTION)
        return _result(game, before)
    value = parsed.get("value")
    if not isinstance(value, str):
        _reject(game, action, value, ERR_VALUE_TYPE)
        return _result(game, before)
    if action == "move":
        _do_move(game, value)
    elif action == "view":
        _do_view(game, value)
    else:
        _do_answer(game, value, parsed.get("reason"))
    return _result(game, before)


def _result(game, before):
    return {"events": game.events[before:], "over": game.over, "outcome": game.outcome}


def _do_move(game, value):
    pos = _parse_cell(value)
    if pos is None:
        _reject(game, "move", value, ERR_CELL_FORMAT)
        return
    if not game._in_grid(pos):
        _reject(game, "move", value, ERR_CELL_UNKNOWN)
        return
    game.action_count += 1
    game.position = pos
    for o in game.objects:
        if game._adjacent(pos, o):
            game.object_state[o["id"]] = "open"
    game.emit("move", value=_canon_cell(*pos))
    game.last_result = {"action": "move", "position": _canon_cell(*pos)}
    game._maybe_limit()


def _do_view(game, value):
    obj = game.by_id.get(value)
    if obj is None:
        _reject(game, "view", value, ERR_OBJECT_MISSING)
        return
    if game.object_state[value] != "open":
        _reject(game, "view", value, ERR_OBJECT_LOCKED)
        return
    game.action_count += 1
    game.last_viewed_id = value
    game.emit("view", value=value)
    puzzle = game.puzzles[game.current]
    arrived = (value == puzzle["object_id"] and game._adjacent(game.position, obj)
               and not game.opened[game.current])
    if arrived:
        game.opened[game.current] = True
        game.emit("npc_dialogue", npc=puzzle["npc"])
    game.last_result = {"action": "view", "arrived": arrived}
    game._maybe_limit()


def _do_answer(game, value, reason):
    if not game.opened[game.current]:
        _reject(game, "answer", value, ERR_ANSWER_EARLY)
        return
    if value.strip() == "":
        _reject(game, "answer", value, ERR_ANSWER_EMPTY)
        return
    if not isinstance(reason, str) or reason.strip() == "":
        _reject(game, "answer", value, ERR_REASON_NEEDED)
        return
    allowed = game.attempts_allowed(game.current)
    game.action_count += 1
    attempt = game.wrong[game.current] + 1
    puzzle = game.puzzles[game.current]
    correct = value.strip().lower() == puzzle["answer"].strip().lower()
    game.emit("answer_submitted", value=value, attempt=attempt,
              correct=correct, reason=reason)
    if correct:
        result = ("solved_by_dialogue" if not game.revealed[game.current]
                  else "solved_with_hint")
        game.emit("puzzle_ended", result=result, attempts_used=attempt)
        game.last_result = {"action": "answer", "correct": True, "attempt": attempt}
        game._advance()
        return
    game.wrong[game.current] += 1
    for hint in puzzle.get("hints", []):
        if hint.get("after_wrong") == game.wrong[game.current]:
            game.revealed[game.current].add(hint.get("level"))
            game.emit("hint_revealed", level=hint.get("level"))
    if game.wrong[game.current] >= allowed:
        game.emit("puzzle_ended", result="failed", attempts_used=allowed)
        game.last_result = {"action": "answer", "correct": False,
                            "attempt": attempt, "failed": True}
        game.reveal_answer = puzzle["answer"]
        game._advance()
        return
    game.last_result = {"action": "answer", "correct": False, "attempt": attempt}
    game._maybe_limit()


def abort(game):
    """Cut a run short: only end(api_error) is appended, no action counted."""
    if game.over:
        raise GameStateError("종료된 실행입니다")
    before = len(game.events)
    game.emit("end", outcome="api_error")
    game.over = True
    game.outcome = "api_error"
    return _result(game, before)


def to_log(game):
    """Full run log. Ended games only; satisfies log.schema.json."""
    if not game.over:
        raise GameStateError("끝나지 않은 실행입니다")
    log = {
        "run_id": game.run_id,
        "persona": copy.deepcopy(game.persona),
        "puzzle_set_id": game.puzzle_set_id,
        "model": game.model,
        "events": copy.deepcopy(game.events),
    }
    if game.seed is not None:
        log["seed"] = game.seed
    return log

