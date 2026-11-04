/* Panels: view photos (<img>), npc_dialogue, on_wrong/on_correct, results.
 * FR-005: answers only once right after puzzle_ended(failed); never show
 * next_instruction, photo paths/hashes, unreleased hints, non-failed answers. */
import { LogEvent, PuzzleData, NpcData, SpaceData } from "./types";

export interface PanelCtx {
  setName: string;
  space: SpaceData;
  puzzle: PuzzleData;
  npc: NpcData;
}

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function puzzleByNumber(ctx: PanelCtx, n: number) {
  return ctx.puzzle.puzzles.find((p) => p.number === n);
}

function imgTag(src: string, alt: string): string {
  return `<img src="${src}" alt="${esc(alt)}" onerror="this.outerHTML='<div class=&quot;photo-empty&quot;></div>'">`;
}

/** Render one playback event into #ghost; results accumulate in #result. */
export function renderEvent(ctx: PanelCtx, ev: LogEvent): void {
  const ghost = document.getElementById("ghost");
  const result = document.getElementById("result");
  if (!ghost || !result) return;
  const dataBase = `../data/${ctx.setName}`;

  if (ev.type === "view" && ev.value) {
    const obj = ctx.space.objects.find((o) => o.id === ev.value);
    const photo = obj?.photos[0];
    ghost.innerHTML =
      `<div><strong>${esc(obj?.label ?? ev.value)}</strong></div>` +
      (photo ? imgTag(`${dataBase}/photos/${photo}`, obj?.label ?? ev.value) : `<div class="photo-empty"></div>`);
  } else if (ev.type === "npc_dialogue" && ev.npc) {
    const p = puzzleByNumber(ctx, ev.puzzle);
    const lines = (p?.dialogue ?? []).map((d) => `<p>${esc(d.text)}</p>`).join("");
    ghost.innerHTML =
      `<div><strong>${esc(ctx.npc.name)}</strong> ${imgTag(`${dataBase}/${ctx.npc.image}`, ctx.npc.name)}</div>` + lines;
  } else if (ev.type === "answer_submitted") {
    const p = puzzleByNumber(ctx, ev.puzzle);
    const reaction = ev.correct ? p?.on_correct : p?.on_wrong;
    ghost.innerHTML =
      `<div>제출: ${esc(String(ev.value))} (${ev.correct ? "정답" : "오답"})</div>` +
      (reaction ? `<div>${esc(reaction)}</div>` : "");
  } else if (ev.type === "hint_revealed") {
    ghost.innerHTML = `<div>힌트 ${ev.level} 공개</div>`;
  } else if (ev.type === "puzzle_ended") {
    const p = puzzleByNumber(ctx, ev.puzzle);
    let html = `<div>퍼즐 ${ev.puzzle} 종료: ${ev.result}</div>`;
    if (ev.result === "failed" && p) {
      html += `<div>정답: ${esc(p.answer)}</div>`;
    }
    result.innerHTML += html;
  } else if (ev.type === "rejected") {
    ghost.innerHTML = `<div>거부: ${esc(String(ev.error ?? ""))}</div>`;
  } else if (ev.type === "end") {
    const done = ev.outcome === "completed" ? "완주" : `완주 아님(${ev.outcome})`;
    result.innerHTML += `<div>종료: ${done}</div>`;
  }
}

export function clearPanels(): void {
  document.getElementById("ghost")!.innerHTML = "";
  document.getElementById("result")!.innerHTML = "";
}
