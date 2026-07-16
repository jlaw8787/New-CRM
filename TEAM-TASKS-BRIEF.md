# TEAM-TASKS-BRIEF

Status: POST-DEMO. Do not build before the exec demo (~21 July 2026).
Depends on: real Supabase auth being in place first (Phase 4). Do not start until auth is done.

## What this is

A task system so the team can allocate work to each other and track it. Consultants, admins, and ops can create tasks, assign them to a team member (or themselves), set a due date, and add notes. The point is for the team to support each other with things that come up day to day, not just track their own work.

## Why it waits until after the demo

Two reasons, both real.

1. It needs a new Supabase table and a create/assign/complete flow. That is a genuine data-model change, not a client-side add like the collapse work. Schema changes are the thing not to do days before a demo.
2. "Assign to a consultant" only means something if the app knows who is actually logged in. Right now the app is on the profile-picker login, not real auth. Tasks depends on real Supabase auth landing first so "assigned to" maps to a real identity. Building tasks on the profile picker means reworking it once auth replaces it.

So the order is: auth first, then tasks.

## Scope when built

- New Supabase table: task. Fields: id, title, notes, assignee (user id), creator (user id), due_date, status (open/done, maybe in-progress), created_at, completed_at.
- Create a task and assign it to any team member, or to yourself.
- Edit and complete a task.
- A per-person view of what is assigned to them, so each person sees their own list.
- Notes field so context can be added when the task is created.

## How it should plug into what already exists

Do not build tasks as a separate silo. The app already has an alert engine (getAutos, used by the Alerts page, the Morning Brief, and the assistant's "what's on today"). Overdue and due-soon tasks should surface through that same engine so they show up in the places the team already looks, rather than being a screen nobody checks.

Open question to settle at build time: does an overdue task generate an alert via getAutos (preferred, keeps everything in one place), or does the task list stand alone. Lean towards reusing getAutos.

## Demo line (for the exec demo, since this is not built)

"Next, the team can allocate tasks to each other with due dates and notes, and overdue ones surface right here in the morning brief and the assistant." Roadmap, not a gap. Shows the tool has a coherent future without needing it live.

## Guardrails (same as every other build on this project)

- Plan before building. One thing at a time.
- Verify real behaviour in the browser and in Supabase before moving on.
- Commit to git after each verified piece.
- Distinguish "technically works" from "right for the team."
