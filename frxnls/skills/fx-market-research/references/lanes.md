# Lane briefs

Hand the relevant section to each subagent verbatim, prefixed with the venture
brief and `$VENTURE_HOME/constraints.md`. Every lane obeys the evidence discipline rules in
SKILL.md Step 2 (tagging, bottom-up, confidence, disconfirmation quota).

Every lane ends with the same three sections:
1. **Confidence** — High/Medium/Low, backed by a compact coverage line: count of
   independent sources; how many are direct-buyer vs behavioral vs
   vendor-authored; recency window; and the single main weakness. A bare
   "Medium" with no coverage line is a defect.
2. **Disconfirming evidence found** — at least one item, or an explicit "searched, found none"
3. **Unknowns** — each with what would resolve it

---

## Lane 1 — Competitors (`competitors.md`)

Find who already serves this buyer. Direct competitors, adjacent tools that
partially cover it, and the status-quo workaround (usually a spreadsheet, an
agency, or an intern — name it, because that's the real competitor).

For each: product, exact positioning, **published pricing with tiers**, apparent
company size (headcount via LinkedIn, funding via Crunchbase), founded date, and
what customers complain about in reviews.

Then answer:
- Is the gap in our wedge real, or has someone quietly closed it?
- Is this a **feature** an incumbent ships next quarter, or a **product**?
- Any dead competitors? Find shut-down post-mortems and failed products — the
  graveyard is more informative than the winners, and a pattern of failures in
  this exact space is a hard signal.
- Price ceiling implied by what's already on the market.

Sources: G2, Capterra, Software Advice, Product Hunt, vendor sites, Crunchbase,
industry-specific vendor directories, "alternatives to X" pages, subreddit
recommendation threads.

---

## Lane 2 — Demand evidence (`demand.md`)

Establish whether the pain is real — and separately, whether anyone *buys* their
way out of it. This is the lane that most often kills an idea, so run it hard.
Report the two kinds of evidence under their own headings; a real problem with
no purchase evidence is a specific, decision-relevant shape of finding.

**Problem evidence** — the pain exists, in the buyer's own unprompted words.
Quote verbatim with links (short quotes only — a sentence, attributed). Cover
frequency, severity, the current workaround, the measurable consequence, and
whether the complainers actually match the brief's persona. Prioritize:

- 1–2 star reviews of incumbents naming this gap
- Subreddit / trade forum / Facebook group / Slack community threads
- Conference talk titles and trade-press articles about the problem

**Purchase evidence** — someone allocates money or intent to it:

- Existing paid tools, however crude — proof of budget
- Job postings describing the manual workaround or a role that exists to do it
- Upwork / Fiverr gigs repeatedly posted for the task
- Consultant / agency service menus covering the workflow
- People asking for recommendations, issuing RFPs, or describing a switch
- Who decides, how they buy, and what triggers the purchase (deadline, audit,
  growth, system change, renewal)

Rules of independence: count a claim once however many sites syndicate it,
require at least two distinct source *types*, and separate vendor-authored
claims from buyer-authored evidence. In confidential or regulated workflows
buyers rarely complain in public — there, purchase-evidence traces are the
primary signal, not a fallback.

Grade overall demand on the ladder: **0 inferred · 1 verbalized ·
2 worked-around · 3 budgeted · 4 sought · 5 switched** — the highest level with
solid support, stating the independent-source count behind it. Finding nothing
is level 0; say so bluntly, do not dress it up.

Also note **who feels it** vs **who signs** — when those differ, it changes the
entire sale.

---

## Lane 3 — Market sizing (`sizing.md`)

Count the buyers. Bottom-up, from real registries.

1. **Total entities** — regulatory registrants (SEC IAPD, state licensing boards),
   trade association membership, Google Maps/Places counts, LinkedIn company
   filters by industry + headcount, government business census (US Census County
   Business Patterns, BLS, NAICS data).
2. **Qualified subset** — filter to those matching the brief's persona: right
   size, right software stack, right geography. Show the filter logic.
3. **Reachable subset** — of the qualified, how many can plausibly be contacted
   given a solo operator's channels? This is the number that matters.
4. **Accounts needed** — from the brief. Compare to reachable. State the implied
   penetration rate. If it needs more than a few percent of the reachable market,
   flag it loudly.

Also: is this segment growing, flat, or consolidating? Consolidation is a
particular threat — it shrinks the buyer count and raises the sophistication of
whoever's left.

---

## Lane 4 — Economics (`economics.md`)

- **Pricing.** What comparable tools charge this buyer, and on what axis (seat,
  usage, flat, % of managed assets). Find their budget for adjacent tools.
- **Per-account revenue.** Realistic monthly revenue per account and the implied
  ACV (annual = monthly × 12), with reasoning. Test the brief's assumption and
  say if it's wrong.
- **CAC.** Estimate against the brief's named channel hypothesis — you cannot
  see the distribution lane, so state that assumption explicitly; the assembly
  step cross-checks it against what distribution actually finds.
- **Payback and time to first dollar.** Sales cycle length for this buyer type.
  Procurement, security review, or committee approval each add months — find
  evidence of how these buyers actually purchase.
- **Churn shape.** Is this sticky (system of record, embedded in workflow) or
  trivially cancellable? What's typical churn for this category?
- **Expansion.** Does revenue grow with the account, or is it flat forever?
  What adjacent action naturally follows the wedge, and what data compounds
  with repeated use? Assess adjacency quality, not platform stories.
- **Cost floor.** API costs, LLM inference, data licensing, hosting per account.
  Watch for anything that scales with usage and compresses margin.

Close with the unit math for the brief's target MRR, showing every input.

---

## Lane 5 — Risk (`risk.md`)

Four categories:

**Regulatory / compliance.** What rules govern this buyer's data and workflow?
(For financial services: SEC/FINRA, books-and-records retention. For health:
HIPAA/BAA. For EU: GDPR.) What must a *vendor* carry — SOC 2, insurance, E&O?
Is any of it required before the first sale, and what does it cost and take?

**Platform / API.** If the product depends on another system's data, read the
actual developer terms of service. Look specifically for: partner-program
gatekeeping, approval requirements, non-compete or non-solicit clauses,
restrictions on storing or displaying data, per-call pricing, rate limits, and
the platform's history of revoking access or building the thing themselves.
This is a common silent killer — quote the specific clauses you find.

**Legal / liability.** Professional liability if the software is wrong. Data
breach exposure. Anything requiring a licensed professional in the loop.

**Concentration.** Does the business depend on one platform, one channel, one
data source, or a handful of customers? Name the single point of failure.

Rate each: Blocking / Serious / Manageable / Minor.

---

## Lane 6 — Distribution (`distribution.md`)

The most decision-relevant lane after demand. Answer concretely: **how do you
get the first 10 paying customers?**

Map every channel where this buyer congregates, and for each give the actual
name, size, and access cost:
- Trade associations and their member directories
- Conferences and trade shows — dates, attendance, booth cost
- Trade publications and newsletters — circulation, ad rates
- Online communities — subreddits, Slack/Discord, Facebook groups, forums (with
  subscriber counts and whether promotion is tolerated)
- Existing consultants / agencies / MSPs serving them, as referral partners
- Integration marketplaces and app directories of the tools they already use
- SEO — what they actually search for, and how contested those terms are
- Purchasable lists, and whether outbound is viable or regulated in this vertical

For each: reachable volume, cost, and whether a solo founder can work it.

Then: **who do these buyers trust?** In tight verticals, purchase decisions run
through a handful of consultants, influencers, or peer networks. Name them.

Verdict on distribution: is there at least one channel that plausibly delivers
the required account count, worked solo? If not, say so directly — it outweighs
almost everything else in the dossier.

---

## Lane 7 — Build & maintain (`build.md`)

**Build to v1 (the wedge only, not the full vision).**
- Core technical components; anything genuinely novel vs. standard CRUD
- Integrations required at launch, and how good each API is
- Data acquisition: what's needed, where it comes from, what it costs, licensing
- Realistic timeline for one senior full-stack developer working with AI tooling
- Hard parts — call out anything that looks easy but isn't (auth into legacy
  systems, PDF/document parsing, real-time sync, reconciliation logic)

**Maintenance surface — score this explicitly.** The user's constraint is low
ongoing maintenance, so this section carries real weight:
- Count of external integrations that can break without warning
- Frequency of breaking change in those APIs (check their changelogs)
- Compliance work recurring annually (SOC 2 renewal, pen tests, audits)
- Expected support load: is this self-serve or does every account need hand-holding?
- On-call implications — does anything break at 2am and cost the customer money?
- Manual ops hiding behind the product (data cleaning, exception handling,
  onboarding each account by hand)

Estimate **hours/week at 25 accounts** and compare to the constraints file. Be
pessimistic; maintenance estimates are wrong in one direction.

---

## Lane 8 — Adoption & switching (`adoption.md`)

What must a buyer do, abandon, or risk to adopt the wedge? Default-on; skipped
only when the screen showed a genuinely greenfield, run-alongside wedge (the
skip reason goes in `_index.md`). Adoption friction kills otherwise-attractive
gaps: many wedges fail not on demand but on the path into the account.

Assess concretely:

- **Time to first value** — from signup to the first moment the buyer sees the
  outcome. Can value be demonstrated with historical or exported data before
  any integration?
- **Integration prerequisites** — what must connect before value is visible,
  and how gated is each API (partner programs, approval queues)?
- **Migration** — does any data or record have to move? From where, at what
  risk?
- **Parallel-run feasibility** — can it run alongside the incumbent without
  migrating the system of record? Is adoption reversible if it disappoints?
- **Stakeholders** — how many people must say yes (user, budget owner, IT,
  security, compliance), and what does each veto look like?
- **Procurement and security review** — is a questionnaire, SOC 2, or committee
  standard for this buyer even at pilot scale? Find evidence of how these
  buyers actually onboard vendors.
- **Behavior change** — who has to work differently, and how much training that
  takes.
- **Perceived switching risk** — what breaks for the buyer if the tool is wrong
  or the vendor disappears.

The strongest wedges are adjacent, additive, and reversible before they become
systems of record. Say plainly where this one sits on that spectrum.
