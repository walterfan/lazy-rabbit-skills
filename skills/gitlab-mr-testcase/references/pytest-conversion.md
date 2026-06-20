# Converting Generated Cases to Pytest

This skill produces test cases as structured markdown. Each case already ships with a thin pytest skeleton so conversion stays mechanical, not creative.

## One TC → One pytest function

The mapping is intentional:

| Markdown field                | Pytest mapping                                                  |
|------------------------------|-----------------------------------------------------------------|
| `### TC-NN: <title>`         | Function name `test_<snake_title>` and docstring                |
| `Type`                       | `@pytest.mark.integration` / `acceptance` / `regression`        |
| `Priority`                   | `@pytest.mark.p0` (optional team convention)                    |
| `Preconditions / Fixtures`   | Function parameters (fixtures) and `pytest.fixture` definitions |
| `Inputs`                     | `@pytest.mark.parametrize` rows, one row per case variant       |
| `Action`                     | The single call under test inside the function body             |
| `Expected`                   | `assert` statements on the return value or HTTP response        |
| `Side-effects to verify`     | Extra `assert` statements after the action (DB, queue, log)     |
| `Out of scope / Not asserted`| Nothing — explicitly skipped in the test                        |
| `Risks if this case fails`   | Test docstring (one line)                                       |

## Minimal conversion recipe

1. Copy the skeleton block from the markdown case verbatim.
2. Rename `test_<snake_case_title>` to match your team's naming convention if needed.
3. Replace `<fixtures>` with the real pytest fixtures that exist in the target test package. If a fixture is listed under `MISSING — please confirm or create`, stop and either create it or change the case.
4. Replace the `Arrange / Act / Assert` placeholders with real call sites, importing the production code under test.
5. If `Inputs` contains multiple rows or the case includes boundary + negative variants, expand `pytest.mark.parametrize` with one `pytest.param(..., id="...")` per row. The `id` should match the human description in the markdown.
6. Implement the `Side-effects to verify` assertions last. Common patterns:
   - DB row: `assert session.query(Model).filter(...).one_or_none() is not None`
   - Outbound HTTP / SDK call: use a captured mock and assert call args.
   - Log line: a `caplog` fixture and `assert "expected substring" in caplog.text`.
   - Metric: stub the metrics client and assert the counter/histogram was incremented.

## Markers

Suggested marker set (configure once in `pyproject.toml` or `pytest.ini`):

```ini
[pytest]
markers =
    integration: integration tests that talk to real or in-process dependencies
    acceptance: stakeholder-facing acceptance tests, usually slower
    regression: tests that pin a specific past defect
    negative: tests that assert error / rejection paths
    boundary: tests that assert behavior at input limits
    p0: must-pass before merge
```

This lets you run a fast loop with `pytest -m "integration and p0"`.

## Anti-patterns

- **Asserting on private internals**: if the generated case includes `assert model._private_field == ...`, rewrite the assertion in terms of an observable surface (API response, persisted row, emitted event) or drop the assertion.
- **Generating one giant test function per TC**: each TC must remain one function. If a TC is genuinely too large, split the TC in the markdown first, then regenerate.
- **Hard-coded environment**: integration tests should pull connection details from fixtures, never inline strings.

## When the skeleton does not fit

Sometimes the production code does not expose a clean seam for an integration test. In that case:

1. Do not invent a seam. Mark the TC as `BLOCKED — needs production refactor`.
2. Open a follow-up task to introduce the seam (dependency injection, port/adapter, public test hook).
3. Keep the TC in the document so coverage is not lost.
