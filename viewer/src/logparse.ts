/* Handwritten playback validation (global script, no import/export, no library).
   Checks only what playback needs. Schema details unrelated to playback
   (e.g. persona content rules) are not checked. reason is never read. */

const CELL_RE = /^(?:[1-9][0-9]*F-)?[A-Z]+[1-9][0-9]*$/;
const OBJECT_RE = /^[a-z][a-z0-9_]*@(?:[1-9][0-9]*F-)?[A-Z]+[1-9][0-9]*$/;

const EVENT_REQUIRED: { [kind: string]: string[] } = {
  move: ["value"],
  view: ["value"],
  npc_dialogue: ["npc"],
  answer_submitted: ["value", "attempt", "correct"],
  hint_revealed: ["level"],
  puzzle_ended: ["result", "attempts_used"],
  rejected: ["attempted_action", "error"],
  end: ["outcome"],
};

const EVENT_ENUMS: { [kind: string]: { [field: string]: string[] } } = {
  puzzle_ended: { result: ["solved_by_dialogue", "solved_with_hint", "failed"] },
  end: { outcome: ["completed", "action_limit", "api_error"] },
};

function isRecord(v: unknown): v is { [k: string]: unknown } {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function checkEventKind(kind: string, ev: { [k: string]: unknown }): string | null {
  const required = EVENT_REQUIRED[kind];
  if (!required) return t("err.unknown", kind);
  for (const field of required) {
    if (!(field in ev)) return t("err.field", kind, field);
  }
  if (kind === "move" || kind === "view") {
    const value = ev["value"];
    if (typeof value !== "string") return t("err.notstr", kind);
    const ok = kind === "move" ? CELL_RE.test(value) : OBJECT_RE.test(value);
    if (!ok) return t("err.format", kind, value);
  }
  if (kind === "npc_dialogue" && typeof ev["npc"] !== "string") {
    return t("err.npc");
  }
  if (kind === "answer_submitted") {
    if (typeof ev["value"] !== "string") return t("err.ans.value");
    if (typeof ev["attempt"] !== "number") return t("err.ans.attempt");
    if (typeof ev["correct"] !== "boolean") return t("err.ans.correct");
  }
  if (kind === "hint_revealed" && typeof ev["level"] !== "number") {
    return t("err.hint");
  }
  if (kind === "rejected" && typeof ev["error"] !== "string") {
    return t("err.rejected");
  }
  const enums = EVENT_ENUMS[kind];
  if (enums) {
    for (const field of Object.keys(enums)) {
      const value = ev[field];
      if (typeof value !== "string" || enums[field].indexOf(value) < 0) {
        return t("err.enum", kind, field);
      }
    }
  }
  return null;
}

/** Null when playable, otherwise a Korean refusal reason for display. */
function validateLogForPlayback(doc: unknown): string | null {
  if (!isRecord(doc)) return t("err.notobj");
  for (const field of ["run_id", "persona", "puzzle_set_id", "model", "events"]) {
    if (!(field in doc)) return t("err.top", field);
  }
  if (typeof doc["run_id"] !== "string") return t("err.topstr", "run_id");
  if (typeof doc["puzzle_set_id"] !== "string") return t("err.topstr", "puzzle_set_id");
  if (typeof doc["model"] !== "string") return t("err.topstr", "model");
  if (!Array.isArray(doc["events"]) || doc["events"].length < 1) {
    return t("err.empty");
  }
  const events = doc["events"] as unknown[];
  for (let i = 0; i < events.length; i++) {
    const raw = events[i];
    if (!isRecord(raw)) return t("err.evobj", i + 1);
    const tn = raw["t"];
    const puzzle = raw["puzzle"];
    const type = raw["type"];
    if (tn !== i + 1) return t("err.torder", i + 1);
    if (typeof puzzle !== "number") return t("err.puzzlenum", tn);
    if (typeof type !== "string") return t("err.typestr", tn);
    const bad = checkEventKind(type, raw);
    if (bad) return bad + " (t=" + tn + ")";
  }
  const last = events[events.length - 1] as { [k: string]: unknown };
  if (last["type"] !== "end") return t("err.lastend");
  for (let i = 0; i < events.length - 1; i++) {
    const mid = events[i] as { [k: string]: unknown };
    if (mid["type"] === "end") return t("err.midend", mid["t"]);
  }
  return null;
}
