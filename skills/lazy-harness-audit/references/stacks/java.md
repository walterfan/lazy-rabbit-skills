# Java Stack Checklist

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

**Markers**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle*`, `src/main/java`, `src/test/java`, `src/main/kotlin`, `mvnw`, `gradlew`.

**Verification surfaces** (rubric §2):
- Build/test commands: `mvn verify`, `mvn test`, `mvn -pl <module> verify`, `gradle check`, `gradle test`, `./mvnw verify`, `./gradlew check`.
- Whether `verify` / `check` actually chains unit tests, integration tests, lint, and static analysis (not just compile).
- Whether `failsafe` (integration tests) is wired in alongside `surefire` (unit tests).

**Architecture fitness** (rubric §3):
- ArchUnit tests under `src/test/java` enforcing layering, package dependencies, naming, or annotation rules.
- Module boundaries in Gradle or Maven multi-module setups.
- API stability: `revapi`, `japicmp`, or contract tests for public modules.

**Behavior harness** (rubric §4):
- Spring Boot tests: `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`, `@Testcontainers`.
- MyBatis / JPA: schema migration (Flyway, Liquibase) plus integration tests that run them.
- Approved fixtures or golden files under `src/test/resources`.

**Safety tooling** (rubric §5):
- Static analysis: Checkstyle, SpotBugs, PMD, Error Prone, NullAway.
- Coverage: JaCoCo with a documented threshold.
- Dependency / security: OWASP Dependency-Check, Snyk, Dependabot/Renovate.
- Secret scanning: gitleaks, trufflehog, or equivalent.

**Priority notes**:
- Reward only checks that are wired into `mvn verify`, `gradle check`, or CI — plugins that exist in `pom.xml` but are never invoked do not count.
- Java harness quality often hides in build plugin configuration; read the relevant `pom.xml` / `build.gradle*` rather than relying on file names alone.
