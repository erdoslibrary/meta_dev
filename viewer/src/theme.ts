/* Parchment/ink/seal tokens (global script). Photos use <img>, never WebGL. */

const INK_MAIN = "#2A2118";
const PAPER_HI = "#E9DCC0";
const PAPER_LO = "#DCCFAC";
const SEAL_RED = "#A0322B";

/** Seal red is for cutoff/failure segments only (landing screen excepted). */
function isSealSegment(kind: string, outcome: string): boolean {
  if (kind === "puzzle_ended" && outcome === "failed") return true;
  if (kind === "end" && (outcome === "action_limit" || outcome === "api_error")) {
    return true;
  }
  return false;
}

/** Code-generated parchment texture (no photo WebGL textures). */
function parchmentTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createLinearGradient(0, 0, 256, 256);
    grad.addColorStop(0, PAPER_HI);
    grad.addColorStop(1, PAPER_LO);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);
    ctx.fillStyle = "rgba(42, 33, 24, 0.06)";
    for (let i = 0; i < 300; i++) {
      const x = (i * 37) % 256;
      const y = (i * 91) % 256;
      ctx.fillRect(x, y, 2, 1);
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  return tex;
}
