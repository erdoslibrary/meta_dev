/* Stage: repeat RAF render + context-loss recovery (R-4). */

export interface Stage {
  scene: THREE.Scene;
  camera: THREE.OrthographicCamera;
  renderer: THREE.WebGLRenderer;
}

export function createStage(canvas: HTMLCanvasElement): Stage {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(800, 600, false);
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-320, 320, 320, -320, 0.1, 2000);
  camera.position.set(300, 300, 500);

  const rebuild = () => buildScene(scene, camera);
  buildScene(scene, camera);

  canvas.addEventListener("webglcontextlost", (e) => e.preventDefault());
  canvas.addEventListener("webglcontextrestored", () => rebuild());

  const light = new THREE.DirectionalLight(0xffffff, 1.0);
  light.position.set(100, 200, 400);
  scene.add(light);

  const frame = () => {
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
  return { scene, camera, renderer };
}

/** Cleared and re-run on context restore; slice modules add content after. */
function buildScene(scene: THREE.Scene, _camera: THREE.OrthographicCamera): void {
  while (scene.children.length > 0) {
    scene.remove(scene.children[0]);
  }
  const light = new THREE.DirectionalLight(0xffffff, 1.0);
  light.position.set(100, 200, 400);
  scene.add(light);
}
