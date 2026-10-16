# AI Decision Copilot

Phase 13 introduces Delphi's **AI Decision Copilot** — a trusted business analyst that sits on top of Delphi's analytical engines. The copilot **never performs calculations**; it only interprets verified outputs from:

```
Statistics Engine → Causal Engine → Simulation Engine → Decision Engine → Executive Intelligence
```

## Architecture

```
Conversation Manager
       ↓
Context Builder → Prompt Composer → Tool Router
       ↓
LLM Provider (replaceable)
       ↓
Response Validator → Citation Generator
       ↓
Conversation History / Persistence
```

| Component | Responsibility |
|-----------|----------------|
| **Conversation Manager** | Orchestrates a single turn: build context, call LLM, validate, persist |
| **Context Builder** | Assembles tenant-scoped structured context from application repositories |
| **Prompt Composer** | Versioned system prompts; no business logic in templates |
| **Tool Router** | Invokes Delphi services via repositories (never direct DB access) |
| **LLM Provider** | Swappable adapter (`mock`, `openai`, future: Anthropic, Azure, Gemini) |
| **Response Validator** | Rejects hallucinated citations and unsupported numeric claims |
| **Citation Generator** | Links statements to persisted analyses |

## Context builder

The context builder (`CopilotContextBuilder`) retrieves:

- Dataset metadata
- Data intelligence / quality scores
- Recent statistical, causal, simulation, and decision runs
- Executive reports
- Decision session state (optional)

Context is rendered as concise prompt sections via `StructuredContext.to_prompt_sections()` — not raw JSON dumps.

## Provider abstraction

`LlmProviderPort` defines a single `complete()` method. `create_llm_provider(settings)` selects the implementation:

| `LLM_PROVIDER` | Behavior |
|----------------|----------|
| `mock` (default) | Deterministic template responses for dev/test |
| `openai` | OpenAI Chat Completions via `httpx` (Azure-compatible `LLM_BASE_URL`) |

Configure via environment:

```env
LLM_PROVIDER=mock
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
COPILOT_MAX_TOKENS=2048
```

## Response validation

Every assistant response is validated before persistence:

- Citation patterns like `[Statistical Analysis #1]` must reference analyses in the context snapshot
- Heuristic checks flag invented p-values or ATEs when no analyses exist
- Failed validation raises `copilot_validation_failed` (HTTP 422)

## API

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/api/v1/copilot/conversations` | `copilot:create` |
| `GET` | `/api/v1/copilot/conversations` | `copilot:read` |
| `GET` | `/api/v1/copilot/conversations/{id}` | `copilot:read` |
| `POST` | `/api/v1/copilot/conversations/{id}/messages` | `copilot:create` |
| `GET` | `/api/v1/copilot/context` | `copilot:read` |

## Security

- Tenant isolation on all repository queries
- RBAC: `COPILOT_READ`, `COPILOT_CREATE`
- Audit events: `copilot.conversation_created`, `copilot.message_sent`
- Prompt construction logged via structured logging on LLM completion

## Frontend

Navigate to **AI Copilot** (`/app/copilot?datasetId=...`) for:

- Conversation sidebar and history
- Evidence panel with citation excerpts
- Context inspector (structured prompt preview)
- Suggested questions
- Export conversation as JSON

## Testing

```bash
cd backend && uv run pytest tests/unit/test_copilot.py tests/integration/test_copilot_endpoints.py -q
```

See [ADR 013](adr/013-ai-copilot.md) for architectural decisions.
