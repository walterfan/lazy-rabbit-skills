# Java Testing and Review

Use this reference when writing tests or reviewing Java service
changes.

## Review order

1. Behavior and correctness
2. Authorization, validation, and injection risk
3. Privacy-safe logging and error handling
4. Transaction boundaries and data consistency
5. Integration timeout, retry, and fallback behavior
6. Concurrency and async safety
7. Missing tests
8. Naming and style

## Common pitfalls

- Catching generic `Exception` and swallowing it
- Returning `null` when `Optional` or explicit absence handling is expected
- Using string concatenation in loops or log statements
- Mixing business logic with controller/framework glue
- Using `System.out` or commented-out debug code
- Using `@Data` on entities and accidentally exposing sensitive fields
- Using `${}` in MyBatis for user input
- `@Transactional` on private methods
- Silent async failures from poorly managed thread pools or scheduled jobs
- Missing validation for page size, sort keys, regex, or uploaded files

## Concurrency and async checks

- Use explicit thread pools instead of unbounded executor shortcuts
- Name thread pools and handle rejected tasks intentionally
- Release locks in `finally`
- Use concurrent collections for shared mutable state
- Document thread-safety expectations for shared services or caches
- Make scheduled jobs idempotent or safe to retry when possible

## Test defaults

- Prefer focused unit tests for service logic and validation branches
- Add controller tests for request validation, auth/error mapping, and response
  shape when API behavior changed
- Add mapper or integration tests when XML, SQL shape, serialization, or client
  behavior changed materially
- Cover happy path, validation failures, dependency failures, and not-found or
  conflict paths
- Prefer deterministic tests over sleep-based timing

## Testing cues by change type

- Controller change -> validate status code, response body, auth path, and bad
  input behavior
- Service change -> validate transaction or business-rule branches
- Mapper change -> validate binding safety, pagination, and result mapping
- Logging/privacy change -> validate that sensitive fields are not exposed if
  tests or snapshots exist around serialization/logging helpers
- Async change -> validate timeout, retry, failure handling, or executor usage

## Good review comments

- `This controller validates shape but not ownership. If the resource is user-scoped, add an authorization check before returning data.`
- `This mapper uses string substitution where parameter binding should be used. Switch to #{...} unless the value is a validated allow-listed identifier.`
- `The new log line includes a request object that may contain sensitive fields. Log stable identifiers and status instead of the raw object.`
- `This transactional flow catches and swallows the exception, which can commit partial work. Re-throw or redesign the transaction boundary.`
- `The new async task uses an implicit executor with no rejection strategy or naming. Move it to an explicit executor managed by the service.`

## Verification defaults

- `./mvnw test` or `mvn test`
- `./gradlew test` or `gradlew test`
- repo-native wrappers if present
- targeted module tests first when they materially reduce turnaround time
