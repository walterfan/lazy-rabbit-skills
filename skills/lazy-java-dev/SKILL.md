---
name: lazy-java-dev
description: >-
  Use when working in a Java backend repo that uses or should use Spring
  Boot services, MyBatis XML mappers, Spring Security, secret-manager-style
  secret handling, privacy-safe logging, and layered controller/service/repository
  design; when the task is to implement, refactor, review, explain, or test
  Java code involving APIs, database access, integrations, scheduled jobs,
  thread pools, or internal common libraries. Make sure to use this skill
  whenever the user mentions Java services, Spring Boot, MyBatis, secrets manager, secure
  logging, integration clients, or Java code review in this style of repo.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - java
  - spring-boot
  - mybatis
  - secrets-management
  - spring-security
  - api
  - security
  - logging
  - pkb
category: dev-tools
use_cases:
  - "implement a Spring Boot service or controller change with tests"
  - "review a Java diff for security, transaction, logging, and API risks"
  - "write MyBatis-safe Java code in a service repo"
  - "explain how this Java service code works across controller, service, and mapper layers"
platforms: [claude-code, cursor, codex]
visibility: public
---

# lazy-java-dev

Practical **Java service development**: follow Spring Boot layering,
prefer MyBatis XML mappers, validate early, keep secrets out of logs, and
verify with repo-native build and test commands before claiming done.

**Progressive detail:** [references/java-service-stack.md](references/java-service-stack.md)
(Spring Boot, MyBatis, integration, internal libs),
[references/java-security-and-logging.md](references/java-security-and-logging.md)
(authorization, secrets manager, privacy-safe logging, secure coding), and
[references/java-testing-and-review.md](references/java-testing-and-review.md)
(pitfalls, review order, testing defaults) only when the task needs that depth.

## When to use

- Java repo mentions Spring Boot, MyBatis, `pom.xml`, Gradle, Spring Security,
  secrets manager, controllers, services, mappers, scheduled jobs, or internal Java
  common libraries
- User wants to implement, fix, refactor, explain, test, or review Java while
  preserving layered architecture and minimum diff
- Repo looks like a backend service where security, logging, and
  authorization correctness matter more than style alone
- Project has `AGENTS.md`, PKB docs, `man/`, or repo conventions that should
  guide the change

## When not to use

- Non-Java primary work
- Generic Java desktop/library work with no Spring Boot or service context
- Main task is deployment, Jira/GitLab workflow, or product-process work rather
  than code
- User explicitly wants to migrate away from the repo's Spring Boot/MyBatis
  stack and is asking for architecture planning instead of scoped code work

## Contract

- **scope_in**: Java backend code and config in repos that use or
  should use Spring Boot layering, MyBatis XML mappers, Spring Security,
  Bean Validation, secret-manager-style secret handling, privacy-safe logging, internal
  integration libraries, thread pools, scheduled jobs, external service calls,
  unit tests, code review, and code explanation; reading `AGENTS.md` or `man/`
  conventions when present
- **scope_out**: Non-Java primary work; broad architecture migrations unless the
  user explicitly asks; replacing MyBatis with JPA or another ORM by default;
  infra-only changes; product-specific runbooks and release workflows
- **Preconditions**: Repo, diff, or snippet is available; Java version, build
  tool, and repo commands are read from `pom.xml`, Gradle files, or CI instead
  of assumed; mapper/XML layout and security/logging conventions are discovered
  before inventing new ones
- **Postconditions**: Recommendations follow Spring Boot service layering,
  validate inputs early, keep SQL parameterized, keep secrets and L3-L5 data
  out of logs, keep errors explicit, avoid speculative framework/library swaps,
  and state exactly what verification did and did not run

## Execution

### Phase 0: Detect context

- **Entry**: User asks to implement, fix, review, explain, or test Java
- **Steps**:
  1. Read `pom.xml`, `build.gradle*`, Maven wrapper, Gradle wrapper, `Makefile`,
     `justfile`, or CI config to detect Java version, build tool, and test/lint
     commands
  2. If `AGENTS.md`, `man/`, or repo conventions exist, skim them for danger
     zones, API stability, security, and verification expectations
  3. Identify the active stack: Spring MVC/WebFlux style, MyBatis mapper
     layout, security annotations, logging conventions, integration libraries,
     and whether async jobs or thread pools are in play
- **Exit**: Tooling path and project conventions are grounded in repo evidence
- **On fail**: Name the missing file or gap and continue from generic Java
  service defaults, clearly labeled as fallback guidance

### Phase 1: Classify the task

- **Entry**: Phase 0 complete
- **Steps**:
  1. Pick one primary mode:
     - **Implement**: write or modify Java code or mapper XML
     - **Review**: assess a diff/file/snippet for correctness, risk, and tests
     - **Test**: add or improve unit tests
     - **Explain**: describe code structure, flow, dependencies, and tradeoffs
     - **Tooling**: adjust Maven/Gradle, validation, test, or logging setup
  2. Keep the task in one mode unless the user clearly asked for both code and
     review
- **Exit**: One primary mode is chosen
- **On fail**: Ask one short question combining scope and mode, for example:
  `Do you want me to implement the Java change, review the diff, or write tests for it?`

### Phase 2: Apply Java defaults

- **Entry**: Phase 1 complete
- **Steps**:
  1. **Core Java shape**
     - Follow repo naming conventions, including project-specific interface and
       DTO/VO/DO patterns when already present
     - Keep classes focused and layer boundaries clear: controller ->
       service -> repository/mapper -> integration client
     - Use constructor injection over field injection
     - Document public classes and methods when adding new surface area
  2. **Implement**
     - Prefer small, reviewable diffs over speculative cleanup
     - Validate input at controller and service boundaries with Bean Validation
       and explicit business-rule checks
     - Keep DTOs separate from entities; do not return raw entities from APIs
  3. **Test**
     - Prefer focused tests near the changed layer: controller tests for request
       validation and response mapping, service tests for business logic and
       transactions, mapper or integration tests when XML, query shape, or
       serialization changed
     - Mock or stub external clients at the service boundary unless the repo
       already uses a heavier integration-test harness
     - Cover validation failures, authorization failures, dependency errors, and
       not-found or conflict branches, not just the happy path
  4. **Tooling**
     - Keep the repo's existing Maven or Gradle path; prefer wrapper commands
       and existing plugins over inventing a new build flow
     - Do not add Spring modules, persistence frameworks, or internal libraries
       speculatively when the repo already has a standard way to do the work
     - Preserve existing checkstyle, static-analysis, and packaging conventions
       unless the user explicitly asked to change them
  5. **Explain**
     - Use the repo's own controller/service/mapper/integration files before
       defaulting to generic Spring advice
     - Explain layer boundaries, data flow, exception mapping, authorization,
       and logging assumptions explicitly
     - State assumptions when exact build, framework, or XML context is missing
  6. **Spring Boot / service layer**
     - Keep transaction boundaries at the service layer
     - Use `@ConfigurationProperties` for grouped config and externalize values
     - Use custom exceptions instead of generic `Exception`
     - Do not rely on private `@Transactional` methods because proxying will not
       apply
  7. **Database / MyBatis**
     - Keep SQL in XML mappers when the repo follows that convention
     - Use `#{}` for parameter binding; never use `${}` with user input
     - Avoid `SELECT *`, use pagination for large lists, and watch for N+1
       access patterns
     - Keep transactions short and focused; use read-only transactions where
       applicable
  8. **Security / authorization**
     - Enforce authorization with Spring Security and repo-standard annotations
       such as `@PreAuthorize`
     - Validate path/query/body input, sort fields, page size, regex, redirects,
       and file uploads
     - Use a secrets manager or repo-standard secret loading instead of hardcoded secrets
  9. **Logging / privacy**
     - Never use `System.out.println`, `printStackTrace`, or string
       concatenation in logs
     - Keep L4-L5 data, secrets, tokens, and sensitive PII out of logs and
       exception messages
     - Follow placeholder conventions and sensitivity annotations when the repo
       uses the logging-extension SDK
  10. **Integrations / async**
     - Set timeouts, retries, and circuit-breaker style protections for external
       calls
     - Prefer repo-standard HTTP/invoker libraries and response wrappers over ad
       hoc clients
     - Propagate request or tracking context through async boundaries when the
       repo already does so
     - Use explicit thread pools, named executors, and safe shutdown/exception
       handling for async work and scheduled jobs
  11. **Review**
     - Lead with behavioral bugs, auth gaps, injection risk, transaction
       mistakes, privacy-logging issues, async hazards, and missing tests before
       style nits
     - Use [java-testing-and-review.md](references/java-testing-and-review.md)
       as the semantic checklist when code touches APIs, mappers, logging,
       external calls, concurrency, or entities
- **Exit**: Code or review notes align with the repo's Java stack and standard
  service conventions
- **On fail**: If the repo clearly uses a different Java stack, follow the repo
  and call out where this skill's defaults were intentionally overridden

### Phase 3: Test and verify

- **Entry**: Code change exists or the user asked for test/review guidance
- **Steps**:
  1. Prefer repo commands first: `./mvnw test`, `mvn test`, `./gradlew test`,
     `spotbugs`, `checkstyle`, `just test`, or project wrappers
  2. For targeted behavior changes, run nearby module/package tests before the
     whole tree when that materially speeds feedback
  3. If mapper XML, serialization, auth, or integration behavior changed,
     prefer targeted tests that exercise those boundaries instead of only pure
     unit tests
  4. If only a review was requested, still state which checks would materially
     reduce risk
- **Exit**: Verification section states exactly which commands ran, what passed
  or failed, and what was not run
- **On fail**: Report failures or environment gaps plainly; do not imply green
  status without evidence

### Phase 4: Shape the response

- **Entry**: Draft code, review findings, or guidance is ready
- **Steps**:
  1. Use this response shape for non-trivial work:
     - `summary`: what changed or what was reviewed
     - `assumptions`: missing repo context or decisions that affected the answer
     - `changes` or `findings`: file-level or risk-level substance
     - `risks`: compatibility, security, logging, performance, or test gaps
     - `verification`: what actually ran
     - `next_step`: only if there is a clear follow-up
  2. For review tasks, present findings first, ordered by severity
  3. For explain tasks, cover purpose, layers, dependencies, error flow,
     security, and integration behavior
- **Exit**: Response is evidence-first and easy to scan
- **On fail**: Fall back to a shorter response, but still state assumptions and
  verification limits

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| No secrets in output | No real tokens, credentials, secret-manager values, raw JWTs, or sensitive PII in logs, code blocks, or examples | Redact and replace with placeholders |
| Safe persistence path | Mapper/query guidance uses parameter binding and avoids unsafe SQL construction | Rewrite query guidance before delivery |
| Privacy-safe logging | Output avoids `System.out`, `printStackTrace`, raw object dumping of sensitive data, and unsafe string-concatenated logs | Replace with repo-safe logging patterns |
| Authorization and validation considered | Controller/service changes validate inputs and preserve auth checks where relevant | Add the missing boundary checks or call out the gap |
| Evidence-first closeout | Verification says what actually ran | Remove unsupported `done/passing` claims |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Tests tied to change | Behavior changes mention a test file or test case | Note the coverage gap |
| Layer boundaries preserved | Controller/service/repository responsibilities stay clear | Call out the coupling risk |
| Public surface documented | New DTOs, APIs, or public classes have docs where appropriate | Suggest or add docs |
| Transaction scope sane | Multi-step mutations have a sensible transaction boundary | Note the risk |
| Review depth | Reviews cover security, behavior, and data flow before naming/style | Reorder and elevate the real risks |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Suggested JPA repositories in a MyBatis repo | Fell back to generic Spring defaults | Re-read this skill: MyBatis XML is the default when the repo uses it |
| Used `${}` in mapper guidance | Missed injection risk in dynamic SQL | Switch to `#{}` and validate any allowed dynamic fragments |
| Logged request objects containing sensitive fields | Ignored privacy-logging conventions | Use sensitivity annotations and safe placeholders instead of raw object logs |
| Used `System.out.println` or `printStackTrace` for debugging | Imported non-production Java habits | Replace with repo-standard logger usage |
| Gave vague test advice with no layer-specific checks | Task mode existed but test workflow was underspecified | Use controller/service/mapper-specific test guidance and name the missing cases |
| Claimed tests passed without running them | No evidence-first verification step | State exactly what ran and what did not |
| Review missed the real problem | Focused on naming or annotations before auth, SQL, logging, or transaction risk | Use the review checklist reference first |

### Boundary examples

- **User**: `add a Spring Boot endpoint for listing secrets` -> implement
  controller/service flow, validate params, preserve auth, and return DTOs
- **User**: `review this mapper XML` -> focus first on `#{}` vs `${}`, query
  scope, pagination, and schema or performance risk
- **User**: `write tests for this service` -> cover happy path, validation,
  mapper/service failure paths, and response translation
- **User**: `explain this Java service` -> describe controller/service/mapper or
  integration flow, exceptions, logging, and security assumptions
- **User**: `migrate this whole service from MyBatis to JPA` -> out of scope
  unless they explicitly ask for a migration plan or implementation

### Improvement triggers

- Java repos increasingly standardize on a different persistence or HTTP
  client stack -> refresh the default references and frontmatter description
- Users repeatedly ask for deeper Maven/Gradle or test-container guidance ->
  add a tooling-focused reference
- Privacy-logging or secrets-management conventions evolve -> refresh the security/logging
  reference and hard-gate wording

## Additional resources

- Spring Boot, MyBatis, integrations, and internal library defaults:
  [references/java-service-stack.md](references/java-service-stack.md)
- Authorization, secrets manager, secure coding, and privacy-safe logging:
  [references/java-security-and-logging.md](references/java-security-and-logging.md)
- Testing defaults, review order, and common pitfalls:
  [references/java-testing-and-review.md](references/java-testing-and-review.md)
