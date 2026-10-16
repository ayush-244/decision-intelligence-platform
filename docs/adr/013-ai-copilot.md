# ADR 013: AI Decision Copilot

## Status

Accepted — Phase 13

## Context

Delphi's core value is statistically rigorous, transparent decision intelligence. Users need help interpreting complex analytical outputs, but a general-purpose chatbot would undermine trust if it invented numbers or performed independent statistical reasoning.

## Decision

Introduce an **AI Decision Copilot** as a modular application service layer that:

1. Consumes **only** verified outputs from Delphi engines via repositories and tool routing
2. Uses a **replaceable LLM provider** (`LlmProviderPort`) defaulting to a deterministic mock for tests
3. Validates every response against the **context snapshot** before persistence
4. Attaches **evidence citations** linking statements to persisted analyses
5. Persists conversations and messages for auditability and future semantic search

The copilot is implemented as a modular monolith slice following existing Clean Architecture patterns (entities → use cases → routers).

## Architecture

```
Presentation (copilot router)
    → Use cases (create, send, list, get, context)
        → Conversation Manager
            → Context Builder (repos)
            → Prompt Composer (versioned templates)
            → LLM Provider (infrastructure adapter)
            → Response Validator + Citation Generator
        → SQL repositories (copilot_conversations, copilot_messages)
```

## Consequences

### Positive

- Trustworthy AI layer aligned with Delphi's "engines compute, AI explains" principle
- Provider-agnostic LLM integration
- Testable validation and citation logic without external APIs
- Full audit trail of copilot interactions

### Negative

- Mock provider responses are template-based; production quality depends on external LLM configuration
- Validation heuristics may require tuning as prompt patterns evolve

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| RAG over raw database | Bypasses engine boundaries; risk of leaking unverified data |
| LLM tool-calling direct to SQL | Violates tenant/RBAC guarantees |
| No validation layer | Unacceptable hallucination risk for enterprise analytics |

## References

- [copilot.md](../copilot.md)
- Phase 5–9 engine documentation
