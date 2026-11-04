/* Ordered playback state (global script). start -> move -> view ->
   npc_dialogue -> answer_submitted -> (hint_revealed | puzzle_ended) ->
   next puzzle or end. */

interface SubmissionResult {
  value: string;
  correct: boolean;
  puzzle: number;
}

interface GhostState {
  t: number;
  puzzle: number;
  cell: string;
  opened: string[];
  submission: SubmissionResult | null;
  result: string | null;
  end: "completed" | "action_limit" | "api_error" | null;
  done: boolean;
}

class Ghost {
  readonly log: RunLog;
  readonly startCell: string;
  private idx = 0;
  private cell: string;
  private opened: string[] = [];
  private submission: SubmissionResult | null = null;
  private result: string | null = null;
  private end: "completed" | "action_limit" | "api_error" | null = null;
  private lastPuzzle: number | null = null;

  constructor(log: RunLog, startCell: string) {
    this.log = log;
    this.startCell = startCell;
    this.cell = startCell;
  }

  reset(): void {
    this.idx = 0;
    this.cell = this.startCell;
    this.opened = [];
    this.submission = null;
    this.result = null;
    this.end = null;
    this.lastPuzzle = null;
  }

  /** Apply the next event; null when the log is exhausted. */
  next(): LogEvent | null {
    if (this.idx >= this.log.events.length) return null;
    const e = this.log.events[this.idx];
    if (this.lastPuzzle !== null && e.puzzle !== this.lastPuzzle) {
      this.submission = null;
      this.result = null;
    }
    this.idx++;
    if (e.type === "move") {
      this.cell = (e as MoveEvent).value;
    } else if (e.type === "view") {
      const v = (e as ViewEvent).value;
      if (this.opened.indexOf(v) < 0) this.opened.push(v);
    } else if (e.type === "answer_submitted") {
      const a = e as AnswerSubmittedEvent;
      this.submission = { value: a.value, correct: a.correct, puzzle: a.puzzle };
    } else if (e.type === "puzzle_ended") {
      this.result = (e as PuzzleEndedEvent).result;
    } else if (e.type === "end") {
      this.end = (e as EndEvent).outcome;
    }
    this.lastPuzzle = e.puzzle;
    return e;
  }

  seek(n: number): void {
    this.reset();
    if (n <= 0) return;
    for (let i = 0; i < n; i++) {
      if (this.next() === null) break;
    }
  }

  state(): GhostState {
    const events = this.log.events;
    const last = events[events.length - 1];
    let puzzle = 1;
    if (this.idx > 0) {
      puzzle = events[this.idx - 1].puzzle;
    } else if (events.length > 0) {
      puzzle = events[0].puzzle;
    }
    return {
      t: this.idx,
      puzzle: puzzle,
      cell: this.cell,
      opened: this.opened.slice(),
      submission: this.submission,
      result: this.result,
      end: this.end,
      done: this.idx >= events.length && !!last && last.type === "end",
    };
  }
}
