# Virtual Architect — Knowledge Pack

Deep reference for the `virtual-architect` skill. Load when a question needs the detailed
patterns behind the SKILL.md summary.

## Influences

- **Eric Evans**, *Domain-Driven Design* (2003): strategic and tactical patterns for
  modeling complex domains — ubiquitous language, bounded context, aggregate, value
  object, entity, repository, domain service, domain event, context map, anti-corruption
  layer.
- **Robert C. Martin**, *Clean Code*, *Clean Architecture*, *The Clean Coder*: SOLID,
  separation of concerns, dependency rule, screaming architecture, TDD as craft.
- **Martin Fowler**, *Refactoring*, *PoEAA*, the "Microservices" series, martinfowler.com
  bliki: refactoring catalog, evolutionary design, integration patterns, when (and when
  not) to use microservices, YAGNI, "Tell, Don't Ask".
- **Kent Beck**, *Test-Driven Development: By Example*, *Tidy First?*: red-green-refactor,
  simple design rules, separating tidying from behavior change.
- **Vaughn Vernon**, *Implementing Domain-Driven Design*: DDD in code, integration between
  contexts, event-driven systems.
- **Sam Newman**, *Building Microservices*: when to split, how to split safely, ownership.
- **Gregor Hohpe**, *Enterprise Integration Patterns*: messaging, channels, routers,
  transformation patterns.

## SOLID

- **Single Responsibility (SRP)** — one reason to change; the reason is a stakeholder/actor.
- **Open/Closed (OCP)** — open for extension, closed for modification, via abstractions and
  polymorphism, not flags.
- **Liskov Substitution (LSP)** — subtypes usable where base types are expected, without
  surprising the caller.
- **Interface Segregation (ISP)** — many small role interfaces over one fat interface.
- **Dependency Inversion (DIP)** — high-level policy depends on abstractions it owns, not on
  low-level details.

Smallest fix for a violation: extract an interface owned by the policy, then flip the
dependency to point inward.

## Clean Architecture

Concentric layers; dependencies point inward only.

1. **Entities / domain** — pure business rules. No framework, IO, or DB.
2. **Use cases / application** — orchestrate entities; define ports for outside needs.
3. **Interface adapters** — controllers, presenters, gateways.
4. **Frameworks and drivers** — web, DB, broker, UI. Replaceable.

Tests: Can you swap framework/DB without touching entities or use cases? Does the directory
structure scream the domain, not the framework?

## Domain-Driven Design

Strategic:
- **Ubiquitous language** — one shared language between developers and domain experts; code
  uses the same words.
- **Bounded context** — a boundary within which a model is consistent; the same word may
  mean different things across boundaries.
- **Context map** — shared kernel, customer-supplier, conformist, anti-corruption layer,
  open host service, published language, separate ways.
- **Core vs supporting vs generic** — invest best effort in the core; buy/copy generic.

Tactical:
- **Entity** — identity matters across time.
- **Value object** — equality by attributes; prefer immutability.
- **Aggregate** — a cluster with one root that enforces invariants in one transaction;
  external code references only the root. The unit of consistency.
- **Repository** — returns aggregates by identity/query; hides persistence.
- **Domain service** — behavior not owned by one entity/value object.
- **Domain event** — a named fact that something important happened.
- **Anti-corruption layer** — translation layer protecting your model from another.

Moves: start from the use case in the user's words; extract nouns/verbs; cluster nouns into
aggregates/value objects; verbs become methods or domain events; draw invariants first;
avoid anaemic models.

## Test-Driven Development

Cycle: **Red** (smallest failing test for the next behavior) → **Green** (smallest code to
pass) → **Refactor** (improve names/structure on green).

Heuristics: one assertion per test where possible; name tests by behavior; outside-in for
features, inside-out for tricky algorithms; triangulate; refactor only on green — if a
refactor goes red, revert and take a smaller step.

Beck's four rules of simple design (in order): passes the tests; reveals intent; no
duplication; fewest elements.

## Refactoring

Small, behavior-preserving change under a green test bar. Named moves:
Extract/Inline Function, Rename, Move Function/Field, Extract/Inline Class, Replace
Conditional with Polymorphism, Replace Magic Number with Symbolic Constant, Introduce
Parameter Object, Replace Temp with Query, Decompose Conditional, Replace Loop with
Pipeline, Replace Type Code with Subclasses/Strategy, Encapsulate Variable/Field, Hide
Delegate / Remove Middle Man, Pull Up / Push Down Method.

Smells: long function, large class, long parameter list; feature envy, inappropriate
intimacy, message chains; primitive obsession, data clumps, repeated switches; shotgun
surgery, divergent change; comments that excuse bad code.

## Evolutionary Architecture

- Prefer reversible decisions; note one-way doors.
- Use **fitness functions**: automated checks that an architectural property still holds
  (dependency direction, response-time budget, max coupling).
- Prefer the **strangler fig** pattern over rewrites.
- Defer commitments. YAGNI. Avoid speculative generality.

## When NOT to Microservice

- Microservices trade intra-process complexity for distributed-systems complexity.
- Preconditions: rapid provisioning, monitoring, rapid deployment, devops culture, mature
  CI/CD.
- Default to a well-modularized monolith. Extract a service only with a clear bounded
  context, an independent change rate, an operational reason (scaling/fault isolation), and
  team capability to operate it.
- Service boundaries follow domain boundaries, not the org chart.

## Metrics-Driven Design

Every important decision is backed by a measurement that would tell us if it was wrong.
Define: the decision; the bet; the metric (p95 latency, deployment lead time, change
failure rate, defect escape rate, code churn, coupling); the unit and threshold; the review
cadence; the trigger to revisit.

Sources: DORA (deploy frequency, lead time, change failure rate, MTTR); code-level
(complexity, coupling, churn, hotspots); quality (defect density, escaped defects, coverage
on changed lines); runtime (latency percentiles, error rate, saturation, cost per
transaction); product (activation, retention, conversion).

Anti-patterns: vanity metrics (LOC, tickets closed, "AI productivity"); single-number
dashboards that hide tail regressions; metrics no one will act on.

## Architectural Decision Records (ADRs)

Short, version-controlled, one per decision. Fields: Title; Status (proposed/accepted/
superseded); Context; Decision; Consequences (positive/negative/neutral); Alternatives
considered; the MDD signal that would force a revisit. Keep it short.

## C4 Model (Simon Brown)

Four zoom levels: **Context** (system + users + external systems); **Container** (deployable
units); **Component** (major pieces inside a container); **Code** (class diagrams, only when
needed). Most teams need only the first three.

## Hexagonal / Ports and Adapters

The application defines **ports** (interfaces) it needs; **adapters** implement them for
specific technologies (HTTP, DB, queue, CLI). Drives testability — swap adapters for
in-memory ones in tests. Aligns with Clean Architecture and DDD.

## CQRS and Event Sourcing — Use With Care

- **CQRS** separates the write model from the read model; useful when workloads diverge
  sharply.
- **Event sourcing** stores domain events as the system of record; powerful but expensive in
  operational complexity, schema evolution, and cognitive load.
- Default: do not introduce them without a concrete business reason and a team that will
  operate them. Often a relational store plus a transactional outbox is better.

## Working With Legacy

- Characterization tests first — pin existing behavior before changing it (Michael Feathers).
- Find seams — places to change behavior without editing in place.
- Strangler fig — front the legacy with a façade, route capability by capability to the new
  implementation, retire legacy when its traffic hits zero.
- Branch by abstraction — for in-process component replacement.

## Code Review Checklist (Architecture-First)

1. Does the change respect the dependency direction?
2. Is the bounded context clear and the language consistent with the model?
3. Are invariants enforced in the aggregate root?
4. Is there a test that would fail if this change broke behavior?
5. Are abstractions justified by current need, not speculation?
6. Are names accurate and aligned with the ubiquitous language?
7. Will this change make the next change easier or harder?
8. Style and formatting last.

## POSA — Pattern-Oriented Software Architecture (Buschmann, Meunier, Rohnert, Sommerlad, Stal; Schmidt, Stal, Rohnert, Buschmann; Kircher, Jain)

POSA is a five-volume *pattern language*: patterns are meant to be composed, not picked in
isolation. Match the pattern to the force it resolves; name the pattern so the team shares
vocabulary.

Volume 1 — architectural and design patterns:
- **Layers** — organize by level of abstraction; higher layers depend on lower. The basis
  of Clean Architecture's dependency rule.
- **Pipes and Filters** — process a stream through independent transformation stages; good
  for data pipelines and composability.
- **Broker** — decouple clients from servers via an intermediary that routes requests;
  underpins RPC, message brokers, and service meshes.
- **Model-View-Controller / Presentation-Abstraction-Control** — separate UI from domain.
- **Microkernel** — a minimal core plus plug-in components; good for platforms and
  extensible products.
- **Reflection** — a meta level that makes structure changeable at runtime; powerful but
  costly in complexity.

Volume 2 — concurrency and networked objects:
- **Reactor** — demultiplex and dispatch events synchronously to handlers (single-threaded
  event loop; e.g. Netty, Node.js core).
- **Proactor** — dispatch on *completion* of async operations (async I/O).
- **Acceptor-Connector** — decouple connection establishment from service processing.
- **Active Object** — decouple method invocation from execution using a scheduler and its
  own thread.
- **Monitor Object** — synchronize concurrent method access to an object.
- **Half-Sync/Half-Async** and **Leader/Followers** — structure thread pools and I/O so
  synchronous processing and asynchronous I/O coexist without lock contention.

Volumes 3-5 — resource management, distributed computing, and pattern-language guidance.
Use POSA names when discussing concurrency, networking, and distribution so trade-offs are
explicit (e.g. "prefer a Reactor over thread-per-connection at this connection count").

## DDIA — Designing Data-Intensive Applications (Martin Kleppmann)

Three properties to design for: **reliability** (works correctly under faults),
**scalability** (handles load growth), **maintainability** (easy to operate, evolve, and
reason about).

- **Data models & storage** — relational vs document vs graph; log-structured (LSM-tree)
  vs update-in-place (B-tree) storage engines and their write/read/space trade-offs.
- **Replication** — single-leader (simple, read-scaling, failover lag), multi-leader
  (write-anywhere, conflict resolution needed), leaderless/quorum (Dynamo-style; R + W > N
  for read-your-writes). Watch replication lag and its consistency consequences.
- **Partitioning (sharding)** — by key range vs by hash; hot spots; secondary-index
  partitioning (local vs global); rebalancing without downtime; request routing.
- **Transactions** — ACID is not one thing. Isolation levels: read committed → snapshot
  isolation (MVCC) → serializable. Know the anomalies each prevents (dirty reads,
  non-repeatable reads, phantoms, write skew, lost updates).
- **Distributed trouble** — unreliable networks, unreliable clocks, partial failure; why
  "detecting failure" is hard; fencing tokens to guard against stale leaders.
- **Consistency & consensus** — linearizability (single up-to-date copy) vs causal
  consistency vs eventual; total-order broadcast; consensus (Raft/Paxos/ZAB) and its cost;
  CAP is a narrow theorem — reason with PACELC (latency vs consistency even without
  partitions).
- **Batch & stream** — the log as the unifying abstraction; change data capture; event
  sourcing; exactly-once as an effect of idempotence + dedup, not magic; the batch/stream
  duality.

Design heuristics: pick the *weakest* consistency model that still meets the invariant;
make the failure mode explicit before choosing a datastore; measure the property you are
betting on (replication lag, p99 under partition, rebalance time) rather than assuming it.
