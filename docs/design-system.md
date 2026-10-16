# Delphi Design System — "Evidence & Ink"

> The complete specification of Delphi's visual language, interaction model,
> and frontend design architecture. Every component, page, and chart follows
> this document. A screenshot styled by these rules should be immediately
> recognizable as Delphi.

---

## 1. Design philosophy

Delphi's product promise is **verified causal evidence**. The design language
borrows from the places evidence has always lived:

| Source | What we take |
| --- | --- |
| Scientific plotting paper | The faint engineering grid on hero/empty canvases |
| Editorial typography | Serif display type for meaning; the product *argues*, it doesn't decorate |
| Swiss graphic design | One signal color, hairline rules, strict alignment |
| Instrument panels (Bloomberg) | Information density, tabular/mono numerals |
| Apple / Linear | Restraint, flatness, motion that explains |

Four rules govern every decision:

1. **Ink on paper.** Surfaces are warm-tinted near-monochrome — paper white in
   light mode, warm ink black in dark mode. Never sterile gray, never colored
   backgrounds for decoration.
2. **One signal.** Vermilion is the only saturated hue in the chrome. It is
   reserved for *causal signal*: primary actions, active navigation, evidence
   citations, and chart emphasis. If everything is highlighted, nothing is.
3. **Hairlines, not shadows.** Structure comes from 1px borders. Elevation is
   reserved for true layering (popovers, dialogs, command palette).
4. **Motion explains.** Animation communicates state change, navigation, or
   progress — never decoration. 120–240 ms, ease-out, ≤ 14 px translation.
   `prefers-reduced-motion` disables all motion globally at the CSS root.

### What Delphi never does

Purple gradients, glassmorphism, floating blobs, particles, neon glows,
oversized cards, giant border radius, template dashboards, default chart
palettes.

---

## 2. Visual identity

### The mark

A minimal **causal graph** — cause flowing to effect (X → M → Y as three nodes
and directed edges) — set in the signal color inside a small rounded square.
Defined once in `src/components/brand.tsx`; SVG masters in `assets/brand/`.

### The signature

- Plotting-paper grid (`.bg-plot-grid` utility) fading into the page.
- Serif display headline with the key word in *vermilion italic*
  (“…that answers **why**”).
- Mono-set evidence strings: `ATE −4.2 pp · 95% CI [−5.1, −3.3]`.

These three elements together are the brand. Use them at every "first
impression" surface: landing hero, auth panel, empty states, loading states.

---

## 3. Color tokens

All tokens are OKLCH CSS custom properties in `src/index.css`, mapped to
Tailwind utilities via `@theme inline`. Components only ever reference
semantic tokens.

### Base surfaces

| Token | Light (paper) | Dark (ink) |
| --- | --- | --- |
| `--background` | `oklch(0.988 0.002 85)` | `oklch(0.165 0.005 75)` |
| `--card` | pure white | `oklch(0.20 0.005 75)` |
| `--foreground` | warm ink `oklch(0.205 0.006 75)` | `oklch(0.955 0.004 85)` |
| `--border` | `oklch(0.905 0.004 85)` | `oklch(1 0 0 / 9%)` |
| `--muted-foreground` | `oklch(0.50 0.008 75)` | `oklch(0.69 0.007 80)` |

The slight chroma (0.002–0.008) at hue ~80 is what makes surfaces feel like
paper and ink instead of a gray wireframe.

### Signal

| Token | Light | Dark | Contrast |
| --- | --- | --- | --- |
| `--primary` (vermilion) | `oklch(0.545 0.175 34)` | `oklch(0.665 0.16 38)` | ≥ 4.5:1 with its foreground |
| `--primary-foreground` | paper white | near-black | — |

Destructive red sits at hue 22–24 and lower lightness so it never reads as the
brand color.

### State colors (badges, status)

emerald = success/verified · sky = running/info · amber = pending/warning ·
red = failed/error. Used only in `Badge` variants and status dots — never as
surface colors.

### Chart palette (`--chart-1…6`)

vermilion (emphasis) · slate blue · moss · ochre · plum · petrol. Muted,
scientific, print-like. Vermilion always marks the series that carries the
finding.

---

## 4. Typography

| Role | Face | Usage |
| --- | --- | --- |
| Display | **Newsreader** (serif, optical sizing) | Page titles, section headings, hero, key findings. Utility: `text-display` |
| UI | **Inter** | Everything interactive and structural |
| Data | **JetBrains Mono** | Numbers, IDs, confidence intervals, code, `kbd` |

Scale (rem): 11/12/13 (dense UI) · 14 (body) · 16/18 (lede) · 24/30/36/48/60
(display). Numerals in tables and evidence strings are always
`tabular-nums` or mono. Uppercase eyebrows: 11px, `tracking-[0.14em]`,
semibold, signal color.

---

## 5. Spacing, grid, radius, elevation

- **Spacing:** Tailwind 4px base. Component padding: 20px (`p-5`) cards,
  12px gaps in dense panels. Page gutter: 16px mobile / 24px desktop.
- **Grid:** App content plane is fluid with `max-w` per page type; marketing
  is a centered 1152px (`max-w-6xl`) column.
- **Radius:** base `0.5rem`; `rounded-md` for controls, `rounded-lg` cards,
  `rounded-xl` only for hero/media frames. Full radius only for pills/dots.
- **Elevation:** `shadow-xs` on interactive controls, none on cards,
  `shadow-2xl` reserved for the command palette, dialogs, and the hero frame.

---

## 6. Motion language

| Pattern | Spec |
| --- | --- |
| Entrance (fade-up) | 14px rise, 450ms ease-out, 50ms stagger per sibling |
| Hover/press | color 150ms; press = `scale(0.98)` |
| Active nav | signal rail fades in 150ms |
| Progress | pulse on the brand mark (route fallback), spinners only inline |
| Charts | ECharts default entrance; no looping animation |

Reduced motion: a global media query zeroes all animation/transition durations.

---

## 7. Component library (`src/components/ui`)

| Component | Notes |
| --- | --- |
| `Button` | 5 variants; vermilion default; focus ring = 2px signal ring with offset; press scale |
| `Card` | flat, hairline `border-border/80`, `p-5` rhythm |
| `Input`, `Label` | h-9, hairline, signal focus ring |
| `Badge` | `default/signal/success/info/warning/destructive/outline`; signal reserved for evidence |
| `EmptyState` | plotting-paper canvas + icon tile + next action |
| `PageHeader` | eyebrow → serif title → description → actions; identical hierarchy on every screen |
| `Skeleton` | muted pulse, matches final layout geometry |
| `kbd` | styled globally: mono, 10px, hairline chip |

Composition primitives come from Radix (via shadcn structure); appearance is
100% Delphi tokens.

---

## 8. Navigation & information architecture

The sidebar is grouped **by intent, mirroring the analytical pipeline**, not
by feature inventory:

- **Workspace** — Overview, Datasets (where work lives)
- **Analyze** — Statistics, Causal Inference, Simulation (the evidence pipeline)
- **Decide** — Recommendations, Reports, AI Copilot (evidence into action)
- **Operate** — Infrastructure

Rules:

- The **signal rail** (2px vermilion bar) + tinted icon marks the active item.
- Dataset-scoped stages route through the dataset list; only a path's
  canonical owner shows active state (no double-highlighting).
- Global search (⌘K) is the centerpiece of the header — the fastest route to
  any dataset, analysis, or session.
- Every page opens with `PageHeader`, so users always know where they are,
  why, and what they can do next.

---

## 9. Charts

A single ECharts theme (`src/lib/chart-theme.ts`, registered as `"delphi"`)
governs every visualization:

- palette from `--chart-*` tokens, re-registered on theme change;
- hairline axes, no axis ticks, muted split lines;
- Inter labels at 10–11px, tooltips on card surface with hairline border;
- bars: 3px top radius, max 28px width; lines: 2px, small circle symbols;
- correlation heatmaps use a diverging slate → paper → vermilion scale;
- vermilion marks *the* finding; supports stay muted.

Pages pass `theme="delphi"` and never hardcode colors (semantic role colors —
treatment/outcome/confounder — are documented palette constants).

---

## 10. Accessibility

- WCAG AA contrast on all text tokens (signal-on-paper ≥ 4.5:1 at body sizes).
- Focus visible everywhere: 2px signal ring with background offset.
- Full keyboard support: ⌘K palette, Esc dismissal, focus trap in overlays.
- `role="alert"` on form errors; labels bound to inputs; `aria-disabled` on
  future-phase nav.
- `prefers-reduced-motion` respected globally.
- Charts accompanied by mono-set textual summaries of the finding.

---

## 11. Performance

- Route-level code splitting: marketing bundle ships zero app code; every app
  page is `lazy()` behind the branded suspense fallback.
- TanStack Query caching with keyed invalidation; no waterfall refetching.
- ECharts theme registered once, not per chart render.
- Fonts: `display=swap`, preconnect, three families with limited weights.
- Virtualized tables (TanStack Virtual) for large datasets; mono numerals
  avoid layout shift.

---

## 12. Technology justification

| Choice | Why |
| --- | --- |
| Vite + React 19 + react-router | SPA with hard client-side interactivity (DAG editing, charts); SSR adds cost without SEO benefit beyond the landing page |
| Tailwind v4 CSS-first tokens | design system lives in CSS custom properties; re-theming never touches components |
| Radix/shadcn structure | accessibility primitives; appearance fully replaced by Delphi tokens |
| Framer Motion | declarative entrance/stagger with reduced-motion support |
| ECharts | best-in-class large-dataset canvas rendering; themable to Delphi's language |
| TanStack Query | server-state caching, retries, invalidation |
| Zod + React Hook Form | typed validation at the only untrusted boundary (user input) |
