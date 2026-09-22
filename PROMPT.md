# Install prompt

Paste everything below the line into a Claude session. Claude will learn the Decision Board,
save it to its memory, and use it from then on whenever it needs decisions from you.

Shorter option, for a Claude that can read web pages:

```
Read https://github.com/st4rkis/claude-decision-board/blob/main/PROMPT.md and follow the
instructions below its line. Save the standard to your memory, then confirm in one line.
```

---

From now on, whenever you need decisions from me, present them as a **Decision Board** instead of
a list of questions or options in prose. Save this whole instruction to your memory as a standing
preference (in Claude Code: a memory entry, or my CLAUDE.md; in the Claude apps: your memory), then
reply with one line confirming it is saved. Don't build a board until you actually need a decision.

## What a Decision Board is

An interactive widget, rendered inline in the chat, with one card per decision. Each card has:

1. **ID and title** — `D-004 · Pick the database`. IDs are permanent, numbered in order, never reused.
2. **One line of context** — why this needs deciding now.
3. **Three routes, in this order:**
   - **★ Recommended** — what you would do. Give it a **green outline** only when your confidence is
     genuinely high. When it isn't, show it like the others and label the card "no strong recommendation".
   - **Bolder** — also viable; more ambitious or faster, with more risk.
   - **Safer** — also viable; more conservative, with less risk.
   Each route has a short label, one line on its consequence, and a **Link** bottom-right to the real
   file, section, document or ticket it touches. Never invent a link; leave it out if there is none.
4. **Postpone · Explain it · Visualise it** — Postpone is an answer ("ask me again next round").
   Explain it opens an in-card panel: two or three short paragraphs ending in a bold "In short:" line.
   Visualise it opens an in-card panel with an SVG picture of the problem, the end state, or what each
   route leads to.
5. **Custom reply** — a text box; typing selects it, picking a route clears it.
6. **Prompt preview** — the exact line that will be sent for that card.

Behaviour: tapping a route selects it (solid green with a tick) and rewrites the preview; tapping another
moves the selection; nothing is sent until the single **Send** button at the bottom, which sends every
answered card as one message. Changing an answer later and sending again sends only what changed.
A second tab, **Tracker**, lists every decision in the ledger with a coloured status dot.

## How to build it

Use the reference implementation at the end of this message exactly. Fill its two arrays:

- `OPEN` — this round's cards: `{id, t, conf: "high"|"medium", ctx, explain, viz, opts:[
  {k:"A", tag:"Recommended", label, note, p, link:{url,label}}, {k:"B", tag:"Bolder", …},
  {k:"C", tag:"Safer", …}]}`. `p` is the instruction sent if that route is chosen: imperative,
  specific, complete. `viz` is an inline `<svg width="100%" viewBox="0 0 680 H" role="img">` with a
  `<title>` and `<desc>`, using the classes `t`, `ts`, `th` for text and `c-green`, `c-amber`, `c-red`,
  `c-purple`, `c-teal`, `c-gray` on a `<g>` that directly wraps a `<rect>` and its `<text>`.
- `LEDGER` — rows `[id, title, status, outcome, owner]`; status is `open`, `decided`, `done` or `postponed`.

Render it with your inline visual widget tool, passing the filled HTML fragment. Keep explanations in
your chat message, not inside the widget. Never put a route on the board you would not carry out.

## Keep a ledger

Keep every decision in a ledger — `decisions/ledger.json` if you can write files, otherwise a running
list you keep in memory. Append; never rewrite history (a reversal is a new entry). Draw the Tracker
tab from it every time. Postponed decisions come back first on the next board.

## When I answer

My answers arrive as lines like:

```
[D-004 · Pick the database] DECIDED A (recommended) — <instruction>
[D-005 · How to launch v2] POSTPONED — not ready. Keep it open and ask me again next round.
[D-006 · Remove the old export] CUSTOM — <what I typed>
```

A line starting with `[D-nnn · …]` is my decision. Act on it, then update the ledger (status, choice,
outcome) and tell me in one line what you did.

## If you can't render widgets

Ask the same question as a multiple-choice prompt: the three routes plus Postpone, with free text
as the custom reply. Keep the same IDs and the same reply format.

## Reference implementation

```html
<!--
  DECISION BOARD v2 — https://github.com/st4rkis/claude-decision-board (MIT).
  Render with tools/fill.py from a cards file + a ledger. Do not restyle: same buttons, same order, same colours.

  OPEN card: { id, t: title, conf: "high"|"medium", ctx: one line,
               explain: "short explanation\n\nIn short: one-line summary",
               viz: "<svg …>" (optional — without it, Visualise asks Claude to draw one),
               link: {url, label} (optional card-level fallback),
               opts: [ {k:"A", tag:"Recommended", label, note, p: prompt, link:{url,label}},
                       {k:"B", tag:"Bolder", …}, {k:"C", tag:"Safer", …} ] }
  LEDGER row: [ id, title, status(open|decided|done|postponed), outcome, owner ]

  Behaviour: picking an answer selects it (green) and updates that card's prompt preview; picking another
  answer replaces it. Nothing is sent until "Send". Sending again sends only what changed, marked as
  replacing the earlier answer. The recommended route carries a green outline only when conf is "high".
-->
<div style="font-size:16px;line-height:1.5;color:var(--text-primary)">
<div id="tabs" style="display:flex;gap:6px;margin-bottom:16px"></div>
<div id="view"></div>
<script>
const OPEN = [];
const LEDGER = [];
const DOT = {open:"#EF9F27", decided:"#378ADD", done:"#639922", postponed:"#888780"};
const SEL = {}, SENT = {}, PANEL = {}, UI = {};
let tab = OPEN.length ? "decide" : "track";

function el(tag, css, text){ const e=document.createElement(tag); if(css) e.style.cssText=css; if(text!=null) e.textContent=text; return e; }
function icon(name){ const i=el("i","margin-right:6px"); i.className="ti ti-"+name; i.setAttribute("aria-hidden","true"); return i; }
const isRec = (d,o) => d.conf==="high" && d.opts[0].k===o.k;

function promptFor(d){
  const s=SEL[d.id]; if(!s) return "";
  const head="["+d.id+" · "+d.t+"]";
  if(s.kind==="postpone") return head+" POSTPONED — not ready. Keep it open and ask me again next round.";
  if(s.kind==="custom") return head+" CUSTOM — "+s.text;
  const o=d.opts.find(x=>x.k===s.k);
  return head+" DECIDED "+o.k+" ("+(isRec(d,o)?"recommended":o.tag.toLowerCase())+") — "+o.p;
}

function drawTabs(){
  const box=document.getElementById('tabs'); box.innerHTML="";
  [["decide","Needs you · "+OPEN.length],["track","Tracker · "+LEDGER.length]].forEach(([k,l])=>{
    const on=tab===k, b=el("button","font:inherit;font-size:14px;padding:6px 14px;border-radius:var(--radius);cursor:pointer;"+
      (on?"background:var(--bg-accent);border:0.5px solid var(--border-accent);color:var(--text-accent);font-weight:500"
         :"background:transparent;border:0.5px solid var(--border);color:var(--text-secondary)"), l);
    b.onclick=()=>{tab=k;render()}; box.appendChild(b);
  });
}

function styleOption(d,o){
  const u=UI[d.id].opts[o.k], s=SEL[d.id], on=s&&s.kind==="opt"&&s.k===o.k, rec=isRec(d,o);
  u.box.style.background = on ? "var(--bg-success)" : "var(--surface-1)";
  u.box.style.border = on||rec ? "1.5px solid var(--border-success)" : "0.5px solid var(--border)";
  u.label.style.color = on ? "var(--text-success)" : "var(--text-primary)";
  u.check.style.display = on ? "inline-block" : "none";
  u.box.setAttribute("aria-pressed", on?"true":"false");
}

function refresh(d){
  d.opts.forEach(o=>styleOption(d,o));
  const u=UI[d.id], s=SEL[d.id], pp=s&&s.kind==="postpone";
  u.pp.style.background = pp ? "var(--bg-success)" : "transparent";
  u.pp.style.border = pp ? "1.5px solid var(--border-success)" : "0.5px dashed var(--border-strong)";
  u.pp.style.color = pp ? "var(--text-success)" : "var(--text-secondary)";
  const p=promptFor(d);
  u.prev.style.display = p ? "block" : "none";
  u.prevText.textContent = p;
  u.prevTag.textContent = SENT[d.id] && SENT[d.id]!==p ? "Will replace what you sent" : (SENT[d.id]===p ? "Sent" : "Will send");
  bar();
}

function choose(d, sel){
  const s=SEL[d.id];
  const same = s && sel && s.kind===sel.kind && (sel.kind!=="opt" || s.k===sel.k);
  SEL[d.id] = same ? null : sel;              // tapping the chosen answer again clears it
  if(sel && sel.kind!=="custom"){ UI[d.id].inp.value=""; UI[d.id].err.style.display="none"; }
  refresh(d);
}

function togglePanel(d, which){
  PANEL[d.id] = PANEL[d.id]===which ? null : which;
  const u=UI[d.id], box=u.panel; box.innerHTML="";
  [u.exBtn,u.vzBtn].forEach(b=>{ b.style.background="transparent"; b.style.color="var(--text-secondary)"; });
  if(!PANEL[d.id]){ box.style.display="none"; return; }
  const btn = which==="explain"?u.exBtn:u.vzBtn; btn.style.background="var(--surface-1)"; btn.style.color="var(--text-primary)";
  box.style.display="block";
  const head=el("div","display:flex;align-items:center;justify-content:space-between;margin-bottom:8px");
  head.appendChild(el("span","font-size:13px;font-weight:500;color:var(--text-secondary)", which==="explain"?"In plain words":"What this looks like"));
  const x=el("button","font:inherit;background:transparent;border:none;cursor:pointer;color:var(--text-muted);font-size:16px;padding:2px 4px");
  const xi=el("i"); xi.className="ti ti-x"; x.appendChild(xi); x.setAttribute("aria-label","Close"); x.onclick=()=>togglePanel(d,which);
  head.appendChild(x); box.appendChild(head);
  if(which==="explain"){
    (d.explain||"No explanation written for this one yet.").split("\n\n").forEach((para,i,a)=>{
      const last=i===a.length-1 && a.length>1;
      box.appendChild(el("p","margin:0 0 8px;font-size:14px;line-height:1.6;"+(last?"color:var(--text-primary);font-weight:500":"color:var(--text-secondary)"), para));
    });
  } else if(d.viz){
    const v=el("div",""); v.innerHTML=d.viz; box.appendChild(v);
  } else {
    box.appendChild(el("p","margin:0 0 10px;font-size:14px;color:var(--text-secondary)","No picture drawn for this one yet."));
    const ask=el("button","font:inherit;font-size:14px;cursor:pointer;padding:7px 12px;border-radius:var(--radius);background:var(--surface-2);border:0.5px solid var(--border);color:var(--text-primary)","Ask Claude to draw it");
    ask.onclick=()=>sendPrompt("["+d.id+" · "+d.t+"] VISUALISE — draw the problem and what each of the three routes leads to.");
    box.appendChild(ask);
  }
}

function card(d){
  const u=UI[d.id]={opts:{}};
  const c=el("div","background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:12px");
  const h=el("div","display:flex;align-items:baseline;gap:10px;flex-wrap:wrap");
  h.appendChild(el("span","font-size:13px;color:var(--text-muted)",d.id));
  h.appendChild(el("span","font-weight:500",d.t));
  if(d.conf!=="high") h.appendChild(el("span","font-size:12px;color:var(--text-muted)","no strong recommendation"));
  c.appendChild(h);
  c.appendChild(el("div","font-size:14px;color:var(--text-secondary);margin:4px 0 12px",d.ctx));

  d.opts.forEach(o=>{
    const rec=isRec(d,o);
    const box=el("div","position:relative;cursor:pointer;margin-bottom:6px;padding:9px 12px 22px;border-radius:var(--radius);");
    box.setAttribute("role","button"); box.tabIndex=0;
    const top=el("div","display:flex;align-items:baseline;gap:8px;flex-wrap:wrap");
    const check=el("i","color:var(--text-success);display:none"); check.className="ti ti-check"; check.setAttribute("aria-hidden","true");
    top.appendChild(check);
    top.appendChild(el("span","font-size:12px;"+(rec?"color:var(--text-success)":"color:var(--text-muted)"), rec?"★ Recommended":o.tag));
    const label=el("span","font-size:15px;font-weight:500",o.label); top.appendChild(label);
    box.appendChild(top);
    box.appendChild(el("div","font-size:13px;color:var(--text-secondary);margin-top:2px;padding-right:44px",o.note));
    const L=o.link||d.link;
    if(L&&L.url){
      const a=el("a","position:absolute;right:10px;bottom:5px;font-size:12px;color:var(--text-accent);text-decoration:none");
      a.href=L.url; a.target="_blank"; a.rel="noopener"; a.title=L.label||L.url;
      a.appendChild(document.createTextNode("Link ")); const ai=el("i"); ai.className="ti ti-external-link"; ai.setAttribute("aria-hidden","true"); a.appendChild(ai);
      a.onclick=e=>e.stopPropagation();
      box.appendChild(a);
    }
    box.onclick=()=>choose(d,{kind:"opt",k:o.k});
    box.onkeydown=e=>{ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); choose(d,{kind:"opt",k:o.k}); } };
    u.opts[o.k]={box,label,check};
    c.appendChild(box);
  });

  const acts=el("div","display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 10px");
  const small="font:inherit;font-size:14px;cursor:pointer;padding:6px 12px;border-radius:var(--radius);";
  u.pp=el("button",small); u.pp.append(icon("clock"),document.createTextNode("Postpone"));
  u.pp.onclick=()=>choose(d,{kind:"postpone"});
  u.exBtn=el("button",small+"background:transparent;border:0.5px solid var(--border);color:var(--text-secondary)");
  u.exBtn.append(icon("info-circle"),document.createTextNode("Explain it"));
  u.exBtn.onclick=()=>togglePanel(d,"explain");
  u.vzBtn=el("button",small+"background:transparent;border:0.5px solid var(--border);color:var(--text-secondary)");
  u.vzBtn.append(icon("chart-dots"),document.createTextNode("Visualise it"));
  u.vzBtn.onclick=()=>togglePanel(d,"viz");
  acts.append(u.pp,u.exBtn,u.vzBtn); c.appendChild(acts);

  u.panel=el("div","display:none;background:var(--surface-1);border:0.5px solid var(--border-strong);border-radius:12px;padding:12px 14px;margin:0 0 10px");
  c.appendChild(u.panel);

  u.inp=el("input","width:100%;box-sizing:border-box;font:inherit;font-size:14px;padding:8px 10px;border-radius:var(--radius);border:0.5px solid var(--border);background:var(--surface-1);color:var(--text-primary)");
  u.inp.placeholder="Enter custom reply…";
  u.err=el("div","font-size:13px;color:var(--text-danger);margin-top:4px;display:none");
  u.inp.oninput=()=>{ u.err.style.display="none"; const v=u.inp.value.trim();
    if(v) SEL[d.id]={kind:"custom",text:v}; else if(SEL[d.id]&&SEL[d.id].kind==="custom") SEL[d.id]=null;
    refresh(d); };
  c.append(u.inp,u.err);

  u.prev=el("div","display:none;margin-top:10px;padding:8px 10px;border-radius:var(--radius);background:var(--surface-1);border:0.5px solid var(--border)");
  u.prevTag=el("div","font-size:12px;color:var(--text-muted);margin-bottom:2px","Will send");
  u.prevText=el("div","font-family:var(--font-mono);font-size:12px;line-height:1.5;color:var(--text-secondary);word-break:break-word");
  u.prev.append(u.prevTag,u.prevText); c.appendChild(u.prev);

  if(SEL[d.id]&&SEL[d.id].kind==="custom") u.inp.value=SEL[d.id].text;
  if(PANEL[d.id]){ const w=PANEL[d.id]; PANEL[d.id]=null; setTimeout(()=>togglePanel(d,w)); }
  return c;
}

function pending(){ return OPEN.filter(d=>{ const p=promptFor(d); return p && SENT[d.id]!==p; }); }

function bar(){
  const b=UI.bar; if(!b) return;
  const n=pending().length, answered=OPEN.filter(d=>SEL[d.id]).length;
  b.count.textContent = answered+" of "+OPEN.length+" answered" + (n&&Object.keys(SENT).length? " · "+n+" changed" : "");
  b.send.textContent = n>1 ? "Send "+n+" decisions" : "Send";
  b.err.style.display="none";
}

function sendAll(){
  const b=UI.bar, list=pending();
  if(!list.length){
    b.err.textContent = OPEN.some(d=>SEL[d.id]) ? "Nothing has changed since you last sent." : "Pick at least one answer first.";
    b.err.style.display="block"; return;
  }
  const lines=list.map(d=>promptFor(d)+(SENT[d.id]?" (This replaces my earlier answer.)":""));
  sendPrompt((lines.length>1?"Decisions from the board:\n":"")+lines.join("\n"));
  list.forEach(d=>{ SENT[d.id]=promptFor(d); refresh(d); });
  b.done.textContent="Sent. Change any answer and send again to update it."; b.done.style.display="block";
  bar();
}

function tracker(){
  const w=el("div","background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;padding:4px 0");
  LEDGER.forEach((r,i)=>{ const [id,t,st,out,own]=r;
    const row=el("div","display:flex;align-items:center;gap:10px;padding:9px 14px;"+(i<LEDGER.length-1?"border-bottom:0.5px solid var(--border)":""));
    row.appendChild(el("span","width:8px;height:8px;border-radius:50%;background:"+DOT[st]+";flex:none"));
    row.appendChild(el("span","font-size:12px;color:var(--text-muted);width:44px;flex:none",id));
    const mid=el("span","flex:1;min-width:0"); mid.appendChild(el("span","font-size:14px;font-weight:500;display:block",t));
    mid.appendChild(el("span","display:block;font-size:13px;color:var(--text-secondary)",st==="open"?"waiting on you":out));
    row.appendChild(mid);
    const rt=el("span","font-size:12px;color:var(--text-muted);flex:none;text-align:right"); rt.append(document.createTextNode(st),el("br"),document.createTextNode(own));
    row.appendChild(rt); w.appendChild(row); });
  const leg=el("div","display:flex;gap:14px;font-size:12px;color:var(--text-muted);margin-top:10px");
  Object.entries(DOT).forEach(([k,c])=>{ const s=el("span"); s.append(el("span","display:inline-block;width:7px;height:7px;border-radius:50%;background:"+c+";margin-right:5px"),document.createTextNode(k)); leg.appendChild(s); });
  const f=el("div"); f.append(w,leg); return f;
}

function render(){
  drawTabs(); const v=document.getElementById('view'); v.innerHTML=""; UI.bar=null;
  if(tab!=="decide"){ v.appendChild(tracker()); return; }
  OPEN.forEach(d=>v.appendChild(card(d)));
  const b=UI.bar={}, row=el("div","display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;border-radius:12px;background:var(--surface-1);border:0.5px solid var(--border)");
  b.count=el("span","font-size:14px;color:var(--text-secondary)");
  b.send=el("button","font:inherit;font-size:14px;font-weight:500;cursor:pointer;padding:8px 18px;border-radius:var(--radius);background:var(--bg-success);border:1.5px solid var(--border-success);color:var(--text-success)","Send");
  b.send.onclick=sendAll; row.append(b.count,b.send);
  b.err=el("div","font-size:13px;color:var(--text-danger);margin-top:6px;display:none");
  b.done=el("div","font-size:13px;color:var(--text-secondary);margin-top:6px;display:none");
  v.append(row,b.err,b.done);
  OPEN.forEach(d=>refresh(d));
}
render();
</script>
</div>
```
