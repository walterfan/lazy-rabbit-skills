# Java Service Stack

Concise defaults for Java backend services derived from the source
rules used to build this skill.

## Core shape

- Prefer Spring Boot layered design: controller -> service -> repository/mapper
- Use constructor injection rather than field injection
- Keep classes focused and interfaces narrow
- Follow repo naming conventions, including project-specific interface and
  DTO/VO/DO suffix patterns when already present
- Externalize configuration with `@ConfigurationProperties` or repo-standard
  config patterns

## Spring Boot defaults

- Validate inputs early with Bean Validation and explicit business checks
- Keep transaction boundaries at the service layer
- Do not rely on private `@Transactional` methods
- Use custom exceptions instead of generic `Exception`
- Return DTOs or response wrappers from APIs instead of raw entities

## MyBatis and persistence defaults

- Keep SQL in XML mappers if the repo follows that convention
- Use `#{}` for parameter binding; treat `${}` as dangerous unless the value is
  validated and allow-listed
- Avoid `SELECT *`; specify fields explicitly
- Use pagination for large lists
- Keep transactions short and focused
- Watch for N+1 access and over-fetching
- Use explicit Lombok annotations on entities rather than `@Data`
- Exclude sensitive fields and collections from `toString`, `equals`, and
  `hashCode` behavior where appropriate

## API defaults

- Version APIs explicitly
- Separate request/response DTOs from entities
- Use OpenAPI or repo-standard docs for externally visible endpoints
- Map domain exceptions to stable HTTP responses
- Validate query params, path variables, and request bodies

## Integration defaults

- Set timeouts for all external calls
- Use repo-standard client abstractions such as service invokers or internal
  wrappers when present
- Use retries with backoff only for retryable failures
- Prefer response wrappers and explicit error mapping over ad hoc parsing
- For async or scheduled work, use explicit executors and predictable shutdown

## Internal library cues

- Prefer repo-standard internal libraries when already in use for:
  - HTTP/service invocation
  - resilience and circuit breakers
  - cache access
  - JWT or token handling
  - crypto
  - config refresh
  - thread pools and APM

Do not add internal libraries speculatively if the repo does not already use
them.

## Commands to prefer

- Maven: `./mvnw test`, `mvn test`
- Gradle: `./gradlew test`, `gradlew test`
- Repo wrapper commands such as `just test`, `make test`, or CI targets if they
  exist

Prefer repo-native entry points over invented ad hoc commands.
