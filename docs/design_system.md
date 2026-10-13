# AURXONQuant — Design System Specification
## Dual-Theme Financial Terminal Architecture

**Project:** AURXON Investment Intelligence Hub  
**Date:** October 13, 2026  
**Status:** IMPLEMENTED & ACTIVE

---

## 1. Design Tokens Architecture

The design system is implemented in pure Vanilla CSS (`frontend/src/index.css`) without heavyweight utility runtimes. Tokens are defined via CSS custom properties scoped to `:root` (Neon Obsidian) and overridden via `[data-theme="glacier"]`.

```
                    ┌────────────────────────────────────────┐
                    │          HTML Root / DOM               │
                    └───────────────────┬────────────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
     [data-theme="neon"] (Dark)                   [data-theme="glacier"] (Light)
     --bg-primary: #080C14                        --bg-primary: #F8FAFC
     --bg-card: rgba(14,21,35,0.82)               --bg-card: #FFFFFF
     --text-main: #F8FAFC                         --text-main: #0F172A
     --border-card: rgba(86,112,156,0.35)         --border-card: #CBD5E1
     --accent-blue: #3B82F6                       --accent-blue: #2563EB
```

---

## 2. Complete Token Inventory

### 2.1 Surfaces & Elevations
| Token | Neon Obsidian Dark | Premium Glacier Light | Usage |
| :--- | :--- | :--- | :--- |
| `--bg-primary` | `#080C14` | `#F8FAFC` | Viewport background |
| `--bg-secondary` | `#0D131F` | `#F1F5F9` | Table headers, secondary panels, pill containers |
| `--bg-surface` | `#121927` | `#FFFFFF` | Dropdown menus, modal dialogs |
| `--bg-surface-hover` | `#172033` | `#E2E8F0` | Table row hover, active chip highlights |
| `--bg-card` | `rgba(14, 21, 35, 0.82)` | `#FFFFFF` | Primary content cards |
| `--bg-input` | `#0A0F19` | `#FFFFFF` | Text inputs, dropdown select boxes |

### 2.2 Borders & Dividers
| Token | Neon Obsidian Dark | Premium Glacier Light | Usage |
| :--- | :--- | :--- | :--- |
| `--border-subtle` | `rgba(74, 96, 134, 0.28)` | `#E2E8F0` | Subtle element separators, table cell borders |
| `--border-card` | `rgba(86, 112, 156, 0.35)` | `#CBD5E1` | Card outlines, header border-bottom |
| `--border-focus` | `#00F0FF` | `#2563EB` | Active input outline |

### 2.3 Typography & Numbers
- **Primary Sans:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Monospace Financial:** `'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace`
- **Tabular Alignment:** `font-variant-numeric: tabular-nums` applied globally to ensure strict vertical digit alignment in financial data tables.

### 2.4 Semantic Status Colors
| Semantic State | Dark Mode Value | Light Mode Value | Meaning |
| :--- | :--- | :--- | :--- |
| **Verified / Positive** | `#10B981` (bg: `rgba(16,185,129,0.14)`) | `#16A34A` (bg: `#DCFCE7`) | Buy recommendations, filled orders, verified sources, passed tests |
| **Uncertain / Warning** | `#F59E0B` (bg: `rgba(245,158,11,0.14)`) | `#D97706` (bg: `#FEF3C7`) | Hold calls, delayed quotes, high uncertainty, pause states |
| **Contradicted / Distress** | `#EF4444` (bg: `rgba(239,68,68,0.14)`) | `#DC2626` (bg: `#FEE2E2`) | Avoid calls, rejected orders, kill switch active, risk limit vetoes |

---

## 3. Component Design System Standards

1. **Buttons (`.btn-primary`, `.chip-btn`):**
   - High contrast, clear hover state with brightness scaling (`filter: brightness(1.1)`), disabled cursor protection.
2. **Cards (`.glass-card`):**
   - Single-tier border and elevation. In light mode, glass blur is disabled (`--glass-blur: none`) to eliminate GPU rendering cost and maintain crisp readability.
3. **Tables (`.data-table`):**
   - Uppercase compact headers (`font-size: 0.72rem`, `letter-spacing: 0.05em`), subtle bottom cell dividers, and row highlight on hover.
4. **Theme Switcher (`.theme-switcher`):**
   - Pill-shaped segmented control housing Light, Dark, and Auto buttons with instant visual feedback and zero layout shift.
