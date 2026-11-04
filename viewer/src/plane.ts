/* Floor plane from space.json (PlaneGeometry, 1 cell = 100 units). */
import { SpaceFloor } from "./types";
import { BASE_FROM, parchmentTexture } from "./theme";

const CELL = 100;

/** "C4" -> center coords; "2F-C4" strips the floor prefix. */
export function cellToXY(cell: string): { x: number; y: number } {
  const bare = cell.includes("-") ? cell.split("-").pop()! : cell;
  const m = /^([A-Z]+)([0-9]+)$/.exec(bare);
  if (!m) throw new Error("bad cell: " + cell);
  const col = lettersToIndex(m[1]);
  const row = parseInt(m[2], 10);
  return { x: (col + 0.5) * CELL, y: (row - 0.5) * CELL };
}

function lettersToIndex(letters: string): number {
  let n = 0;
  for (const ch of letters) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}

/** Floor plane with walls; centered at the grid middle for the camera. */
export function buildFloorPlane(floor: SpaceFloor): THREE.Group {
  const group = new THREE.Group();
  group.name = "floor-" + floor.id;
  const w = floor.columns * CELL;
  const h = floor.rows * CELL;
  const geo = new THREE.PlaneGeometry(w, h);
  const mat = new THREE.MeshBasicMaterial({ map: parchmentTexture(), color: BASE_FROM });
  const plane = new THREE.Mesh(geo, mat);
  plane.position.set(w / 2, h / 2, 0);
  group.add(plane);

  const wallMat = new THREE.LineBasicMaterial({ color: 0x2a2118 });
  // Space px coords grow downward; scene coords grow upward (A1 bottom-left).
  const flip = (p: { x: number; y: number }) =>
    new THREE.Vector3(p.x, floor.rows * CELL - p.y, 1);
  for (const wall of [...floor.walls, ...floor.doors]) {
    const g = new THREE.BufferGeometry().setFromPoints([flip(wall.from), flip(wall.to)]);
    group.add(new THREE.Line(g, wallMat));
  }
  return group;
}
