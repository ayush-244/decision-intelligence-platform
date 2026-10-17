# `features/`

Feature-first modules. Each future capability (e.g. `datasets/`, `causal/`,
`simulation/`) gets its own folder that co-locates everything it needs:
components, hooks, API bindings, and types. This keeps features cohesive and
independently ownable rather than scattering code across global `components/`
and `hooks/` folders.

Suggested shape for a feature:

```
features/<feature>/
  components/    # UI specific to this feature
  hooks/         # feature-scoped hooks
  api/           # queries/mutations for this feature
  types.ts       # feature-scoped types
  index.ts       # public surface re-exported for pages/routes
```

Empty for now — no analytical features exist in the foundation phase.
