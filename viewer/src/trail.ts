/* Footprint trail: start_cell + move order as Line + Points. */
import { LogEvent } from "./types";
import { INK, SEAL_RED } from "./theme";
import { cellToXY } from "./plane";

export interface Trail {
  group: THREE.Group;
  pointCount: number;
  stuck: boolean;
}

/** Points = move events + 1 (US1 independent test). Stuck end -> seal-red tail. */
export function buildTrail(startCell: string, events: LogEvent[]): Trail {
  const moves = events.filter((e) => e.type === "move").map((e) => String(e.value));
  const cells = [startCell, ...moves];
  const pts = cells.map((c) => {
    const p = cellToXY(c);
    return new THREE.Vector3(p.x, p.y, 2);
  });
  const end = events[events.length - 1];
  const stuck = end.type === "end" && end.outcome !== "completed";

  const group = new THREE.Group();
  group.name = "trail";
  const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
  group.add(new THREE.Line(lineGeo, new THREE.LineBasicMaterial({ color: INK })));
  const dotGeo = new THREE.BufferGeometry().setFromPoints(pts);
  group.add(new THREE.Points(dotGeo, new THREE.PointsMaterial({ color: INK, size: 6 })));

  if (stuck && pts.length > 1) {
    const tail = new THREE.BufferGeometry().setFromPoints(pts.slice(-2));
    group.add(new THREE.Line(tail, new THREE.LineBasicMaterial({ color: SEAL_RED })));
    const mark = new THREE.BufferGeometry().setFromPoints([pts[pts.length - 1]]);
    group.add(new THREE.Points(mark, new THREE.PointsMaterial({ color: SEAL_RED, size: 14 })));
  }
  return { group, pointCount: pts.length, stuck };
}
