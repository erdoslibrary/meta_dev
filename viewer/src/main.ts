/* Program entry + US1 wiring (global script, runs after DOMContentLoaded). */

let currentLog: RunLog | null = null;
let currentStatic: { space: SpaceData; puzzle: PuzzleData } | null = null;
let filePuzzle: FilePuzzleData | null = null;
let currentReveal: { [puzzleNumber: string]: RevealEntry } | null = null;
let currentFileLog = false;
let currentPhotoBase = "";
let currentNpcNames: { [id: string]: string } = {};
let logFloorKeys: string[] = [];
let activeFloor: string | null = null;
let ghost: Ghost | null = null;
let playTimer = 0;
let contentGroup: THREE.Group | null = null;

function el(id: string): HTMLElement | null {
  return document.getElementById(id);
}

function setStatus(text: string): void {
  const s = el("status");
  if (s) s.textContent = text;
}

function staticFor(log: RunLog, data: RtData | null): { space: SpaceData; puzzle: PuzzleData } | null {
  if (!data) return null;
  const set = data.sets[log.puzzle_set_id];
  if (set) return { space: set.space, puzzle: set.puzzle };
  const sample = data.sample_sets[log.puzzle_set_id];
  if (sample && sample.space && sample.puzzle) {
    return { space: sample.space, puzzle: sample.puzzle };
  }
  return null;
}

function moveCells(log: RunLog, upto: number): string[] {
  const cells: string[] = [];
  const events = log.events.slice(0, upto);
  for (const e of events) {
    if (e.type === "move") cells.push((e as MoveEvent).value);
  }
  return cells;
}

function logOutcome(log: RunLog, upto: number): EndEvent | PuzzleEndedEvent | null {
  const events = log.events.slice(0, upto);
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.type === "end" || e.type === "puzzle_ended") {
      return e as EndEvent | PuzzleEndedEvent;
    }
  }
  return null;
}

function renderAll(): void {
  const scene = currentScene();
  if (!scene) return;
  if (contentGroup) {
    scene.remove(contentGroup);
    contentGroup = null;
  }
  if (!currentLog || !ghost) {
    const info0 = el("trail-info");
    if (info0) info0.textContent = "";
    const feed0 = el("ghost");
    if (feed0) feed0.textContent = "";
    const resultBox0 = el("result");
    if (resultBox0) resultBox0.textContent = "";
    return;
  }
  contentGroup = new THREE.Group();
  scene.add(contentGroup);

  const log = currentLog;
  const st = ghost.state();
  const space = currentStatic ? currentStatic.space : null;
  const multi = logFloorKeys.length > 1;
  const activeKey = multi ? (activeFloor || logFloorKeys[0]) : logFloorKeys[0];
  const activeFloorObj = space && activeKey !== undefined ? floorForKey(space, activeKey) : null;
  const columns = activeFloorObj ? activeFloorObj.columns : 6;
  const rows = activeFloorObj ? activeFloorObj.rows : 6;
  setSceneExtent(columns, rows);
  const visible = multi ? activeFloor : null;
  if (space) {
    const explored = st.t > 0;
    const targetFloor = activeFloorObj || space.floors[0];
    for (const floor of space.floors) {
      const key = floor.id || "";
      if (multi && key !== (visible || logFloorKeys[0])) continue;
      if (!multi && floor !== targetFloor) continue;
      contentGroup.add(buildFloorPlane(floor, explored));
    }
  }
  const start = currentStatic ? currentStatic.puzzle.start_cell : "A1";
  const onFloor = (cell: string): boolean =>
    !multi || floorKeyOfCell(cell) === (visible || logFloorKeys[0]);
  const moves = moveCells(log, st.t);
  const seq = [start].concat(moves);
  const cells = seq.filter(onFloor);
  const pts = cells.map((c) => cellToXY(c, columns, rows));
  const tail = logOutcome(log, st.t);
  const redSeal: number[] = [];
  const filteredIndex = (u: number): number | null => {
    if (!onFloor(seq[u])) return null;
    let k = -1;
    for (let i = 0; i <= u; i++) if (onFloor(seq[i])) k++;
    return k;
  };
  if (tail && tail.type === "end" && tail.outcome !== "completed") {
    if (cells.length >= 2) redSeal.push(cells.length - 2, cells.length - 1);
    else if (cells.length === 1) redSeal.push(0);
  }

  // Mark puzzle results at the cell where each puzzle ended.
  const events = log.events.slice(0, st.t);
  let mi = 0;
  const marks: { pos: TrailPoint; result: "solved_by_dialogue" | "solved_with_hint" | "failed" }[] = [];
  for (const e of events) {
    if (e.type === "move") mi++;
    if (e.type === "puzzle_ended") {
      const pe = e as PuzzleEndedEvent;
      const atCell = mi === 0 ? cells[0] : moves[mi - 1];
      if (!atCell || !onFloor(atCell)) continue;
      const pos = cellToXY(atCell, columns, rows);
      marks.push({ pos, result: pe.result });
      if (pe.result === "failed") {
        const j = filteredIndex(mi);
        if (j !== null) {
          if (j > 0) redSeal.push(j - 1);
          redSeal.push(j);
        }
      }
    }
  }
  const trail = buildTrail(pts, redSeal);
  for (const mk of marks) addResultMarker(trail, mk.pos, mk.result);
  contentGroup.add(trail);

  const movesTotal = moveCells(log, log.events.length).length;
  const info = el("trail-info");
  if (info) {
    const scope = multi ? "층 " + floorLabel(visible || logFloorKeys[0]) + " " : "";
    info.textContent = scope + "발자국 " + pts.length + "점 (move " + movesTotal + " + 시작점)";
  }
  if (tail && tail.type === "end" && tail.outcome !== "completed") {
    setStatus("끊김(" + tail.outcome + "): 끊긴 지점에서 멈춤. 끝까지 재생되지 않음.");
  } else if (tail && tail.type === "puzzle_ended" && tail.result === "failed") {
    setStatus("실패 구간: Seal Red 표시.");
  } else if (st.t >= log.events.length) {
    setStatus("재생 완료.");
  } else {
    setStatus("재생 중: " + st.t + "/" + log.events.length);
  }
  const feed = el("ghost");
  const resultBox = el("result");
  if (feed && resultBox) {
    renderPanels(feed, resultBox, log, st.t, {
      space: currentStatic ? currentStatic.space : null,
      puzzle: currentStatic ? currentStatic.puzzle : null,
      filePuzzle,
      reveals: currentReveal,
      fileLog: currentFileLog,
      photoBase: currentPhotoBase,
      npcNames: currentNpcNames,
      floor: multi ? (visible || logFloorKeys[0]) : null,
    });
  }
  onSceneRebuild(renderAll);
}

function setLog(log: RunLog, data: RtData | null, logKey: string | null): void {
  const bad = validateLogForPlayback(log);
  if (bad) {
    stopPlay();
    currentLog = null;
    ghost = null;
    renderAll();
    setStatus("재생 거부: " + bad);
    return;
  }
  currentLog = log;
  currentStatic = staticFor(log, data);
  currentFileLog = (logKey === null);
  currentReveal = null;
  if (data && logKey !== null) {
    const set = data.sets[log.puzzle_set_id];
    if (set && set.reveals) currentReveal = set.reveals[logKey] ?? null;
    else {
      const sample = data.sample_sets[log.puzzle_set_id];
      if (sample && sample.reveals) currentReveal = sample.reveals[logKey] ?? null;
    }
  }
  currentPhotoBase = "";
  currentNpcNames = {};
  if (data) {
    const set = data.sets[log.puzzle_set_id];
    if (set) {
      currentPhotoBase = "../data/" + log.puzzle_set_id + "/";
      currentNpcNames[set.npc.id] = set.npc.name;
    } else {
      const sample = data.sample_sets[log.puzzle_set_id];
      if (sample) {
        currentPhotoBase = "testdata/sets/" + log.puzzle_set_id + "/";
        if (sample.npc) currentNpcNames[sample.npc.id] = sample.npc.name;
      }
    }
  }
  const startCell = currentStatic ? currentStatic.puzzle.start_cell : "A1";
  logFloorKeys = logFloors(log, startCell);
  activeFloor = logFloorKeys.length > 0 ? logFloorKeys[0] : null;
  const floorSel = el("floor") as HTMLSelectElement | null;
  if (floorSel) {
    floorSel.innerHTML = "";
    if (logFloorKeys.length > 1) {
      floorSel.style.display = "";
      for (const key of logFloorKeys) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = floorLabel(key);
        floorSel.appendChild(opt);
      }
      floorSel.value = activeFloor || "";
    } else {
      floorSel.style.display = "none";
    }
  }
  ghost = new Ghost(log, startCell);
  ghost.reset();
  stopPlay();
  renderAll();
}

function stepOnce(): void {
  if (!currentLog || !ghost) return;
  const e = ghost.next();
  renderAll();
  if (e === null) stopPlay();
}

function stopPlay(): void {
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = 0;
  }
}

function startPlay(): void {
  if (!currentLog || !ghost || playTimer) return;
  playTimer = window.setInterval(() => {
    if (!currentLog || !ghost || ghost.state().t >= currentLog.events.length) {
      stopPlay();
      return;
    }
    stepOnce();
  }, 500);
}

function builtinLogEntries(data: RtData): { label: string; log: RunLog; key: string }[] {
  const out: { label: string; log: RunLog; key: string }[] = [];
  for (const setName of Object.keys(data.sets)) {
    const set = data.sets[setName];
    for (const key of Object.keys(set.logs)) {
      out.push({ label: setName + "/" + key, log: set.logs[key], key });
    }
  }
  for (const name of Object.keys(data.testdata)) {
    out.push({ label: "testdata/" + name, log: data.testdata[name], key: "testdata/" + name });
  }
  for (const name of Object.keys(data.refusal)) {
    out.push({ label: "refusal/" + name, log: data.refusal[name], key: "refusal/" + name });
  }
  return out;
}

function fillLogSelect(data: RtData | null): void {
  const sel = el("logsel") as HTMLSelectElement | null;
  if (!sel || !data) return;
  sel.innerHTML = "";
  const entries = builtinLogEntries(data);
  for (let i = 0; i < entries.length; i++) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = entries[i].label;
    sel.appendChild(opt);
  }
  sel.onchange = () => {
    const idx = parseInt(sel.value, 10);
    if (!isNaN(idx) && entries[idx]) setLog(entries[idx].log, data, entries[idx].key);
  };
  if (entries.length > 0) setLog(entries[0].log, data, entries[0].key);
}

function startApp(): void {
  const canvas = document.getElementById("map") as HTMLCanvasElement | null;
  if (canvas) startScene(canvas);
  const data = builtinData();
  fillLogSelect(data);
  if (!data) setStatus("내장 기록 없음. 파일로 로그를 열어주세요.");

  const enter = el("enter");
  if (enter) {
    enter.addEventListener("click", () => {
      const landing = el("landing");
      const app = el("app");
      if (landing) landing.style.display = "none";
      if (app) app.style.display = "block";
    });
  }
  const floorSel = el("floor") as HTMLSelectElement | null;
  if (floorSel) {
    floorSel.addEventListener("change", () => {
      activeFloor = floorSel.value;
      renderAll();
    });
  }
  const play = el("play");
  if (play) play.addEventListener("click", startPlay);
  const step = el("step");
  if (step) step.addEventListener("click", () => { stopPlay(); stepOnce(); });
  const reset = el("reset");
  if (reset) {
    reset.addEventListener("click", () => {
      if (!currentLog || !ghost) return;
      ghost.reset();
      stopPlay();
      renderAll();
    });
  }
  const puzzleFile = el("puzzlefile") as HTMLInputElement | null;
  if (puzzleFile) {
    puzzleFile.addEventListener("change", () => {
      if (!puzzleFile.files || puzzleFile.files.length === 0) return;
      loadPuzzleFile(puzzleFile.files[0]).then(
        (puzzle) => {
          filePuzzle = puzzle;
          setStatus("퍼즐 데이터 선택됨.");
          renderAll();
        },
        (err) => setStatus("퍼즐 읽기 실패: " + String(err && (err as Error).message || err))
      );
    });
  }
  const file = el("logfile") as HTMLInputElement | null;
  if (file) {
    file.addEventListener("change", () => {
      if (!file.files || file.files.length === 0) return;
      loadLogFile(file.files[0]).then(
        (log) => setLog(log, builtinData(), null),
        (err) => setStatus("재생 거부: " + String(err && (err as Error).message || err))
      );
    });
  }
  onSceneRebuild(renderAll);
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    playOrderIntro();
    startApp();
  });
}
