# Interview Question Bank

Question seeds by domain, hint templates, scoring rubric, and behavioral prompts. **Adapt
every question to the actual JD and resume** — these are starting points, not a script. Ask
one at a time and follow the candidate's answers with "why" and "trade-off" probes.

Difficulty tags: `[J]` junior, `[M]` mid, `[S]` senior/staff.

---

## General technical (any domain)

- `[J]` Walk me through a project on your resume you're most proud of. What was your part?
- `[J]` What was the hardest bug you've debugged? How did you find the root cause?
- `[M]` Tell me about a technical decision you later regretted. What would you do differently?
- `[M]` How do you decide when code is "done"? What's your bar for tests and review?
- `[S]` Describe a system you designed end-to-end. What were the key trade-offs?
- `[S]` Where have you traded correctness or quality for speed, and how did you manage the risk?

---

## Backend / services

- `[J]` REST vs RPC — when would you pick each? What does idempotency mean for an API?
- `[J]` Explain the difference between a process and a thread; when is each appropriate?
- `[M]` How do you make an operation safe under retries? (idempotency keys, dedup, exactly-once)
- `[M]` SQL vs NoSQL for a given workload — how do you choose? Give a concrete example.
- `[M]` Explain database transactions and isolation levels. Where have you hit a race?
- `[S]` Design a rate limiter for a distributed API. Token bucket vs sliding window trade-offs?
- `[S]` How would you handle a hot partition / thundering herd on a shared datastore?
- `[S]` Explain eventual consistency and how you'd expose it safely to clients.

### Language spot-checks
- **Java** `[M]`: hashCode/equals contract; `[S]`: memory model, `volatile`, GC tuning basics.
- **Go** `[M]`: goroutine leaks and how to prevent them; `[S]`: context cancellation, channels vs mutex.
- **Python** `[M]`: GIL implications for concurrency; `[S]`: async vs threads vs processes.
- **Node** `[M]`: event loop and blocking the loop; `[S]`: backpressure in streams.

---

## Frontend / web

- `[J]` Explain the box model / flexbox vs grid. When do you reach for each?
- `[J]` What is the virtual DOM and why does a framework use it?
- `[M]` How do you manage state in a large app? Local vs global vs server state.
- `[M]` Explain reflow/repaint and three ways to keep rendering fast.
- `[M]` How do you prevent XSS in a modern SPA? Where does sanitization belong?
- `[S]` Design a component library API. How do you balance flexibility vs consistency?
- `[S]` How would you cut Time-to-Interactive on a slow page? Measure first — what metrics?

---

## Mobile (iOS / Android)

- `[J]` Explain the app lifecycle. Where do you save/restore state?
- `[M]` How do you keep the main/UI thread free? Background work patterns you've used.
- `[M]` How do you handle offline-first sync and conflict resolution?
- `[S]` How would you diagnose and fix a memory leak / retain cycle in production?

---

## Data engineering / ML

- `[J]` Batch vs streaming — when would you choose each?
- `[M]` Explain a data pipeline you built: sources, transforms, sinks, and how you handled bad data.
- `[M]` What is data partitioning and why does it matter for query performance/cost?
- `[S]` `[ML]` How do you prevent train/serve skew and detect model drift in production?
- `[S]` Design an idempotent, backfillable ETL job. How do you handle late-arriving data?

---

## Infra / SRE / DevOps

- `[J]` What's the difference between availability and reliability? What is an SLO?
- `[M]` Walk me through what happens from `git push` to running in production.
- `[M]` How do you design a health check and a rollback strategy for a deploy?
- `[S]` A service's p99 latency tripled with no code change — how do you investigate?
- `[S]` Design an alerting strategy that pages on symptoms, not causes. Avoid alert fatigue how?

---

## Security

- `[J]` Explain the difference between authentication and authorization.
- `[M]` How do you store passwords? What's wrong with a fast hash?
- `[M]` Name the top injection risks for your stack and how you defend against each.
- `[S]` Design secrets management for a fleet of services. Rotation, blast radius, audit.
- `[S]` Threat-model a new public endpoint. What are the abuse cases?

---

## System design prompts (mid+)

Give an open prompt, then drive requirements → high-level design → deep-dive → trade-offs →
failure modes. Score the *process*, not a single "correct" answer.

- Design a URL shortener. (keys, redirects, analytics, scale)
- Design a news feed / timeline. (fan-out on read vs write)
- Design a chat system. (delivery guarantees, ordering, presence)
- Design a rate limiter / API gateway.
- Design a file/object storage upload+CDN path.
- Design a job scheduler with retries and idempotency.

Look for: clarifying questions first, explicit assumptions, capacity estimates, clear
data model, identification of bottlenecks, and honest discussion of trade-offs.

---

## Behavioral (STAR)

Ask for a specific story, then probe Situation / Task / Action / Result.

- Tell me about a time you disagreed with a teammate on a technical approach.
- Tell me about a time you shipped something that broke in production. What did you learn?
- Tell me about a time you had to deliver under an unrealistic deadline.
- Tell me about mentoring someone or raising the bar on your team.
- Tell me about the most ambiguous problem you've owned. How did you make progress?

Signals: ownership vs blame, concrete actions (not "we"), measurable result, reflection.

---

## Hint templates (Hint Ladder)

1. **Nudge** — "Let me rephrase: I'm asking specifically about X, not Y."
2. **Direction** — "Think about what happens under concurrency / at 100x scale / on failure."
3. **Partial** — "One approach uses an idempotency key. What would you store, and where?"
4. **Walkthrough** — Explain the concept, then: "Given that, how would you apply it here?"

Record the highest hint level used per competency; more help → lower score.

---

## Scoring rubric (per competency, relative to seniority bar)

| Score | Behavior observed |
|-------|-------------------|
| 5 | Correct, deep, well-structured; anticipates trade-offs and edge cases unprompted |
| 4 | Correct and solid; minor gaps; reasons well with light probing |
| 3 | Meets the role's bar; correct core with some hints; limited depth |
| 2 | Notable gaps; needed heavy hinting; shaky fundamentals |
| 1 | Could not demonstrate the competency even with walkthrough-level hints |

Weight must-have JD skills higher than nice-to-haves when computing the overall recommendation.

---

## SWOT analysis guide (candidate vs role)

Build the SWOT in Phase 4 from the competency scores + resume-vs-JD gap map. Two axes:
**internal vs external** and **positive vs negative**. Every item must be evidence-backed
(a quoted answer, a resume fact, or a JD requirement).

| | Positive (+) | Negative (−) |
|---|---|---|
| **Internal** (is/has today) | **Strengths** | **Weaknesses** |
| **External** (could happen next) | **Opportunities** | **Threats** |

- **Strengths** — competencies scored 4–5; demonstrated depth, ownership, standout projects,
  skills that exceed the JD. Source: high-scoring answers + strong resume facts.
- **Weaknesses** — must-have competencies scored 1–2; shallow areas needing heavy hints;
  missing required hands-on experience. Source: low-scoring answers + JD gaps.
- **Opportunities** — coachable gaps, transferable adjacent skills, growth runway, fast
  onboarding paths, or a strong learning signal ("I don't know, but here's how I'd find out").
- **Threats** — hiring risks: a critical must-have gap, long ramp-up, level mismatch,
  retention/flight risk, or resume claims that collapsed under probing and need verification.

Common mistakes to avoid:
- Putting the same fact verbatim in two quadrants (reframe it if it belongs in both).
- Writing generic HR-speak ("good communicator") with no evidence — cite the moment.
- Confusing internal with external — a *skill they have* is a Strength; a *chance to grow into
  the role* is an Opportunity.

Example (Senior Backend, Go):
- **S**: Deep idempotency/retry reasoning on a real payment service (answer scored 5).
- **W**: Couldn't design a distributed rate limiter; Postgres scaling was shallow (scored 2).
- **O**: Strong fundamentals + eager learner → likely closes the distributed-systems gap in a
  quarter with mentoring.
- **T**: "high-throughput" is a must-have and remained unproven; risk of under-leveling if the
  role needs it on day one.

---

## Red flags & positive signals

**Red flags**
- Memorized buzzwords with no depth when probed ("I used Kafka" → can't explain why).
- Blames others in every behavioral story; no ownership.
- Resume claims collapse under one follow-up ("led" → actually observed).
- Confidently wrong and unwilling to reconsider when given evidence.

**Positive signals**
- Asks clarifying questions before answering.
- States assumptions and trade-offs explicitly.
- Says "I don't know, but here's how I'd find out."
- Reflects on past mistakes with concrete lessons.
