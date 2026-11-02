"""The Legal Agent: the agentic loop.

run_agent works the case; resume_run continues a run that stopped.
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from agent_kit import progress, settings, tools


def _instructions(root: Path) -> str:
    # System prompt is always the file in legal_agent/, but a resumed run's
    # copy in workspace/runs/<id>/instructions.md is preserved if it exists.
    run_instructions = None
    # caller will pick the right one; default is the file next to this module
    return (Path(__file__).parent / "system_instructions.md").read_text()


def _objective(root: Path) -> str:
    return (settings.case_dir(Path(root)) / "objective.md").read_text()


def _loop(
    *,
    root: Path,
    client: OpenAI,
    run_id: str,
    instructions: str,
    messages: list,
    turns: int,
) -> dict:
    root = Path(root)
    for idx in range(turns):
        is_last = idx == turns - 1
        if is_last:
            messages.append(
                {
                    "role": "user",
                    "content": "It is your last turn. File the memo now with submit_memo using what you have. If any checklist item remains unproven, list it as a gap.",
                }
            )

        try:
            response = client.responses.create(
                model=settings.model(),
                instructions=instructions,
                input=messages,
                tools=tools.definitions(root, run_id),
            )
        except Exception as error:  # API outage -> pause so it can resume
            progress.save_progress(root, run_id, messages, status="paused", note=str(error))
            data = progress.load_progress(root, run_id)
            return {
                "run_id": run_id,
                "status": "paused",
                "turn": data["turn"],
                "note": str(error),
            }

        output = list(getattr(response, "output", []) or [])
        messages.extend(output)

        call = None
        for item in output:
            t = getattr(item, "type", None) if not isinstance(item, dict) else item.get("type")
            if t == "function_call":
                call = item
                break

        if call is None:
            # Model answered in plain text -> nudge to call a tool.
            messages.append(
                {
                    "role": "user",
                    "content": "Call exactly one tool. Never answer in plain text.",
                }
            )
            progress.save_progress(root, run_id, messages, response, status="running")
            continue

        result = tools.run(client, root, run_id, call)
        call_id = getattr(call, "call_id", None)
        if call_id is None and isinstance(call, dict):
            call_id = call.get("call_id", "")

        messages.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result),
            }
        )

        status = result.get("status", "running") if isinstance(result, dict) else "running"
        progress.save_progress(root, run_id, messages, response, status=status)
        if status != "running":
            data = progress.load_progress(root, run_id)
            out: dict = {"run_id": run_id, "status": status, "turn": data["turn"]}
            # keep note if present (e.g. paused)
            if isinstance(result, dict) and result.get("error"):
                out["note"] = result["error"]
            return out

    data = progress.load_progress(root, run_id)
    if data["status"] == "running":
        progress.save_progress(root, run_id, messages, status="paused")
        data = progress.load_progress(root, run_id)
        return {"run_id": run_id, "status": "paused", "turn": data["turn"], "note": "turn limit reached"}
    return {"run_id": run_id, "status": data["status"], "turn": data["turn"]}


def run_agent(*, root: Path, client: OpenAI, turns: int = 30) -> dict:
    root = Path(root)
    instructions = _instructions(root)
    objective = _objective(root)
    run_id = progress.new_run(root, instructions=instructions, objective=objective)
    messages: list = [{"role": "user", "content": objective}]
    return _loop(
        root=root, client=client, run_id=run_id, instructions=instructions, messages=messages, turns=turns
    )


def resume_run(*, root: Path, run_id: str, client: OpenAI, turns: int = 15) -> dict:
    root = Path(root)
    # Prefer the run's own instructions copy so a resumed run keeps its original prompt.
    run_instr_path = root / "workspace/runs" / run_id / "instructions.md"
    if run_instr_path.is_file():
        instructions = run_instr_path.read_text()
    else:
        instructions = _instructions(root)

    data = progress.load_progress(root, run_id)
    step = progress.resume(root, run_id)
    if step["message"] is None:
        return {
            "run_id": run_id,
            "status": step["status"],
            "turn": data["turn"],
            "note": step["note"],
        }

    messages = list(data["messages"]) + [{"role": "user", "content": step["message"]}]
    return _loop(
        root=root, client=client, run_id=run_id, instructions=instructions, messages=messages, turns=turns
    )
