# `store/`

Global client-side state that is **not** server state. Server data lives in
TanStack Query (`services/api`); this folder is reserved for cross-cutting UI
state (e.g. workspace selection, command palette) once it is actually needed.

No global store is introduced prematurely — reach for one only when prop
drilling or context becomes unwieldy.
