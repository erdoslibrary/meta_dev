/* Footprint trajectory: Line + Points (global script). */

interface TrailPoint { x: number; z: number; }

/** Points = move count + 1 (caller prepends start_cell). */
function buildTrail(points: TrailPoint[], sealAt: number[]): THREE.Group {
  const group = new THREE.Group();
  const positions = new Float32Array(points.length * 3);
  const dotPositions = new Float32Array(points.length * 3);
  const colors = new Float32Array(points.length * 3);
  const ink = new THREE.Color(INK_MAIN);
  const seal = new THREE.Color(SEAL_RED);
  for (let i = 0; i < points.length; i++) {
    positions[i * 3] = points[i].x;
    positions[i * 3 + 1] = 0.03;
    positions[i * 3 + 2] = points[i].z;
    dotPositions[i * 3] = points[i].x;
    dotPositions[i * 3 + 1] = 0.035;
    dotPositions[i * 3 + 2] = points[i].z;
    const last = sealAt.indexOf(i) !== -1;
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
    new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      depthWrite: false
    })
  );
  line.renderOrder = 4;
  group.add(line);

  const dashCoords: number[] = [];
  for (let i = 1; i < points.length; i++) {
    if (sealAt.indexOf(i) !== -1 && sealAt.indexOf(i - 1) !== -1) {
      dashCoords.push(
        points[i - 1].x, 0.032, points[i - 1].z,
        points[i].x, 0.032, points[i].z
      );
    }
  }
  if (dashCoords.length > 0) {
    const dashGeo = new THREE.BufferGeometry();
    dashGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(dashCoords), 3));
    const dashLine = new THREE.LineSegments(
      dashGeo,
      new THREE.LineDashedMaterial({
        color: SEAL_RED,
        dashSize: 0.22,
        gapSize: 0.14,
        transparent: true,
        depthWrite: false
      })
    );
    dashLine.computeLineDistances();
    dashLine.renderOrder = 4;
    group.add(dashLine);
  }

  const dotGeo = new THREE.BufferGeometry();
  dotGeo.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
  dotGeo.setAttribute("color", new THREE.BufferAttribute(colors.slice(), 3));
  const dots = new THREE.Points(
    dotGeo,
    new THREE.PointsMaterial({
      size: 0.34,
      map: inkDotTexture(),
      vertexColors: true,
      alphaTest: 0.1,
      transparent: true,
      depthWrite: false,
      sizeAttenuation: true
    })
  );
  dots.renderOrder = 5;
  group.add(dots);

  if (points.length > 0) {
    const head = points[points.length - 1];
    const headRing = new THREE.Mesh(
      new THREE.RingGeometry(0.2, 0.3, 32),
      new THREE.MeshBasicMaterial({
        color: INK_MAIN,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide
      })
    );
    headRing.rotation.x = -Math.PI / 2;
    headRing.position.set(head.x, 0.05, head.z);
    headRing.renderOrder = 7;
    group.add(headRing);
  }

  if (points.length > 0 && sealAt.indexOf(points.length - 1) !== -1) {
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
  const stamp = new THREE.Mesh(
    new THREE.PlaneGeometry(1.8, 1.8),
    new THREE.MeshBasicMaterial({
      map: stampTexture(result === "failed" ? "failed" : "solved"),
      transparent: true,
      opacity: 0.92,
      depthWrite: false
    })
  );
  stamp.rotation.x = -Math.PI / 2;
  stamp.rotation.z = result === "failed" ? 0.22 : -0.18;
  stamp.position.set(at.x, 0.04, at.z);
  stamp.renderOrder = 6;
  group.add(stamp);
}
