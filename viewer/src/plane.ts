/* Floor planes from space.json (global script). 1 cell = 1 m. */

function lettersToIndex(letters: string): number {
  let n = 0;
  for (let i = 0; i < letters.length; i++) {
    n = n * 26 + (letters.charCodeAt(i) - 64);
  }
  return n - 1;
}

/** "2F-C4" -> "2F", "C4" -> null. */
function floorOf(cell: string): string | null {
  const dash = cell.indexOf("-");
  return dash >= 0 ? cell.slice(0, dash) : null;
}

function parseCell(cell: string): { col: number; row: number } {
  const bare = cell.indexOf("-") >= 0 ? cell.split("-").pop() as string : cell;
  const m = /^([A-Z]+)([0-9]+)$/.exec(bare);
  if (!m) throw new Error("bad cell: " + cell);
  return { col: lettersToIndex(m[1]), row: parseInt(m[2], 10) - 1 };
}

/** Cell center in meters, grid centered at origin. */
function cellToXY(cell: string, columns: number, rows: number): { x: number; z: number } {
  const c = parseCell(cell);
  return { x: c.col - (columns - 1) / 2, z: (rows - 1) / 2 - c.row };
}

function pxToWorld(
  px: SpacePoint, floor: SpaceFloor
): { x: number; z: number } {
  const mpp = floor.meters_per_pixel;
  return {
    x: (px.x - floor.origin_px.x) * mpp - floor.columns / 2,
    z: (px.y - floor.origin_px.y) * mpp + floor.rows / 2,
  };
}

/** One floor plane with walls. Unexplored = desaturated + translucent. */
function buildFloorPlane(floor: SpaceFloor, explored: boolean): THREE.Group {
  const group = new THREE.Group();
  const geo = new THREE.PlaneGeometry(floor.columns, floor.rows);
  const mat = new THREE.MeshBasicMaterial({ map: parchmentTexture() });
  if (!explored) {
    mat.color.set("#8a8378");
    mat.transparent = true;
    mat.opacity = 0.55;
  }
  const plane = new THREE.Mesh(geo, mat);
  plane.rotation.x = -Math.PI / 2;
  group.add(plane);

  const pts: number[] = [];
  const push = (p: SpacePoint): void => {
    const w = pxToWorld(p, floor);
    pts.push(w.x, 0.02, w.z);
  };
  for (const wall of floor.walls) {
    push(wall.from);
    push(wall.to);
  }
  const wallGeo = new THREE.BufferGeometry();
  wallGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  const wallMat = new THREE.LineBasicMaterial({
    color: explored ? INK_MAIN : "#6a655c",
  });
  group.add(new THREE.LineSegments(wallGeo, wallMat));
  return group;
}
