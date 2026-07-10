# HCA CRM FULL REGRESSION TEST PLAN
# Run ONLY after all UPGRADE-BRIEF.md stages are complete.
# Claude Code executes this with browser access against localhost:8080.

## Ground rules

- Test as three roles in this order: Sarah Keating (consultant),
  Lisa Bennett (admin), Josh Dermody (ops). Log out between roles.
- Prefix every record you create with TEST- so it is identifiable.
- Record results as a table: # | Workflow | Step | Expected | Actual |
  PASS/FAIL | Severity (blocker/major/minor/cosmetic).
- Do NOT fix anything mid-run. Complete the full pass first, report,
  then we fix failures in severity order and re-test only the failures.
- After each page load, check the browser console for red errors and
  record any found, even if the page looks fine.
- At the end, list every TEST- record created so it can be cleaned up.

## W1: Login and role visibility
1. Login screen lists all 7 users with role preview text
2. Login as Sarah Keating: candidate count is only her candidates
3. Sidebar badge counts are non-zero and match actual list contents
4. Switch user works and lands cleanly back at login

## W2: Candidate lifecycle (the big one)
1. Add Candidate: create TEST-Nurse Alpha with full details, save
2. New candidate appears in list, phase New Lead, assigned to Sarah
3. Open full page: every tab renders (Overview, Profile, Work
   Preferences, Compliance, Pipeline, History), no console errors
4. Edit a field in each editable section, save, hard refresh browser,
   confirm every edit persisted (this catches silent write failures)
5. Create Standard Checklist on Compliance tab: 13 items appear
6. Set two items to Verified with an expiry date, card % and section
   bar and tab label all update and agree with each other
7. Advance phase through the dropdown: each change persists and logs
   an activity entry automatically
8. Toggle hot flag on, candidate appears on Hot List

## W3: Submission flow end to end
1. From TEST-Nurse Alpha, + Submit, complete all 5 steps of the flow
2. Submission appears on candidate Pipeline tab AND Submissions page
3. Submissions list: change status via inline dropdown, colour
   updates, persists after refresh
4. Pipeline view: card in correct column, days-in-stage shows, Next
   Stage moves it, three-dot menu jumps it to Declined
5. Verify each status change wrote an activity row (check candidate
   History tab)
6. SLA chips visible on seeded stale submissions

## W4: Alerts work queue
1. Alerts page groups: Critical, Follow-ups, Check-ins, Expiring
2. Log Check-in inline on a check-in alert: composer opens, save
   resolves the alert, activity written, last check-in date updated
3. Snooze hides an alert
4. Mark Verified on a compliance alert works inline
5. Clicking an alert ROW navigates to the exact item with highlight
   flash, compliance item and submission cases both
6. Alert badge count decreases as alerts are resolved

## W5: Facilities and Job Board
1. Facility list renders, open a facility full page, all sections load
2. Edit facility contact info, persists after refresh
3. Job Board: roles render with facility names, create TEST-Role,
   appears immediately
4. Role links: clicking through to facility works

## W6: Contracts and travel
1. Open a seeded On Assignment candidate, Pipeline tab shows contract
2. Edit contract dates, persists
3. Add a TEST flight and accommodation entry, both save and re-render
4. Travel & Expenses page reflects the additions

## W7: Cross-role integrity
1. Login as Lisa Bennett: sees Sarah AND Marcus candidates, not Priya
   or Dan's
2. Lisa opens TEST-Nurse Alpha and edits a field, works, activity
   logs her as author
3. Login as Josh Dermody: sees everything, management dashboard
   renders with pipeline value, consultant table, expiring contracts
4. Consultant switcher on management dashboard filters correctly

## W8: Guard rails
1. Try to create a candidate with no name: blocked with clear message
2. Try an obviously bad email format: handled gracefully
   NOTE: candidate id 231, "TEST-Guardrail Candidate" (email
   "not-an-email"), is the persisted record from this exact check.
   It is an intentional malformed-input test record — do NOT delete
   it or "fix" its email. Keep it as a live guard-rail fixture so
   this case stays covered on future runs.
3. Kill the server, click something that saves: red error toast (not
   silent), restart server, retry succeeds
4. Search for gibberish: clean empty state, not a crash

## W9: Visual QA sweep (Stage 3 verification)
On every page: no emoji icons, no unstyled hover states, no off-grid
spacing that looks obviously broken, loading skeleton on refresh,
designed empty states where lists are empty, consistent page headers.
Screenshot anything that looks wrong.

## Wrap-up
1. Produce the full results table with severity ratings
2. List all TEST- records for cleanup — EXCEPT candidate id 231
   ("TEST-Guardrail Candidate"), which stays permanently per W8.2
3. Recommend the fix order for failures
