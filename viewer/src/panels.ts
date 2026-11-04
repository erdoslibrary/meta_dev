/* Panels: per-event feed + per-puzzle results (global script, FR-005).
   Never shows: next_object_id, photo paths/hashes, unreleased hints,
   reason, answers of non-failed puzzles. Photos via <img>; missing photo
   becomes an empty frame so trajectory/dialogue continue. */

interface PanelOptions {
  space: SpaceData | null;
  puzzle: PuzzleData | null;
  filePuzzle: FilePuzzleData | null;
  reveals: { [puzzleNumber: string]: RevealEntry } | null;
  fileLog: boolean;
  photoBase: string;
  npcNames: { [id: string]: string };
  npcs?: { [id: string]: NpcData };
  floor?: string | null;
  subStep?: number;
}

function findObject(space: SpaceData | null, id: string): SpaceObject | null {
  if (!space) return null;
  for (const o of space.objects) {
    if (o.id === id) return o;
  }
  return null;
}

function findRoomName(space: SpaceData | null, cell: string): string | null {
  if (!space || !space.rooms) return null;
  let target: { col: number; row: number };
  try {
    target = parseCell(cell);
  } catch {
    return null;
  }
  const targetFloor = floorKeyOfCell(cell);
  for (const room of space.rooms) {
    if (!room.cells) continue;
    const parts = room.cells.split(":");
    const cStart = parts[0].trim();
    const cEnd = (parts.length > 1 ? parts[1] : parts[0]).trim();
    if (floorKeyOfCell(cStart) !== targetFloor) continue;
    try {
      const a = parseCell(cStart);
      const b = parseCell(cEnd);
      const minCol = Math.min(a.col, b.col);
      const maxCol = Math.max(a.col, b.col);
      const minRow = Math.min(a.row, b.row);
      const maxRow = Math.max(a.row, b.row);
      if (
        target.col >= minCol && target.col <= maxCol &&
        target.row >= minRow && target.row <= maxRow
      ) {
        return room.name;
      }
    } catch {
      continue;
    }
  }
  return null;
}

function panelText(parent: HTMLElement, text: string, cls?: string): HTMLElement {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.textContent = text;
  parent.appendChild(div);
  return div;
}

function panelPhoto(
  parent: HTMLElement, src: string, label: string
): void {
  const frame = document.createElement("div");
  frame.className = "photo";
  const img = document.createElement("img");
  img.alt = label;
  img.addEventListener("error", () => {
    frame.textContent = "";
    const empty = document.createElement("div");
    empty.className = "photo-empty";
    empty.textContent = t("photo.empty");
    frame.appendChild(empty);
  });
  if (src) img.src = src;
  else {
    const empty = document.createElement("div");
    empty.className = "photo-empty";
    empty.textContent = t("photo.empty");
    frame.appendChild(empty);
    parent.appendChild(frame);
    return;
  }
  frame.appendChild(img);
  parent.appendChild(frame);
}

function findEntry(
  puzzle: PuzzleData | FilePuzzleData | null, n: number
): PuzzleEntry | null {
  if (!puzzle) return null;
  for (const e of puzzle.puzzles) {
    if (e.number === n) return e;
  }
  return null;
}

function countEventSubSteps(
  e: LogEvent, staticPuzzle: PuzzleData | FilePuzzleData | null
): number {
  if (e.type === "npc_dialogue") {
    const entry = findEntry(staticPuzzle, e.puzzle);
    const dLen =
      entry && entry.dialogue && entry.dialogue.length > 0
        ? entry.dialogue.length
        : 1;
    const hasQuiz =
      entry && ((entry.image && entry.image.path) || entry.question) ? 1 : 0;
    return 1 + dLen + hasQuiz;
  }
  if (e.type === "answer_submitted") {
    const entry = findEntry(staticPuzzle, e.puzzle);
    const hasReact =
      entry && (e.correct ? entry.on_correct : entry.on_wrong) ? 1 : 0;
    return 1 + hasReact;
  }
  return 1;
}

function buildChronicleSteps(
  log: RunLog, staticPuzzle: PuzzleData | FilePuzzleData | null
): ChronicleStep[] {
  const steps: ChronicleStep[] = [{ upto: 0, subStep: 0 }];
  for (let i = 0; i < log.events.length; i++) {
    const totalSub = countEventSubSteps(log.events[i], staticPuzzle);
    for (let s = 1; s <= totalSub; s++) {
      steps.push({ upto: i + 1, subStep: s });
    }
  }
  return steps;
}

function showFailedAnswer(
  feed: HTMLElement, n: number, opts: PanelOptions
): void {
  if (!opts.fileLog) {
    const rev = opts.reveals ? opts.reveals[String(n)] : undefined;
    if (rev && rev.answer) {
      panelText(feed, t("answer.label", rev.answer));
      if (rev.next_instruction) panelText(feed, t("answer.next", td(rev.next_instruction)));
    } else {
      panelText(feed, t("answer.missing"));
    }
    return;
  }
  const entry = findEntry(opts.filePuzzle, n) as FilePuzzleEntry | null;
  if (entry && entry.answer) {
    panelText(feed, t("answer.label", entry.answer));
    if (entry.next_instruction) panelText(feed, t("answer.next", td(entry.next_instruction)));
  } else {
    panelText(feed, t("answer.missing"));
  }
}

function renderPanels(
  feed: HTMLElement, resultBox: HTMLElement,
  log: RunLog, upto: number, opts: PanelOptions
): void {
  feed.textContent = "";
  resultBox.textContent = "";
  const events = log.events.slice(0, upto);
  const staticPuzzle = opts.puzzle || opts.filePuzzle;
  const ended: PuzzleEndedEvent[] = [];

  if (log.persona) {
    panelText(
      feed,
      t(
        "feed.participant", log.persona.age, td(log.persona.job),
        td(log.persona.vocab), td(log.persona.thinking)
      ),
      "chron-intro"
    );
  }
  if (staticPuzzle && staticPuzzle.start_instruction) {
    panelText(
      feed,
      t("feed.start", td(staticPuzzle.start_instruction), staticPuzzle.start_cell),
      "chron-intro"
    );
  }

  let currentCell =
    staticPuzzle && staticPuzzle.start_cell ? staticPuzzle.start_cell : "A1";

  for (let idx = 0; idx < events.length; idx++) {
    const e = events[idx];
    const subLimit =
      idx === events.length - 1 && opts.subStep !== undefined
        ? opts.subStep
        : Infinity;

    if (e.type === "move") {
      const m = e as MoveEvent;
      const prevCell = currentCell;
      currentCell = m.value;
      if (opts.floor && eventFloor(e) !== opts.floor) continue;
      const room = findRoomName(opts.space, m.value);
      panelText(
        feed,
        t("feed.move", prevCell, m.value, room ? " (" + td(room) + ")" : ""),
        "chron-move"
      );
      continue;
    }

    if (e.type === "view" && opts.floor && eventFloor(e) !== opts.floor) {
      continue;
    }

    if (e.type === "view") {
      const v = e as ViewEvent;
      const obj = findObject(opts.space, v.value);
      const file = obj && obj.photos.length > 0 ? obj.photos[0] : "";
      panelPhoto(
        feed, file ? opts.photoBase + "photos/" + file : "",
        obj ? obj.label : t("photo.fallback")
      );
      panelText(feed, t("feed.view", v.value), "chron-view");
      if (obj && (obj.label || obj.description)) {
        panelText(
          feed,
          td(obj.label) + (obj.description ? " — " + td(obj.description) : ""),
          "chron-desc"
        );
      }
    } else if (e.type === "npc_dialogue") {
      const n = e as NpcDialogueEvent;
      const npcObj = opts.npcs ? opts.npcs[n.npc] : undefined;
      const name = (npcObj && npcObj.name) || opts.npcNames[n.npc] || n.npc;
      const entry = findEntry(staticPuzzle, n.puzzle);
      const dLen =
        entry && entry.dialogue && entry.dialogue.length > 0
          ? entry.dialogue.length
          : 1;
      const hasQuiz = !!(
        entry && ((entry.image && entry.image.path) || entry.question)
      );
      if (subLimit >= 1) {
        if (npcObj && npcObj.image) {
          panelPhoto(feed, opts.photoBase + npcObj.image, td(name));
        }
        panelText(feed, t("feed.appear", td(name)), "chron-npc");
      }
      if (entry && entry.dialogue && entry.dialogue.length > 0) {
        for (let k = 0; k < entry.dialogue.length; k++) {
          if (subLimit >= 2 + k) {
            panelText(feed, td(name) + ": " + td(entry.dialogue[k].text), "chron-dialogue");
          }
        }
      } else if (subLimit >= 2) {
        panelText(feed, t("feed.nodialogue", td(name)), "chron-dialogue");
      }
      if (hasQuiz && subLimit >= 2 + dLen && entry) {
        if (entry.image && entry.image.path) {
          panelPhoto(
            feed,
            opts.photoBase + entry.image.path,
            t("feed.quizpic", n.puzzle)
          );
        }
        if (entry.question) {
          const meta = entry.answer_letter_count
            ? (entry.max_attempts
              ? t("quiz.meta.full", entry.answer_letter_count, entry.max_attempts)
              : t("quiz.meta.short", entry.answer_letter_count))
            : "";
          panelText(feed, t("feed.quiz", td(entry.question), meta), "chron-quiz");
        }
      }
    } else if (e.type === "answer_submitted") {
      const a = e as AnswerSubmittedEvent;
      if (subLimit >= 1) {
        const dv = a.value +
          (ansGloss(a.value) != null ? " (" + ansGloss(a.value) + ")" : "");
        panelText(
          feed,
          t("feed.submit", dv, a.correct ? t("submit.ok") : t("submit.ng")),
          a.correct ? "ans-ok" : "ans-wrong"
        );
      }
      if (subLimit >= 2) {
        const entry = findEntry(staticPuzzle, a.puzzle);
        if (entry) {
          if (a.correct && entry.on_correct) {
            panelText(feed, td(entry.on_correct), "chron-dialogue");
          } else if (!a.correct && entry.on_wrong) {
            panelText(feed, td(entry.on_wrong), "chron-dialogue");
          }
        }
      }
    } else if (e.type === "hint_revealed") {
      panelText(feed, t("feed.hint", (e as HintRevealedEvent).level), "chron-hint");
    } else if (e.type === "rejected") {
      const r = e as RejectedEvent;
      panelText(
        feed,
        t("feed.reject", r.attempted_action || t("reject.action"), r.error),
        "chron-reject"
      );
    } else if (e.type === "puzzle_ended") {
      const pe = e as PuzzleEndedEvent;
      ended.push(pe);
      panelText(
        feed,
        t("feed.result", pe.puzzle, pe.result),
        pe.result === "failed" ? "seal" : undefined
      );
      if (pe.result === "failed") showFailedAnswer(feed, pe.puzzle, opts);
    }
  }

  for (const pe of ended) {
    panelText(resultBox, t("result.puzzle", pe.puzzle, pe.result));
  }
  const last = events.length > 0 ? events[events.length - 1] : null;
  if (last && last.type === "end") {
    const outcome = (last as EndEvent).outcome;
    panelText(
      resultBox,
      outcome === "completed" ? t("result.done") : t("result.cut", outcome)
    );
    if (outcome === "completed") {
      panelText(resultBox, "So long, and thanks for all the fish", "closing");
    }
  }
  if (
    feed.lastElementChild &&
    typeof feed.lastElementChild.scrollIntoView === "function"
  ) {
    feed.lastElementChild.scrollIntoView({ block: "nearest" });
  }
}
