/* Entry: US1 trajectory + US2 ghost wiring. */
import { RunLog, SetBundle } from "./types";
import { builtinData, loadLogFile } from "./dataload";
import { validatePlaybackOrder } from "./logparse";
import { createStage } from "./scene";
import { cellToXY } from "./plane";
import { buildFloorViews, showFloor, FloorView } from "./floors";
import { GhostPlayer } from "./ghost";
import { renderEvent, clearPanels } from "./panels";
import { showLanding } from "./order";

let stage: ReturnType<typeof createStage> | null = null;
let ghost: GhostPlayer | null = null;
let bundle: SetBundle | null = null;
let setName = "";
let marker: THREE.Mesh | null = null;
let timer: number | null = null;

function status(msg: string): void {
  const el = document.getElementById("status");
  if (el) textContentSafe(el, msg);
}

function textContentSafe(el: HTMLElement, msg: string): void {
  el.textContent = msg;
}

/** Default log: oracle r0 when bundled, else the first available log. */
export function defaultLog(): { name: string; key: string; log: RunLog } | null {
  const data = builtinData();
  if (!data) return null;
  for (const name of Object.keys(data.sets)) {
    const logs = data.sets[name].logs;
    if (logs["oracle/r0"]) return { name, key: "oracle/r0", log: logs["oracle/r0"] };
    const keys = Object.keys(logs);
    if (keys.length > 0) return { name, key: keys[0], log: logs[keys[0]] };
  }
  const tkeys = Object.keys(data.testdata);
  if (tkeys.length > 0) {
    return { name: "", key: tkeys[0], log: data.testdata[tkeys[0]] };
  }
  return null;
}

function moveMarker(cell: string): void {
  if (!marker) return;
  try {
    const p = cellToXY(cell);
    marker.position.set(p.x, p.y, 4);
  } catch {
    /* unknown cell: leave marker */
  }
}

function stepGhost(): void {
  if (!ghost || !bundle || ghost.done) {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
    return;
  }
  const ev = ghost.next()!;
  moveMarker(ghost.position);
  renderEvent({ setName, space: bundle.space, puzzle: bundle.puzzle, npc: bundle.npc }, ev);
}

export function showLog(name: string, log: RunLog): void {
  const data = builtinData();
  bundle = (name ? data?.sets[name] : null) ?? data?.sets[Object.keys(data?.sets ?? {})[0]] ?? null;
  if (!bundle || !stage) {
    status("데이터 없음");
    return;
  }
  setName = name || Object.keys(data!.sets)[0];
  const check = validatePlaybackOrder(log.events);
  if (!check.ok) {
    status(check.reason);
    return;
  }
  while (stage.scene.children.length > 1) {
    stage.scene.remove(stage.scene.children[1]);
  }
  clearPanels();
  const views: FloorView[] = buildFloorViews(bundle.space, bundle.puzzle.start_cell, log.events);
  for (const v of views) stage.scene.add(v.group);
  renderFloorSelector(views);

  const markerGeo = new THREE.SphereGeometry(10, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0xa0322b });
  marker = new THREE.Mesh(markerGeo, markerMat);
  stage.scene.add(marker);

  ghost = new GhostPlayer(bundle.puzzle.start_cell, log.events);
  moveMarker(ghost.position);
  const moves = log.events.filter((e) => e.type === "move").length;
  const end = log.events[log.events.length - 1];
  const tail = end.type === "end" && end.outcome !== "completed"
    ? ` 끊김(${end.outcome}) 표시.`
    : " 완주.";
  status(`궤적 점 ${moves + 1} = move ${moves} + 1.${tail}`);
}

function renderFloorSelector(views: FloorView[]): void {
  const box = document.getElementById("floors");
  if (!box) return;
  box.innerHTML = "";
  if (views.length < 2) {
    box.style.display = "none";
    return;
  }
  box.style.display = "block";
  for (const v of views) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = v.id;
    btn.addEventListener("click", () => showFloor(views, v.id));
    box.appendChild(btn);
  }
}

function init(): void {
  const canvas = document.getElementById("map") as HTMLCanvasElement;
  if (!canvas) return;
  stage = createStage(canvas);
  // Entry method (Slice 4 decision): explicit button on the landing screen.
  showLanding(() => {
    enterProgram();
  });
  pendingFirst = defaultLog();
}

let pendingFirst: { name: string; log: RunLog } | null = null;

function enterProgram(): void {
  const first = pendingFirst;
  if (first) showLog(first.name, first.log);
  else status("내장 데이터 없음. 로그 파일을 선택하세요.");

  const input = document.getElementById("logfile") as HTMLInputElement;
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      const log = await loadLogFile(file);
      showLog(first ? first.name : "", log);
    } catch (e) {
      status(String(e));
    }
  });

  document.getElementById("play")!.addEventListener("click", () => {
    if (timer !== null) return;
    timer = window.setInterval(stepGhost, 800);
  });
  document.getElementById("step")!.addEventListener("click", stepGhost);
  document.getElementById("reset")!.addEventListener("click", () => {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
    if (ghost && bundle) {
      ghost.reset();
      clearPanels();
      moveMarker(ghost.position);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
