#!/usr/bin/env python3
"""Render a decision board from a cards file and a ledger.

    python3 tools/fill.py examples/cards.json --ledger examples/ledger.json > board.html
    python3 tools/fill.py examples/cards.json --ledger examples/ledger.json --standalone > demo/index.html

Without --standalone the output is the widget fragment a Claude client renders inline
(pass it as the widget's HTML). With --standalone it is a complete page that runs in any
browser: it supplies the colours, icons and a stand-in for sendPrompt that shows and
copies the message instead of sending it.

Standard library only. Open or postponed ledger entries with no card this round are
reported on stderr, so a postponed decision is never silently dropped.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "board" / "board-template.html"

STANDALONE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decision Board</title>
<meta name="description" content="Ask for decisions with three routes, a clear recommendation, and one Send.">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>
:root{
  --text-primary:#1f1e1d;--text-secondary:#5f5e5a;--text-muted:#888780;--text-accent:#185FA5;--text-danger:#A32D2D;--text-success:#3B6D11;
  --bg-accent:#E6F1FB;--bg-success:#EAF3DE;--border:#d3d1c7;--border-strong:#b4b2a9;--border-accent:#378ADD;--border-success:#639922;
  --surface-1:#f5f4ef;--surface-2:#ffffff;--page:#fbfaf7;--radius:8px;--font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;
  --g50:#F1EFE8;--g6:#5F5E5A;--g8:#444441;--te50:#E1F5EE;--te6:#0F6E56;--te8:#085041;--gr50:#EAF3DE;--gr6:#3B6D11;--gr8:#27500A;
  --am50:#FAEEDA;--am6:#854F0B;--am8:#633806;--re50:#FCEBEB;--re6:#A32D2D;--re8:#791F1F;--pu50:#EEEDFE;--pu6:#534AB7;--pu8:#3C3489;
}
@media (prefers-color-scheme: dark){:root{
  --text-primary:#ecebe6;--text-secondary:#b4b2a9;--text-muted:#888780;--text-accent:#85B7EB;--text-danger:#F09595;--text-success:#C0DD97;
  --bg-accent:#0C447C;--bg-success:#173404;--border:#3a3936;--border-strong:#5F5E5A;--border-accent:#378ADD;--border-success:#639922;
  --surface-1:#252523;--surface-2:#2c2c2a;--page:#1b1b1a;
  --g50:#444441;--g6:#B4B2A9;--g8:#F1EFE8;--te50:#085041;--te6:#5DCAA5;--te8:#E1F5EE;--gr50:#27500A;--gr6:#97C459;--gr8:#EAF3DE;
  --am50:#633806;--am6:#EF9F27;--am8:#FAEEDA;--re50:#791F1F;--re6:#F09595;--re8:#FCEBEB;--pu50:#3C3489;--pu6:#AFA9EC;--pu8:#EEEDFE;
}}
body{margin:0;background:var(--page);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;color:var(--text-primary)}
main{max-width:680px;margin:0 auto;padding:28px 16px 48px}
.intro{font-size:14px;color:var(--text-secondary);margin:0 0 20px;line-height:1.6}
.intro b{color:var(--text-primary);font-weight:500}
.t{font-size:14px;fill:var(--text-primary)}.ts{font-size:12px;fill:var(--text-secondary)}.th{font-size:14px;font-weight:500;fill:var(--text-primary)}
.c-gray>rect{fill:var(--g50);stroke:var(--g6);stroke-width:.5}.c-gray>text{fill:var(--g8)}
.c-teal>rect{fill:var(--te50);stroke:var(--te6);stroke-width:.5}.c-teal>text{fill:var(--te8)}
.c-green>rect{fill:var(--gr50);stroke:var(--gr6);stroke-width:.5}.c-green>text{fill:var(--gr8)}
.c-amber>rect{fill:var(--am50);stroke:var(--am6);stroke-width:.5}.c-amber>text{fill:var(--am8)}
.c-red>rect{fill:var(--re50);stroke:var(--re6);stroke-width:.5}.c-red>text{fill:var(--re8)}
.c-purple>rect{fill:var(--pu50);stroke:var(--pu6);stroke-width:.5}.c-purple>text{fill:var(--pu8)}
#outbox{display:none;margin-top:18px;padding:14px 16px;border-radius:12px;background:var(--surface-1);border:0.5px solid var(--border)}
#outbox pre{white-space:pre-wrap;word-break:break-word;font-family:var(--font-mono);font-size:12px;line-height:1.55;margin:8px 0 10px;color:var(--text-secondary)}
#outbox button{font:inherit;font-size:13px;padding:6px 12px;border-radius:var(--radius);border:0.5px solid var(--border);background:var(--surface-2);color:var(--text-primary);cursor:pointer}
</style>
<script>
// Stand-in for the Claude client's sendPrompt: show the message and copy it.
window.sendPrompt = function (text) {
  var box = document.getElementById('outbox');
  box.style.display = 'block';
  box.querySelector('pre').textContent = text;
  try { navigator.clipboard.writeText(text); box.querySelector('.note').textContent = 'Copied. Inside Claude, this goes straight to the chat.'; }
  catch (e) { box.querySelector('.note').textContent = 'Inside Claude, this goes straight to the chat.'; }
  box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
};
window.openLink = function (url) { window.open(url, '_blank', 'noopener'); };
</script>
</head>
<body>
<main>
<p class="intro"><b>Decision Board</b> — standalone demo. Pick an answer on each card, open <b>Explain it</b> or <b>Visualise it</b>, then press <b>Send</b>. Inside Claude, Send posts the message to the chat; here it appears below and is copied to your clipboard. <a href="https://github.com/st4rkis/claude-decision-board" style="color:var(--text-accent)">Get it on GitHub</a>.</p>
"""

STANDALONE_TAIL = """
<div id="outbox"><div style="font-size:13px;font-weight:500;color:var(--text-secondary)">Message that would be sent</div><pre></pre><span class="note" style="font-size:12px;color:var(--text-muted);margin-right:10px"></span><button onclick="navigator.clipboard.writeText(this.parentNode.querySelector('pre').textContent)">Copy again</button></div>
</main>
</body>
</html>
"""


def render(cards, ledger, standalone):
    rows = [[e["id"], e["title"], e["status"], e.get("outcome", "-"), e.get("owner", "-")] for e in ledger]
    tpl = TEMPLATE.read_text()
    body = tpl[tpl.index("<div"):]  # drop the header comment: the widget is the fragment itself
    body = body.replace("const OPEN = [];", "const OPEN = " + json.dumps(cards, ensure_ascii=False) + ";", 1)
    body = body.replace("const LEDGER = [];", "const LEDGER = " + json.dumps(rows, ensure_ascii=False) + ";", 1)
    return STANDALONE_HEAD + body + STANDALONE_TAIL if standalone else body


def main():
    ap = argparse.ArgumentParser(description="Render a decision board.")
    ap.add_argument("cards", help="JSON list of the cards to ask this round")
    ap.add_argument("--ledger", help="ledger JSON (default: ledger.json next to the cards file)")
    ap.add_argument("--standalone", action="store_true", help="emit a full page that runs in any browser")
    args = ap.parse_args()

    cards_path = Path(args.cards)
    cards = json.loads(cards_path.read_text())
    ledger_path = Path(args.ledger) if args.ledger else cards_path.with_name("ledger.json")
    ledger = json.loads(ledger_path.read_text())["decisions"] if ledger_path.exists() else []

    asked = {c["id"] for c in cards}
    for e in ledger:
        if e["status"] in ("open", "postponed") and e["id"] not in asked:
            print(f"warning: {e['id']} is {e['status']} in the ledger but has no card this round", file=sys.stderr)

    sys.stdout.write(render(cards, ledger, args.standalone))


if __name__ == "__main__":
    main()
