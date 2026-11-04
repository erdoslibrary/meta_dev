/* Floor views: one group per floor prefix; selector hidden when single. */
import { LogEvent, SpaceData } from "./types";
import { buildFloorPlane } from "./plane";
import { buildTrail } from "./trail";

export interface FloorView {
  id: string;
  group: THREE.Group;
}

/** "2F-C4" -> "2F", "C4" -> null. */
export function floorOf(cell: string): string | null {
  const i = cell.indexOf("-");
  return i < 0 ? null : cell.slice(0, i);
}

function fallbackFloor(id: string, like: { columns: number; rows: number }) {
  const n = like.columns * 100;
  return {
    id,
    walls: [
      { from: { x: 0, y: n }, to: { x: n, y: n } },
      { from: { x: n, y: n }, to: { x: n, y: 0 } },
      { from: { x: n, y: 0 }, to: { x: 0, y: 0 } },
      { from: { x: 0, y: 0 }, to: { x: 0, y: n } },
    ],
    doors: [],
    meters_per_pixel: 0.01,
    origin_px: { x: 0, y: n },
    columns: like.columns,
    rows: like.rows,
  };
}

/** Build one view per floor; views after the first start hidden. */
export function buildFloorViews(
  space: SpaceData,
  startCell: string,
  events: LogEvent[],
): FloorView[] {
  const moves = events.filter((e) => e.type === "move").map((e) => String(e.value));
  const prefixes: (string | null)[] = [];
  for (const c of [startCell, ...moves]) {
    const f = floorOf(c);
    if (!prefixes.includes(f)) prefixes.push(f);
  }
  const base = space.floors[0];
  const end = events[events.length - 1];
  return prefixes.map((prefix, i) => {
    const id = prefix ?? base.id;
    const def = space.floors.find((f) => f.id === id) ?? fallbackFloor(id, base);
    const group = new THREE.Group();
    group.name = "floorview-" + id;
    group.add(buildFloorPlane(def));
    const cells = [startCell, ...moves].filter((c) => floorOf(c) === prefix);
    const leg: LogEvent[] = cells.slice(1).map((c, k) => ({
      t: k + 1, puzzle: 1, type: "move", value: c,
    }));
    if (end.type === "end") leg.push({ ...end, t: leg.length + 1 });
    group.add(buildTrail(cells[0], leg).group);
    group.visible = i === 0;
    return { id, group };
  });
}

/** Show only the named floor view. */
export function showFloor(views: FloorView[], id: string): void {
  for (const v of views) v.group.visible = v.id === id;
}
