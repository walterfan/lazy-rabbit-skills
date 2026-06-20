# C4-First Architecture Standard

<!-- Keep in sync with the summary in SKILL.md -->

Use the C4 model as the default architecture lens for `/PKB-architecture` and any architecture-related sections in other docs.

## Required C4 Levels

1. **Context**: System boundary, external users/systems, and high-level interactions.
2. **Container**: Deployable/runtime building blocks (services, apps, databases, queues) and communication paths.
3. **Component**: Internal module decomposition inside each key container.
4. **Code**: Representative code-level structures for critical components (types/classes/interfaces and key interaction flows).

## C4 to UML Mapping Reference

| C4 Model | UML Equivalent |
|---------|----------------|
| Context | No direct UML match (closest: system context) |
| Container | Component / Deployment diagrams |
| Component | Component / Class diagrams |
| Code | Class diagrams, sequence diagrams |

## Generation Rules for `/PKB-architecture`

- Always organize architecture content from **Context -> Container -> Component -> Code**.
- Include at least one Mermaid diagram for Context/Container and one for Component/Code where feasible.
- If exact UML artifacts are requested, use the mapping table above to choose the nearest UML representation while preserving C4 intent.
- Keep Code level selective: document only business-critical or high-change areas, not every class in the repo.
