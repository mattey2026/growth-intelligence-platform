# Growth Intelligence Design System

The permanent visual language for every dashboard the platform generates. The reference implementation is `skills/artifact-dashboard-intelligence/assets/command-center.css`. Any other renderer (React, Next.js, portal, mobile) must reproduce these tokens and rules.

## Principles
1. **Trust comes from provenance, not effects.** Every material number carries a provenance mark (a small bordered count) that opens its evidence. This is the system's signature element.
2. **Uncertainty is visible.** Confidence is shown as a meter with a percentage. Claim types (FACT, CALC, INFERENCE, CORRELATION, HYPOTHESIS, PREDICTION, MODELED, RECOMMENDATION) are labelled. Unavailable data reads "Not available" and says what it needs. **Never a zero standing in for "unknown".**
3. **Color communicates meaning.** Nothing is colored for decoration.
4. **Restraint and density.** One accent. Subtle 1px borders. A 3px radius. Shadows only on overlays (the drawer and dropdown menus); the focus highlight is a 2px accent ring. No gradients, glass effects, sparkles, emojis or neon.

## Color tokens
Light is the default; dark uses the **same token names**.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | `#F3F5F7` cool white | `#151A20` graphite | Page |
| `--surface` | `#FFFFFF` | `#1B2128` | Panels |
| `--raised` / `--sunken` | `#F8FAFB` / `#EDF0F3` | `#20272F` / `#12161B` | Hover, meters |
| `--line` / `--line-strong` | `#DDE2E7` / `#C6CDD5` | `#2B343E` / `#3A4552` | Borders |
| `--ink` / `--slate` / `--muted` | `#18212B` / `#4B5A6A` / `#6E7A87` | `#E4E8EC` / `#A3AFBB` / `#8793A0` | Text |
| `--accent` | `#0F5C78` deep blue-teal | `#4FA3C2` | The single analytical accent: actual series, selection, focus |
| `--pos` | `#2F7A4F` restrained green | `#5DAE7E` | Positive |
| `--warn` | `#A87718` amber | `#D2A34A` | Warning, inferences, annotations |
| `--risk` | `#B03A3A` restrained red | `#D46A6A` | Risk |
| `--info` | `#2F6DA8` | `#6A9FD4` | Information, predictions |
| `--crit` | `#7C1F1F` | `#E38B8B` | Critical |

**Categorical palette** (six colors, never rainbow): `--c1` blue-teal, `--c2` teal, `--c3` muted violet, `--c4` muted amber, `--c5` restrained green, `--c6` restrained orange. Categories keep a fixed order, so a color always means the same category.

**Sentiment is semantic, not directional.** A rise in value at risk is red. A falling competitive exposure is green. An accelerating *displacement opportunity* is green. The contract supplies `sentiment`; renderers never infer it from arrow direction.

## Typography
- **Families:** IBM Plex Sans for the UI, and IBM Plex Sans Condensed for dense labels and table headers. Fallback: `"Segoe UI", system-ui, sans-serif`.
- **Numerals:** tabular and lining (`font-variant-numeric: tabular-nums lining-nums`), so columns align.

| Element | Size | Weight |
|---|---|---|
| KPI values | 22px | 600 (19px below 1440) |
| Widget titles | 14px | 600 |
| Body and tables | 12.5–13px | 400 |
| Metadata | 11–11.5px | 400 |

- **Case:** sentence case. No tracked all-caps labels. The only all-caps text is the wordmark.

## Grid and layout
- 12-column grid, 16px gutter, 20px page margin, maximum content width 1880px. Breakpoints are designed for **1280 / 1440 / 1600 / 1920**.
- Every row sums to 12 columns. Paired widgets are trend + drivers (8 + 4) and radar + risk matrix (7 + 5). All others are full width. The builder's `pack()` enforces this.
- Tablet (below 1100px): all widgets go full width. Below 720px: two-column KPIs, and SWOT stacks.
- Wide tables scroll inside their own container. The page never scrolls sideways.

## Components
- **KPI tile:** label; value; delta with arrow and sentiment color; previous value; sparkline; confidence; provenance mark. Clicking a tile opens its drill-down.
- **Tables:** sticky headers, sorting, a row filter, column visibility, compact density, sparklines, conditional pills, and drill-down on rows.
- **Charts:** 2D only. Hairline grids. Axis labels in the muted color. Line charts use a data-fitted baseline. Bridges state their non-zero baseline on the axis. Scatter labels avoid collisions (right, then left, above, below), or are dropped in favour of the tooltip.
- **Drawer:** right side, 520px; like dropdown menus it is an overlay, and only overlays cast a shadow. It is used for evidence, drill-down, and thread timelines.
- **Motion:** only in response to an action (the drawer slides in). Respects reduced-motion preferences.

## Forbidden
Claude's default beige or purple, AI gradients, heavy purple, neon, large rounded cards, glassmorphism, chatbot styling, decorative sparkles, emojis, 3D charts, rainbow palettes, and color used for decoration.
