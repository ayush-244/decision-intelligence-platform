# Decision Intelligence Platform — Frontend

React 19 + TypeScript + Vite SPA, styled with Tailwind CSS v4 and shadcn/ui.

## Architecture

Feature-first, with a small set of global concerns. The dependency direction is
`pages → features/components → services → lib/config`.

```
src/
  app/         # Composition root: providers (theme, query) + route table
  components/  # Shared, reusable UI (incl. ui/ = shadcn primitives)
  features/    # Feature-first modules (added per phase; empty for now)
  pages/       # Route entrypoints, composed from features/components
  layouts/     # Page shells (marketing, app + sidebar)
  hooks/       # App-wide reusable hooks
  services/    # API client + typed endpoints + query hooks
  store/       # Global client state (introduced only when needed)
  config/      # Typed environment access
  lib/         # Framework-agnostic utilities (cn, formatters)
  types/       # Shared cross-cutting types
  styles/      # (index.css lives at src root by shadcn convention)
```

## Prerequisites

- Node.js 20+ (22 recommended)

## Setup & run

```bash
npm ci            # install exact locked dependencies
npm run dev       # http://localhost:5173
```

The dev server reads `VITE_*` variables from `.env.local` (copy `.env.example`).

## Quality gates

```bash
npm run typecheck    # tsc project references, no emit
npm run lint         # ESLint (type-aware, flat config)
npm run format:check # Prettier
npm run test         # Vitest + Testing Library
npm run build        # production build to dist/
```

## Adding shadcn/ui components

```bash
npx shadcn@latest add <component>
```

Configuration lives in `components.json` (New York style, neutral base, CSS
variables). Components are copied into `src/components/ui` and owned by us.
