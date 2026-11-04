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
    z: (floor.origin_px.y - px.y) * mpp - floor.rows / 2,
  };
}

/** One floor plane with walls. Unexplored = desaturated + translucent. */
function buildFloorPlane(floor: SpaceFloor, explored: boolean): THREE.Group {
  const W = floor.columns;
  const H = floor.rows;
  const hw = W / 2;
  const hh = H / 2;
  const group = new THREE.Group();

  const mount = new THREE.Mesh(
    new THREE.PlaneGeometry(W + 2.8, H + 2.8),
    new THREE.MeshBasicMaterial({ map: parchmentTexture("mount"), color: "#d9cdb4" })
  );
  mount.rotation.x = -Math.PI / 2;
  mount.position.set(0, -0.01, 0);
  group.add(mount);

  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry(W, H),
    new THREE.MeshBasicMaterial({
      map: parchmentTexture("main"),
      color: explored ? "#ffffff" : "#e4dfd6",
      transparent: !explored,
      opacity: explored ? 1 : 0.72,
    })
  );
  plane.rotation.x = -Math.PI / 2;
  plane.position.set(0, 0, 0);
  group.add(plane);

  const segs = (
    list: number[], color: string, opacity: number, ro: number
  ): THREE.LineSegments => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(list, 3));
    const ls = new THREE.LineSegments(
      geo,
      new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false })
    );
    ls.renderOrder = ro || 1;
    return ls;
  };

  const thick = (
    out: number[], ax: number, az: number, bx: number, bz: number,
    y: number, offs: number[], ext: number
  ): void => {
    const dx = bx - ax;
    const dz = bz - az;
    const L = Math.hypot(dx, dz) || 1;
    const ux = dx / L;
    const uz = dz / L;
    const nx = -uz;
    const nz = ux;
    for (const o of offs) {
      out.push(
        ax - ux * ext + nx * o, y, az - uz * ext + nz * o,
        bx + ux * ext + nx * o, y, bz + uz * ext + nz * o
      );
    }
  };

  const rect = (
    out: number[], x0: number, z0: number, x1: number, z1: number,
    y: number, offs: number[]
  ): void => {
    thick(out, x0, z0, x1, z0, y, offs, 0);
    thick(out, x1, z0, x1, z1, y, offs, 0);
    thick(out, x1, z1, x0, z1, y, offs, 0);
    thick(out, x0, z1, x0, z0, y, offs, 0);
  };

  const grid: number[] = [];
  for (let ix = 1; ix < W; ix++) {
    const x = -hw + ix;
    grid.push(x, 0.004, -hh, x, 0.004, hh);
  }
  for (let iz = 1; iz < H; iz++) {
    const z = -hh + iz;
    grid.push(-hw, 0.004, z, hw, 0.004, z);
  }
  group.add(segs(grid, INK_MAIN, explored ? 0.11 : 0.07, 1));

  const o1 = 0.62;
  const o2 = 0.38;
  const border: number[] = [];
  const ticks: number[] = [];
  rect(border, -hw - o1, -hh - o1, hw + o1, hh + o1, 0.006, [-0.03, -0.015, 0, 0.015]);
  rect(border, -hw - o2, -hh - o2, hw + o2, hh + o2, 0.006, [0]);
  group.add(segs(border, INK_MAIN, 0.9, 2));
  for (let ix = 0; ix <= W; ix++) {
    const x = -hw + ix;
    const l = ix % 5 === 0 ? o1 - 0.05 : o2 + 0.1;
    ticks.push(x, 0.006, -hh - o2, x, 0.006, -hh - l, x, 0.006, hh + o2, x, 0.006, hh + l);
  }
  for (let iz = 0; iz <= H; iz++) {
    const z = -hh + iz;
    const l = iz % 5 === 0 ? o1 - 0.05 : o2 + 0.1;
    ticks.push(-hw - o2, 0.006, z, -hw - l, 0.006, z, hw + o2, 0.006, z, hw + l, 0.006, z);
  }
  group.add(segs(ticks, INK_MAIN, 0.7, 2));

  const walls: number[] = [];
  const offs = [-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06];
  for (const wall of floor.walls) {
    const a = pxToWorld(wall.from, floor);
    const b = pxToWorld(wall.to, floor);
    thick(walls, a.x, a.z, b.x, b.z, 0.01, offs, 0.06);
  }
  group.add(segs(walls, explored ? INK_MAIN : INK_FADED, explored ? 1 : 0.55, 3));
  return group;
}
