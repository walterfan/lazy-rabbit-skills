# CEVF Examples by Domain

Real-world examples showing how CEVF applies across different domains — not just coding.

---

## Example 1: Incident Report Writer (Ops Domain)

### Contract
```markdown
- scope_in: Slack threads, PagerDuty alerts, or free-text incident descriptions
- scope_out: Security incidents (redirect to security-incident skill), planned maintenance
- Preconditions: At least one data source provided (alert, thread, or description)
- Postconditions: Report has all 5 required sections; timeline has >= 3 entries; action items have owners
```

### Execution
```markdown
Phase A: Extract facts
- Entry: user has provided incident data
- Steps: identify service, impact, timeline events, root cause indicators
- Exit: structured fact set with no contradictions
- On fail: list contradictions, ask user to clarify

Phase B: Draft report
- Entry: Phase A complete
- Steps: fill incident template, assign severity, draft action items
- Exit: all 5 sections populated
- On fail: mark incomplete sections with [NEEDS INFO], deliver partial

Phase C: Review
- Entry: Phase B complete
- Steps: check tone (blameless), verify timeline order, ensure action items are actionable
- Exit: report ready for delivery
- On fail: fix tone issues automatically, flag non-actionable items
```

### Verification
```markdown
Hard gates:
- All 5 sections present (Impact, Root Cause, Timeline, Resolution, Action Items)
- Timeline has >= 3 chronological entries
- Every action item has an owner

Soft gates:
- Report under 800 words
- No blame language ("failed to", "should have")
```

### Feedback
```markdown
Failure modes:
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Timeline is just 1 entry | Input lacks time data | Ask user for key timestamps |
| Action items are vague | "Improve monitoring" | Require specific tool + metric + owner |
| Report too long | Retelling the whole Slack thread | Summarize, don't transcribe |

Boundary examples:
- Minimal: single-sentence "API was down for 2 hours" → still produces full template with [NEEDS INFO] markers
- Edge: incident spanning multiple services → produce one report per service or combined with clear separation
```

---

## Example 2: Press Release Drafter (Marketing/Writing Domain)

### Contract
```markdown
- scope_in: Product launches, partnerships, company milestones, executive announcements
- scope_out: Internal memos, crisis communications (redirect to crisis-comms skill), social media posts
- Preconditions: User has provided the key news (what happened, who's involved, why it matters)
- Postconditions: 300-500 words, AP style, includes headline + subhead + 3-5 paragraphs + boilerplate + contact info placeholder
```

### Execution
```markdown
Phase A: Extract the news
- Entry: user has described what to announce
- Steps: identify the WHO, WHAT, WHEN, WHERE, WHY
- Exit: all 5 Ws answered
- On fail: ask user for missing Ws — don't guess

Phase B: Draft
- Entry: Phase A complete
- Steps:
  1. Write headline (max 10 words, active voice)
  2. Write lead paragraph (who + what + when)
  3. Write supporting paragraphs (why it matters, quotes, details)
  4. Add boilerplate and contact placeholder
- Exit: complete draft with all sections
- On fail: deliver with [QUOTE NEEDED] or [DETAIL NEEDED] markers

Phase C: Polish
- Entry: Phase B complete
- Steps: AP style check, remove jargon, verify word count
- Exit: 300-500 words, clean prose
- On fail: trim or expand to hit target, flag forced changes
```

### Verification
```markdown
Hard gates:
- Word count 300-500
- Has headline, at least 3 body paragraphs, boilerplate section
- No first person ("we are excited" → "Company X announced")

Soft gates:
- Flesch reading ease > 50
- No sentences over 30 words
```

### Feedback
```markdown
Failure modes:
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Reads like a blog post | Tone not formal enough | Reinforce AP style in Phase C |
| Too much jargon | Domain terms not translated | Add "translate for general audience" step |
| Missing quote | No spokesperson identified | Ask user for quotable source |

Improvement triggers:
- If editors consistently rewrite the lead → study their preferred lead structure
- If word count is always trimmed → lower the default upper bound
```

---

## Example 3: Data Pipeline Validator (Data Domain)

### Contract
```markdown
- scope_in: SQL queries, dbt models, Airflow DAGs, data quality check definitions
- scope_out: Application code that happens to query a database, BI dashboard configs
- Preconditions: At least one pipeline definition file provided
- Postconditions: Validation report with pass/fail per check, 0 critical issues for PASS verdict
```

### Execution
```markdown
Phase A: Parse pipeline
- Entry: file matches scope_in
- Steps: identify sources, transformations, sinks, dependencies
- Exit: dependency graph extracted
- On fail: report unparseable sections, continue with parseable parts

Phase B: Run checks
- Entry: Phase A complete
- Steps:
  1. Schema consistency: column types match across joins
  2. Null handling: nullable columns handled explicitly
  3. Dedup logic: no unintentional row multiplication
  4. Freshness: SLA-relevant timestamps referenced
- Exit: check results for each rule
- On fail per check: log as finding, continue other checks

Phase C: Generate report
- Entry: Phase B complete
- Steps: aggregate findings, assign severity, determine overall verdict
- Exit: structured report with PASS/WARN/FAIL verdict
- On fail: deliver partial report noting which checks couldn't run
```

### Verification
```markdown
Hard gates:
- Every check has a severity (critical/warning/info)
- Overall verdict logic: FAIL if any critical, WARN if any warning, PASS otherwise
- Report includes file path and line number for each finding

Soft gates:
- Finding descriptions under 100 words each
- Report under 50 findings (consolidate if more)
```

### Feedback
```markdown
Failure modes:
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| False positive on CTEs | Parser treats CTE as separate query | Track CTE scope in Phase A |
| Misses implicit joins | Only checks explicit JOIN | Add comma-join detection |
| Too many info findings | Threshold too sensitive | Raise info threshold or suppress |

Boundary examples:
- Minimal: single SELECT query → 1-3 findings or clean verdict
- Edge: 50-table DAG → sample top 20 by dependency depth
- Out of scope: Python script with embedded SQL → refuse, suggest code-review skill
```

---

## Example 4: Customer Support Response (Support Domain)

### Contract
```markdown
- scope_in: Customer tickets, chat messages, email complaints about product issues
- scope_out: Internal escalation emails, feature requests (redirect to feature-triage skill), billing disputes (redirect to billing skill)
- Preconditions: Customer message provided; product knowledge base accessible
- Postconditions: Response is empathetic, addresses the specific issue, includes next steps, under 200 words
```

### Execution
```markdown
Phase A: Understand the issue
- Entry: customer message provided
- Steps:
  1. Classify issue type (bug, how-to, account, other)
  2. Identify customer emotion (frustrated, confused, neutral)
  3. Extract specific product/feature mentioned
- Exit: issue classified with confidence
- On fail: if ambiguous, draft clarifying question instead of guessing

Phase B: Draft response
- Entry: Phase A complete
- Steps:
  1. Open with empathy matching emotion level
  2. Address the specific issue with solution or workaround
  3. Provide clear next steps
  4. Close with offer to help further
- Exit: complete response draft
- On fail: if no solution found, acknowledge and escalate transparently

Phase C: Tone check
- Entry: Phase B complete
- Steps: verify empathetic but not condescending, specific but not jargon-heavy
- Exit: response ready
- On fail: rewrite flagged sentences
```

### Verification
```markdown
Hard gates:
- Response under 200 words
- Contains at least one specific next step
- Does not blame the customer ("you should have", "you need to")

Soft gates:
- Opens with acknowledgment of the issue
- Closes with offer for further help
```

### Feedback
```markdown
Failure modes:
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Response is generic | Issue classification too broad | Add sub-categories |
| Tone is robotic | Template too rigid | Allow more natural phrasing in Phase B |
| Wrong solution suggested | Knowledge base outdated | Add "verify solution is current" step |

Improvement triggers:
- Customer replies "that didn't help" > 20% of the time → review solution accuracy
- Response length consistently trimmed by agents → lower word target
```
