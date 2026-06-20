# Section-by-Section Writing Guide

Per-section guidance for filling in the microservice design document template. Each section lists what to include, common pitfalls, and tips.

---

## 1. Introduction

### 1.1.1 Business Requirements

- Start with the "why" — what business problem does this service solve?
- List user scenarios as concrete stories, not abstract statements.
- Include a PlantUML use-case diagram. Even 3-4 use cases make the scope tangible.
- Assign priorities (P0/P1/P2) to every scenario.

**Pitfall**: Listing features without explaining who benefits or why it matters.

### 1.1.2 Technical Requirements

- Quantify everything: QPS, data size, latency targets, availability SLA.
- If numbers are unknown, write **[TBD]** with a note on who will provide them.
- Cover all four dimensions: capacity, availability, security, scalability.

**Pitfall**: Vague statements like "must be fast" or "highly available" without numbers.

### 1.2 Background

- Describe the current state before jumping to the proposed design.
- Include an architecture diagram of the existing system.
- Quantify current capacity and explicitly state what is inadequate.

**Pitfall**: Skipping the "as-is" state, making it impossible to evaluate the "to-be" design.

---

## 2. Design

### 2.1 Overall Architecture

- Provide a high-level block diagram (ASCII art or PlantUML component diagram).
- Label every arrow with the protocol/transport (gRPC, HTTP, Kafka, etc.).
- List key design decisions in a table with rationale.

### 2.2 Alternatives

- Always present at least two options.
- Use a comparison table with consistent dimensions: pros, cons, cost, risk.
- State the chosen option and the deciding factor clearly.

**Pitfall**: Presenting only the chosen approach with no evidence that alternatives were considered.

### 2.3 Domain Design

- Identify bounded contexts and aggregate roots.
- Include an ER diagram (PlantUML `entity` notation or Mermaid erDiagram).
- Show the core business flow as a sequence or activity diagram.

### 2.4 Scope and Impact

- List every component touched (new, modified, deprecated).
- For each upstream/downstream service, state the impact and mitigation.

**Pitfall**: Underestimating downstream impact by ignoring contract changes.

### 2.5 Detailed Design

#### 2.5.1 API Description

- List all endpoints in a summary table first, then detail each one.
- For each endpoint: method, path, request schema, response schema, error codes.
- Use concrete JSON examples, not just type annotations.

#### 2.5.2 Logic Description

- Describe the core business logic in prose, supplemented by flowcharts.
- Highlight non-obvious edge cases and branching logic.

#### 2.5.3 Data Structures

- Provide full DDL (CREATE TABLE) for relational databases.
- Document indexes and their purpose.
- For NoSQL, show the document/key schema with access patterns.

#### 2.5.4 Limitations

- Be honest about what the design does NOT handle.

#### 2.5.5 Performance

- Identify hot paths and potential bottlenecks.
- Describe caching strategy, connection pooling, and async patterns.

#### 2.5.6 Design Constraints

- Distinguish between hard constraints (policy, regulation) and soft constraints (team preference).

#### 2.5.7 Exception Handling

- List failure scenarios in a table: scenario, impact, handling strategy.
- Cover at least: downstream timeout, database failure, message queue backpressure, and bad input.

---

## 3. Dependencies

- List every external dependency with version and purpose.
- Flag any dependency with licensing concerns.
- Note which dependencies are shared vs. owned by this team.

---

## 4. Deployment

- Configuration: provide a full table of config keys, defaults, and descriptions.
- Installation: step-by-step, copy-pasteable commands.
- Verification: a checklist the deployer can follow post-deployment.

**Pitfall**: "Deploy to K8s" with no detail on Helm values, resource limits, or health checks.

---

## 5. Metrics

- Define KPIs tied to business goals (e.g., "order completion rate" not just "request count").
- For each custom metric: name, type (counter/gauge/histogram), labels, and description.
- State the monitoring and alerting tools.
- Include alert thresholds if known.

---

## 6. Testing

- Test cases should map to the use cases in Section 1.1.1.
- API tests: describe the tool (e.g., k6, Postman) and what is validated.
- Integration/E2E: describe the test environment and how dependencies are handled (mocks, staging, etc.).
- Performance tests: specify the load profile, duration, and success criteria.

**Pitfall**: "We will test it" with no specifics.

---

## 7. Issues and Risks

- Separate known issues (things already broken) from risks (things that might go wrong).
- Rate likelihood and impact (High/Medium/Low).
- Every risk needs a mitigation plan.

---

## 8. References

- Link to related design docs, API specs, wiki pages, and external standards.
- Prefer permanent links over transient ones.
