# Dashboard redesign: context and handoff (Sun Sep 27, ~00:40 CDT)

Mohith's session with Claude. It covers the manager dashboard (`app/manager/`) from the first review to a working
redesign that is ready to commit. **Nothing is committed or deployed yet.**

---

## 1. Starting point

- Read first: `CLAUDE.md`, `docs/ASSAY_REPORT.md` (§8.8 dashboard, §11 commands), `docs/SUBMISSION_KIT.md`, `docs/NEXT_STEPS.md`.
- Working rules for this session:
  - Mohith runs every git command himself. Claude gives him the commands and the folder, and never runs git.
  - Discuss before building anything big.
  - Use the ui-ux-pro-max skill and the 21st MCP for UI work. 21st components are React/shadcn and their code costs
    a paid retrieval, so they were used only as pattern references, rebuilt in plain HTML/CSS.
- Deadlines: redeploy at **07:00**, record the video at **08:30**, code freeze at **10:30**, submit at **10:45**.
- Changes need krish's review before they reach `main`. Deploys follow the `CLAUDE.md` §6 protocol.

## 2. What the audit found (live data, read-only)

- **The one real model switch was invisible.** The server sends the latest 12 model requests but the page drew only 6,
  and all 6 said "Normal". The switch (SPARK-51070: Llama 70B busy → Qwen 80B, held for review) was the 7th, and two
  more "Check new tickets now" presses would have pushed it out of the 12 entirely. The video at 1:20 depends on it.
- **Assay's four questions weren't on the page.** The data for all four verdicts was there, but spread over five panels.
- **The page was called "Ticket Assistant";** "Assay" was only a small chip.
- **The 21-of-21 card** (the video's 0:30 moment) was 6th in the list.
- **75% of the to-do list is "related"** (101 of 135), the least reliable label type, and there was no filter.
- **Accessibility:**
  - The "Handled" tag measured 4.49:1 in light mode (needs 4.5), and button outlines were 1.4:1.
  - Keyboard focus was lost on the 60 s refresh and after each answer.
  - Icons weren't hidden from screen readers, there was no skip link, and the undo message timed out even while hovered.
- **Phone:** nothing overflowed at 375px, but the sticky header took about a fifth of the screen and the buttons
  stacked unevenly.

## 3. The approach

The page was polished in place; it was not rebuilt. It stays one page of plain HTML/CSS/JS, so the deploy script is
unchanged. React/shadcn was rejected: it's a new framework with a build step, and there was too little time.

## 4. What was built

Files changed: `app/manager/server.py`, `app/manager/static/index.html`, `tests/test_manager.py`, and docs.

- **`server.py`:**
  - `last_switch`: the newest switch found in the whole log, not only the latest rows.
  - Two new counts: `main_answers` and `typical_ms`.
- **Page:**
  - **Header:** "Assay · AI agent manager", "Agent: Jira ticket triage", "Live on Databricks", a colour switch
    (device / light / dark), "Show me around".
  - **What Assay decided:** four tiles (act alone? / which AI? / did a correction help? / reuse past answers?), each
    with a verdict, evidence from the tables, and a "See why" link. Phones show only the four verdicts.
  - **Needs your OK:**
    - filter chips with live counts (Same problem 15 · Part of a project 19 · Connected 101 · New 5)
    - the model's confidence shown as "says 90% sure", since it is never used to decide
    - after each answer, a message saying what moved ("Version-upgrade look-alikes: 22 of 29 answers, about 7 more to
      prove it"), and that pattern's bar pulses
  - **Earning your trust:** bars with a mark where the proof is reached ("21 so far · 29 prove it"), split bars for
    mixed patterns, and "1 is in your list: show it" links.
  - **Handled for you:** when empty, it names the closest pattern and links to its open case.
  - **Held back for your safety:** evidence cards with one big number each; the example and p-value fold underneath.
  - **Which AI answered:**
    - the pinned "Latest switch"
    - the order the models answer in, with the cheaper model marked "Not allowed"
    - "41 of 42 answered by the main model, usually in about 3.0 s"
    - the 5 latest requests
  - **Check new tickets now:** a seconds counter while it runs, then a summary card.
  - **Accessibility and phone:**
    - contrast fixes, focus kept on refresh and after answering, hidden decorative icons, skip link
    - the undo message holds while hovered or focused, one status line for screen readers
    - a two-row phone header, Yes and No side by side, a loading skeleton
  - **Unchanged:** the API routes, the table writes, the 12-step tour (step 5 is still the hands-on step), the deploy script.
- **Tests:** 65 pass. The 2 new tests check that `last_switch` is found beyond the rows the page shows, and that every
  tour step and page element exists with no emoji.
- **Docs:**
  - report §8.8 rewritten
  - video script (kit §2) screen directions updated
  - NEXT_STEPS log entry
  - test count 63 → 65 everywhere it's quoted
  - `docs/ASSAY_REPORT.pdf` **not** regenerated

## 5. How it was checked

- A local practice copy ran the real app code on a read-only snapshot of the tables (taken at 00:13 CDT). Every
  answer, undo and live run stayed in memory, so nothing was written to Databricks and no model was called.
- Checked there:
  - answering, and the message it shows
  - filters and "show it"
  - the live-run card
  - "Handled for you" with 8 simulated answers (first time it was seen with items)
  - tour steps 2, 5 and 9
- Screenshots at 1440px (light and dark) and a true 375px phone width showed no script errors.
- Not checked: clicks against the real tables (the API calls are unchanged), the deployed app, and keyboard or
  screen-reader use by hand.

## 6. Important for the video: the Gradle card

- "Upgrade Gradle to 8.12.1" vs "Upgrade Gradle to 8.12" is the **only** open card of the version-upgrade kind, the
  pattern with 21 of 21 "No" answers. The video's 0:30–0:55 beat answers it live.
- If anyone answers it before the recording, it disappears from the list, and a "Yes" would turn the pattern into
  mixed answers.
- **Don't answer it before the take.** If it's already gone, point at the bar ("22 so far · 29 prove it") instead.
  Answering other cards is fine, but every answer is real evidence.

## 7. Seeing it before it's deployed

- **Locally, against the real data (recommended):**
  `.venv\Scripts\python.exe -m uvicorn app.manager.server:app --port 8000`, then open http://localhost:8000
  (add `#tour` for the tour).
  - The first load can take up to a minute.
  - "Check new tickets now" is hidden, because model calls are off.
  - Yes/No clicks are real answers.
- **A separate preview app on Databricks:** `.venv\Scripts\python.exe scripts\deploy_manager.py --name assay-manager-preview`.
  - This doesn't replace the shared `assay-manager` app.
  - Free Edition may refuse an extra app.
  - It uses the same tables and stops after 24 h.
- **Don't** redeploy the real `assay-manager` app before krish's review.

## 8. Commit and PR commands (Mohith runs these, in Git Bash)

```bash
cd "/c/Users/mohit/OneDrive - UW-Madison/Desktop/Project/assay/assay/event-build"
git checkout -b mohith/dashboard-ui
git status --short        # expect the modified files listed in section 4 (plus this file, if you add it)

# commit 1: the code
git add app/manager/server.py app/manager/static/index.html tests/test_manager.py
git diff --cached | grep -nE 'sk-ant-|sk-proj-|sk-[A-Za-z0-9]{20,}|dapi[0-9a-f]{20,}|ANTHROPIC_API_KEY=.+|OPENAI_API_KEY=.+|DATABRICKS_TOKEN=.+' && echo "STOP: secret"
git commit -m "app: dashboard shows Assay's four decisions and pins the live model switch" -m "The page drew 6 of the 12 routing rows it receives, so the one real switch (the 7th) never showed; server.py now finds the newest switch in the whole log. Adds the four-decision row, filter chips, target bars, evidence cards, a live-run summary, and accessibility and phone fixes. Two new tests." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

# commit 2: the docs
git add docs/ASSAY_REPORT.md docs/SUBMISSION_KIT.md docs/NEXT_STEPS.md docs/DATABRICKS_SETUP.md CLAUDE.md README.md
git diff --cached | grep -nE 'sk-ant-|sk-proj-|sk-[A-Za-z0-9]{20,}|dapi[0-9a-f]{20,}|ANTHROPIC_API_KEY=.+|OPENAI_API_KEY=.+|DATABRICKS_TOKEN=.+' && echo "STOP: secret"
git commit -m "docs: describe the redesigned dashboard; 65 tests" -m "Report 8.8, the video script and the NEXT_STEPS log match the new page; the test count is updated wherever it is quoted." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

# push and open the PR for krish
git pull --rebase origin main
.venv/Scripts/python -m pytest -q    # must say 65 passed
git push -u origin mohith/dashboard-ui
gh pr create --base main --head mohith/dashboard-ui --title "Dashboard: Assay's four decisions, pinned model switch, accessibility"
```

- **Expected false alarm:** the commit 2 scan prints `DATABRICKS_TOKEN=<your own token>`. That's a placeholder in
  `docs/DATABRICKS_SETUP.md`, not a secret.

## 9. Next steps

1. Mohith reviews the page locally (section 7), then commits and opens the PR (section 8).
2. krish reviews and merges.
3. 07:00 redeploy by the `CLAUDE.md` §6 protocol: compare the live app's files with the merged code first; whoever
   deploys last wins.
4. 08:30 video, following the updated script in `docs/SUBMISSION_KIT.md` §2 and section 6 above.
