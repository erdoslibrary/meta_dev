/* Floor grouping by cell prefix (global script). Prefix-less cells attach
   to the single floor. Group-visibility switching shows only the active
   floor's moves and observations. */

/** "2F-C4" -> "2F", "C4" -> "". */
function floorKeyOfCell(cell: string): string {
  const dash = cell.indexOf("-");
  return dash >= 0 ? cell.slice(0, dash) : "";
}

/** Floor key for a spatial event, null for floor-agnostic events. */
function eventFloor(e: LogEvent): string | null {
  if (e.type === "move") return floorKeyOfCell((e as MoveEvent).value);
  if (e.type === "view") {
    const v = (e as ViewEvent).value;
    const at = v.indexOf("@");
    return floorKeyOfCell(at >= 0 ? v.slice(at + 1) : v);
  }
  return null;
}

/** Floors present in the log (start cell first), in order of appearance. */
function logFloors(log: RunLog, startCell: string): string[] {
  const out: string[] = [];
  const push = (key: string): void => {
    if (out.indexOf(key) < 0) out.push(key);
  };
  push(floorKeyOfCell(startCell));
  for (const e of log.events) {
    const f = eventFloor(e);
    if (f !== null) push(f);
  }
  return out;
}

/** Match a floor key to a space floor (prefix-less goes to the single floor). */
function floorForKey(space: SpaceData, key: string): SpaceFloor | null {
  if (!space.floors.length) return null;
  if (key === "") return space.floors[0];
  for (const floor of space.floors) {
    if (floor.id === key) return floor;
  }
  return null;
}

/** Display label for a floor key. */
function floorLabel(key: string): string {
  return key === "" ? t("floor.single") : key;
}
