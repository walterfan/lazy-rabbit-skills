# Implementation Handoff: Approved Acceptance Baseline

Implement `<module or change>` against the human-approved QA baseline below.
Treat case IDs and expected outcomes as immutable unless the requirement owner
approves a documented baseline revision.

## Project facts

- Read repository guidance, architecture docs, build configuration, CI, tests,
  fixtures, and safety rules that actually exist.
- Discover commands from project files. Report missing commands or rules; do
  not invent them.

## Approved design and acceptance baseline

- **HLD / design version:** <path or version>
- **Test plan version:** <path or version>
- **Approved ATCs:** <paste or link ATC IDs and Given-When-Then cases>
- **Open approved waivers:** <none or list with owner/expiry>

## Workflow

1. Report the project facts, target files, real verification entrypoint, and
   unresolved gaps before editing.
2. Map each ATC to the test level that will provide evidence.
3. Add or update tests before implementation where practical; preserve approved
   oracles, fixtures, and golden files.
4. Implement the smallest change that satisfies the baseline and architecture.
5. Run Maintainability, Architecture Fitness, and Behavior gates through the
   project's real entrypoint.
6. Report command, target, environment, results, unrun checks, and residual risk.
7. If an ATC cannot be satisfied, stop and explain the conflict. Do not weaken
   the ATC or disguise a real boundary with a mock.

## Safety boundary

Do not access secrets or production data, deploy, migrate, delete, or perform
destructive Git operations without explicit human approval.
