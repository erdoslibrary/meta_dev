/* THREE scene with repeat rendering + context-loss recovery (global script). */

let sceneRenderer: THREE.WebGLRenderer | null = null;
let sceneHandle: THREE.Scene | null = null;
let sceneCamera: THREE.PerspectiveCamera | null = null;
let rafId = 0;
let canvasEl: HTMLCanvasElement | null = null;

const orbit = { theta: 0, phi: 0.72, radius: 23.2 };

/** Rebuild hook set by the wiring (plane/trail re-add their objects). */
let rebuildHook: (() => void) | null = null;
function onSceneRebuild(hook: () => void): void {
  rebuildHook = hook;
}

function sceneSize(): { w: number; h: number } {
  const w = canvasEl ? canvasEl.clientWidth : 800;
  const h = canvasEl ? canvasEl.clientHeight : 600;
  return { w: Math.max(320, w), h: Math.max(240, h) };
}

let sceneColumns = 0;
let sceneRows = 0;

/** Fit the perspective orbit radius to the active floor grid. */
function setSceneExtent(columns: number, rows: number): void {
  if (columns !== sceneColumns || rows !== sceneRows) {
    sceneColumns = columns;
    sceneRows = rows;
    if (columns > 0 && rows > 0) {
      orbit.radius = Math.max(columns, rows) * 1.45;
    }
  }
}

function buildScene(): void {
  resetThemeTextures();
  sceneHandle = new THREE.Scene();
  sceneHandle.background = new THREE.Color(INK_MAIN);
  const { w, h } = sceneSize();
  sceneCamera = new THREE.PerspectiveCamera(38, w / h, 0.1, 500);
  if (rebuildHook) rebuildHook();
}

function renderLoop(): void {
  rafId = requestAnimationFrame(renderLoop);
  if (sceneRenderer && sceneHandle && sceneCamera) {
    const { w, h } = sceneSize();
    sceneRenderer.setSize(w, h, false);
    sceneCamera.aspect = w / h;
    sceneCamera.updateProjectionMatrix();
    sceneCamera.position.set(
      orbit.radius * Math.sin(orbit.phi) * Math.sin(orbit.theta),
      orbit.radius * Math.cos(orbit.phi),
      orbit.radius * Math.sin(orbit.phi) * Math.cos(orbit.theta)
    );
    sceneCamera.lookAt(0, 0, 0);
    sceneRenderer.render(sceneHandle, sceneCamera);
  }
}

/** Attach the canvas and start repeat rendering. Safe to call once. */
function startScene(canvas: HTMLCanvasElement): void {
  if (sceneRenderer) return;
  canvasEl = canvas;
  sceneRenderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  sceneRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  sceneRenderer.setClearColor(INK_MAIN, 1);

  let drag: { x: number; y: number } | null = null;
  canvas.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY };
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = "grabbing";
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    orbit.theta -= (e.clientX - drag.x) * 0.006;
    orbit.phi = Math.min(1.35, Math.max(0.08, orbit.phi - (e.clientY - drag.y) * 0.005));
    drag = { x: e.clientX, y: e.clientY };
  });
  const up = (): void => {
    drag = null;
    canvas.style.cursor = "grab";
  };
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", up);
  canvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      orbit.radius = Math.min(80, Math.max(5, orbit.radius * (1 + e.deltaY * 0.001)));
    },
    { passive: false }
  );

  buildScene();
  canvas.addEventListener("webglcontextlost", (e) => {
    e.preventDefault();
    cancelAnimationFrame(rafId);
    rafId = 0;
  });
  canvas.addEventListener("webglcontextrestored", () => {
    buildScene();
    if (!rafId) renderLoop();
  });
  renderLoop();
}

function currentScene(): THREE.Scene | null {
  return sceneHandle;
}
