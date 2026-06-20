# Java Security and Logging

Use this reference when Java work touches controllers, mappers, auth, secret
loading, file handling, external calls, or anything that could leak sensitive
data.

## Authorization and validation

- Validate body, path, and query inputs at the boundary
- Apply authorization checks with Spring Security and repo-standard annotations
  such as `@PreAuthorize`
- Protect user-owned resources from IDOR by checking ownership explicitly when
  needed
- Validate pagination, sorting, regex, redirects, and uploaded file metadata
- Do not return raw entities from controllers when DTOs are expected

## Secret and crypto defaults

- Never hardcode credentials, private keys, or tokens
- Prefer a secrets manager or the repo-standard secret loading path
- Use `SecureRandom`, strong hashing, and modern encryption modes
- Avoid Trust-All SSL or homegrown crypto shortcuts

## Persistence security

- Use `#{}` in MyBatis for user-controlled values
- Never concatenate user input into SQL or JSON query bodies
- Validate any dynamic sort, table, or column names against an allow-list
- Use safe builders or framework query objects for search/integration queries

## Logging rules

- Never use `System.out.println()` or `printStackTrace()`
- Never use string concatenation in log statements
- Never log secrets, tokens, raw JWTs, passwords, payment data, or sensitive PII
- Keep credentials and sensitive values out of exception messages
- Use repo-standard logging placeholders and sensitivity annotations when the
  logging-extension SDK is present
- Log enough context to debug behavior without leaking data

## Privacy-safe object logging

- Treat raw request or response object logging as dangerous unless the object is
  already annotated for safe desensitization
- Exclude sensitive and large collection fields from `toString`
- Prefer logging identifiers, counts, status, and operation context over full
  payloads

## File and command safety

- Sanitize filenames and prevent path traversal
- Validate file type by more than header or extension alone when the repo cares
  about uploaded content
- Avoid shell or command execution with user input; use structured APIs where
  possible

## Good patterns

- `@Valid` DTO plus business-rule validation in service layer
- `@PreAuthorize(...)` plus ownership check where resource identity matters
- custom exceptions with safe user-facing messages
- structured logger usage with placeholders and redacted fields

## Review prompts

- Could this controller accept unbounded or unsafe input?
- Could this mapper or integration call be injected?
- Could this log line leak L3-L5 or secret data?
- Is authorization enforced only at UI level instead of service or controller?
- Are secrets loaded from a safe runtime source instead of code or properties?
