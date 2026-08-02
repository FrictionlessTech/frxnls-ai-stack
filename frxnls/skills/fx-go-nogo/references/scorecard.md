# Scorecard rubric

Ten dimensions. Score 1–5, cite the lane, note evidence confidence.
Reweight per `$VENTURE_HOME/constraints.md` — these defaults assume a solo bootstrapper
targeting $5–10k MRR with low maintenance tolerance.

| # | Dimension | Default weight | Gate? |
|---|---|---|---|
| 1 | Demand evidence | 3× | **Yes** |
| 2 | Distribution | 3× | **Yes** |
| 3 | Regulatory & platform risk | 2× | **Yes** (blocking only) |
| 4 | Economics | 2× | No |
| 5 | Maintenance surface | 2× | No |
| 6 | Time to first dollar | 2× | No |
| 7 | Competition | 1× | No |
| 8 | Build effort | 1× | No |
| 9 | Founder fit | 1× | No |
| 10 | Defensibility | 1× | No |

A gate scoring 1–2 forces No-Go regardless of the weighted total.

---

## 1. Demand evidence — GATE

- **5** — Multiple unprompted public complaints naming this exact pain; people already paying for inadequate alternatives.
- **4** — Clear complaints found, some evidence of budget.
- **3** — Adjacent pain well-documented; this specific gap inferred.
- **2** — Thin, mostly reasoning from first principles.
- **1** — Nothing found. Searched properly, silence.

Score 1–2 → No-Go. Silence is not a green field.

## 2. Distribution — GATE

- **5** — Named channel with enough reachable buyers to hit the account target, workable solo, low cost.
- **4** — Named channel, workable, needs effort or money.
- **3** — Channels exist but each is slow or partial; requires stacking several.
- **2** — Only generic channels (cold email at scale, paid ads, "content").
- **1** — No identified way to reach these buyers.

Score 1–2 → No-Go.

## 3. Regulatory & platform risk — GATE (blocking only)

- **5** — No meaningful regulatory or platform dependency.
- **4** — Manageable; standard privacy/security hygiene.
- **3** — Real compliance cost, but achievable post-revenue.
- **2** — Serious: certification required before first sale, or a hostile platform TOS.
- **1** — Blocking: licensing required, API terms forbid it, or a single platform can kill the business at will.

Score 1 → No-Go.

## 4. Economics

Judge on: ACV × accounts-needed math being plausible; CAC payback under ~12 months; sticky rather than trivially cancellable; margin not eaten by per-account API/inference/data cost.

- **5** — Strong ACV, short payback, sticky, clean margin.
- **3** — Workable but tight on one axis.
- **1** — Requires far more accounts than reachable, or margin is structurally thin.

## 5. Maintenance surface

Weighted heavily when the user's constraint is low ongoing maintenance. Estimate hours/week at target account count.

- **5** — Few or no brittle integrations, self-serve onboarding, no recurring compliance, <2 hrs/wk.
- **4** — 1–2 stable integrations, light support, ~2–5 hrs/wk.
- **3** — Several integrations or moderate support load, ~5–10 hrs/wk.
- **2** — Many fragile dependencies, hands-on onboarding, annual audits, 10–20 hrs/wk.
- **1** — Effectively a services business wearing a SaaS costume, or genuine on-call.

## 6. Time to first dollar

- **5** — Self-serve, days to weeks.
- **4** — Short sales cycle, under a month.
- **3** — 1–3 months, a real but survivable sale.
- **2** — 3–6 months, procurement or committee involved.
- **1** — 6+ months, security review and legal on every deal.

## 7. Competition

- **5** — Real gap; incumbents structurally unable or unwilling to close it.
- **4** — Competitors exist but leave the wedge open; validated category.
- **3** — Crowded, differentiation possible.
- **2** — Crowded and commoditized, or it's obviously a feature the incumbent ships next.
- **1** — Cloneable in a weekend, or a graveyard of failed attempts with no explanation of why you'd differ.

Note: zero competitors is a **2**, not a 5, unless the demand lane independently proves the market. Empty categories are usually empty for a reason.

## 8. Build effort

- **5** — Weeks to a useful wedge.
- **3** — A few months.
- **1** — Six months-plus before anyone can pay, or depends on data you can't get.

## 9. Founder fit

Score against the unfair advantages in `$VENTURE_HOME/constraints.md`: domain knowledge, existing network in the vertical, relevant prior product, technical stack alignment.

- **5** — Genuine edge others can't easily copy.
- **3** — Transferable skills, no specific advantage.
- **1** — Requires domain access or credibility the user doesn't have.

## 10. Defensibility

- **5** — Accumulating data, workflow lock-in, or network effects.
- **3** — Ordinary switching costs once embedded.
- **1** — No moat; success invites immediate cloning.

---

## Reporting format

```
DIMENSION            SCORE  WEIGHT  CONF   BASIS
Demand evidence      4/5    3×      High   demand.md — 9 named complaints, 3 paying for workarounds
Distribution         2/5    3×      Med    distribution.md — no channel reaching >200 qualified buyers
...
WEIGHTED TOTAL: 61/100
GATE FAILURE: Distribution (2/5)
VERDICT: NO-GO
```

Report the gate failure above the total, always. A failed gate is the headline;
the weighted total is context.
