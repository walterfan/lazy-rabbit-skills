# Acceptance Test Case Patterns

A useful acceptance case is traceable, deterministic, reproducible, and
bounded. Given-When-Then provides the behavior skeleton; metadata makes the
case operable by a QA team.

## Required case fields

- Stable ID (`ATC-001`) and descriptive title
- Requirement/risk link and priority (`P0`-`P3`)
- Test level and applicable dimension
- Preconditions, environment, and test data
- Given-When-Then steps
- Deterministic expected result and retained evidence
- Automation candidate (`yes`, `no`, or `partial`) with rationale

## Strong oracle rules

1. Turn implicit assumptions into observable assertions.
2. Use exact values when the requirement is exact.
3. Use a tolerance only when it is bounded and justified. For example,
   `4.9 <= emitted_tokens <= 5.1` is testable; `about 5` is not.
4. Define time using a controllable clock where possible; avoid sleep-based
   flakiness.
5. Assert externally meaningful behavior, not implementation details.
6. Include error semantics, side effects, and recovery where applicable.

## Risk-based coverage dimensions

Select dimensions because risk warrants them, not because a checklist demands
every category.

| Dimension | Typical questions |
| --- | --- |
| Functional | Does the primary user outcome hold? |
| Boundary/equivalence | Min, max, empty, one, duplicate, invalid class? |
| State/sequence | Are transitions and repeated operations correct? |
| Negative/error | Is rejection explicit and safe? |
| Integration | Do contracts hold across real boundaries? |
| Concurrency | Are ordering and shared state safe? |
| Recovery/resilience | Does degradation and restoration match the design? |
| Compatibility/migration | Are old clients/data and rollback safe? |
| Security/privacy | Are authorization, sensitive data, and audit behavior correct? |
| Accessibility | Can supported users complete the flow? |
| Performance/stress | Are specified budgets met under representative load? |
| Observability | Can operators identify success, failure, and recovery safely? |

Record `N/A` with rationale for non-applicable dimensions.

## Worked example

```gherkin
@ATC-003 @P0 @concurrency
Scenario: A whole-second boundary does not grant a second full quota
  Given a token bucket with rate 10 tokens/second and capacity 10
  And the bucket is full
  And time is controlled by a monotonic test clock
  When 10 requests arrive at t=999ms
  And 10 requests arrive at t=1001ms
  Then the first 10 requests are allowed
  And the second 10 requests are rejected with HTTP 429
  And the next request is allowed only after at least 100ms of refill time
```

This case rejects a fixed-window shortcut by making the continuous-refill
invariant observable.

## Anti-patterns

- Vague outcomes such as "reasonable", "fast", or "works correctly".
- Cases with no requirement/risk link or no stable ID.
- Only happy paths.
- Asserting internal method calls instead of accepted behavior.
- Real-time sleeps where a controllable clock is possible.
- A mock replacing the boundary whose behavior is being accepted.
- Expected results changed because implementation failed.
