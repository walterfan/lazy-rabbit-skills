# Harness Model Summary

Use this as lightweight conceptual background when the scoring rubric alone is not enough.

## Core Idea

A coding agent's reliability depends on the model plus the harness around it. The harness is the project's guidance, tools, checks, permissions, feedback loops, and maintenance process.

## Feedforward and Feedback

- **Feedforward** tells the agent how to work before it edits: `AGENTS.md`, project maps, architecture rules, workflow docs, task templates, security rules, and examples.
- **Feedback** tells the agent whether its work is acceptable after it edits: tests, lint, typecheck, CI, hooks, architecture checks, review gates, and acceptance tests.

Strong harnesses need both. Guidance without checks becomes policy wallpaper; checks without guidance create repeated avoidable mistakes.

## Deterministic First, Judgment Second

Prefer cheap deterministic checks for facts machines can verify: tests, linters, type checkers, static analysis, dependency scans, secret scans, schema validation, and architecture boundary tests.

Use LLM or human review for semantic judgment: whether the implementation solves the real problem, whether tests are meaningful, whether design is overcomplicated, and whether product behavior is acceptable.

## Three Harness Layers

- **Maintainability harness**: formatting, lint, complexity, dependency health, test coverage, dead code, and style consistency.
- **Architecture fitness harness**: module boundaries, allowed dependencies, API contracts, performance budgets, observability expectations, and security invariants.
- **Behavior harness**: user-visible flows, approved fixtures, golden examples, E2E tests, acceptance criteria, QA/product review, and safeguards against agents rewriting tests to match incorrect behavior.

## Agent Workbench Components

- **Agent guide**: concise root and module-level instructions.
- **Verification matrix**: real commands per stack, not generic "run tests" advice.
- **Rules**: safety and permission boundaries for destructive commands, secrets, production data, deployments, and migrations.
- **Hooks**: lightweight automated checks at session start, after edits, before risky actions, or before stopping.
- **Skills/plugins/tools**: reusable workflows and controlled external capabilities.
- **Entropy management**: scheduled freshness checks, dependency audits, documentation maintenance, and harness ownership.

## Audit Posture

Score evidence, not intent. A project earns more trust when guidance is short, executable checks are close to the agent's workflow, and the harness has an owner or cadence for staying current.
