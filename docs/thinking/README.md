# How our thinking evolved (Sep 26)

1. **Before the event (ideas only, no code carried over):** an agent cost control plane → "certify cheaper models."
   Overnight experiments with real Claude showed real cache costs, but every model scored 100% on clean tasks, so we
   needed real, messy data.
2. **11:00–13:00:** Databricks already routes models automatically but doesn't prove quality. We kept the engine
   idea and looked for a real task with real ground truth: Apache Jira triage (maintainer links as truth).
3. **~14:30, [`01-brief-1430.md`](01-brief-1430.md):** Assay = a proof engine with three questions; Jira triage as the
   demo agent. First real results: retrieval recall, the 60-ticket hardness test, "Haiku REJECTED at +90% cost."
4. **~15:20, [`02-brief-v2-databricks-research.md`](02-brief-v2-databricks-research.md):** a teammate researched
   Databricks: what Free Edition has, what Assay adds on top of it (A1–A7), "act alone" becomes the lead question,
   and "Haiku +90%" is about our setup, not the model.
5. **~15:40, [`03-brief-v3-fact-check.md`](03-brief-v3-fact-check.md):** we fact-checked v2 against the docs and our
   data. It found that a duplicate-heavy sample would fake the precision proof (base rate), that we have only 142
   duplicate tickets to prove with, and it tiered A1–A7 into Must / Should / Could for the remaining hours.
