/* Pre-entry landing intro (global script). Executor-self framing: the
   viewer reads the spell themselves; no in-fiction caster. Spell text +
   red seal overlay + SVG ink trail, finishing within 5 seconds. */

const INK_PATH_LENGTH = 600;
const INTRO_MS = 2600;

function playOrderIntro(): void {
  const path = document.getElementById("ink-path") as unknown as SVGPathElement | null;
  const spell = document.getElementById("spell");
  const reduce = typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (spell) spell.style.opacity = "1";
  if (!path) return;
  if (reduce) {
    path.style.strokeDashoffset = "0";
    return;
  }
  path.style.transition = "none";
  path.style.strokeDasharray = String(INK_PATH_LENGTH);
  path.style.strokeDashoffset = String(INK_PATH_LENGTH);
  void path.getBoundingClientRect();
  path.style.transition = "stroke-dashoffset " + INTRO_MS + "ms linear";
  path.style.strokeDashoffset = "0";
}
