# Min-Max Log

A phone-first workout logger for the 12-week Min-Max Program (4x per week).

- `index.html` – the app as a standalone page (open it in any browser; data stays in that browser, back up from Guide → Your data).
- `app.html` – the same app formatted for publishing as a claude.ai artifact, where workouts sync to private storage.
- `src/program.json` – the program (12 weeks × Full Body / Upper / Lower / Arms-Delts), generated from the tracker spreadsheet.
- `src/app.template.html` – the app source.

## Rebuilding

```sh
python3 scripts/parse_xlsx.py Min-Max_Program_4x.xlsx src/program.json   # only if the spreadsheet changes
python3 scripts/build.py                                                 # writes app.html and index.html
python3 scripts/import_log.py Min-Max_Program_4x.xlsx 2026-10-28 backup.json  # sets logged in the sheet -> restorable backup
```
