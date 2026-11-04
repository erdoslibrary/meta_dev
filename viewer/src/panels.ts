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
  floor?: string | null;
}

function findObject(space: SpaceData | null, id: string): SpaceObject | null {
  if (!space) return null;
  for (const o of space.objects) {
    if (o.id === id) return o;
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
    empty.textContent = "사진 없음";
    frame.appendChild(empty);
  });
  if (src) img.src = src;
  else {
    const empty = document.createElement("div");
    empty.className = "photo-empty";
    empty.textContent = "사진 없음";
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

function showFailedAnswer(
  feed: HTMLElement, n: number, opts: PanelOptions
): void {
  if (!opts.fileLog) {
    const rev = opts.reveals ? opts.reveals[String(n)] : undefined;
    if (rev && rev.answer) {
      panelText(feed, "정답: " + rev.answer);
      if (rev.next_instruction) panelText(feed, "다음: " + rev.next_instruction);
    } else {
      panelText(feed, "정답 데이터 없음");
    }
    return;
  }
  const entry = findEntry(opts.filePuzzle, n) as FilePuzzleEntry | null;
  if (entry && entry.answer) {
    panelText(feed, "정답: " + entry.answer);
    if (entry.next_instruction) panelText(feed, "다음: " + entry.next_instruction);
  } else {
    panelText(feed, "정답 데이터 없음");
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
  let dialogueIdx = 0;
  let dialoguePuzzle = 0;
  const ended: PuzzleEndedEvent[] = [];

  for (const e of events) {
    if ((e.type === "move" || e.type === "view") && opts.floor) {
      if (eventFloor(e) !== opts.floor) continue;
    }
    if (e.type === "view") {
      const v = e as ViewEvent;
      const obj = findObject(opts.space, v.value);
      const file = obj && obj.photos.length > 0 ? obj.photos[0] : "";
      panelPhoto(
        feed, file ? opts.photoBase + "photos/" + file : "",
        obj ? obj.label : "사물 사진"
      );
      panelText(feed, "보기: " + v.value);
    } else if (e.type === "npc_dialogue") {
      const n = e as NpcDialogueEvent;
      const name = opts.npcNames[n.npc] || n.npc;
      if (n.puzzle !== dialoguePuzzle) {
        dialoguePuzzle = n.puzzle;
        dialogueIdx = 0;
      }
      const entry = findEntry(staticPuzzle, n.puzzle);
      const line = entry && entry.dialogue && entry.dialogue[dialogueIdx];
      dialogueIdx++;
      panelText(feed, name + ": " + (line ? line.text : "(대화)"));
    } else if (e.type === "answer_submitted") {
      const a = e as AnswerSubmittedEvent;
      panelText(feed, "제출: " + a.value + (a.correct ? " (정답)" : " (오답)"));
      const entry = findEntry(staticPuzzle, a.puzzle);
      if (entry) {
        if (a.correct && entry.on_correct) panelText(feed, entry.on_correct);
        else if (!a.correct && entry.on_wrong) panelText(feed, entry.on_wrong);
      }
    } else if (e.type === "hint_revealed") {
      panelText(feed, "힌트 Lv." + (e as HintRevealedEvent).level);
    } else if (e.type === "puzzle_ended") {
      const pe = e as PuzzleEndedEvent;
      ended.push(pe);
      panelText(
        feed,
        "퍼즐 " + pe.puzzle + " 결과: " + pe.result,
        pe.result === "failed" ? "seal" : undefined
      );
      if (pe.result === "failed") showFailedAnswer(feed, pe.puzzle, opts);
    }
  }

  for (const pe of ended) {
    panelText(resultBox, "퍼즐 " + pe.puzzle + ": " + pe.result);
  }
  const last = events.length > 0 ? events[events.length - 1] : null;
  if (last && last.type === "end") {
    const outcome = (last as EndEvent).outcome;
    panelText(
      resultBox,
      outcome === "completed" ? "완주" : "끊김(" + outcome + "): 완주 아님"
    );
  }
}
