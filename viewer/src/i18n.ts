/* i18n: default English, ?lang=ko switches to Korean (global script).
   t(): UI strings. td(): data Korean->English (en only, else input).
   ansGloss(): answer_submitted gloss or null (English originals: null). */

type Lang = "en" | "ko";

function detectLang(): Lang {
  try {
    if (typeof window !== "undefined" && window.location && window.location.search) {
      const q = new URLSearchParams(window.location.search);
      if (q.get("lang") === "ko") return "ko";
    }
  } catch {
    /* fall through to English */
  }
  return "en";
}

const LANG: Lang = detectLang();

const I18N: { [key: string]: { en: string; ko: string } } = {
  "title": { en: "Real-to-Sim Archive", ko: "Real-to-Sim Archive" },
  "ctrl.record": { en: "Log", ko: "기록" },
  "ctrl.logsel.aria": { en: "Select built-in log", ko: "내장 로그 선택" },
  "ctrl.floor": { en: "Floor", ko: "층" },
  "ctrl.floor.aria": { en: "Select floor", ko: "층 선택" },
  "file.log": { en: "Log JSON", ko: "기록 JSON" },
  "file.puzzle": { en: "Puzzle JSON", ko: "퍼즐 JSON" },
  "btn.play": { en: "Play", ko: "재생" },
  "btn.step": { en: "Next", ko: "다음" },
  "btn.reset": { en: "From start", ko: "처음부터" },
  "map.hint": { en: "Drag to rotate · scroll to zoom", ko: "드래그 회전 · 휠 확대" },
  "chronicle": { en: "Chronicle", ko: "연대기" },
  "lang.toggle": { en: "KO", ko: "EN" },
  "photo.empty": { en: "No photo", ko: "사진 없음" },
  "answer.label": { en: "Answer: {0}", ko: "정답: {0}" },
  "answer.next": { en: "Next: {0}", ko: "다음: {0}" },
  "answer.missing": { en: "No answer data", ko: "정답 데이터 없음" },
  "feed.participant": { en: "Participant: {0}y {1} · vocab {2} · {3}", ko: "참가자: {0}세 {1} · 어휘 {2} · {3}" },
  "feed.start": { en: "Start: {0} (start {1})", ko: "시작 지시: {0} (시작점 {1})" },
  "feed.move": { en: "Move: {0} → {1}{2}", ko: "이동: {0} → {1}{2}" },
  "photo.fallback": { en: "Object photo", ko: "사물 사진" },
  "feed.view": { en: "View: {0}", ko: "보기: {0}" },
  "feed.appear": { en: "Enter: {0}", ko: "등장: {0}" },
  "feed.nodialogue": { en: "{0}: (dialogue)", ko: "{0}: (대화)" },
  "feed.quizpic": { en: "Puzzle {0} quiz image", ko: "퍼즐 {0} 퀴즈 그림" },
  "quiz.meta.full": { en: " ({0}-letter · {1} tries)", ko: " ({0}글자 · 시도 {1}회)" },
  "quiz.meta.short": { en: " ({0}-letter)", ko: " ({0}글자)" },
  "feed.quiz": { en: "Question: {0}{1}", ko: "문제: {0}{1}" },
  "feed.submit": { en: "Submit: {0}{1}", ko: "제출: {0}{1}" },
  "submit.ok": { en: " (correct)", ko: " (정답)" },
  "submit.ng": { en: " (wrong)", ko: " (오답)" },
  "feed.hint": { en: "Hint Lv.{0}", ko: "힌트 Lv.{0}" },
  "feed.reject": { en: "Reject({0}): {1}", ko: "거절({0}): {1}" },
  "reject.action": { en: "action", ko: "행동" },
  "feed.result": { en: "Puzzle {0} result: {1}", ko: "퍼즐 {0} 결과: {1}" },
  "result.puzzle": { en: "Puzzle {0}: {1}", ko: "퍼즐 {0}: {1}" },
  "result.done": { en: "Complete", ko: "완주" },
  "result.cut": { en: "Cut({0}): incomplete", ko: "끊김({0}): 완주 아님" },
  "trail.scope": { en: "Floor {0}", ko: "층 {0}" },
  "trail.info": { en: "Footprints {0} pts (move {1} + start)", ko: "발자국 {0}점 (move {1} + 시작점)" },
  "floor.single": { en: "Single floor", ko: "단층" },
  "status.cut": { en: "Cut({0}): stopped at the break. Not played to the end.", ko: "끊김({0}): 끊긴 지점에서 멈춤. 끝까지 재생되지 않음." },
  "status.failed": { en: "Failed segment: Seal Red shown.", ko: "실패 구간: Seal Red 표시." },
  "status.done": { en: "Playback complete.", ko: "재생 완료." },
  "status.playing": { en: "Playing: {0}/{1}", ko: "재생 중: {0}/{1}" },
  "status.reject": { en: "Playback refused: {0}", ko: "재생 거부: {0}" },
  "status.nodata": { en: "No built-in logs. Open a log file.", ko: "내장 기록 없음. 파일로 로그를 열어주세요." },
  "status.puzzle.ok": { en: "Puzzle data selected.", ko: "퍼즐 데이터 선택됨." },
  "status.puzzle.fail": { en: "Puzzle read failed: {0}", ko: "퍼즐 읽기 실패: {0}" },
  "err.fileread": { en: "File read failed", ko: "파일 읽기 실패" },
  "err.json": { en: "JSON parse failed: {0}", ko: "JSON 파싱 실패: {0}" },
  "err.unknown": { en: "Unknown event kind: {0}", ko: "알 수 없는 이벤트 종류: {0}" },
  "err.field": { en: "{0} missing {1}", ko: "{0}에 {1} 없음" },
  "err.notstr": { en: "{0}.value is not a string", ko: "{0}.value가 문자열 아님" },
  "err.format": { en: "{0}.value format error: {1}", ko: "{0}.value 형식 오류: {1}" },
  "err.npc": { en: "npc_dialogue.npc is not a string", ko: "npc_dialogue.npc가 문자열 아님" },
  "err.ans.value": { en: "answer_submitted.value is not a string", ko: "answer_submitted.value가 문자열 아님" },
  "err.ans.attempt": { en: "answer_submitted.attempt is not a number", ko: "answer_submitted.attempt가 숫자 아님" },
  "err.ans.correct": { en: "answer_submitted.correct is not a boolean", ko: "answer_submitted.correct가 불리언 아님" },
  "err.hint": { en: "hint_revealed.level is not a number", ko: "hint_revealed.level이 숫자 아님" },
  "err.rejected": { en: "rejected.error is not a string", ko: "rejected.error가 문자열 아님" },
  "err.enum": { en: "{0}.{1} invalid value", ko: "{0}.{1} 값 오류" },
  "err.notobj": { en: "Log is not an object", ko: "로그가 객체 아님" },
  "err.top": { en: "Missing top-level {0}", ko: "최상위 {0} 없음" },
  "err.topstr": { en: "{0} is not a string", ko: "{0}가 문자열 아님" },
  "err.empty": { en: "events is empty", ko: "events가 비어 있음" },
  "err.evobj": { en: "Event {0} is not an object", ko: "{0}번째 이벤트가 객체 아님" },
  "err.torder": { en: "t must increase by 1 from 1 (at {0})", ko: "t가 1부터 1씩 증가하지 않음 (위치 {0})" },
  "err.puzzlenum": { en: "puzzle is not a number (t={0})", ko: "puzzle이 숫자 아님 (t={0})" },
  "err.typestr": { en: "type is not a string (t={0})", ko: "type이 문자열 아님 (t={0})" },
  "err.lastend": { en: "Last event is not end", ko: "마지막 이벤트가 end 아님" },
  "err.midend": { en: "end at non-final position (t={0})", ko: "끝이 아닌 위치에 end 있음 (t={0})" }
};

function t(key: string, ...args: unknown[]): string {
  const row = I18N[key];
  let s = row ? (LANG === "ko" ? row.ko : row.en) : key;
  for (let i = 0; i < args.length; i++) {
    s = s.split("{" + i + "}").join(String(args[i]));
  }
  return s;
}

const TD: { [ko: string]: string } = {
  "술꾼": "Drunkard",
  "공무원": "Civil servant",
  "교사": "Teacher",
  "농부": "Farmer",
  "디자이너": "Designer",
  "약사": "Pharmacist",
  "어부": "Fisher",
  "연구원": "Researcher",
  "판매원": "Salesperson",
  "학생": "Student",
  "개발자": "Developer",
  "상": "High",
  "중": "Mid",
  "하": "Low",
  "말장난을 먼저 떠올림": "Reaches for wordplay first",
  "문자 그대로 읽음": "Reads literally",
  "연상을 따라감": "Follows associations",
  "1층 휴게실 앞": "In front of the 1F lounge",
  "2층 복도": "2F corridor",
  "3층 화장실 앞": "In front of the 3F restroom",
  "분리배출 안내판": "Recycling guide sign",
  "2층 안내판": "2F guide sign",
  "벽면에 붙어 있는 분리배출 안내판.": "Recycling guide sign posted on the wall.",
  "2층 복도 벽면에 붙어 있는 안내판.": "Sign posted on the 2F corridor wall.",
  "3층 화장실 앞 벽면에 붙어 있는 '42 경산 깨끗하게 분리배출해요!' 안내판.": "Sign in front of the 3F restroom: 'Keep 42 Gyeongsan clean — sort your waste!'",
  "어.. 자네도 부끄러운 기억을 잊으러 왔나??": "Er... did you come to forget a shameful memory, too??",
  "기억을 찾으러 왔다고?? 왜 굳이... 어려운 선택을 하나. 딸꾹": "You came looking for a memory?? Why... why choose the hard path. *hiccup*",
  "나는 잊기 위해서 술을 마시네.": "I drink to forget.",
  "술을 마시면 부끄러워지고, 부끄러우니 술을 마시고, 술을 마시면 또 부끄러워지고... 부끄러우니 또 마시지..": "I drink and feel ashamed, feel ashamed so I drink, drink and feel ashamed again... so I drink again...",
  "오랜만에 찾아온 길손인데.. 같이 놀이 하나 하지 않겠나?": "First traveler in ages... care to play a game with me?",
  "내가 이기면 한 잔 더 마시는 거고.. 자네가 이기면 어디로 갈지 알려주지.": "If I win, one more drink for me... if you win, I will tell you where to go.",
  "무슨 놀이 할 거냐고? 내가 이미 얘기하지 않았나? 아니라고? 딸꾹": "What game, you ask? Did I not tell you already? No? *hiccup*",
  "(갑자기 노래를 부르기 시작한다.) 다시 돌고~ 돌고~ 돌고~ 돌고~ 다시 돌고~": "(Bursts into song.) Round and round~ round~ round~ round~ round again~",
  "어.. 자네도 분리배출 때문에 왔나?": "Er... did you come about recycling, too?",
  "2층까지 올라오다니 대단하구먼.": "Coming all the way up to 2F, impressive.",
  "두 번째 놀이도 분리배출 안내판에 있네.": "The second game is on the recycling sign, too.",
  "빨간 글자만 따라 읽어 보게나.": "Read only the red letters.",
  "파란 글자만 따라 읽어 보게나.": "Read only the blue letters.",
  "술꾼이 말한 놀이를 풀어 다음으로 가야 할 장소를 답하세요.": "Solve the drunkard's game and answer where to go next.",
  "안내판의 빨간 첫 글자만 순서대로 읽으면?": "What do the sign's red first letters spell, in order?",
  "안내판의 파란 글자만 순서대로 읽으면?": "What do the sign's blue letters spell, in order?",
  "2층 안내판의 빨간 첫 글자만 순서대로 읽으면?": "What do the 2F sign's red first letters spell, in order?",
  "허허, 제대로 돌아 나왔구먼. 자네가 갈 곳은 SPIRAL일세.": "Haha, you spun your way out properly. Where you go is SPIRAL.",
  "허허, 2층까지 정복했구먼.": "Haha, you conquered your way up to 2F.",
  "허허, 두 번째도 제대로 읽었구먼.": "Haha, you read the second one right, too.",
  "허허, 제대로 돌아 나왔구먼.": "Haha, you came back around properly.",
  "틀렸구먼! 그럼 내가 한 잔 더... 딸꾹": "Wrong! Then one more for me... *hiccup*",
  "아깝구먼! 한 번 더 읽어 보게나.": "So close! Read it once more.",
  "틀렸구먼! 다시 올라오게나.": "Wrong! Climb back up.",
  "틀렸구먼! 한 잔 더 마셔야겠네.": "Wrong! Looks like one more drink for me.",
  "3층 화장실 앞(C4)의 분리배출 안내판을 확인하라": "Check the recycling sign in front of the 3F restroom (C4)",
  "다음은 C4의 분리배출 안내판이다.": "Next is the recycling sign at C4."
};

function td(text: string): string {
  if (LANG !== "ko") {
    const hit = TD[text];
    if (hit !== undefined) return hit;
  }
  return text;
}

const ANS_GLOSS: { [ko: string]: string } = {
  "3층 나선계단": "3F spiral staircase",
  "1층 나선계단": "1F spiral staircase",
  "4층 나선계단": "4F spiral staircase",
  "나선형계단앞": "in front of the spiral staircase",
  "나선형계단 앞": "in front of the spiral staircase",
  "나선형 계단 앞": "in front of the spiral staircase",
  "스파이럴계단": "spiral staircase",
  "소용돌이계단": "whirlpool staircase",
  "3층 계단실 앞": "in front of the 3F stairwell",
  "보기1": "option 1",
  "보기2": "option 2",
  "보기3": "option 3",
  "보기4": "option 4",
  "보기5": "option 5"
};

function ansGloss(v: string): string | null {
  if (LANG !== "en") return null;
  const hit = ANS_GLOSS[v];
  return hit !== undefined ? hit : null;
}
