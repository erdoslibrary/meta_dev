/* Ghost: ordered playback state over start -> move -> view -> npc -> submit -> hint/end. */
import { LogEvent } from "./types";

export class GhostPlayer {
  private idx = 0;
  readonly events: LogEvent[];
  readonly startCell: string;
  position: string;

  constructor(startCell: string, events: LogEvent[]) {
    this.startCell = startCell;
    this.events = events;
    this.position = startCell;
  }

  reset(): void {
    this.idx = 0;
    this.position = this.startCell;
  }

  get done(): boolean {
    return this.idx >= this.events.length;
  }

  get step(): number {
    return this.idx;
  }

  /** Advance one event; move events update position. Returns null at end. */
  next(): LogEvent | null {
    if (this.done) return null;
    const ev = this.events[this.idx];
    this.idx++;
    if (ev.type === "move" && ev.value) this.position = ev.value;
    return ev;
  }
}
