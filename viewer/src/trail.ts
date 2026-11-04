/* Footprint trajectory: Line + Points (global script). */

interface TrailPoint { x: number; z: number; }

/** Points = move count + 1 (caller prepends start_cell). */
function buildTrail(points: TrailPoint[], sealTail: boolean): THREE.Group {
  const group = new THREE.Group();
  const positions = new Float32Array(points.length * 3);
  const colors = new Float32Array(points.length * 3);
  const ink = new THREE.Color(INK_MAIN);
  const seal = new THREE.Color(SEAL_RED);
  for (let i = 0; i < points.length; i++) {
    positions[i * 3] = points[i].x;
    positions[i * 3 + 1] = 0.05;
    positions[i * 3 + 2] = points[i].z;
    const last = sealTail && i >= points.length - 2;
    const c = last ? seal : ink;
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }
  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  lineGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const line = new THREE.Line(
    lineGeo,
    new THREE.LineBasicMaterial({ vertexColors: true })
  );
  group.add(line);

  const dotGeo = new THREE.BufferGeometry();
  dotGeo.setAttribute("position", new THREE.BufferAttribute(positions.slice(), 3));
  const dots = new THREE.Points(
    dotGeo,
    new THREE.PointsMaterial({ size: 0.22, vertexColors: false, color: ink })
  );
  group.add(dots);
  if (sealTail && points.length > 0) {
    const tip = points[points.length - 1];
    const marker = new THREE.Mesh(
      new THREE.CircleGeometry(0.28, 24),
      new THREE.MeshBasicMaterial({ color: seal })
    );
    marker.rotation.x = -Math.PI / 2;
    marker.position.set(tip.x, 0.06, tip.z);
    group.add(marker);
  }
  return group;
}

/** Mark a puzzle_ended result on the trajectory (FR-004). */
function addResultMarker(
  group: THREE.Group, at: TrailPoint,
  result: "solved_by_dialogue" | "solved_with_hint" | "failed"
): void {
  const color = result === "failed" ? SEAL_RED : INK_MAIN;
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.3, 0.42, 24),
    new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide })
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(at.x, 0.06, at.z);
  group.add(ring);
}
