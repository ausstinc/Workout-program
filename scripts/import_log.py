"""Turn sets already logged in the tracker spreadsheet into an app backup you can restore.

Usage: python3 scripts/import_log.py Min-Max_Program_4x.xlsx 2026-10-28 out.json
The date is used for every imported workout (the sheet has no dates).
"""
import datetime
import json
import sys

from parse_xlsx import parse


def main(xlsx, date, out):
    weeks = parse(xlsx)
    start = datetime.datetime.fromisoformat(date + "T18:00:00")
    sessions = {}
    for w in weeks:
        for di, d in enumerate(w["days"]):
            ex, any_logged = [], False
            for e in d["exercises"]:
                sets = []
                for (load, reps) in e.get("logged", [])[: e["sets"]]:
                    done = load is not None or reps is not None
                    any_logged |= done
                    fmt = lambda v: "" if v is None else str(int(v)) if float(v).is_integer() else str(v)
                    sets.append({"w": fmt(load), "r": fmt(reps), "rir": "", "done": done})
                while len(sets) < e["sets"]:
                    sets.append({"w": "", "r": "", "rir": "", "done": False})
                ex.append({"name": e["name"], "note": "", "tech": False, "skipped": False, "sets": sets})
            if not any_logged:
                continue
            t = int(start.timestamp() * 1000)
            sid = f"imp-w{w['week']}d{di}"
            sessions[sid] = {"id": sid, "week": w["week"], "day": di, "status": "done", "startedAt": t,
                             "finishedAt": t + 60 * 60000, "notes": "Imported from the tracker spreadsheet",
                             "ex": ex, "updatedAt": t}
    json.dump({"app": "min-max-log", "version": 1, "sessions": sessions}, open(out, "w"), indent=1)
    print(f"{len(sessions)} workout(s) written to {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
