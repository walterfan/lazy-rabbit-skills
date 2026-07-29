# Pydantic Best Practices (v2)

Reference for the `pydantic` review focus. Pydantic is the **runtime safety belt**
at system boundaries: it turns untrusted input into type- and business-constrained
Python objects. It is NOT a static type checker (that's mypy/pyright) and NOT a
business-logic or authz system.

Source: "Python 动态语言里的安全带：Pydantic 用法与最佳实践" (Walter Fan). Assumes
Pydantic v2.

## What Pydantic is for

Turn untrusted input into a validated object at the boundary:

| Boundary | Risk without a model | Value of a model |
|----------|----------------------|------------------|
| HTTP request body | missing fields, type drift | one clear failure point |
| MQ message | old/new schemas mixed | explicit, evolvable schema |
| Config / env vars | `"false"` parsed as truthy string | fail at startup, cheaply |
| LLM structured output | JSON-shaped but untrusted fields | validate before use |
| DB / external API response | upstream field change breaks silently | contract break caught early |

Pydantic vs static checks vs tests — they cover different things:
- Linter (ruff/pylint): source text/style, dead code.
- Static type checker (mypy/pyright): type relationships in the code.
- Pydantic: the **actual runtime data** the program receives.
- Tests: whether the business behavior is correct.
Use all of them; wire lint + types + tests into one `make check` in pre-commit + CI.

## The 7 best practices

### 1. All external input goes through a model
Don't hand a raw `dict` to business code. Validate at the entrance:
```python
req = CreateInvoiceRequest.model_validate(payload)  # v2 entry point
```
From here on, business code sees `req`, not a bare dict.

### 2. Default lenient, key fields strict
Pydantic coerces by default (`"123"` -> `123`, `"false"` -> `True`!). Fine for
env/query/JSON, dangerous for money/permissions/flags/quotas.
```python
class Payment(BaseModel):
    amount: int = Field(strict=True, gt=0)
# or per-call: Payment.model_validate(data, strict=True)
# or per-model: model_config = ConfigDict(strict=True, extra="forbid")
```
Guidance: money/quota/permission/internal-command -> strict; user search input ->
lenient but length-limited; env vars -> convert but validate at startup;
third-party webhook -> receive leniently, then convert explicitly.

### 3. Use validators for business boundaries
```python
class MeetingRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @field_validator("participants")
    @classmethod
    def normalize(cls, v: list[str]) -> list[str]:
        cleaned = sorted({p.strip().lower() for p in v if p.strip()})
        if not cleaned:
            raise ValueError("participants cannot be empty")
        return cleaned

    @model_validator(mode="after")
    def check_range(self) -> "MeetingRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        return self
```
Keep validators PURE: normalize/strip/enum-compat/cross-field OK; DB uniqueness
check cautiously; network/DB writes/side effects NEVER. The model is a gatekeeper,
not a business manager.

### 4. Don't let config run around as strings
Use `pydantic-settings` (separate package in v2); fail fast at startup; mask
secrets.
```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")
    debug: bool = False
    request_timeout_seconds: int = Field(default=3, ge=1, le=60)
    database_url: SecretStr
```
`.env` is for local dev only; production secrets belong in a secret manager.

### 5. `TypeAdapter` for non-model types
```python
events_adapter = TypeAdapter(list[Event])   # module-level, reused
def handle(payload: object) -> list[Event]:
    return events_adapter.validate_python(payload)
```
Good for `list[Model]`, `dict[str,int]`, JSON Schema of simple types. Reuse the
adapter; don't build one per request.

### 6. Output has boundaries too
Don't hand-build response dicts. Use output models + `model_dump`.
```python
class InvoiceView(BaseModel):
    invoice_id: str
    amount: Decimal
    internal_note: str | None = Field(default=None, exclude=True)

payload = view.model_dump(mode="json", exclude_none=True)
```
Input is a contract; output is a contract. `exclude=True` keeps internal fields
from leaking.

### 7. Treat schema as a team asset
`Model.model_json_schema()` feeds API docs, CI schema-diff, LLM structured-output
constraints, OpenAPI/AsyncAPI, and contract tests. In microservice/event systems,
schema is the boundary language.

## Common Pydantic traps

1. Believing type hints validate at runtime — they don't. Use a model or
   `@validate_call` (sparingly) at boundaries.
2. Trusting default coercion for product decisions (`"001"`, `"false"`, `""`).
   Strict + explicit validators for key fields.
3. Forgetting extra fields — default is ignore; prefer `extra="forbid"` for
   API requests / internal commands.
4. Mixing ORM and API models in one class — leaks DB fields, tangles validators.
   Layer: API Request -> Domain -> ORM -> API Response.
5. Side effects in validators (DB/HTTP/cache) — validators can run in tests,
   retries, schema generation. Keep them pure.
6. v1/v2 confusion — see the migration table below; don't mix.
7. Treating Pydantic as a static type system — it's runtime validation; still
   need mypy/pyright + tests.

## v1 -> v2 migration

| Pydantic v1 | Pydantic v2 |
|-------------|-------------|
| `parse_obj()` | `model_validate()` |
| `.dict()` | `model_dump()` |
| `.json()` | `model_dump_json()` |
| `schema()` | `model_json_schema()` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `BaseSettings` in `pydantic` | `BaseSettings` in `pydantic-settings` |
| inner `class Config:` | `model_config = ConfigDict(...)` |

## Recommended templates

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=128)
    priority: Literal["low", "medium", "high"] = "medium"
    assignee: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in value if t.strip()})

    @model_validator(mode="after")
    def high_priority_needs_owner(self) -> "CreateTaskRequest":
        if self.priority == "high" and not self.assignee:
            raise ValueError("high priority task must have an assignee")
        return self


class TaskView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    title: str
    priority: str
    assignee: str | None
    tags: list[str]
```
Handler shape: validate at entry, business in the middle, model_dump at exit.

## Security review card

- Pydantic is not authn/authz/risk control; it validates input structure + local
  constraints only.
- Never log raw sensitive input in validators (tokens, passwords, connection
  strings, PII).
- `.env` is local-dev only; production secrets via a secret manager / K8s Secret.
- Keep user-facing errors terse; structured internal logs are fine, but don't
  leak sensitive fields or internals in responses.
