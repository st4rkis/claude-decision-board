# The Decision Board standard

This is the full specification. The [README](../README.md) is the short version.

## When to use a board

Whenever an assistant is about to end a message with "here are your options" or a list of questions, it builds a board instead. One card per decision. A board with one card is fine.

## One card

Every card has, top to bottom:

1. **ID and title.** `D-004 · Pick the database for the booking service`. IDs are permanent and never reused.
2. **One line of context.** Why this needs deciding now. Not an essay; that is what *Explain it* is for.
3. **Three routes, always in this order:**

   | Position | Label | What it is |
   |---|---|---|
   | 1 | ★ Recommended | What the assistant would do. Only marked when confidence is genuinely high. |
   | 2 | Bolder | Also viable. More ambitious, faster, or bigger — and more risk. |
   | 3 | Safer | Also viable. More conservative, slower, or smaller — and less risk. |

   Each route shows a short label, one line on its consequence, and a **Link** in its bottom-right corner to the file, section, document or ticket it touches. Links must be real; if there is nothing to link, leave it out rather than inventing one.

4. **Postpone · Explain it · Visualise it** — three quieter buttons.
   - **Postpone** is an answer: "not ready, ask me again". The decision stays open and comes back first on the next board.
   - **Explain it** opens a panel inside the card: a plain-words explanation in two or three short paragraphs, ending with a bold *In short:* line.
   - **Visualise it** opens a panel inside the card with a picture of the problem, the end state, or what each route leads to. If no picture was drawn, it offers to ask the assistant for one.
5. **Custom reply.** A text box. Typing in it selects it as the answer; picking a route clears it.
6. **Prompt preview.** Once anything is selected, the card shows the exact line that will be sent.

## Confidence and the green outline {#confidence}

The recommended route carries a **green outline** — but only when the assistant's confidence is high. When it is not, the first route is shown like the others and the card says **"no strong recommendation"**. A star on a coin-flip teaches people to stop trusting the star.

## Selection and sending

- Tapping a route **selects** it: it turns solid green with a tick. Nothing is sent yet.
- Tapping a different route **moves the selection and rewrites the preview**.
- Tapping the selected route again clears it.
- One **Send** button at the bottom sends every answered card as a single message.
- After sending, changing an answer and pressing Send again sends **only the changed cards**, each marked *(This replaces my earlier answer.)*.

## What gets sent

Every line is a complete instruction the assistant can act on without asking again:

```
Decisions from the board:
[D-004 · Pick the database for the booking service] DECIDED A (recommended) — Move the booking service to managed Postgres this week. …
[D-005 · How to launch v2] DECIDED B (bolder) — Launch v2 to everyone on Monday. …
[D-006 · Remove the legacy CSV export] POSTPONED — not ready. Keep it open and ask me again next round.
[D-007 · …] CUSTOM — whatever the person typed
```

The `[D-nnn · title]` prefix is how the assistant recognises a decision. On receiving one it acts on it, then records it in the ledger.

Write each route's instruction (`p` in the card data) the way you would want to receive it: imperative, specific, with the owner and the next step. Never put a route on the board that you would not be willing to carry out.

## The ledger and the tracker

The ledger is a JSON file that holds every decision, open or closed. Statuses: `open`, `decided`, `done`, `postponed`. Append to it; never rewrite history — a reversal is a new entry that references the old one.

The board's **Tracker** tab lists the whole ledger with coloured status dots. The widget keeps no memory between renders, so the tracker is always drawn fresh from the ledger. That is what keeps it true.

## Pictures

Pictures are inline SVG, 680 units wide, with a `<title>` and `<desc>`. Keep them to one idea: the three routes side by side, a before/after, or a small flow. The template's colour classes (`c-green`, `c-amber`, `c-purple`, `c-gray`, `c-red`, `c-teal`) and text classes (`t`, `ts`, `th`) adapt to light and dark mode. Colour carries meaning: green for the good outcome, amber for a warning, red for what breaks.

## Where it runs

- **Inside an AI chat**, in clients that render interactive visuals inline and provide `sendPrompt`. Send posts the message to the chat.
- **In any browser**, via the standalone page `tools/fill.py --standalone` produces. Send shows the message and copies it.
- **Where neither is available** (a terminal-only session, a headless agent), ask the same question as a multiple-choice prompt: the three routes plus Postpone, with free text as the custom reply.

## Rules of thumb

- Explanatory prose goes in the chat message, not inside the widget.
- Pop-ups open inside the card. Some hosts collapse anything with `position: fixed`.
- Keep every card's context to one line and every route's note to one line.
- Postponed decisions return first on the next board.
