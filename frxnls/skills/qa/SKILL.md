---
name: qa
description: Systematically QA-test a running web app with a real browser, then fix the bugs found and verify each fix. Use when asked to "qa", "test this site", "find bugs", "test and fix", or "does this work?". Drives a real browser via the Playwright MCP server.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_navigate_back
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_click
  - mcp__plugin_playwright_playwright__browser_type
  - mcp__plugin_playwright_playwright__browser_fill_form
  - mcp__plugin_playwright_playwright__browser_select_option
  - mcp__plugin_playwright_playwright__browser_hover
  - mcp__plugin_playwright_playwright__browser_press_key
  - mcp__plugin_playwright_playwright__browser_take_screenshot
  - mcp__plugin_playwright_playwright__browser_resize
  - mcp__plugin_playwright_playwright__browser_console_messages
  - mcp__plugin_playwright_playwright__browser_network_requests
  - mcp__plugin_playwright_playwright__browser_evaluate
  - mcp__plugin_playwright_playwright__browser_handle_dialog
  - mcp__plugin_playwright_playwright__browser_wait_for
  - mcp__plugin_playwright_playwright__browser_file_upload
  - mcp__plugin_playwright_playwright__browser_tabs
---

# /qa: Test → Fix → Verify

Browser-based QA. Test a running app as a user, document bugs with screenshot
evidence, fix them at the source, and verify each fix. Adapted from Garry Tan's
gstack `qa` skill — browser layer rewired to the Playwright MCP server, all
gstack telemetry/config/brain plumbing removed.

## Browser tool mapping (Playwright MCP)

This skill uses the `mcp__plugin_playwright_playwright__*` tools. Shorthand used
below → actual tool:

| Shorthand        | Playwright MCP tool                     | Notes |
|------------------|------------------------------------------|-------|
| navigate         | `browser_navigate`                       | go to URL |
| snapshot         | `browser_snapshot`                       | accessibility tree + element refs (use refs to click/type) |
| click            | `browser_click`                          | takes an element ref from the last snapshot |
| type / fill      | `browser_type` / `browser_fill_form`     | `fill_form` for multi-field forms in one call |
| select           | `browser_select_option`                  | dropdowns |
| screenshot       | `browser_take_screenshot`                | pass `filename`; save under the report dir |
| viewport         | `browser_resize`                         | e.g. 375x812 mobile, 1280x720 desktop |
| console          | `browser_console_messages`               | filter to errors |
| network          | `browser_network_requests`               | check failed requests / API calls |
| eval             | `browser_evaluate`                       | run JS, e.g. `await fetch('/api/...')` |
| dialog           | `browser_handle_dialog`                  | alerts/confirms |
| wait             | `browser_wait_for`                       | text appears/disappears or timeout |

There is no "diff snapshot" command — take a `browser_snapshot` before and after
an action and compare the trees yourself.

## Setup (run first)

```bash
REPORT_DIR=".qa-reports/$(date +%Y-%m-%d)"
mkdir -p "$REPORT_DIR/screenshots"
BASE_BRANCH=$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p' || echo main)
BRANCH=$(git branch --show-current 2>/dev/null || echo unknown)
echo "REPORT_DIR=$REPORT_DIR BRANCH=$BRANCH BASE=$BASE_BRANCH"
```

Confirm the Playwright MCP server is connected (its tools appear in your tool
list). If it is not, tell the user and stop — do NOT substitute unit tests or
evals. This skill is browser-based by definition.

## Modes

### Diff-aware (default when on a feature branch with no URL given)

Primary mode for verifying your own work.

1. Analyze the diff to learn what changed:
   ```bash
   git diff "$BASE_BRANCH"...HEAD --name-only
   git log "$BASE_BRANCH"..HEAD --oneline
   ```
2. Map changed files → affected pages/routes:
   - route/controller files → URL paths
   - view/component files → pages that render them
   - model/service files → pages using them
   - API endpoints → test directly with `browser_evaluate` (`await fetch('/api/...')`)
   - style files → pages including them
   - If no pages are obvious, do NOT skip the browser. Fall back to Quick mode.
3. Detect the running app — probe common dev ports (3000/4000/8080/5173/8081).
   If none respond, ask the user for the URL.
4. Test each affected page: navigate, snapshot, screenshot, check console, and
   exercise any interaction the change touched end-to-end.
5. Cross-reference commit messages / PR intent — verify the change does what it
   claims, not just that the page loads.
6. Report scoped to the branch: pages affected, does each work (screenshot
   evidence), any regressions on adjacent pages.

### Full (default when a URL is provided)
Systematic exploration. Visit every reachable page. Document 5-10 well-evidenced
issues. Produce a health score. 5-15 min.

### Quick (`--quick`)
30-second smoke test. Homepage + top 5 nav targets. Page loads? Console errors?
Broken links? Health score only, no detailed issue docs.

### Regression (`--regression <baseline.json>`)
Run Full, then diff against a prior `baseline.json`: which issues are fixed,
which are new, score delta. Append a regression section to the report.

## Workflow

### Phase 1: Initialize
Run Setup. Start a timer (note the time).

### Phase 2: Authenticate (if needed)
- Credentials given: navigate to login, snapshot to find fields, fill, submit,
  snapshot to verify. **Never write real passwords to the report — use `[REDACTED]`.**
- This project: use phone `3025665675`, verification code `123456` when a login
  is required (per AGENTS.md).
- 2FA/OTP: ask the user for the code and wait.
- CAPTCHA: ask the user to complete it in the browser, then continue.

### Phase 3: Orient
Navigate to the target. Take an initial snapshot + screenshot. Map navigation.
Check console for landing errors. Detect framework (Next.js `__next`, Rails
`csrf-token`, SPA client routing). For SPAs, `links` are sparse — use snapshot
refs (buttons/menu items) to navigate.

### Phase 4: Explore
Visit pages systematically. At each page: navigate → snapshot → screenshot →
check console. Then per-page checklist:
1. Visual scan of the screenshot for layout issues
2. Interactive elements — click buttons/links/controls; do they work?
3. Forms — fill and submit; test empty, invalid, edge cases
4. Navigation — all paths in and out
5. States — empty, loading, error, overflow
6. Console — new JS errors after interactions?
7. Responsiveness — resize to 375x812, screenshot, resize back to 1280x720

Depth over breadth: spend time on core flows (home, dashboard, the changed
feature), less on about/terms/privacy. Quick mode: homepage + top 5 only,
skip the checklist.

### Phase 5: Document
Document each issue **immediately when found**, not batched.
- Interactive bug: screenshot before → perform action → screenshot after →
  describe what changed → write repro steps referencing the screenshots.
- Static bug: one screenshot + description.
Append each issue to the report as you go.

### Phase 6: Wrap Up
1. Compute the health score (rubric below).
2. Write "Top 3 Things to Fix" (highest severity).
3. Aggregate console errors across all pages.
4. Fill report metadata: date, duration, pages visited, screenshot count, framework.
5. Save `$REPORT_DIR/baseline.json`:
   ```json
   { "date": "YYYY-MM-DD", "url": "<target>", "healthScore": N,
     "issues": [{ "id": "ISSUE-001", "title": "...", "severity": "...", "category": "..." }],
     "categoryScores": { "console": N, "links": N } }
   ```

## Health Score Rubric
Per-category 0-100, then weighted average.

- **Console** (15%): 0 err→100, 1-3→70, 4-10→40, 10+→10
- **Links** (10%): 0 broken→100, each broken −15 (min 0)
- **Visual / Functional / UX / Content / Performance / Accessibility**: start 100,
  deduct per finding — critical −25, high −15, medium −8, low −3 (min 0)

Weights: Console 15, Links 10, Visual 10, Functional 20, UX 15, Performance 10,
Content 5, Accessibility 15. `score = Σ(category × weight)`.

## Important Rules
1. **Repro is everything.** Every issue needs ≥1 screenshot.
2. **Verify before documenting.** Retry once to confirm it's real, not a fluke.
3. **Never include credentials.** `[REDACTED]` for passwords.
4. **Write incrementally.** Append issues as found.
5. **Test as a user, not a developer** during discovery — don't read source until the fix loop.
6. **Check console after every interaction.** Invisible JS errors are still bugs.
7. **Use realistic data; walk complete workflows end-to-end.**
8. **Depth over breadth.** 5-10 evidenced issues > 20 vague ones.
9. **Never delete output files.** Screenshots/reports accumulate intentionally.
10. **Show screenshots to the user.** After every screenshot, `Read` the file so it renders inline.
11. **Never refuse the browser.** Even if the diff looks backend-only, backend changes affect behavior — open the browser and test.

## Output Structure
```
.qa-reports/<YYYY-MM-DD>/
├── qa-report-<slug>-<YYYY-MM-DD>.md
├── screenshots/
│   ├── initial.png
│   ├── issue-001-before.png
│   ├── issue-001-after.png
│   └── ...
└── baseline.json
```

## Phase 7: Triage
Sort issues by severity. Fix scope by tier:
- **Quick:** critical + high only; defer the rest.
- **Standard (default):** critical + high + medium; defer low.
- **Exhaustive:** all, including cosmetic.
Mark un-fixable-from-source issues (third-party widgets, infra) as "deferred".

## Phase 8: Fix Loop
For each fixable issue, in severity order:

**8a. Locate source** — Grep error strings / component names; Glob file patterns
for the affected page. Only touch files related to the issue.

**8b. Fix** — Read the code, make the **minimal** fix. No refactors, no unrelated
"improvements".

**8c. Commit** — one commit per fix:
```bash
git add <only-changed-files>
git commit -m "fix(qa): ISSUE-NNN - short description"
```

**8d. Re-test** — navigate back, screenshot after, check console, snapshot to
confirm the change had the expected effect.

**8e. Classify** — `verified` (re-test passes, no new errors), `best-effort`
(applied, couldn't fully verify), or `reverted` (`git revert HEAD`, mark deferred).

**8e.5. Regression test** (skip if not verified, pure CSS, or no test setup):
Study 2-3 nearby test files and match their style. Trace the bug's codepath
(precondition → path → break point → adjacent edge cases). Write a test that sets
up the triggering state, performs the action, and asserts correct behavior (not
just "renders"). Use `bun test` (this repo's runner). Attribution comment:
```
// Regression: ISSUE-NNN - {what broke}
// Found by /qa on {YYYY-MM-DD}
```
Passes → `git commit -m "test(qa): regression test for ISSUE-NNN"`. Fails → fix
once, else delete and defer.

**8f. Self-regulation (STOP AND EVALUATE).** Every 5 fixes or after any revert,
compute WTF-likelihood: start 0%, +15% per revert, +5% per fix touching >3 files,
+1% per fix after #15, +10% if all remaining are low severity, +20% if touching
unrelated files. **If >20%, STOP** and ask the user before continuing.
**Hard cap: 50 fixes.**

## Phase 9: Final QA
Re-run QA on all affected pages. Compute final score. **If worse than baseline,
warn prominently — something regressed.**

## Phase 10: Report
Write `.qa-reports/<date>/qa-report-<slug>-<date>.md` with: metadata, summary
table (severity counts), Top 3 fixes, per-issue detail with screenshot paths,
console health summary, and (regression mode) the baseline diff. State the
before/after health scores plainly.
