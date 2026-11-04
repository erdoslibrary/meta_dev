/* Design tokens (spec Design Direction, R-8). Photos use <img>, never textures. */

export const BASE_FROM = "#E9DCC0";
export const BASE_TO = "#DCCFAC";
export const INK = "#2A2118";
export const SEAL_RED = "#A0322B";
export const SERIF = 'Georgia, "Times New Roman", serif';

/** Code-generated parchment grain; no image files, no webfonts. */
export function parchmentTexture(): THREE.CanvasTexture {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = BASE_FROM;
  ctx.fillRect(0, 0, size, size);
  for (let i = 0; i < 2500; i++) {
    const x = Math.floor(Math.random() * size);
    const y = Math.floor(Math.random() * size);
    ctx.fillStyle = Math.random() < 0.5 ? BASE_TO : BASE_FROM;
    ctx.fillRect(x, y, 2, 2);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}
