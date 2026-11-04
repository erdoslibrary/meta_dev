/* Playback-order validation (spec Edge Cases, data-model Validation Rules). */
import { LogEvent } from "./types";

export interface ParseResult {
  ok: boolean;
  reason: string;
}

/** Refuse playback unless events pass schema order: t from 1 by 1, last only end. */
export function validatePlaybackOrder(events: LogEvent[]): ParseResult {
  if (events.length === 0) {
    return { ok: false, reason: "재생 거부: 이벤트가 비어 있다." };
  }
  for (let i = 0; i < events.length; i++) {
    if (events[i].t !== i + 1) {
      return { ok: false, reason: `재생 거부: t가 1부터 1씩 증가하지 않는다 (index ${i}, t=${events[i].t}).` };
    }
    if (events[i].type === "end" && i !== events.length - 1) {
      return { ok: false, reason: "재생 거부: 마지막이 아닌 지점에 end가 있다." };
    }
  }
  const last = events[events.length - 1];
  if (last.type !== "end") {
    return { ok: false, reason: "재생 거부: 마지막 이벤트가 end가 아니다." };
  }
  return { ok: true, reason: "" };
}
