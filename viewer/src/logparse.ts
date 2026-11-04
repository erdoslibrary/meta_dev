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
  if (!required) return "알 수 없는 이벤트 종류: " + kind;
  for (const field of required) {
    if (!(field in ev)) return kind + "에 " + field + " 없음";
  }
  if (kind === "move" || kind === "view") {
    const value = ev["value"];
    if (typeof value !== "string") return kind + ".value가 문자열 아님";
    const ok = kind === "move" ? CELL_RE.test(value) : OBJECT_RE.test(value);
    if (!ok) return kind + ".value 형식 오류: " + value;
  }
  if (kind === "npc_dialogue" && typeof ev["npc"] !== "string") {
    return "npc_dialogue.npc가 문자열 아님";
  }
  if (kind === "answer_submitted") {
    if (typeof ev["value"] !== "string") return "answer_submitted.value가 문자열 아님";
    if (typeof ev["attempt"] !== "number") return "answer_submitted.attempt가 숫자 아님";
    if (typeof ev["correct"] !== "boolean") return "answer_submitted.correct가 불리언 아님";
  }
  if (kind === "hint_revealed" && typeof ev["level"] !== "number") {
    return "hint_revealed.level이 숫자 아님";
  }
  if (kind === "rejected" && typeof ev["error"] !== "string") {
    return "rejected.error가 문자열 아님";
  }
  const enums = EVENT_ENUMS[kind];
  if (enums) {
    for (const field of Object.keys(enums)) {
      const value = ev[field];
      if (typeof value !== "string" || enums[field].indexOf(value) < 0) {
        return kind + "." + field + " 값 오류";
      }
    }
  }
  return null;
}

/** Null when playable, otherwise a Korean refusal reason for display. */
function validateLogForPlayback(doc: unknown): string | null {
  if (!isRecord(doc)) return "로그가 객체 아님";
  for (const field of ["run_id", "persona", "puzzle_set_id", "model", "events"]) {
    if (!(field in doc)) return "최상위 " + field + " 없음";
  }
  if (typeof doc["run_id"] !== "string") return "run_id가 문자열 아님";
  if (typeof doc["puzzle_set_id"] !== "string") return "puzzle_set_id가 문자열 아님";
  if (typeof doc["model"] !== "string") return "model가 문자열 아님";
  if (!Array.isArray(doc["events"]) || doc["events"].length < 1) {
    return "events가 비어 있음";
  }
  const events = doc["events"] as unknown[];
  for (let i = 0; i < events.length; i++) {
    const raw = events[i];
    if (!isRecord(raw)) return (i + 1) + "번째 이벤트가 객체 아님";
    const t = raw["t"];
    const puzzle = raw["puzzle"];
    const type = raw["type"];
    if (t !== i + 1) return "t가 1부터 1씩 증가하지 않음 (위치 " + (i + 1) + ")";
    if (typeof puzzle !== "number") return "puzzle이 숫자 아님 (t=" + t + ")";
    if (typeof type !== "string") return "type이 문자열 아님 (t=" + t + ")";
    const bad = checkEventKind(type, raw);
    if (bad) return bad + " (t=" + t + ")";
  }
  const last = events[events.length - 1] as { [k: string]: unknown };
  if (last["type"] !== "end") return "마지막 이벤트가 end 아님";
  for (let i = 0; i < events.length - 1; i++) {
    const mid = events[i] as { [k: string]: unknown };
    if (mid["type"] === "end") return "끝이 아닌 위치에 end 있음 (t=" + mid["t"] + ")";
  }
  return null;
}
