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
  const host = canvasEl && canvasEl.parentElement;
  const w = host ? host.clientWidth : 800;
  const h = host ? host.clientHeight : 600;
  return { w: Math.max(320, w), h: Math.max(240, h) };
}

function buildScene(): void {
  sceneHandle = new THREE.Scene();
  sceneHandle.background = new THREE.Color("#E9DCC0");
  const { w, h } = sceneSize();
  const half = 8;
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
