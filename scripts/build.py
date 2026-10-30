"""Build the app from src/.

  docs/              - installable phone app with NO program content; it loads your spreadsheet on first run.
                       GitHub Pages serves this folder.
  private/app.html   - claude.ai artifact version with the program built in (git-ignored: never commit it)
  private/index.html - standalone page with the program built in (git-ignored)

The private builds need src/program.json, made from your own spreadsheet with scripts/parse_xlsx.py.
"""
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
PWA = ROOT / "docs"
PRIVATE = ROOT / "private"

template = (ROOT / "src/app.template.html").read_text()
parser = (ROOT / "src/parse-sheet.js").read_text()
program_file = ROOT / "src/program.json"
program = json.dumps(json.loads(program_file.read_text()), ensure_ascii=False, separators=(",", ":")) if program_file.exists() else None


def body(program_js, pwa_head=""):
    return (template.replace("__PROGRAM__", program_js)
            .replace("/*PARSER*/", parser if pwa_head else "")
            .replace("<!--PWA-HEAD-->", pwa_head))


def page(head_extra, content):
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            "<meta name=\"theme-color\" content=\"#77856b\">\n" + head_extra +
            "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
            "body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n" + content + "\n</body>\n</html>\n")


if program:
    PRIVATE.mkdir(exist_ok=True)
    (PRIVATE / "app.html").write_text(body(program))
    (PRIVATE / "index.html").write_text(page("", body(program)))

# Installable app
shutil.rmtree(PWA, ignore_errors=True)
(PWA / "vendor").mkdir(parents=True)
(PWA / "icons").mkdir()
shutil.copy(ROOT / "vendor/xlsx.full.min.js", PWA / "vendor/xlsx.full.min.js")
for f in (ROOT / "src/icons").glob("*.png"):
    shutil.copy(f, PWA / "icons" / f.name)
head = ("<link rel=\"manifest\" href=\"manifest.webmanifest\">\n"
        "<link rel=\"apple-touch-icon\" href=\"icons/icon-180.png\">\n"
        "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
        "<meta name=\"mobile-web-app-capable\" content=\"yes\">\n"
        "<meta name=\"apple-mobile-web-app-title\" content=\"Min-Max\">\n"
        "<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\">\n")
pwa_scripts = ("<script src=\"vendor/xlsx.full.min.js\" defer></script>\n"
               "<script>if (\"serviceWorker\" in navigator) addEventListener(\"load\", () => navigator.serviceWorker.register(\"sw.js\").catch(() => {}));</script>\n")
html = page(head, body("null", pwa_scripts))
(PWA / "index.html").write_text(html)
(PWA / "manifest.webmanifest").write_text(json.dumps({
    "name": "Min-Max Log", "short_name": "Min-Max", "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#f2f3ee", "theme_color": "#77856b",
    "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
              {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
}, indent=1))
version = hashlib.sha256((html + (ROOT / "src/sw.js").read_text()).encode()).hexdigest()[:10]
(PWA / "sw.js").write_text((ROOT / "src/sw.js").read_text().replace("__VERSION__", version))
shutil.copy(ROOT / "src/pwa-README.md", PWA / "README.md")
(PWA / ".nojekyll").write_text("")
assert "Lying Leg Curl" not in html, "program content leaked into the public build"
print("built docs/ (version " + version + ")" + (" and private/" if program else "; no src/program.json, so private builds skipped"))
