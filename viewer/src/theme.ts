/* Parchment/ink/seal tokens (global script). Photos use <img>, never WebGL. */

const INK_MAIN = "#2A2118";
const PAPER_HI = "#E9DCC0";
const PAPER_LO = "#DCCFAC";
const SEAL_RED = "#A0322B";
const INK_FADED = "#8a8378";

/** Seal red is for cutoff/failure segments only (landing screen excepted). */
function isSealSegment(kind: string, outcome: string): boolean {
  if (kind === "puzzle_ended" && outcome === "failed") return true;
  if (kind === "end" && (outcome === "action_limit" || outcome === "api_error")) {
    return true;
  }
  return false;
}

let _seedBump = 0;

function seeded(seed: number): () => number {
  let s = (seed >>> 0) || 1;
  return () => {
    s ^= s << 13;
    s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5;
    s >>>= 0;
    return s / 4294967296;
  };
}

function makeParchmentCanvas(): HTMLCanvasElement {
  const S = 512;
  const cv = document.createElement("canvas");
  cv.width = cv.height = S;
  const g = cv.getContext("2d")!;
  const r = seeded(1851 + 97 * _seedBump++);
  const base = g.createLinearGradient(0, 0, S, S);
  base.addColorStop(0, PAPER_HI);
  base.addColorStop(0.55, "#E3D5B6");
  base.addColorStop(1, PAPER_LO);
  g.fillStyle = base;
  g.fillRect(0, 0, S, S);
  for (let i = 0; i < 46; i++) {
    const x = r() * S;
    const y = r() * S;
    const rad = 18 + r() * 90;
    const a = 0.025 + r() * 0.05;
    const m = g.createRadialGradient(x, y, 0, x, y, rad);
    m.addColorStop(0, `rgba(150,112,62,${a})`);
    m.addColorStop(1, "rgba(150,112,62,0)");
    g.fillStyle = m;
    g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  const fold = (x0: number, y0: number, x1: number, y1: number): void => {
    const line = (o: number, w: number, c: string): void => {
      g.beginPath();
      g.moveTo(x0 + o, y0);
      g.lineTo(x1 + o, y1);
      g.lineWidth = w;
      g.strokeStyle = c;
      g.stroke();
    };
    line(0, 14, "rgba(120,85,45,0.035)");
    line(0, 1.1, "rgba(90,62,30,0.17)");
    line(1.6, 1, "rgba(255,250,235,0.32)");
  };
  fold(0, 0, S, S);
  fold(S, 0, 0, S);
  fold(S * 0.5, 0, S * 0.46, S);
  const img = g.getImageData(0, 0, S, S);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    const n = (r() - 0.5) * 14;
    d[i] += n;
    d[i + 1] += n;
    d[i + 2] += n * 0.8;
  }
  g.putImageData(img, 0, 0);
  for (let i = 0; i < 900; i++) {
    g.fillStyle = `rgba(60,40,20,${0.08 + r() * 0.25})`;
    g.beginPath();
    g.arc(r() * S, r() * S, 0.3 + r() * 1.1, 0, Math.PI * 2);
    g.fill();
  }
  g.strokeStyle = "rgba(90,66,40,0.12)";
  g.lineWidth = 0.6;
  for (let i = 0; i < 70; i++) {
    const x = r() * S;
    const y = r() * S;
    const a = r() * Math.PI;
    const l = 3 + r() * 9;
    g.beginPath();
    g.moveTo(x, y);
    g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l);
    g.stroke();
  }
  const e = g.createRadialGradient(S / 2, S / 2, S * 0.3, S / 2, S / 2, S * 0.74);
  e.addColorStop(0, "rgba(92,58,26,0)");
  e.addColorStop(0.66, "rgba(110,72,34,0.1)");
  e.addColorStop(0.88, "rgba(84,50,20,0.3)");
  e.addColorStop(1, "rgba(48,28,12,0.55)");
  g.fillStyle = e;
  g.fillRect(0, 0, S, S);
  for (let i = 0; i < 60; i++) {
    const side = i % 4;
    const t = r() * S;
    const x = side === 0 ? t : side === 1 ? S : side === 2 ? t : 0;
    const y = side === 0 ? 0 : side === 1 ? t : side === 2 ? S : t;
    const rad = 10 + r() * 34;
    const m = g.createRadialGradient(x, y, 0, x, y, rad);
    m.addColorStop(0, "rgba(55,32,14,0.4)");
    m.addColorStop(1, "rgba(55,32,14,0)");
    g.fillStyle = m;
    g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  return cv;
}

function makeInkDotCanvas(): HTMLCanvasElement {
  const S = 64;
  const cv = document.createElement("canvas");
  cv.width = cv.height = S;
  const g = cv.getContext("2d")!;
  const r = seeded(77);
  g.fillStyle = "#fff";
  g.beginPath();
  for (let i = 0; i <= 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    const rad = 17 + (r() - 0.5) * 6;
    const x = 32 + Math.cos(a) * rad;
    const y = 32 + Math.sin(a) * rad;
    if (i) g.lineTo(x, y);
    else g.moveTo(x, y);
  }
  g.fill();
  for (let i = 0; i < 6; i++) {
    const a = r() * Math.PI * 2;
    const d = 21 + r() * 7;
    g.beginPath();
    g.arc(32 + Math.cos(a) * d, 32 + Math.sin(a) * d, 1.2 + r() * 2.4, 0, Math.PI * 2);
    g.fill();
  }
  g.globalCompositeOperation = "destination-out";
  const hole = g.createRadialGradient(28, 28, 0, 32, 32, 16);
  hole.addColorStop(0, "rgba(0,0,0,0.35)");
  hole.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = hole;
  g.fillRect(0, 0, S, S);
  return cv;
}

function makeStampCanvas(result: "solved" | "failed"): HTMLCanvasElement {
  const S = 256;
  const cv = document.createElement("canvas");
  cv.width = cv.height = S;
  const g = cv.getContext("2d")!;
  const r = seeded(result === "solved" ? 5 : 9);
  const c = result === "solved" ? INK_MAIN : SEAL_RED;
  g.strokeStyle = c;
  g.fillStyle = c;
  g.lineWidth = 12;
  g.beginPath();
  g.arc(128, 128, 114, 0, Math.PI * 2);
  g.stroke();
  g.lineWidth = 3;
  g.beginPath();
  g.arc(128, 128, 96, 0, Math.PI * 2);
  g.stroke();
  for (let i = 0; i < 4; i++) {
    const a = (i * Math.PI) / 2 + Math.PI / 4;
    g.beginPath();
    g.arc(128 + Math.cos(a) * 105, 128 + Math.sin(a) * 105, 3, 0, Math.PI * 2);
    g.fill();
  }
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.font = 'bold 58px Georgia, "Times New Roman", "Batang", serif';
  g.fillText(result === "solved" ? "해결" : "봉인", 128, 118);
  g.font = 'italic 20px Georgia, "Times New Roman", serif';
  g.fillText(result === "solved" ? "SOLVED" : "SEALED", 128, 166);
  g.globalCompositeOperation = "destination-out";
  for (let i = 0; i < 520; i++) {
    g.fillStyle = `rgba(0,0,0,${0.3 + r() * 0.6})`;
    g.beginPath();
    g.arc(r() * S, r() * S, 0.6 + r() * 2.2, 0, Math.PI * 2);
    g.fill();
  }
  return cv;
}

let _texParchmentMount: THREE.CanvasTexture | null = null;
let _texParchmentMain: THREE.CanvasTexture | null = null;
let _texInkDot: THREE.CanvasTexture | null = null;
let _texStampSolved: THREE.CanvasTexture | null = null;
let _texStampFailed: THREE.CanvasTexture | null = null;

function resetThemeTextures(): void {
  _seedBump = 0;
  _texParchmentMount = null;
  _texParchmentMain = null;
  _texInkDot = null;
  _texStampSolved = null;
  _texStampFailed = null;
}

/** Code-generated parchment texture (no photo WebGL textures). */
function parchmentTexture(kind: "mount" | "main" = "main"): THREE.CanvasTexture {
  if (kind === "mount") {
    if (!_texParchmentMount) {
      _texParchmentMount = new THREE.CanvasTexture(makeParchmentCanvas());
      _texParchmentMount.colorSpace = THREE.SRGBColorSpace;
    }
    return _texParchmentMount;
  }
  if (!_texParchmentMain) {
    _texParchmentMain = new THREE.CanvasTexture(makeParchmentCanvas());
    _texParchmentMain.colorSpace = THREE.SRGBColorSpace;
  }
  return _texParchmentMain;
}

function inkDotTexture(): THREE.CanvasTexture {
  if (!_texInkDot) {
    _texInkDot = new THREE.CanvasTexture(makeInkDotCanvas());
    _texInkDot.colorSpace = THREE.SRGBColorSpace;
  }
  return _texInkDot;
}

function stampTexture(result: "solved" | "failed"): THREE.CanvasTexture {
  if (result === "solved") {
    if (!_texStampSolved) {
      _texStampSolved = new THREE.CanvasTexture(makeStampCanvas("solved"));
      _texStampSolved.colorSpace = THREE.SRGBColorSpace;
    }
    return _texStampSolved;
  }
  if (!_texStampFailed) {
    _texStampFailed = new THREE.CanvasTexture(makeStampCanvas("failed"));
    _texStampFailed.colorSpace = THREE.SRGBColorSpace;
  }
  return _texStampFailed;
}
