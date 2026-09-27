from pathlib import Path
base = Path(__file__).with_name('build_planning_docs.py')
source = base.read_text(encoding='utf-8').split("print(json.dumps([create(")[0]
source = source.replace('IMPLEMENTATION PENDING APPROVAL', 'STAGE 1 AUTHORIZED / LATER GATES PENDING')
exec(compile(source, str(base), 'exec'))
pages = [
('Decision and scope', '''
ASSAY / REVISED EVENT PLAN / v3
# Evidence first. A usable start.
**Status:** the user approved the recommendations and starting milestone. This revision incorporates the v2 review and replaces the event build order, while preserving the full PRD and post-event roadmap. Model spending remains zero; commits and pushes remain Mohit's responsibility.
## Product direction
Assay decides, with evidence, how much freedom an agent receives. Jira is the demonstration adapter. The product has an observation function and a decision function; this build retains the team's existing page names: Review queue, Trust, Try a ticket and Model check.
## What changes from v2
Keep evidence and configuration fixes early. Freeze complete experiment inputs before either arm. Scope resume identity to task, configuration and input plan. Never infer missing legacy settings. Use one declared action per task for a later permission experiment, with a defined tie-break and clustering policy.
Do not retain the existing cost certification unchanged. Do not treat a best-effort file mirror as durable storage. Do not call prompt-version mismatch a demonstration of rollback. Keep reviewer feedback separate from confirmatory evidence unless collected under the approved evaluation protocol.
## What stays unchanged
Start locally. Databricks remains Stage 4, as the user requested. No paid API call or subscription-consuming model run is included in starting-stage approval. No external Jira actions are performed. Later stages require review of the working milestone and dependent decisions.
## Starting deliverable
A local recorded-data workbench: review tickets, save a correction, write one human-approved sandbox link, inspect the receipt and reopen after restart. AUTO remains off. A zero-call preparation tool freezes the next experiment without producing an invented verdict.
The event checkout is separate from the old device prototype and preserves the team's original Git history. No pre-event source is merged into it. This PDF distinguishes proposed later work from the bounded starting implementation.
'''),
('Review findings', '''
# What the review established
## Code and tests
The reviewed baseline is event main 8fefe93. Confirmed issues include ticket/model-only resume, injected targets in the hardness sample, pair-level evidence, missing configuration scoping, prediction-based handled counts, permissive statistical fallback and confidence-exposed feedback used as evidence.
The pre-change test run collected 40 cases from 39 functions: 38 passed and two Streamlit cases were skipped in the old runtime. The starting build installs the declared UI dependencies and must rerun the full suite. Final build results belong in the milestone handoff, not in this baseline count.
## Sample size, not wishful thinking
At a 90% target, a single one-sided 95% Clopper-Pearson test needs 29 correct observations with zero errors, or 46 observations with one error. Splitting alpha across the default two walks increases those passing-bound counts to 36 and 54. Across three relations and two walks, the counts are 46 and 66.
The walk can still stop before reaching a passing bound. In the reviewed implementation, a highest-confidence mistake blocks the 54-item example; the second walk starts at 85. Thirty predicted duplicates are not enough for the proposed default procedure.
The dataset has 142 recorded duplicate-positive tickets among 16,919 tickets from 2025 onward. An unfiltered random 300-task sample has about 2.5 such positives in expectation. This is not a forecast of model-predicted duplicates or of the filtered stream; the filter and representative predictions are not yet available.
## Concrete defects beyond v2
The old comparison returns CERTIFY with a zero-width quality interval for 30 identical outcomes and cheaper candidate cost. The existing app bundle explicitly lists files, so adding a module does not automatically include it. Cloud mirroring catches and ignores upload errors. New API judgments currently lack priced cost unless accounting is added.
These findings justify conservative scope. A working refusal, correction proposal or human-approved action is useful without an unsupported AUTO claim.
'''),
('Starting stage', '''
# Stage 1 / foundations you can use
**Owner:** engine/integration plus app support. **Estimate:** 4-7 engineer-hours including environment and UI checks; re-estimate from actual progress. **Approval:** granted for this starting stage. No model runs.
## A. Configuration and experiment preparation
Add prompt versions v1, v2 and a deliberately bad stress-test version. Include rules, system prompt, backend, model, formatting and known settings in identity. Record unresolved aliases/defaults as unverified; do not claim exact deployment equivalence until resolved.
Fix the old diagnostic runner's resume identity and retain usage provenance. Provide a separate zero-call frozen-plan path containing full ticket/candidate content, order, source hashes and unknown labels. Refuse overwrite and reject modified manifests. The existing candidate snapshot remains diagnostic, not a representative permission sample.
## B. Human review and truthful actions
Keep the four page names. Show recorded configuration, saved reviews, actual sandbox-link counts and clear no-inference labels. Approval writes the review and local link in one transaction. Corrections are proposals only. Repeated or concurrent acceptance of the same proposal must create one link.
Use a small SQLite store locally for atomic uniqueness and restart persistence. This is not a seven-state external-action system and is not proposed as Databricks durable storage. The rejected shortcut was unreliable mirroring, not JSONL as a format. Choose cloud persistence separately in Stage 4.
## C. Fail closed by construction
No imported hardness evidence or ordinary review click may grant AUTO. The workbench shows SUGGEST and explains why no validated permission exists. Do not display existing bootstrap output as certification. Fresh inference controls remain disabled; local search is still useful.
## Acceptance gate
Demonstrate: inspect a real recorded ticket, accept once, retry safely, restart and see the same receipt; save a correction without activating it; switch configuration without pooling reviews; freeze inputs and load them for another prompt with unchanged order. Test persistence failure and malformed inputs. Run existing tests and targeted new tests.
At handoff, provide the app URL, launch instructions, changed-file list and exact test outcome. Stop before the next model experiment or later-stage build decision.
'''),
('Evidence stages', '''
# Stages 2 and 3 / earn the verdict
## Stage 2 - honest permission evidence
**Owner:** evidence lead. **Estimate:** 4-7 engineer-hours plus labeling/evaluation time. Define the action policy, quality target and confidence/error allocation before judging. Recommended demo target is 90%, subject to team confirmation; do not tune it after observing outcomes.
Build retrieval across the actual eligible stream, choose the score filter without labels, freeze a uniform sample and never inject targets. Use historical metadata where available or disclose snapshot leakage. Select one action per ticket using the deployed rule. Account for dependent umbrella clusters and specify the population supported by deduplication.
Unknown labels and retrieval failure must not become correct abstentions. Blindly adjudicate a preselected confirmation sample. Allocate error across relation decisions and planned looks, or narrow the claims. A fixed threshold on untouched data may be simpler than validating adaptive threshold search during the event.
Persist immutable permission receipts with configuration, population, action policy, method, target, evidence references and expiry/invalidation conditions. Missing/invalid receipts must fail closed. A real SUGGEST-only outcome is acceptable; synthetic passing tests must stay labeled as software tests.
## Stage 3 - correction gate
**Owner:** evidence lead with app integration. **Estimate:** 3-5 engineer-hours plus model execution, only after separate usage approval. Compare v1/v2 on identical frozen inputs. Develop corrections on separate data; seed changes alone do not guarantee disjoint sets.
Score the selected action against accepted candidate-specific truth. Unknown, malformed, failed and abstained tasks have explicit policies. Require planned completion accounting instead of silently taking only successful pairs. A sign test at zero margin can support directional evidence under its assumptions; do not report the current scaled interval as a general effect-size guarantee.
Show fixes, regressions and UNPROVEN honestly. The poisoned correction is a stress test, not guaranteed to be rejected. KEEP is a recommendation requiring human approval; activation and rollback remain separate capabilities.
## Experiment launch gate
Before any run, show the exact command, frozen input count, provider/configuration, estimated usage and authorized cap. Subscription calls also consume limited usage. The proposed $10 cap is not approved. Implement paid-run enforcement before offering unattended API execution.
'''),
('Release and priorities', '''
# Stage 4 / integration and release
**Owner:** platform/demo lead with team review. **Estimate:** 3-6 engineer-hours, plus optional Q2 work. Databricks remains here; this revision does not silently move it earlier.
## Actual Databricks integration
Verify workspace capabilities and the chosen durable storage path. Include every new module in the app bundle and every required state artifact in deployment/restore tests. A local write plus swallowed upload failure cannot be reported as a durable cloud action. Confirm restart/redeploy restoration and disclose exactly what runs on the platform.
SQLite on local disk is only the starting-stage store. A cloud action record needs an acknowledged durable write and idempotency appropriate to the selected service. Keep the integration minimal, but verify it. If access fails, show the local app and disclose the challenge integration gap.
## Optional Q2
Only enable certification after fixing the zero-disagreement uncertainty problem and measuring complete-task cost once. Persist usage and explicitly configure/verify thinking behavior. Distinguish observed bills, API-equivalent estimates and simulations. Resolve aliases and missing usage before claiming a configuration comparison. Otherwise show diagnostic costs and defer the verdict.
## Demo and Break Card
Demonstrate a real case, one approved sandbox link, a receipt, and the current evidence limit. Add a correction result only when it has actually been measured. Show configuration mismatch revocation only when a real or explicitly synthetic receipt exists; no permission cannot be presented as a permission that was revoked.
Choose a reproduced failure from the team's own agent design. Keep source version, inputs, expected/observed behavior, root cause, fix and independent retest. Every claimed result needs its file and denominator. Prepare video, README, written answers and organizer checklist; verify current requirements with the team.
## Cut order and time
Use relative milestones rather than the now-stale 19:00/21:30 launch promises. Reserve the final 2-3 hours before the confirmed cutoff. Cut optional Haiku/Q2, visual polish and extra connectors first. Never replace honest evidence with a stronger-looking diagnostic result. If no valid AUTO region exists, retain SUGGEST and explain the next evidence needed.
Post-event Stages 5-7 from the full plan remain: second-agent onboarding, prospective optimization, then production operations. They are not part of this starting-stage approval.
'''),
('Team handoff', '''
# Team decisions and handoff
## Assign ownership
Three people cover engine/evidence, app/platform and data/demo/story. Confirm actual names. Agree the data contract before parallel edits. Existing page labels are retained to limit conflicts; a later redesign requires team agreement.
## Decisions still required
Lock the permission target, error family, action unit, tie-break, clustering treatment and missing-label policy before confirmation data. Approve the specific model run and cap separately. Verify challenge declaration and submission requirements with the organizers. Do not infer completion from a document mentioning an earlier deadline.
## Working with this milestone
Use the separate event-build checkout. The local launch script opens the recorded-data workbench; model calls are disabled. Read docs/STAGE_ONE.md for exact commands and limits. Input data stays separate from the local review database. Back up local-state if reviews need to be carried to another machine.
The prepared frozen sample is intentionally labeled diagnostic because the supplied candidate file is incomplete for a population-wide claim. It is useful for testing preparation and input stability; Stage 2 creates the permission experiment. Prompt v2 is a candidate, not a proven improvement.
## Mohit's commits
Review status and diffs inside event-build, not the parent prototype repository. Inspect selected files for keys and bulk data. Stage explicit paths, verify local author identity and commit the completed milestone yourself. Inspect remote changes before pushing and coordinate with teammates. No force push or history rewrite. The assistant does not commit, push, or add a co-author trailer on your behalf.
## Source and confidence boundary
Sources: event main 8fefe93; assay-handover-1600.zip; Assay-Build-Plan-v2.md; the reviewed scripts, statistical engine, app data layer and bundler; offline baseline tests and numerical edge-case calculations. These are code/evidence findings, not a deployment audit or fresh model evaluation.
The full PRD remains the long-term specification. This revision changes the event sequence and explicitly narrows the first milestone. Later stages are proposals, not claims of completion. Updated test results and a runnable local app are delivered separately with the implementation.
''')]
print(create('Assay-Revised-Event-Plan-v3','Assay / revised event plan v3',pages))
