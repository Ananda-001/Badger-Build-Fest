# NEXT_STEPS: from now to submission (updated Sat Sep 26, 23:30 CDT)

**For a teammate's Claude:** read `CLAUDE.md` first (rules, repo map, the Databricks deploy protocol in §6), then
this file. The build is done; what's left is testing, polish and the submission. Close to the deadline, fix and
polish; don't start new features without the team.

The 15:05 handoff (tracks A–E: workbench setup, moving the code into this repo, Databricks setup, prompt v2 and the
learning gate) is **done**; it is in the git history of this file. Results are in `docs/ASSAY_REPORT.md` §8.

**Commit rule:** as in `CLAUDE.md` §5. Your human approves each commit; work goes on `<name>/<topic>` branches;
**nothing merges into `main` until krish has reviewed it.** No force-push, no backdating, no `git add -A`.

---

## Track A: A new teammate gets set up (20 min)

1. Access to the workspace: `docs/DATABRICKS_SETUP.md`, top section. krish adds the email and runs the grants,
   including `MANAGE` on the schema for anyone who will deploy (`CLAUDE.md` §6).
2. Make your own Databricks token; put it in `.env` with `DATABRICKS_HOST` and `DATABRICKS_WAREHOUSE_ID`.
3. `pip install -r requirements.txt`, `python scripts/fetch_data.py`, `python -m pytest -q` → **65 passed**.
4. **Done when** `SELECT COUNT(*) FROM workspace.assay_triage.tickets` returns 37,853 through `dbx.sql`.

## Track B: Test the dashboard like a manager would (30 min, everyone)

1. Open https://assay-manager-7474649367590010.aws.databricksapps.com (add `#tour`), take the 12-step tour.
2. Answer a few suggestions; watch "answered by you" and the trust bars move. Press "Check new tickets now" once.
3. Write anything confusing, broken or ugly into the **Log** below (time, who, what, screenshot if it helps).
4. Don't answer suggestions at random: every Yes / No is saved to `actions` and becomes evidence.

**Done when** each teammate has clicked through once and the Log lists what to fix.

## Track C: Polish the dashboard from the Log (until ~09:30)

1. Branch `<name>/<topic>`. Edit `app/manager/static/index.html` (page, tour) or `app/manager/server.py` (API).
2. Preview locally: `uvicorn app.manager.server:app --port 8000` (reads the same live tables).
3. Tests pass → commit on your human's OK → PR → krish reviews.
4. Deploy only by the protocol in `CLAUDE.md` §6: compare with the live app first, one person deploys, whoever
   deploys last wins. Tell the team chat before and after each deploy.

## Track D: Story (Sat night / Sun morning)

Everything is drafted in `docs/SUBMISSION_KIT.md`; every number there has a source. Change wording freely, never a
number without its source.
- Video (≤ 2 min): script in §2 of the kit. Open the dashboard with `#tour` for a clean first frame.
- Devpost: paste §1 of the kit, add repo + video links, declare Xorbix + Art of the Break.
- Break Card: §3 of the kit. Three mentor visits logged.

## Track E: Sunday morning

- **07:00** Redeploy the dashboard (apps stop 24 h after a deploy): `python scripts/deploy_manager.py`, by the §6
  protocol. Open it once to wake the warehouse. Check the workbench app `assay` too.
- **08:30** Record the video.
- **09:30** Devpost filled in.
- **10:30** Code freeze. Last reviewed commit; tag `v1.0-submission` only with the user's OK.
- **10:45** Submit. Don't wait for 11:00.
- After the event: rotate every API key that was pasted into a chat.

---

## Log (append: time, who, what happened)
- 15:05 krish's Claude: wrote CLAUDE.md + the first version of this file; the workbench zip `assay-workbench-1505.zip` is in `Downloads\Assay`.
- 21:45 krish: teammate quick start added to `docs/DATABRICKS_SETUP.md`; full report `docs/ASSAY_REPORT.md`.
- 23:15 Mohit: set up via Track A; reads, schema grants and CAN_MANAGE on both apps verified. `MANAGE` on the
  schema was granted too, because `deploy_manager.py` runs `GRANT`s and `sync_results.py` replaces tables krish owns.
  Added to `CLAUDE.md` §6.
- 23:30 Mohit's Claude: rewrote `CLAUDE.md` and this file to match the current state (report, submission kit,
  Databricks setup).
- 00:40 Mohith's Claude: dashboard redesign on branch `mohith/dashboard-ui` (report §8.8 lists every change). It
  names the page after Assay, adds a "What Assay decided" row (the four questions), filter chips, target bars,
  evidence cards and a live-run summary. It also pins the one real model switch: before this it was drawn nowhere,
  and two more live runs would have dropped it from the log the page receives. Plus accessibility and phone fixes.
  Tested in a local practice copy (writes kept in memory, nothing sent to Databricks); 65 tests pass. **Needs krish's
  review, then a deploy by the `CLAUDE.md` §6 protocol before the 08:30 recording.** Video script (kit §2) updated.
