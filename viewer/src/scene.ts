/* THREE scene with repeat rendering + context-loss recovery (global script). */

let sceneRenderer: THREE.WebGLRenderer | null = null;
let sceneHandle: THREE.Scene | null = null;
let sceneCamera: THREE.OrthographicCamera | null = null;
let rafId = 0;
let canvasEl: HTMLCanvasElement | null = null;

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

function extentHalf(): number {
  if (sceneColumns > 0 && sceneRows > 0) return Math.max(sceneColumns, sceneRows) / 2 * 1.2;
  return 8;
}

/** Fit the orthographic view to the active floor grid. */
function setSceneExtent(columns: number, rows: number): void {
  sceneColumns = columns;
  sceneRows = rows;
  if (sceneCamera) {
    const { w, h } = sceneSize();
    const half = extentHalf();
    sceneCamera.left = -half * (w / h);
    sceneCamera.right = half * (w / h);
    sceneCamera.top = half;
    sceneCamera.bottom = -half;
    sceneCamera.updateProjectionMatrix();
  }
}

function buildScene(): void {
  sceneHandle = new THREE.Scene();
  sceneHandle.background = new THREE.Color("#E9DCC0");
  const { w, h } = sceneSize();
  const half = extentHalf();
  sceneCamera = new THREE.OrthographicCamera(
    -half * (w / h), half * (w / h), half, -half, 0.1, 100
  );
  sceneCamera.position.set(0, 10, 0.01);
  sceneCamera.lookAt(0, 0, 0);
  if (rebuildHook) rebuildHook();
}

function renderLoop(): void {
  rafId = requestAnimationFrame(renderLoop);
  if (sceneRenderer && sceneHandle && sceneCamera) {
    const { w, h } = sceneSize();
    sceneRenderer.setSize(w, h, false);
    sceneRenderer.render(sceneHandle, sceneCamera);
  }
}

/** Attach the canvas and start repeat rendering. Safe to call once. */
function startScene(canvas: HTMLCanvasElement): void {
  if (sceneRenderer) return;
  canvasEl = canvas;
  sceneRenderer = new THREE.WebGLRenderer({ canvas, antialias: true });
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
