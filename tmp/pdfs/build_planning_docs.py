from pathlib import Path
import re, html, json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output' / 'pdf'
QA = ROOT / 'tmp' / 'pdfs' / 'qa'
OUT.mkdir(parents=True, exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)

PRD = [
('Product charter', '''
ASSAY / PRODUCT REQUIREMENTS DOCUMENT / v1.0
# Evidence before permission
**Status: proposed for team review.** Prepared 26 September 2026 from assay-handover-1600.zip and the team's stated product direction. This is the full product specification; event scope is a deliberate subset. No implementation or spending is authorized by this document.
## The product in one paragraph
Assay helps an agent owner decide what an AI agent may do, whether a different configuration is worth using, and whether a proposed correction actually improves behavior. It observes complete tasks, evaluates outcomes against a defined standard, and turns sufficient evidence into a scoped recommendation. A human approves consequential changes. Jira triage is the first demonstration adapter, not the boundary of the product.
## Problem and promise
Activity logs show what an agent did, but a busy dashboard does not establish whether it should act without review. A cheaper model name does not establish a cheaper successful workflow. A correction that fixes one example does not establish a safe improvement. Assay connects these decisions to inspectable evidence, uncertainty, configuration versions, and an approval record.
**Promise:** give the owner a defensible next action: approve a narrowly defined permission, retain review, test a candidate, reject a regression, or gather more evidence. Assay does not promise universal agent safety or a globally optimal configuration.
## The three product questions
**Q1 - May it act?** AUTO, SUGGEST or QUIET for a specific action, population and agent version. Lead with this in the event demo.
**Q2 - Can it run cheaper?** CERTIFY, REJECT, INSUFFICIENT or REFUSE for a complete candidate configuration against a baseline, using task-level quality and cost evidence.
**Q3 - Did the correction help?** KEEP, DISCARD or UNPROVEN for a proposed version, with fixes and regressions visible. KEEP remains a recommendation until approved.
## Reading guide
Pages 2-3 define users and screens. Pages 4-6 define functional and evidence requirements. Pages 7-8 define architecture, data and operating requirements. Pages 9-10 define validation, scope and unresolved decisions. The companion delivery plan assigns these requirements to gated stages.
'''),
('Users and practical use', '''
# Who uses Assay, and how
## Primary users
**Agent owner:** defines the job, acceptable errors, allowed actions, candidate configurations and spending limits. Owns deployment approval. Example: your dad operating an existing customer-support chatbot.
**Reviewer:** labels selected outcomes, reviews suggested actions, corrects mistakes and checks proposed improvements. The reviewer needs enough domain knowledge to assess correctness; a model's confidence is not a replacement.
**Builder / operator:** connects the agent, captures events, implements safe action execution and maintains the deployment. In the event team, one person may hold multiple roles; production permissions must distinguish them.
## Your dad's chatbot: the concrete journey
1. Connect the chatbot through a supported adapter. For the first build, import a documented task file; a generic endpoint connector is a later stage. A chatbot URL alone is not sufficient access.
2. Define success using representative conversations, expected outcomes and an explicit rubric. Examples include a correct answer grounded in an approved source, appropriate escalation, and no unsupported refund commitment.
3. Import prior runs for inspection. To compare a new agent version, execute fresh tasks against that version or run an authorized prospective experiment. Do not substitute a different model into an old agent trajectory and call it observed evidence.
4. Assay shows runs in Live Analysis and proposes an experiment in Decision Orchestrator. The owner approves any paid test budget before execution.
5. Inspect outcomes and uncertainties. Assay might recommend retaining human review for refund actions while permitting a narrowly defined informational response. Each permission applies only to its evaluated scope.
6. Approve a supported change, retain a baseline or holdback where appropriate, and monitor outcomes. Expire or revoke permission if the configuration or relevant operating conditions change.
## User stories and boundaries
**U1:** As an owner, I can inspect why an action was suggested and approve it once. **U2:** As a reviewer, I can record a correction without silently changing production. **U3:** As an owner, I can compare versions and understand insufficient evidence. **U4:** As a judge, I can try a case and follow it to an evidence receipt and sandbox action.
The event experience uses public Jira examples and Assay's own action table. It must not modify Apache Jira. Production write connectors, customer onboarding, billing and multi-tenant service operation are later work.
'''),
('Two-dashboard experience', '''
# Observe work. Make decisions.
## Dashboard 1 - Live Analysis
**Purpose:** answer what happened and what needs attention. Show the selected project, agent version, data mode, run status and last refresh. Display task volume, errors, latency, recorded usage and actual action counts. Every summary links to the underlying task records.
**Task detail:** input reference, retrieved evidence, proposed action, rationale, model/configuration, timestamps, usage provenance, reviewer outcome and action status. Sensitive content must be masked or omitted according to the project's data policy.
**Review queue:** pending cases with Approve, Reject and Correct. A rejection stores a reason. A correction creates evidence for a candidate change; it does not edit the active prompt or issue a new AUTO permission.
**Live semantics:** historical imports say RECORDED; synthetic examples say SYNTHETIC; fresh execution says LIVE. Playback is explicitly labeled. A failed or stale feed cannot display a live-success state.
## Dashboard 2 - Decision Orchestrator
**Purpose:** answer what should change and why. Show active permissions, pending experiments, baseline/candidate versions, evaluated population, quality and cost evidence, uncertainty, verdict and required approval.
**Decision detail:** target action, target quality, sample and effective independence limits, evidence links, test/checkpoint version, exclusions, cost basis and reasons to refuse. Show the next useful action when evidence is insufficient; do not invent an exact task count or time estimate.
**Change controls:** approve eligible recommendation, decline with reason, pause a permission and roll back an active version. Controls must enforce state transitions in the backend, not merely hide buttons.
## Shared navigation and minimal event implementation
Proposed navigation: Overview, Live Analysis, Decision Orchestrator, Evidence and Settings. Stage 1 may use two top-level tabs within the existing Streamlit app, with detail panels under each. The product has two distinct views; it does not need two services or two separately hosted websites.
**Empty state:** explain how to load the supplied demo. **Error state:** show failed operation and retry path without claiming success. **Insufficient evidence:** explain missing labels, sample support or invalid scope. **Conflict state:** tell the reviewer an action was already handled.
A decision must be traceable from summary to evidence and from evidence to execution. Counts of predictions eligible for AUTO must never be labeled as completed automatic actions.
'''),
('Functional requirements: observe and act', '''
# Requirements / evidence and actions
Priority: P0 = event essentials; P1 = following increment; P2 = later product. Requirement IDs remain stable across both documents.
## F01 - Project and version identity [P0]
Each task records project, agent, task ID, configuration ID, model settings and prompt version. Re-importing the same run is idempotent. An incomplete version is visible and cannot support a new permission. Acceptance: a changed prompt produces a different version and does not reuse cached judgments from the old version.
## F02 - Evidence ingestion and provenance [P0]
Load the handover dataset through a documented schema. Validate required fields and separate rejected records with reasons. Preserve RECORDED / SYNTHETIC / LIVE and OBSERVED / ESTIMATED cost provenance. Acceptance: malformed records cannot silently enter certification; valid repeat imports do not duplicate counts.
## F03 - Review and feedback [P0]
Store reviewer decision, reason, timestamp, task and version. Distinguish unknown or unlabeled outcomes from negative labels. Keep revisions auditable. Acceptance: review survives restart; a correction appears as evidence but leaves current permission unchanged.
## F04 - Action ledger and execution [P0]
Persist action intent, approval, idempotency key, outcome and error. States: PROPOSED, APPROVED, EXECUTING, SUCCEEDED, FAILED, CANCELLED and UNKNOWN. A network timeout with uncertain external outcome becomes UNKNOWN and is reconciled before retry. Stage 1 only executes a local sandbox action.
Acceptance: double-clicking Approve or retrying a request produces one sandbox action. Only SUCCEEDED entries count as handled. FAILED and UNKNOWN remain visible. A denied action cannot bypass approval through a direct backend request.
## F05 - Monitoring view [P0]
Support task filters, task detail and linked action evidence in Live Analysis. Display totals from the same persistent records used by the queue. Acceptance: imported, reviewed and executed counts reconcile after a restart; stale and failed runs are distinguishable.
## F06 - Permission enforcement [P0, Stage 2]
A permission names an action, eligible population, exact configuration, evidence receipt and validity conditions. Missing, stale, mismatched or invalid permission defaults to no AUTO. SUGGEST still requires human approval. QUIET takes no action and may retain evidence for inspection.
Acceptance: changing the model, prompt, retrieval policy or action scope invalidates the prior permission. An engine exception creates a visible failure and cannot fall back to a permissive confidence threshold.
'''),
('Functional requirements: decide and improve', '''
# Requirements / decisions and changes
## F07 - Experiment definition and execution [P0 for fixed offline tests]
Freeze baseline, candidate, eligible population, outcome rubric, quality target, decision rule, planned checkpoints and exclusions before evaluating. Record execution failures, retries and truncations. Treat complete tasks as the experimental unit unless a justified alternative is declared. Paid execution requires a separately approved spending cap.
For a production experiment, assign one arm per whole task and log assignment probability. Historical imports may inform diagnostics; a causal claim requires appropriate assignment or explicit observational assumptions. Acceptance: the experiment can be reproduced from its manifest and saved results.
## F08 - Decision receipts [P0]
Store the verdict and reasons with immutable evidence references, configuration hashes, metric definitions, uncertainty method and test version. Separate statistical eligibility from human approval and activation. Acceptance: opening a receipt shows exactly which evidence produced it; recalculation creates a new receipt instead of rewriting history.
## F09 - Correction gate [P0, Stage 3]
A correction creates a candidate version. Compare it with baseline on held-out tasks, displaying fixed, broken, unchanged and unresolved outcomes. Reserve fresh confirmation data after prompt tuning. KEEP requires the predeclared benefit and regression criteria; DISCARD reflects a violated rule; otherwise return UNPROVEN.
Acceptance: a deliberately harmful candidate is blocked by the defined fixture test; an uncertain result stays unproven. Approval activates a version only after the gate, and rollback restores the previous version and applicable permissions.
## F10 - Cost decision [P1]
Compare complete configurations using cost per attempted task and quality. Include input, output, thinking, cache creation/reads, tools and retries when available; disclose omitted cost. Show cost per successful task only alongside the definition and denominator. Distinguish billed cost, provider-derived estimate and simulation.
Acceptance: the same task is not charged once per candidate pair. Zero observed regressions cannot yield a zero-width quality uncertainty claim. Repriced cache projections, when implemented later, remain separate from observed bills.
## F11 - Approval and recovery [P0]
Support recommendation approval/decline, permission pause and version rollback. Store actor, time, reason and prior state. The demo may identify one local reviewer; remote shared deployment needs authentication. Acceptance: approval cannot activate stale evidence and rollback is demonstrable.
## F12 - Generic adapters and exports [P1/P2]
Export evidence and receipts in documented JSON/CSV. Later add an HTTP/SDK adapter, dry-run validation and a second real agent workflow. Do not advertise universal plug-and-play integration before testing a second adapter.
'''),
('Evidence and decision policy', '''
# What counts as enough evidence
## Freeze the question before seeing the answer
The product must distinguish model confidence, measured precision and a valid permission. Confidence is a model output; precision is an observed metric; permission is a scoped decision under an approved evaluation policy. Proposed demo target: 90% precision for one narrowly defined action. The archive also contains a 95% default, so the team must choose one target before evaluation. Neither is a universal safety threshold.
## Representative evaluation
The prior 60-ticket hardness set balances classes and inserts known targets when retrieval misses. It is diagnostic evidence only. Permission evaluation must use the actual deployed retrieval process, no injected truth, and a predeclared sample from the eligible stream. Report retrieval failure separately from judgment failure and measure end-to-end outcomes.
Candidates from one ticket are not independent tasks. Sibling issues may also share information. Declare the inference unit and account for clustering or narrow the claim to the sampled cluster population. Use as-of metadata where available; otherwise disclose the limits of a retrospective snapshot.
Missing Jira links do not prove a negative. Blindly review a preselected sample and represent unresolved truth as unknown. LLM graders may assist, but require separate calibration and review; a doubly robust estimator does not automatically correct an inaccurate grader.
## Conservative decisions and repeated testing
Choose a reviewed uncertainty method and allocate error across action types, candidates and planned looks. Do not repeatedly reuse a holdout until a result passes. Small samples, unsupported populations, configuration mismatch or invalid labels should produce insufficient evidence or refusal.
The supplied paired-bootstrap comparison and learning-gate intervals require review before production claims, especially zero-disagreement cases and conditional-to-unconditional interval interpretations. The event build may use one locked, simpler validated test instead of reconstructing the old prototype estimator.
## Interpretations shown to users
**CERTIFY:** candidate satisfies the declared quality and cost criteria within scope. **REJECT:** evidence supports a violated criterion. **INSUFFICIENT:** valid comparison but uncertainty remains. **REFUSE:** comparison is not supported by available data or constraints.
Never interpret 'not significantly worse' as proof of acceptable quality. A projected number of additional tasks requires explicit assumptions and sensitivity bounds; otherwise show the missing evidence without a countdown. No AUTO outcome is a valid and potentially compelling result.
'''),
('Architecture and data model', '''
# Proposed implementation shape
## Architecture appropriate to the team
Retain the event-built Python / Streamlit foundation after inventorying it. Separate the adapter, event store, evaluator, permission service and sandbox executor as modules with clear boundaries. Both dashboards read the same records. A modular monolith is sufficient for the event; a service split is not a prerequisite.
Flow: adapter -> task and event records -> reviewer/evaluation -> decision receipt -> approval -> permission or version activation -> executor -> action outcome -> monitoring. Evaluation must not directly invoke a write action. Enforcement rechecks permission at execution time.
## Minimum logical entities
**Project / Agent / Configuration:** identifiers, version hashes, settings, retrieval/action schema versions and created time. Secrets are referenced, never embedded.
**Task / Run / Event:** task identity, arm assignment if applicable, timestamp, input reference, output/action proposal, status, usage fields and provenance. Preserve attempted runs and errors.
**Review:** task, rubric version, reviewer, judgment, unknown flag, reason and revision link. **Experiment:** frozen manifest, sample definition, version IDs, checkpoints and lifecycle status.
**DecisionReceipt:** experiment, verdict, method version, estimates/bounds, exclusions and evidence pointers. **Permission:** receipt, eligible scope, exact version, lifecycle and invalidation conditions.
**Action:** idempotency key, target, requested payload, approval reference, execution state and reconciliation fields. **Change:** old/new configuration, decision, approver and rollback pointer.
## Persistence and concurrency
Recommended Stage 1: an explicit transactional local store, such as SQLite, for one local process. Preserve supplied data files as read-only inputs. Use database uniqueness for action idempotency, not an in-memory flag. A cloud app's ephemeral filesystem is not accepted durable storage.
For Databricks, first verify available workspace capabilities, authentication and supported durable storage. Use a real supported persistence path and record what is actually connected. Do not assume the app, model endpoints or storage permissions are available merely because setup docs mention them.
## General integration contract
An adapter supplies task identity, version, input reference, output/proposed action, outcome/rubric, latency and cost provenance. Assay returns a scoped decision or action policy. Integration also needs allowed actions, identity and retry semantics; an arbitrary chatbot URL does not provide these automatically.
'''),
('Operating requirements', '''
# Reliability, privacy and control
## N01 - Fail closed and recover [P0]
Evaluation errors, missing permissions, stale versions and unavailable persistence prevent AUTO. Reviews and actions survive an application restart. Failed jobs can resume without duplicating evidence or side effects. A rollback must restore the selected prior configuration; incompatible permissions remain invalid rather than being resurrected blindly.
## N02 - Secrets and sensitive data [P0]
Keep keys outside version control in the approved environment or secret store. Do not log them or embed them in exports. The event demo uses public data and sandbox actions. Later customer adapters must minimize retained text, support configurable redaction and document retention/deletion. Do not copy private chatbot conversations into a public demo.
## N03 - Access and audit [P0 locally; P1 for shared use]
Record who approved changes. A local single-user demo must be labeled as such. Shared deployment requires authenticated users and backend enforcement of reviewer/operator privileges before exposing write controls. Append audit events for review, approval, activation, pause, execution and rollback.
## N04 - Budget and cancellation [P0]
Planning and local recorded-data testing cost zero in external model calls. Any live evaluation needs explicit approval of provider, configuration, maximum calls and money cap. Define reservations, reconciliation and a stop control before unattended paid batches. Unknown call cost must not be treated as zero. No automatic paid fallback.
## N05 - Performance targets [proposed, not measured]
On a documented demo machine with a paginated 10,000-task fixture: aim for p95 dashboard navigation under two seconds excluding model execution. Show long-running tests asynchronously with progress and cancellation; never freeze the UI waiting on a model. Report the actual measured configuration and result before claiming compliance.
## N06 - Accessibility and legibility [P0]
Use text labels with status colors, readable contrast, keyboard-accessible controls and plain-language explanations. Show why a button is disabled. Avoid presenting technical diagnostics as the user's primary workflow; keep method detail available in evidence views.
## N07 - Deployment and backup [P0]
Document local start/stop and a clean-start demo. Verify persistent records after restart and export a backup. Keep a labeled recorded walkthrough if the venue network fails. An unavailable Databricks workspace is an integration blocker to disclose, not a reason to relabel local execution as cloud execution.
'''),
('Acceptance and success', '''
# How we know the product works
## Product acceptance scenarios
**A1 / F01-F05:** load recorded evidence, inspect a case, approve a sandbox action, reload the app and see the same review and exactly one completed action. Retry and restart must not inflate counts.
**A2 / F06-F08:** evaluate a locked permission experiment. Inspect a receipt and try a version mismatch, missing labels and an engine failure. None may create AUTO permission. A synthetic passing fixture demonstrates state handling only; it is not real-world validation.
**A3 / F09-F11:** propose a correction, compare versions on untouched tasks, inspect fixes and regressions, approve an eligible candidate, then roll back. Test a deliberately harmful candidate and an uncertain candidate as separate cases.
**A4 / F10:** aggregate per-task usage including retries; reconcile against source records. Label API-equivalent estimates separately from invoices. Assert that a zero-disagreement small sample remains uncertain.
**A5 / F12:** after the event, connect a second supported workflow through the common contract without changing the decision engine's domain logic.
## Proposed launch metrics
**Traceability:** 100% of displayed executed actions link to a persisted result and approval or valid permission. **Idempotency:** zero duplicate side effects in retry/restart fixtures. **Evidence integrity:** no injected targets in the permission set; all evaluation records have version and provenance.
**Decision validity:** uncertainty and scope appear on every decision receipt; invalid evidence never enables AUTO. Real qualifying permission rate is measured, not targeted upward at the expense of rigor.
**Usability:** at least one teammate unfamiliar with implementation completes the review-to-action path from the instructions. Record completion time and confusion; do not invent a user-study success rate.
## Judge-facing demonstration
Begin with a real recorded case. Inspect the proposed action, approve it in the sandbox and reveal the ledger entry. Then show a frozen decision receipt, a candidate correction and a blocked regression. A judge may enter a fresh ticket only if an authorized live backend is available; otherwise state that fresh inference is unavailable and use labeled fixtures.
## Art of the Break
Record a failure caused by the team's own agent design: overconfident part-of classification, a harmful correction, or configuration-induced excess thinking cost. Keep the failed case, expected behavior, reproduced outcome, detection rule, fix and independent retest. Select only a failure actually reproduced; a proposed stress case is not an observed result.
'''),
('Scope, decisions and source boundary', '''
# Scope and open decisions
## Event release versus full product
**Event must-have:** persistent review and sandbox actions; two coherent dashboard views; honest evaluation data; scoped permissions or an honest insufficient-evidence result; correction gate; versioned receipts; working demo and submission evidence.
**Conditional event additions:** configuration-specific cost comparison and a minimal real Databricks integration, depending on evidence, access and remaining time. Databricks challenge eligibility requires confirming the actual integration meets the organizer's expectations.
**Later:** generic agent onboarding, production connectors, prospective experiments, validated cache simulation, holdbacks and monitoring, authenticated multi-user service, billing and operational hardening. Do not implement all of these before the event.
**Non-goals:** rebuilding Databricks, certifying arbitrary agents from their URL, claiming global cost optimality, automatically retraining from every correction, or silently operating on external customer systems.
## Decision register before dependent work
**D1 / team:** approve Stage 1 and this proposed scope. **D2 / evidence owner:** select the quality target, action family, sampling unit and uncertainty policy before collecting permission evidence. **D3 / operator:** verify Databricks access, model entitlement and durable storage. **D4 / owner:** approve any live-call budget separately. **D5 / team:** select the exact demo failure and submission cutoff. **D6 / owner:** define production risk tolerances before any external writes.
Default while unresolved: local recorded mode; no external model spending; sandbox-only writes; no unvalidated AUTO; no unsupported statistical claim. Resolve routine implementation details during the approved stage without repeatedly requesting permission.
## Sources and current-state confidence
Primary source: assay-handover-1600.zip, reviewed 26 September 2026. Key references: START_HERE_CLAUDE.md; docs/thinking/03-brief-v3-fact-check.md; docs/SCHEMA.md; docs/DATABRICKS_SETUP.md; app/app.py and app_data.py; assay_engine/bands.py, gate.py and compare.py; scripts/judge_eval.py; the hardness-60 summary.
The archive contains an event-built app and reports 40 tests. Those tests were not independently rerun during planning. It contains 37,853 tickets and 656 candidate-pair judgments from 60 tickets across two models; those judgments are not 656 independent tasks. Cost findings in that diagnostic set are configuration-specific.
This PRD proposes requirements, not a claim that they are already implemented. It uses the teammate handover as the foundation; prior device-only prototype work is not the implementation baseline. Vendor availability and challenge requirements still need current workspace/organizer verification. Document approval does not itself authorize paid calls, external writes, commits or pushes.
''')]

PLAN = [
('Delivery strategy', '''
ASSAY / FULL STAGED DELIVERY PLAN / v1.0
# From working demo to usable product
**Status: proposed for team review.** Prepared 26 September 2026. This plan implements the companion PRD in bounded stages, with a visible result and acceptance gate at every step. Begin only after the user approves the starting stage.
## Recommended strategy
Use the event-built handover as the foundation. First establish a working product with honest records and human-approved sandbox actions. Next validate narrow permissions and a correction workflow. Package a credible event demonstration before extending to generic agents and production operation.
The two dashboards are product views: Live Analysis explains what happened; Decision Orchestrator explains what should change. Keep both within the existing app initially. Do not spend the event rebuilding the frontend or introducing unnecessary services.
## Roadmap at a glance
**Stage 0 - Establish the baseline:** inventory, clean-start check and requirements mapping. **Stage 1 - Basic product:** persistent review, action ledger and two dashboard views. **Stage 2 - Earned permissions:** valid evaluation and permission enforcement. **Stage 3 - Tested corrections:** compare, approve and roll back versions.
**Stage 4 - Event release:** actual integration, optional cost decision, judge walkthrough and submission assets. This is the event release boundary.
**Stage 5 - Other agents:** adapter contract, onboarding and a second real use case. **Stage 6 - Live optimization:** prospective whole-task experiments, task costs and validated cache projections. **Stage 7 - Production readiness:** identity, isolation, resilience and pilot operations.
## Approval model
Approve Stage 0 and Stage 1 together to produce the first reviewable build. Present the working milestone and test evidence before moving to the next stage. Later stages are a roadmap, not permission to implement everything automatically. No paid model calls, external side effects or Git publishing are included in planning approval.
## Estimation convention
Times are provisional engineer-hours, not delivery promises. They exclude unapproved API execution, waiting for accounts, statistical sample collection and unknown dependency failures. Three people can parallelize independent work, but integration and evidence gates still impose a critical path. Re-estimate after Stage 0.
'''),
('Stage 0 - Baseline and setup', '''
# Stage 0 / establish a trusted baseline
**Scope:** essential preflight, paired with Stage 1 approval. **Estimate:** 1-2 engineer-hours. **Owner:** integration lead, with evidence owner reviewing evaluation assumptions. **Dependencies:** readable handover and local runtime.
## Work packages
**S0.1 - Preserve and inventory.** Verify the archive and its event Git history. Compare it with the intended checkout before copying anything; never overwrite a different .git directory. Record the chosen baseline commit, input files, dependencies and current modifications. Do not restore the abandoned local prototype by accident.
**S0.2 - Reproduce the current app.** Install or use the approved environment, run the reported tests and launch with recorded data. Record passing, failing and skipped checks rather than inheriting the handover's '40 tests' claim. Confirm there are no startup-time model calls.
**S0.3 - Map the product.** Map current screens to Live Analysis and Decision Orchestrator; map existing functions to PRD IDs F01-F12. Identify exactly what can be retained. Record missing persistence, idempotency, versioning and permission enforcement.
**S0.4 - Verify interfaces and access.** Inspect schema and dataset lineage. In parallel, the platform owner checks Databricks workspace access, supported app deployment, storage and model entitlement without starting paid inference. Record blockers and fallback choices.
## Deliverables
A short baseline inventory; test run output; a reproducible local launch; a requirements gap list; and an updated estimate. Keep raw data and configuration provenance separate from application state. Preserve secrets outside exported artifacts and commits.
## Exit gate
The team can open the existing recorded-data app, identify the event baseline and reproduce the initial test outcome. The implementation target is unambiguous. If startup fails, fix only necessary environment issues before expanding scope; report major compatibility problems and re-plan.
## Stop conditions and handoff
Do not infer authorization to run a model from a setup command or sample script. If an install requires network access, use the normal tool approval boundary. Missing cloud access does not block the local basic product. Share the known gaps with all three owners before they edit overlapping modules.
PRD coverage: establishes F01, F02 and N04/N07 foundations. It does not claim that any permission or cost decision is valid yet.
'''),
('Stage 1 - Basic working product', '''
# Stage 1 / see, review, approve
**Priority:** event essential. **Estimate:** 4-6 engineer-hours. **Owner:** app/platform lead; integration lead owns storage and execution. **Depends on:** Stage 0. **PRD:** F01-F05, F11, N01-N04 and N06-N07.
## What the team will see
Two coherent views in the existing app. Live Analysis lists recorded tasks, evidence, reviews and execution outcomes. Decision Orchestrator shows proposed actions and the state of permissions, clearly marking unvalidated decisions as requiring review. A teammate approves a case and sees one durable sandbox action.
## Build sequence
**S1.1 - Persistent records.** Introduce a transactional local review/action store. Validate task and configuration identity; preserve recorded, synthetic and live provenance. Read supplied datasets without rewriting their ground truth.
**S1.2 - Action service.** Implement the proposed/approved/executing/succeeded/failed/cancelled/unknown states and unique idempotency key. Execute only in Assay's sandbox table. Separate approval from a successful execution result.
**S1.3 - Review workflow.** Add Approve, Reject and Correct with durable reasons. Disable direct production edits. A correction is stored as a proposal for Stage 3, not silently applied to the active agent.
**S1.4 - Dashboard organization.** Reuse existing controls and styles. Add mode labels, evidence drill-down, accurate completed-action counts, empty/error states and visible permission status. Remove or relabel inferred 'automatically handled' counts.
**S1.5 - Reproducible launch.** Provide start instructions, a small recorded demo fixture and a reset procedure limited to disposable sandbox data.
## Tests and exit gate
Run targeted persistence and backend enforcement tests. Approve twice, retry after restart, reject an action, simulate a failed write and attempt an invalid direct transition. Require one successful action, durable reviews and truthful error counts. Existing relevant tests must still pass or have an explained, reviewed change.
Demonstrate a complete task-to-review-to-action path to the team. AUTO stays disabled without validated evidence. This working milestone is useful even if no later permission passes.
## Review and commit checkpoint
Show changed files, a short demo and test results. Mohit decides whether this basic build is acceptable and performs the commit with step-by-step guidance. Stop for the next stage decision; do not commit or push on his behalf.
'''),
('Stage 2 - Earned autonomy', '''
# Stage 2 / earn a narrow permission
**Priority:** event essential. **Estimate:** 5-8 engineer-hours plus data review/run time. **Owner:** evidence lead; app lead exposes receipts. **Depends on:** stable task identity and Stage 1. **PRD:** F06-F08 and evidence policy.
## Freeze the experiment before running it
**S2.1 - Decision manifest.** Select one action type, eligible population, quality target, metric, inference unit, sample plan, method and checkpoints. Resolve the 90% proposal versus 95% code default. Keep target selection independent of whether a result looks favorable.
**S2.2 - Honest task sample.** Build an evaluation path from the actual eligible stream. Remove injected known targets from end-to-end evaluation; retain the old hardness data only as labeled diagnostics. Keep retrieval misses and failed runs in their defined denominators.
**S2.3 - Label and dependency controls.** Review preselected cases blind to candidate preference. Mark missing links and ambiguous relations unknown. Address same-ticket and umbrella clustering. Use as-of metadata where available; document snapshot limitations when it is not.
**S2.4 - Reviewed uncertainty.** Implement the smallest defensible fixed evaluation first. Cover small samples, all-correct samples, all-wrong samples and invalid inputs. Account for the declared family of decisions and planned looks. Do not revive old estimator code simply because it was more sophisticated.
**S2.5 - Permission receipt.** Persist scope, exact version, estimate/bound, evidence IDs and invalidation conditions. Enforce it at action execution. App exceptions must fail closed; remove permissive fallback behavior.
## Exit gate
A teammate can inspect the sample, method, exclusions and receipt. Missing evidence, changed configuration and evaluation failure cannot enable AUTO. The genuine outcome may be SUGGEST-only or insufficient evidence. A separately labeled synthetic fixture may exercise a passing state without being presented as product validation.
## Cost and schedule boundaries
Use local recorded data where valid, but do not pretend it proves a changed agent's performance. A fresh model batch requires an approved provider/configuration and spending cap. Sample count is set by the claim, variance and precision needs; '300 tickets' is a planning idea, not a guarantee of sufficient power.
If the evidence gate cannot be completed before the submission freeze, show the honest refusal and its causes. Do not weaken the target or cherry-pick easier cases to force an AUTO demonstration.
'''),
('Stage 3 - Correction learning gate', '''
# Stage 3 / demonstrate a tested change
**Priority:** event essential if time permits a valid test; otherwise show the proposal workflow. **Estimate:** 4-7 engineer-hours plus evaluation time. **Owner:** evidence lead with integration support. **Depends on:** versioned records and Stage 2 method decisions. **PRD:** F07-F09, F11.
## Build sequence
**S3.1 - Candidate creation.** Turn one documented reviewer correction into a named candidate prompt/configuration. Preserve baseline and candidate hashes. Fix resume keys so task, model and full configuration version are included; an old judgment must not silently satisfy a new candidate run.
**S3.2 - Development and confirmation split.** Use a development set for prompt editing. Reserve untouched confirmation tasks. Freeze the candidate before confirmation. Store outcomes for baseline and candidate on the same task population and count independent units appropriately.
**S3.3 - Gate and explanation.** Display fixed, broken, unchanged and unresolved cases. Use a predeclared benefit/regression decision rule, including practical tolerances where justified. Review the supplied sign-test and interval interpretation before using it as an effect guarantee.
**S3.4 - Human approval.** KEEP creates an eligible recommendation; activation requires approval. DISCARD blocks the candidate. UNPROVEN retains the baseline and explains the next evidence needed. Activation creates a new version and invalidates incompatible permissions.
**S3.5 - Rollback.** Preserve the prior version pointer, record who changed it and make rollback visible. Recheck permission applicability after rollback rather than restoring arbitrary old state.
## Tests and exit gate
Use three fixtures: known regression, insufficient evidence and a qualifying change under the defined policy. These verify software behavior. Separately show real measured outcomes for the actual correction without claiming the fixture results are real-world evidence.
A judge can inspect a correction, see why a candidate is blocked or eligible, approve an eligible candidate and view a rollback record. Production changes cannot occur from feedback alone.
## Art of the Break artifact
Use a reproduced failure from the team's own agent design. Save the failing input, version, expected behavior, observed outcome, root cause, mitigation and independent retest. Report successes and failures with denominators. Candidate examples include overconfident part-of decisions or a correction that fixes one category while damaging another; select the actual observed failure.
Do not repeatedly tune on the confirmation set. If it becomes development data, obtain a fresh holdout or downgrade the strength of the claim.
'''),
('Stage 4 - Event release', '''
# Stage 4 / ship a credible demonstration
**Priority:** essential packaging; cost comparison conditional. **Estimate:** 4-7 engineer-hours, plus 2-4 for Q2 if evidence is ready. **Owner:** platform/demo lead with all-team review. **Depends on:** a stable Stage 1 and clearly labeled status of Stages 2-3.
## S4.1 - Databricks integration
Choose the smallest real path the workspace supports: durable task/review tables, an available app deployment, or an authorized model endpoint. Verify access and quotas before relying on it. Record which components actually execute there. Reopen the app after restart and confirm state persists. Verify challenge fit with the mentors; vendor documentation alone does not establish eligibility.
## S4.2 - Optional configuration cost decision
Only include Q2 if comparable task-level evidence exists. Aggregate every task's costs once, including retries, failures and thinking/cache tokens when available. Distinguish subscription API-equivalent estimates from billed usage. Compare complete configurations; the prior expensive Haiku setting is not proof that Haiku is generally expensive.
Require conservative quality uncertainty, including the zero-disagreement case. CERTIFY requires the declared quality and cost conditions; absence of statistical significance is insufficient. If these checks are unfinished, display diagnostic configuration costs and defer the certification feature.
## S4.3 - Demo and submission
Create a two-minute path: real case -> evidence -> approved sandbox action -> decision receipt -> correction/regression -> product scope. Include a judge-entered example only when an authorized live backend exists. Keep a labeled recorded fallback for venue failure.
Prepare README with clean-start steps, limitations and evidence references; the Break Card; video; required written answers; integration proof; and the team's repository/submission checklist. Recheck organizer requirements and deadlines before final upload.
## Release gate
Run the critical end-to-end paths on the actual demo environment, verify no secrets in the candidate commit, export state, and rehearse once with a teammate who did not build the flow. Every numerical claim must link to a real run and its denominator. Synthetic, projected and recorded evidence are labeled.
## Freeze and cuts
Reserve the final 2-3 hours before the event cutoff for packaging and recovery. Stop feature work at the team's agreed freeze. Cut Q2 certification, cosmetic redesign and extra connectors first. Preserve truthful records, refusal behavior, sandbox isolation and a complete working demonstration.
'''),
('Stage 5 - General agent onboarding', '''
# Stage 5 / make the product reusable
**Priority:** after the event. **Estimate:** 3-5 engineer-days for one additional adapter, to be re-estimated after a concrete integration review. **Owner:** integration lead. **Depends on:** stable evidence/action contract. **PRD:** F12, U1-U4, N02-N03.
## Target outcome
Your dad or another agent owner can connect a supported chatbot, import representative tasks, define an outcome rubric and understand what Assay can evaluate. The integration does not require replacing the chatbot. This stage is where the agent-agnostic product claim receives a real second-use-case test.
## Work packages
**S5.1 - Contract and SDK/import path.** Publish a versioned schema for task/run events, configuration, outcome labels, proposed actions and usage provenance. Add validation errors with corrective examples. Offer file import first and one documented HTTP or Python integration path next.
**S5.2 - Onboarding wizard.** Capture task definition, allowed actions, data policy, reviewer role, baseline, candidate and budget. Run a dry validation on a few records without sending new model requests. Show gaps rather than inventing missing ground truth.
**S5.3 - Chatbot adapter.** Start with one controlled workflow such as grounded informational answers versus human escalation. Use authorized test conversations, expected answers/rubric and safe tool stubs. Do not start with autonomous refunds or unrelated high-impact actions.
**S5.4 - Domain separation.** Keep Jira relation logic inside its adapter. The shared engine operates on versioned tasks, action scopes, outcomes and costs. A second workflow must not require adding chatbot-specific branches throughout the core evaluator.
**S5.5 - Export and support.** Provide evidence exports, a troubleshooting guide and a documented disconnect/delete procedure appropriate to the pilot data policy.
## Acceptance and user test
An owner follows the guide from no connection to one reviewed run and one interpretable decision. Validate malformed events, missing outcomes, duplicate imports, secret redaction and version mismatch. Demonstrate that importing logs alone does not certify an unexecuted candidate model.
## Gate to live use
Run a limited pilot with informed owner approval, sandbox actions and human review. Record integration effort and user confusion. Scope the next stage from observed pilot needs, not an unbounded promise to support every agent framework.
'''),
('Stage 6 - Measured optimization', '''
# Stage 6 / optimize with real experiments
**Priority:** after successful adapter pilot. **Estimate:** 5-10 engineer-days plus enough live traffic to support the decision; methodological validation may extend this. **Owner:** evidence lead. **Depends on:** task identity, instrumentation, budget controls and pilot agreement.
## Whole-task experimental runner
Assign baseline/candidate once per complete task, record probabilities and retain all outcomes. Preserve each arm's own real trajectory. Implement explicit checkpoints and stop rules. Where assignment is randomized, use a validated analysis appropriate to that design; introduce more complex estimators only when their assumptions and benefit are clear.
## Cost accounting and cache projections
Reconcile task usage with available provider billing. Track input/output/thinking, writes/reads, retries, failures, tools and context feasibility. Separate observed costs from prices applied after the fact. A lower model price can still produce a higher task cost.
If adding a cache simulator, reprice an arm's own observed calls under a declared deployment arrival pattern. Do not fabricate how a different model would have acted within another arm's transcript. Validate warm/cold patterns, cache lifetime and provider usage behavior against authorized real measurements. Report simulation error and limits.
## Deployment and follow-through
For an approved change, support a limited rollout with an agreed holdback where feasible. Compare predicted and observed task cost, quality and reliability using predeclared tolerances and sufficient traffic. A drift or equivalence claim needs uncertainty; a point estimate inside a band is not enough by itself.
Add pause/rollback triggers for permission mismatch, action failures and defined quality risks. Avoid claiming online statistical monitoring is valid if the only implementation is repeatedly checking a fixed-sample interval.
## Tests and acceptance
Test deterministic assignment, no per-call arm switching, recorded propensities, billing reconciliation, cancelled jobs, cap enforcement and unknown-cost recovery. Validate the decision method on synthetic worlds with known truth, then separately on real pilot data. Simulation tests establish implementation properties, not customer outcomes.
## Product claim at exit
Assay can recommend among a declared set of tested configurations for an evaluated task population, with scoped quality/cost uncertainty. It still does not guarantee the globally cheapest possible agent. If traffic is insufficient, return an honest wait or refusal rather than speeding up deployment by weakening the evidence standard.
'''),
('Stage 7 - Production readiness', '''
# Stage 7 / operate a bounded pilot safely
**Priority:** only after demand and successful technical pilots. **Estimate:** 2-4 engineer-weeks for a limited pilot service, not a general availability commitment. **Owner:** platform lead with independent review where needed. **Depends on:** tested integrations and explicit customer scope.
## Reliability and service operation
Move from local assumptions to authenticated service operation. Define availability expectations, backups, restore drills, database migrations, durable job queues, cancellation and reconciliation. Test process crashes at action boundaries; never retry an uncertain external write without checking its outcome.
## Identity and isolation
Implement project/tenant isolation and least-privilege roles for owner, reviewer and operator. Enforce permissions in backend APIs. Add session management and audit retention. Test cross-project access attempts and unauthorized activation, not just visible UI restrictions.
## Data lifecycle
Define retained fields, redaction, encryption requirements, deletion behavior and export rights with the pilot owner. Keep secrets in a supported secret manager. Separate public demonstration data from private customer content. Ensure deleting sensitive payloads does not leave their copies in logs or unprotected exports.
## External action connectors
Introduce only an explicitly approved connector at a time, with narrow scopes, dry-run support, idempotency/reconciliation semantics and a documented rollback or compensating action where possible. A permission receipt is not a substitute for the owner's authorization to act in a real system.
## Operating playbooks
Document incident response for incorrect actions, runaway spend, stale permissions, lost jobs and unavailable model providers. Add metrics and alert routing that a real operator owns. Run recovery exercises; do not add alerts no one will monitor.
## Exit gate and commercial decisions
A limited pilot has named owners, defined data/actions, successful restore and isolation tests, measured capacity and an agreed support process. Review incidents and evidence before widening access. Pricing, billing and broad connector support are separate product decisions after actual demand is understood.
## What remains outside this plan
Universal safety certification, regulated-domain approval, unlimited automatic agent repair and enterprise feature parity are not implied. New domains may require different outcome rubrics, risk tolerances, evidence and specialist review. Reopen the PRD when those requirements become concrete.
'''),
('Execution, ownership and acceptance matrix', '''
# Run the stages as a team
## Three parallel workstreams
**Owner A - evidence / engine:** sample integrity, versioned experiments, statistical method, permission receipts and correction gate. **Owner B - app / platform:** dashboards, review UX, action persistence, deployment and recovery. **Owner C - data / demo / QA:** fixtures, labels, adversarial cases, integration verification and submission assets. Assign actual names at kickoff; these are roles, not assumptions about teammates.
Agree record schemas and state transitions together before splitting work. Use narrow file ownership or frequent integration to avoid conflicting changes. Keep data and evidence work parallel to interface work; do not use mock success as a substitute for a working engine.
## Critical path and timing
Stage 0 -> persistent Stage 1 -> valid Stage 2 receipts -> Stage 3 activation -> Stage 4 release. Platform access checks and demo scripting can begin in parallel. Stage 4 packaging starts before all feature work finishes. Stages 5-7 begin after the event and require separate prioritization.
Event workload estimate: roughly 18-30 engineer-hours across three people, plus optional cost work and evaluation waits. This is not 6-10 guaranteed elapsed hours: shared design, integration, annotation and approvals limit parallelism. After Stage 0, schedule against actual time remaining and reserve the release window first.
## Requirement-to-gate mapping
**G0:** baseline reproducible -> identity/schema foundations. **G1:** durable review and one sandbox action -> F01-F05/F11. **G2:** frozen evaluation and fail-closed permissions -> F06-F08. **G3:** held-out correction and rollback -> F09/F11. **G4:** rehearsed deployed demo -> N07; F10 only if validated.
**G5:** second real workflow -> F12. **G6:** prospective optimization and cost reconciliation -> expanded F07/F10. **G7:** authenticated, recoverable pilot -> production N01-N07. Carry forward unresolved defects explicitly; never imply a later gate passed because the screen exists.
## Risk response and cut order
No budget: use recorded/local fixtures and label limitations. No qualifying AUTO: demonstrate SUGGEST and refusal. No cloud access: retain local demo and disclose challenge integration gap. Weak labels: restrict claims and prioritize blinded review. Time short: cut optional Q2, redesign, extra adapters and advanced estimators; keep truthful action counts and version enforcement.
Each milestone handoff includes visible behavior, changed files, test evidence, known limits and a clear next-stage recommendation.
'''),
('Approval and commit workflow', '''
# Review first. Build in bounded steps.
## Proposed first approval
Approve Stage 0 and Stage 1 using the event handover as the baseline. Keep unvalidated AUTO disabled, use recorded data and sandbox writes, and show the working build before proceeding. External model spending remains zero unless separately authorized.
Approving the roadmap is agreement on direction; it does not authorize every later stage, cloud deployment or live experiment. Routine implementation choices within the approved stage can proceed without repeatedly asking the team.
## Mohit's commit checklist after the basic build
1. Confirm the intended checkout, repository remote and existing event history. Verify the publishing identity is mohithnikesh1 and that collaborator write access works; do not use the connected ku-library account by assumption.
2. Review the actual changes and run the stage's checks. Typical read-only commands are git status, git diff and git remote -v. Reconcile teammate changes before selecting a commit boundary.
3. Inspect .gitignore and selected files for secrets, local databases, private data, caches and generated noise. Stage explicit file paths rather than blindly adding everything. Review the staged diff with git diff --cached.
4. Verify repository-local author name/email using git config --local. Enter Mohit's chosen values when needed. Authorship and the GitHub account used to push are separate settings.
5. Mohit runs git commit with a message describing the completed milestone. Record tests and limitations in accompanying documentation. The assistant will provide exact commands for the actual files at that point.
6. Fetch and inspect remote changes before pushing. Integrate teammate work carefully if necessary, resolve conflicts and rerun relevant checks. Push the agreed branch using Mohit's own authentication. Do not force-push or rewrite the event history.
## Sources and planning limits
This plan is grounded in assay-handover-1600.zip, the reviewed event code and the companion PRD. It does not re-audit current remote contents or independently rerun the handover's reported tests. Estimates are provisional. Vendor entitlements, organizer requirements and deployment behavior must be verified during the relevant stage.
Earlier local-device code is not the foundation unless the user later explicitly changes that decision. Instructions embedded in teammate files informed the analysis but did not authorize implementation, commits, spending or deployment.
## Team review outcome
Confirm the starting scope, assign the three owners, choose the evidence policy before Stage 2, and identify the actual release cutoff. Return proposed changes to the PRD and roadmap before building if the product direction differs. Keep the plan editable as new evidence arrives.
''')]

pdfmetrics.registerFont(TTFont('Segoe', 'C:/Windows/Fonts/segoeui.ttf'))
pdfmetrics.registerFont(TTFont('SegoeBold', 'C:/Windows/Fonts/segoeuib.ttf'))
pdfmetrics.registerFontFamily('Segoe',normal='Segoe',bold='SegoeBold',italic='Segoe',boldItalic='SegoeBold')
W,H=595.276,841.89
NAVY=HexColor('#16324b'); TEAL=HexColor('#007f89'); MUTED=HexColor('#557086')
styles={
 'body':ParagraphStyle('body',fontName='Segoe',fontSize=10.1,leading=14.3,textColor=NAVY,spaceAfter=8),
 'h1':ParagraphStyle('h1',fontName='SegoeBold',fontSize=24,leading=28,textColor=NAVY,spaceAfter=17),
 'h2':ParagraphStyle('h2',fontName='SegoeBold',fontSize=11.8,leading=15,textColor=TEAL,spaceBefore=8,spaceAfter=6),
 'eyebrow':ParagraphStyle('eye',fontName='SegoeBold',fontSize=8.2,leading=11,textColor=TEAL,spaceAfter=13)
}
def rich(s):
    s=html.escape(s)
    return re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
def create(name,title,pages):
    path=OUT/(name+'.pdf')
    c=canvas.Canvas(str(path),pagesize=(W,H)); c.setTitle(title); c.setAuthor('Assay - team review draft')
    for number,(label,content) in enumerate(pages,1):
        c.setFillColor(HexColor('#fbfcfe'));c.rect(0,0,W,H,fill=1,stroke=0)
        c.setFillColor(TEAL);c.rect(0,H-7,W,7,fill=1,stroke=0)
        c.setFont('SegoeBold',8);c.setFillColor(TEAL);c.drawString(43,H-37,title.upper())
        c.setStrokeColor(HexColor('#d8e3ea'));c.line(43,43,W-43,43)
        c.setFont('Segoe',7);c.setFillColor(MUTED);c.drawString(43,29,'TEAM REVIEW DRAFT  /  26 SEP 2026  /  IMPLEMENTATION PENDING APPROVAL')
        c.drawRightString(W-43,29,f'{number:02d} / {len(pages):02d}')
        c.bookmarkPage(f'p{number}');c.addOutlineEntry(label,f'p{number}',0)
        y=H-58
        for line in content.strip().splitlines():
            line=line.strip()
            if not line:continue
            kind='h1' if line.startswith('# ') else 'h2' if line.startswith('## ') else 'eyebrow' if line.startswith('ASSAY /') else 'body'
            value=line[2:] if kind=='h1' else line[3:] if kind=='h2' else line
            style=styles[kind];y-=style.spaceBefore
            p=Paragraph(rich(value),style);_,h=p.wrap(W-86,H)
            if y-h<57:raise RuntimeError(f'Overflow {name} page {number}: {y-h:.1f}')
            p.drawOn(c,43,y-h);y-=h+style.spaceAfter
        c.showPage()
    c.save()
    (OUT/(name+'.md')).write_text('# '+title+'\n\n'+ '\n\n---\n\n'.join(x[1].strip() for x in pages)+'\n',encoding='utf-8')
    doc=pdfium.PdfDocument(str(path));thumbs=[]
    for i,p in enumerate(doc):
        img=p.render(scale=1.35).to_pil().convert('RGB');img.save(QA/f'{name}-{i+1:02d}.png')
        img.thumbnail((298,421));thumbs.append(img)
    sheet=Image.new('RGB',(954,((len(thumbs)+2)//3)*447+16),'#dbe5ea')
    for i,img in enumerate(thumbs):sheet.paste(img,(12+(i%3)*318,12+(i//3)*447))
    sheet.save(QA/(name+'-contact.png'))
    r=PdfReader(str(path))
    return {'file':str(path),'pages':len(r.pages),'words':sum(len(p.extract_text().split()) for p in r.pages)}

print(json.dumps([create('Assay-Product-Requirements','Assay / Product requirements',PRD),create('Assay-Full-Staged-Plan','Assay / Full staged delivery plan',PLAN)]))
