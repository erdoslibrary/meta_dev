/* Shared log + static-data types (read-only; engine/log formats unchanged). */

export type EventType =
  | "move" | "view" | "npc_dialogue" | "answer_submitted"
  | "hint_revealed" | "puzzle_ended" | "rejected" | "end";

export interface LogEvent {
  t: number;
  puzzle: number;
  type: EventType;
  value?: string | null;
  npc?: string;
  attempt?: number;
  correct?: boolean;
  reason?: string;
  level?: number;
  result?: "solved_by_dialogue" | "solved_with_hint" | "failed";
  attempts_used?: number;
  attempted_action?: string | null;
  error?: string;
  outcome?: "completed" | "action_limit" | "api_error";
}

export interface RunLog {
  run_id: string;
  persona: unknown;
  puzzle_set_id: string;
  model: string;
  seed?: number;
  events: LogEvent[];
}

export interface SpaceFloor {
  id: string;
  walls: { from: { x: number; y: number }; to: { x: number; y: number } }[];
  doors: { id: string; from: { x: number; y: number }; to: { x: number; y: number } }[];
  meters_per_pixel: number;
  origin_px: { x: number; y: number };
  columns: number;
  rows: number;
}

export interface SpaceData {
  space_id: string;
  floors: SpaceFloor[];
  rooms: { name: string; cells: string }[];
  objects: {
    id: string; label: string; cells: string;
    description: string; photos: string[]; state: string;
  }[];
}

export interface PuzzleData {
  puzzle_set_id: string;
  space_id: string;
  start_cell: string;
  puzzles: {
    number: number;
    object_id: string;
    npc: string;
    dialogue: { text: string; contains_hint: boolean }[];
    on_wrong: string;
    on_correct: string;
    answer: string;
  }[];
}

export interface NpcData {
  id: string;
  name: string;
  image: string;
  tone: string;
}

export interface SetBundle {
  space: SpaceData;
  puzzle: PuzzleData;
  npc: NpcData;
  logs: Record<string, RunLog>;
}

export interface RtData {
  sets: Record<string, SetBundle>;
  testdata: Record<string, RunLog>;
}
