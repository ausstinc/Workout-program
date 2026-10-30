// Reads the Min-Max tracker spreadsheet (first sheet) into the app's program format,
// plus any sets already logged in it. Mirrors scripts/parse_xlsx.py.
function parseWorkbook(XLSX, data) {
  const wb = XLSX.read(data, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  if (!ws || !ws["!ref"]) throw new Error("The spreadsheet is empty.");
  const ref = XLSX.utils.decode_range(ws["!ref"]);
  const cell = (r, c) => ws[XLSX.utils.encode_cell({ r, c })];
  const raw = (r, c) => { const x = cell(r, c); return x ? x.v : null; };
  const link = (r, c) => { const x = cell(r, c); return x && x.l && x.l.Target ? x.l.Target : null; };
  // Excel turned ranges like "6-8" into dates (June 8); turn them back.
  const rng = (v) => {
    if (v == null || v === "") return null;
    if (v instanceof Date) return v.getMonth() + 1 + "-" + v.getDate();
    if (typeof v === "number") {
      if (v > 1000) { const d = XLSX.SSF.parse_date_code(v); return d.m + "-" + d.d; }
      return String(v);
    }
    return String(v).trim();
  };
  const str = (v) => (typeof v === "string" ? v.trim() : "");
  const HEAVY = ["Squat (Your Choice)", "Barbell Incline Press", "Leg Press"];
  const B = 1, C = 2;

  const weeks = [];
  let week = null, day = null, block = null, label = null;
  for (let r = ref.s.r; r <= ref.e.r; r++) {
    const b = str(raw(r, B)), c = raw(r, C);
    if (b.startsWith("Block")) { block = parseInt(b.split(/\s+/)[1], 10); continue; }
    if (b === "Intro Week" || b === "Deload Week") { label = b; continue; }
    if (b.startsWith("Week") && c === "Exercise") {
      week = { week: parseInt(b.split(/\s+/)[1], 10), block, label, days: [] };
      label = null; weeks.push(week); continue;
    }
    if (!week || !c || c === "Exercise") continue;
    if (b && !/rest/i.test(b)) { day = { name: b, exercises: [] }; week.days.push(day); }
    if (!day) continue;
    const tech = rng(raw(r, 3));
    day.exercises.push({
      name: String(c).trim(), link: link(r, C), tech: tech === "N/A" ? null : tech,
      warmup: rng(raw(r, 4)), sets: parseInt(raw(r, 5), 10) || 0, reps: rng(raw(r, 6)),
      rir: [rng(raw(r, 11)), rng(raw(r, 12))], rest: rng(raw(r, 13)),
      subs: [14, 15].map((k) => ({ name: rng(raw(r, k)), link: link(r, k) })).filter((s) => s.name && s.name !== "N/A" && s.name !== "See Notes"),
      notes: rng(raw(r, 16)),
      logged: [[raw(r, 7), raw(r, 8)], [raw(r, 9), raw(r, 10)]],
    });
  }
  if (!weeks.length || !weeks[0].days.length) throw new Error("This doesn't look like the Min-Max tracker: no weeks of exercises found.");
  const shape = (w) => w.days.map((d) => d.name + ":" + d.exercises.length).join("|");
  if (weeks.some((w) => shape(w) !== shape(weeks[0]))) throw new Error("Every week needs the same days and exercises as Week 1.");

  // Only technique and RIR change week to week, so store each exercise once per day.
  const days = weeks[0].days.map((d, di) => ({
    name: d.name,
    exercises: d.exercises.map((e, ei) => {
      const per = weeks.map((w) => w.days[di].exercises[ei]);
      const ex = { name: e.name, link: e.link, warmup: e.warmup, sets: e.sets, reps: e.reps, rest: e.rest, subs: e.subs, notes: e.notes,
        rir: per.map((p) => p.rir.slice(0, e.sets)), tech: per.map((p) => p.tech) };
      if (HEAVY.includes(e.name)) ex.heavy = true;
      if (e.name.startsWith("Dead Hang")) { ex.timed = true; ex.optional = true; }
      const m = /^This can be an? (.*)\.$/.exec(e.notes || "");
      if (m && !ex.subs.length) ex.subs = m[1].split(/, (?:or )?/).map((n) => ({ name: n.trim(), link: null }));
      return ex;
    }),
  }));

  // Sets already typed into the sheet become finished workouts.
  const fmt = (v) => (v == null || v === "" ? "" : String(v));
  const logged = [];
  weeks.forEach((w) => w.days.forEach((d, di) => {
    let any = false;
    const ex = d.exercises.map((e) => {
      const sets = [];
      for (let i = 0; i < e.sets; i++) {
        const [load, reps] = e.logged[i] || [null, null];
        const done = (load != null && load !== "") || (reps != null && reps !== "");
        any = any || done;
        sets.push({ w: fmt(load), r: fmt(reps), rir: "", done });
      }
      return { name: e.name, note: "", tech: false, skipped: false, sets };
    });
    if (any) logged.push({ week: w.week, day: di, ex });
  }));

  return { program: { weeks: weeks.map((w) => ({ week: w.week, block: w.block, label: w.label })), days }, logged };
}
if (typeof module !== "undefined") module.exports = { parseWorkbook };
