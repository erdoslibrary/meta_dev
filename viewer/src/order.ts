/* Order/ink intro: pre-entry landing, executor-self framing, no in-fiction caster. */
import { BASE_FROM, INK, SEAL_RED, SERIF } from "./theme";

const SPELL = "지도를 펼치고, 발자취를 따라가리라.";

export function showLanding(onEnter: () => void): void {
  const landing = document.getElementById("landing");
  if (!landing) {
    onEnter();
    return;
  }
  landing.style.fontFamily = SERIF;
  landing.style.background = `radial-gradient(ellipse at center, ${BASE_FROM} 55%, rgba(42,33,24,0.55) 100%)`;
  landing.innerHTML =
    `<div style="text-align:center;max-width:36em;">` +
    `<div style="border:3px double ${SEAL_RED};padding:1.5em 2em;">` +
    `<svg width="320" height="60" viewBox="0 0 320 60" aria-hidden="true">` +
    `<path d="M10 45 C 80 10, 160 60, 310 25" fill="none" stroke="${INK}" stroke-width="3" ` +
    `stroke-dasharray="340" stroke-dashoffset="340" style="animation: ink 3s ease-out forwards;"></path>` +
    `<style>@keyframes ink { to { stroke-dashoffset: 0; } }</style>` +
    `</svg>` +
    `<p class="seal" style="color:${SEAL_RED};">${SPELL}</p>` +
    `<p>기록된 실행을 처음부터 끝까지 재생한다.</p>` +
    `<button id="enter" type="button">입장</button>` +
    `</div></div>`;
  document.getElementById("enter")!.addEventListener("click", () => {
    landing.style.display = "none";
    document.getElementById("app")!.style.display = "block";
    onEnter();
  });
}
