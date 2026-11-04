/* Log event + static-data types (global script, no import/export). */

type MoveValue = string;
type ObjectRef = string;
type NpcId = string;

interface MoveEvent {
  t: number; puzzle: number; type: "move"; value: MoveValue;
}
interface ViewEvent {
  t: number; puzzle: number; type: "view"; value: ObjectRef;
}
interface NpcDialogueEvent {
  t: number; puzzle: number; type: "npc_dialogue"; npc: NpcId;
}
interface AnswerSubmittedEvent {
  t: number; puzzle: number; type: "answer_submitted";
  value: string; attempt: number; correct: boolean;
}
interface HintRevealedEvent {
  t: number; puzzle: number; type: "hint_revealed"; level: number;
}
interface PuzzleEndedEvent {
  t: number; puzzle: number; type: "puzzle_ended";
  result: "solved_by_dialogue" | "solved_with_hint" | "failed";
  attempts_used: number;
}
interface RejectedEvent {
  t: number; puzzle: number; type: "rejected";
  attempted_action: string | null; error: string; value?: string | null;
}
interface EndEvent {
  t: number; puzzle: number; type: "end";
  outcome: "completed" | "action_limit" | "api_error";
}
type LogEvent =
  | MoveEvent | ViewEvent | NpcDialogueEvent | AnswerSubmittedEvent
  | HintRevealedEvent | PuzzleEndedEvent | RejectedEvent | EndEvent;

interface Persona {
  age: number; job: string; vocab: string; thinking: string; name?: string;
}
interface RunLog {
  run_id: string; persona: Persona; puzzle_set_id: string;
  model: string; seed?: number; events: LogEvent[];
}

interface SpacePoint { x: number; y: number; }
interface SpaceWall { from: SpacePoint; to: SpacePoint; }
interface SpaceDoor { id: string; from: SpacePoint; to: SpacePoint; }
interface SpaceFloor {
  id?: string; walls: SpaceWall[]; doors: SpaceDoor[];
  origin_px: SpacePoint; meters_per_pixel: number;
  columns: number; rows: number; background_image?: string;
}
interface SpaceRoom { name: string; cells: string; }
interface SpaceObject {
  id: string; cells: string; photos: string[]; label: string;
}
interface SpaceData {
  space_id: string; floors: SpaceFloor[];
  rooms: SpaceRoom[]; objects: SpaceObject[];
}

interface PuzzleDialogue { text: string; }
interface PuzzleEntry {
  number: number; object_id: string; npc: string;
  question?: string; dialogue?: PuzzleDialogue[];
  on_wrong: string; on_correct: string;
  image?: { path: string };
  answer_letter_count?: number; max_attempts?: number;
}
/* File-input original puzzle.json only (decision B): keeps failed-puzzle answer/next_instruction. Embedded PuzzleEntry stays answer-free. */
interface FilePuzzleEntry extends PuzzleEntry {
  answer: string; next_instruction: string | null;
}
/* File-input original puzzle.json container (decision B). */
interface FilePuzzleData {
  puzzle_set_id: string; space_id: string; start_cell: string;
  start_instruction?: string; puzzles: FilePuzzleEntry[];
}
interface RevealEntry { answer: string; next_instruction?: string; }
type Reveals = { [logKey: string]: { [puzzleNumber: string]: RevealEntry } };
interface PuzzleData {
  puzzle_set_id: string; space_id: string; start_cell: string;
  start_instruction?: string; puzzles: PuzzleEntry[];
}
interface NpcData { id: string; name: string; image: string; }

interface SetBundle {
  space: SpaceData; puzzle: PuzzleData; npc: NpcData;
  logs: { [key: string]: RunLog };
  reveals: Reveals;
}
interface SampleSetBundle { space?: SpaceData; puzzle?: PuzzleData; npc?: NpcData; reveals: Reveals; }
interface RtData {
  sets: { [setName: string]: SetBundle };
  testdata: { [name: string]: RunLog };
  refusal: { [name: string]: RunLog };
  sample_sets: { [setId: string]: SampleSetBundle };
}
