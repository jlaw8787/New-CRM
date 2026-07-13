# AI-ASSISTANT-BRIEF.md

A per-consultant AI assistant ("laser-fast assistant") in the CRM. Uses the
robot nurse avatar. Demo-critical: this is the wow feature.

Written 2026-07-11.

---

## Scope (phased) - CONCEPT FIRST for the demo

DEMO APPROACH (decided): build a CONCEPT assistant for the demo - it looks and
works (consultant types, it responds), but responses are scripted/canned for
the specific things shown in the demo, NOT a real AI call. Reasons: no API key
yet, cost is trivial but the secure key setup is real risk days before the
demo, and a concept version never breaks live and demos the same vision. The
REAL thinking assistant (real AI calls) is a post-demo build.

PHASE 1 (BEFORE DEMO): CONCEPT assistant.
- Slide-out / dockable chat panel, robot-nurse avatar, styled to the app.
- Consultant can type; it responds with believable, well-crafted canned
  responses for the demo scenarios (draft a candidate submission email, draft a
  follow-up, summarise a candidate, "what's on today").
- Quick-action chips that trigger these scripted responses.
- It can show it "knows" the current screen (e.g. "viewing Hannah Johnson") by
  reading context already in the app - the canned draft can include real
  on-screen names/data via simple templating, so it feels real.
- NO API key, NO external AI call, NO cost, NO backend. Cannot break live.
- Framed honestly in the demo as "a preview of the assistant we're building."

PHASE 2 (AFTER DEMO): REAL AI assistant.
- Replace the canned responses with real AI calls via a Supabase Edge Function
  (key held server-side, never in the client). Needs an API key (cheap - well
  under a cent per interaction - but needs signup + secure setup).
- Then Phase 3: real CRM actions (create reminders, write data) via tool use.

## Build stages (CONCEPT version for demo)

### STAGE 1 - Panel UI + launcher
Floating "Ask assistant" launcher bottom-right on every screen. Clicking slides
in a ~370px right panel with the robot-nurse avatar in the header, a chat
message area, quick-action chips, and an input box. Styled to the current
design language. No AI yet - just the UI.

### STAGE 2 - Scripted responses
Wire the input + quick-action chips to believable canned responses for the demo
scenarios: draft submission email (pulls the real on-screen candidate name/role
via templating so it looks live), draft follow-up, summarise candidate, what's
on today. Assistant "typing" delay for realism. Draft outputs get Copy/Refine
buttons. Everything client-side, no external calls.

### STAGE 3 (post-demo) - real AI
Swap canned logic for a Supabase Edge Function calling a real model. Separate.

## Avatars (small task, do first - quick win)
Two brand images provided: platypus in purple scrubs (app brand mascot/logo),
robot nurse (AI assistant avatar). Save both into the project, reference them:
platypus in the sidebar/logo area, robot in the assistant panel header + launcher.

## Guard rails
- API key NEVER in index.html or git. Server-side only.
- Phase 1 assistant does not write to Supabase / take real actions - drafts only.
- Style the panel to whatever the current design language is at build time
  (note: a restrained re-skin may be in progress - match it).
- This is additive - must not break existing app functionality.
