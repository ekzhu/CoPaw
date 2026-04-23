# Console Theme / Skin System — Design Doc

Status: **Draft** · Owner: _TBD_ · Target: `console/` package · Discussion: _TBD_

## 1. Summary

Introduce a configurable theme/skin module for the QwenPaw Console so users and
third parties can restyle the UI — from a simple color palette swap, up to
replacing entire presentational components (backgrounds, buttons, sidebar) —
without forking the console.

The proposal is intentionally **staged**. Each stage ships as an independently
reviewable PR so maintainers can accept Stage 1 and evaluate demand before
Stage 2/3 widen the surface area.

## 2. Goals & Non-Goals

### Goals

1. Let users pick a theme from the Settings UI and persist the choice.
2. Let community authors publish themes **without patching the console source**.
3. Keep the default light/dark experience identical to today — themes opt in.
4. Keep the maintenance surface small. A reviewer should be able to accept
   Stage 1 in one sitting.
5. Clearly bound what a theme can and cannot do, so "a bad theme" cannot break
   the app shell.

### Non-Goals

1. A visual theme editor in-browser (out of scope; a later proposal could add
   one on top of the token model defined here).
2. Rewriting the existing dark-mode overrides in
   `console/src/styles/layout.css` — that is acknowledged tech debt (see §4)
   but not the charter of this doc.
3. Theming the Python backend, DingTalk/Feishu channel UIs, or the Desktop
   app shell chrome outside the web console.
4. Runtime code-loading from arbitrary URLs (always goes through the
   backend plugin loader; see §8 Security).

## 3. Current State

Relevant primitives already exist and should be **reused, not duplicated**:

| Concern | Current implementation | File |
|---|---|---|
| Framework | React 18 + TypeScript + Vite | `console/vite.config.ts`, `package.json` |
| Component kit | Ant Design 5, wrapped with `@agentscope-ai/design` tokens (`bailianTheme`, `bailianDarkTheme`) | `console/src/App.tsx:1-7` |
| Light/Dark state | `ThemeContext` with `"light" \| "dark" \| "system"`, persisted in `localStorage["qwenpaw-theme"]`; toggles `html.dark-mode` class | `console/src/contexts/ThemeContext.tsx` |
| Global styles | Plain CSS + `!important` overrides, plus `antd-style`'s `createGlobalStyle` | `console/src/styles/layout.css`, `console/src/styles/form-override.css`, `console/src/App.tsx:50-55` |
| Per-component styles | CSS Modules + LESS (`*.module.less`), with `:global(.dark-mode) { … }` escape hatch for dark overrides | `console/src/components/ThemeToggleButton/index.module.less`, `console/src/layouts/index.module.less` |
| AntD tokens at runtime | `<ConfigProvider>` with `prefixCls="qwenpaw"` and `colorPrimary: #FF7F16` | `console/src/App.tsx:169-183` |
| Existing theme picker UI | `ThemeToggleButton` in the header offers light / dark / system via a dropdown | `console/src/components/ThemeToggleButton/index.tsx`, rendered in `console/src/layouts/Header.tsx:213` |
| Plugin runtime | Backend serves `GET /api/plugins`; frontend fetches each plugin's JS entry, executes via a same-origin Blob URL, plugin calls `window.QwenPaw.registerRoutes` / `registerToolRender` | `console/src/plugins/hostExternals.ts`, `console/src/plugins/usePluginLoader.ts` |
| Backend plugin manifest | `plugin.json` with `entry.frontend` → served under `/api/plugins/{id}/files/…` | `src/qwenpaw/app/routers/plugins.py`, `src/qwenpaw/plugins/` |
| Settings pages | `console/src/pages/Settings/*/index.tsx` (Agents, Debug, Models, …) | — |

**Take-away:** light/dark, a shared token contract, and a plugin loader all
already exist. A theme system should slot between them rather than reinvent.

## 4. Motivation & Maintenance Warning

`console/src/styles/layout.css` has grown to ~1000 lines of `!important`
overrides targeting AntD internals (`.ant-modal-*`, `.ant-picker-*`, …) just to
support a single built-in dark mode. That pattern does not scale to N community
themes — every new theme would multiply the `!important` surface.

The design therefore treats **tokens as the contract** and limits raw CSS
override escape hatches to explicitly namespaced classes. This is the single
most important decision in the doc for long-term maintenance.

## 5. Design Overview

Three staged tiers, shipping in order:

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3:  Full skin plugin                                      │ (future)
│           Ships React components for specific slots (Sidebar    │
│           header, Login background, welcome card, etc.)         │
├─────────────────────────────────────────────────────────────────┤
│ Stage 2:  Themed component slots                                │ (follow-up)
│           Host exposes a small set of named "slots" whose        │
│           rendering can be overridden by a theme.               │
├─────────────────────────────────────────────────────────────────┤
│ Stage 1:  Token + CSS theme pack                                │ (first PR)
│           Declarative JSON of design tokens + optional           │
│           scoped CSS string. No JS. No arbitrary DOM.           │
└─────────────────────────────────────────────────────────────────┘
```

Each tier is additive — Stage 2 does not require changing Stage 1's contract.

### 5.1 Stage 1 — Token + CSS theme pack (FIRST PR)

A theme is a JSON manifest plus an optional CSS file:

```json
{
  "id": "solarized",
  "name": "Solarized",
  "version": "1.0.0",
  "author": "community",
  "mode": "light",                    // "light" | "dark" | "auto"
  "tokens": {
    "colorPrimary": "#268bd2",
    "colorBgBase":  "#fdf6e3",
    "colorTextBase": "#586e75",
    "borderRadius": 6,
    "fontFamily": "IBM Plex Sans, sans-serif"
  },
  "css": "themes/solarized.css"       // optional, resolved relative to manifest
}
```

- **Tokens** are fed straight into AntD's `ConfigProvider.theme.token`. This is
  already AntD's own contract, so we avoid inventing a parallel vocabulary.
- **`mode`** picks whether AntD uses `defaultAlgorithm` or `darkAlgorithm`; if
  `"auto"` the existing `ThemeContext` system preference still applies.
- **`css`**, if present, is loaded as a `<link rel="stylesheet">` injected into
  `<head>` and wrapped with a body-level class `.qwenpaw-theme-<id>` so rules
  only match when the theme is active. Themes MUST scope selectors under that
  class — lint-enforced (see §10).

**Where themes come from (Stage 1):**

1. **Built-in**: bundled under `console/src/themes/<id>/{theme.json,theme.css}`
   and discovered via `import.meta.glob` at build time — same pattern already
   used by `dynamicModuleRegistry.ts`.
2. **User-supplied**: dropped into the backend plugin dir as a plugin of kind
   `"theme"` (reuses the existing `/api/plugins` machinery — see §7).

**Runtime data flow:**

```
┌─────────────┐   selected theme id    ┌────────────────┐
│ Settings UI │ ─────────────────────► │ ThemeContext   │
└─────────────┘                        │ (extended)     │
                                       └───────┬────────┘
                                               │ tokens + css url
                                               ▼
                            ┌──────────────────────────────────┐
                            │ <ConfigProvider theme={...tokens}│
                            │ algorithm={…}/>                  │
                            │ <link rel=stylesheet href=css/>  │
                            │ <html class="qwenpaw-theme-…">   │
                            └──────────────────────────────────┘
```

### 5.2 Stage 2 — Themed component slots (follow-up)

Add a thin `<Slot name="…">default</Slot>` primitive. Themes may register
renderers for an **allow-listed** set of slots — initially:

| Slot id          | Intent                              |
|------------------|--------------------------------------|
| `login.background` | Full-bleed background on `/login`  |
| `sidebar.header`   | Top of the sidebar (logo area)     |
| `welcome.hero`     | Chat welcome-screen hero block     |
| `button.primary`   | Optional restyle wrapper for CTA   |

The allow-list is deliberately short and lives in host code. A theme targeting
a slot that does not exist is ignored with a console warning — themes cannot
inject arbitrary DOM wherever they like.

Implementation reuses the existing plugin registry shape:

```ts
window.QwenPaw.registerThemeSlots("solarized", {
  "login.background": LoginBg,
  "sidebar.header":   Logo,
});
```

### 5.3 Stage 3 — Full skin plugin (future)

A theme may ship as a standard plugin bundle (same loader as today's
`registerRoutes` flow) that brings its own React components for slots plus
tokens and CSS. Nothing new needs to be invented — it is Stage 1 + Stage 2
packaged through the existing plugin system.

## 6. Proposed Code Changes (Stage 1 PR)

Deliberately small. Intended diff shape:

| File | Change |
|---|---|
| `console/src/contexts/ThemeContext.tsx` | Extend value with `activeThemeId`, `availableThemes`, `setTheme(id)`. Existing light/dark/system API is unchanged. |
| `console/src/themes/index.ts` **(new)** | Glob-based registry of built-in themes (mirrors `dynamicModuleRegistry.ts` pattern). |
| `console/src/themes/default/theme.json` **(new)** | Formalises today's default palette as a theme — baseline for authors. |
| `console/src/themes/__builtins__/` **(new, optional)** | One or two starter themes to prove the contract (e.g. "High Contrast"). |
| `console/src/App.tsx` | Feed `activeTheme.tokens` into `<ConfigProvider theme.token>`; inject `<link>` for `activeTheme.css`; toggle `html.qwenpaw-theme-<id>` class. |
| `console/src/pages/Settings/Appearance/index.tsx` **(new)** | New settings page: mode (light/dark/system) + theme picker. Add to sidebar in `console/src/layouts/Sidebar.tsx`. |
| `console/src/components/ThemeToggleButton/index.tsx` | Extend dropdown with a "More themes…" item linking to `/settings/appearance`; the existing light/dark/system control stays. Alternative: leave untouched and put the full picker only in Settings. |
| `console/src/themes/loader.ts` **(new)** | Validates manifests (zod schema), resolves CSS URLs, exposes hooks. |
| `console/src/locales/{en,zh,ja,ru}.json` | Add `appearance.*` keys for the new page (title, subtitle, "Default theme", preview alt-text). |
| `console/docs/design/theme-system.md` | This document. |

Estimated: ~400–600 lines additive, zero changes to existing behaviour when
`activeThemeId === "default"`.

### 6.1 API sketch

```ts
// console/src/themes/types.ts
export interface ThemeManifest {
  id: string;
  name: string;
  version: string;
  mode: "light" | "dark" | "auto";
  tokens?: Partial<AliasToken>;      // AntD token subset
  css?: string;                      // relative to manifest dir
  preview?: string;                  // screenshot for the picker
}

// console/src/contexts/ThemeContext.tsx (extended)
interface ThemeContextValue {
  themeMode: ThemeMode;              // unchanged
  isDark: boolean;                   // unchanged
  setThemeMode: (m: ThemeMode) => void;
  toggleTheme: () => void;

  /** NEW */
  activeThemeId: string;                     // "default" if unset
  availableThemes: ThemeManifest[];
  setTheme: (id: string) => void;
}
```

### 6.2 Packaging a theme

```
my-theme-pack/
├── plugin.json          { "id": "my-theme-pack", "kind": "theme",
│                          "entry": { "themes": "themes/index.json" } }
└── themes/
    ├── index.json       [ "solarized", "gruvbox" ]
    ├── solarized/
    │   ├── theme.json
    │   ├── theme.css
    │   └── preview.png
    └── gruvbox/
        └── theme.json
```

Backend change in Stage 1 is minimal: the existing plugin directory scan in
`src/qwenpaw/app/routers/plugins.py` already serves static files under
`/api/plugins/{id}/files/…`. The frontend theme loader fetches
`themes/index.json` from any plugin whose manifest declares `kind: "theme"`.
(A `kind` field is a trivial addition to `plugin.json`; the loader falls back
gracefully if absent.)

## 7. Discovery & Configuration

1. On app start, `ThemeContext` resolves `availableThemes` by merging:
   - Built-ins (via `import.meta.glob` over `src/themes/**/theme.json`).
   - Themes from plugins with `kind: "theme"` (fetched once in parallel with
     `loadAllPlugins()`).
2. User's selected `activeThemeId` is persisted in
   `localStorage["qwenpaw-active-theme"]` (alongside the existing
   `"qwenpaw-theme"` key for light/dark).
3. `Settings → Appearance` renders a grid of theme cards (preview + name) and
   a light/dark/system switch.
4. If the stored id cannot be resolved (e.g. plugin uninstalled), the system
   silently falls back to `"default"`.

## 8. Security Considerations

The Console already executes plugin JavaScript from the backend's own origin,
so adding CSS is a strict subset of the existing trust boundary. Still:

- **No remote URLs.** Theme CSS and preview assets must be served by the
  backend (same-origin). The loader rejects absolute-URL `css` fields.
- **CSS scoping.** A lint rule / runtime check requires every top-level
  selector in a theme CSS to start with `.qwenpaw-theme-<id>` or `:where`
  wrapping the same. Unscoped themes are rejected in dev and warned in prod.
- **Token allow-list.** The loader strips any `tokens` key not in AntD's known
  token set to prevent themes from stuffing arbitrary objects into
  `ConfigProvider`.
- **No `<script>` in Stage 1.** The Stage 1 contract deliberately has no JS
  hook. JS arrives in Stage 2 via the allow-listed slot API, not raw DOM.
- **CSP note.** The injected `<link>` uses a same-origin URL; no inline
  `<style>` is required.

## 9. Compatibility & Migration

- **Zero-change default.** With `activeThemeId = "default"`, tokens and CSS
  match today's output byte-for-byte. `ThemeContext`'s existing shape is
  preserved; fields are added, none removed.
- **Dark mode.** Continues to work exactly as today — the `html.dark-mode`
  class and `layout.css` remain untouched. A theme whose `mode` is `"dark"`
  simply forces that class; themes with `"auto"` defer to user preference.
- **`layout.css` debt.** Not cleaned up by this PR. A follow-up could migrate
  chunks of it into the default theme's `theme.css` under a scoped class, but
  that is a separable refactor (see §11).

## 10. Testing & Review Plan

Sized to keep the reviewer's load small.

- **Unit**: manifest validation (zod), CSS-selector scoping rule, fallback
  behaviour when a theme id is missing.
- **Smoke**: one Playwright/Vitest-jsdom test that mounts `<App>` with each
  built-in theme and asserts the `html` class + injected `<link>`.
- **Manual checklist** for reviewers (added to the PR description):
  - [ ] Default theme unchanged visually (diff screenshots).
  - [ ] Toggling light ↔ dark still works with each built-in theme.
  - [ ] Dropping an example theme plugin into the plugins dir makes it
        appear in the Settings picker without a rebuild.
  - [ ] Removing that plugin at runtime falls back to default without error.
  - [ ] `eslint` passes (incl. the new CSS-scoping rule).
  - [ ] `cd console && npm run format` clean; commit message follows
        `feat(console): …` per CONTRIBUTING.md §Commit message format.

## 11. Open Questions

1. **Should the default palette live inside `@agentscope-ai/design` instead of
   being re-declared here?** Leaning yes, as a later cleanup — for Stage 1 we
   treat `bailianTheme` as the upstream and only override via tokens.
2. **Do we want per-user theming on multi-user deployments**, or is
   `localStorage` sufficient? Simplest answer: localStorage for now; later,
   persist via the existing user-settings API if/when multi-user lands in
   scope for the console.
3. **Preview-before-apply UX.** Stage 1 applies immediately on pick. If users
   ask for "preview then save", we can add a staged `pendingThemeId`
   state without changing the loader contract.
4. **Slot allow-list for Stage 2** — which slots first? Proposal: start with
   `login.background`, `sidebar.header`, `welcome.hero` (three user-visible,
   low-risk surfaces). More can be added case by case.
5. **Dark-mode CSS migration.** Worth opening a separate issue to gradually
   move `layout.css` dark overrides behind scoped theme CSS — tracked, not
   blocked on.

## 12. Why this shape is easy to review

- **Additive**: every change is behind an opt-in id; default path is
  unmodified.
- **Leverages existing primitives**: `ThemeContext`, `ConfigProvider`,
  `import.meta.glob`, and the plugin loader are all reused, not duplicated.
- **Small surface for Stage 1**: a single new settings page, one new context
  field, one new themes directory, one zod schema. Roughly 400–600 lines.
- **Bounded blast radius**: a broken theme only affects users who select it;
  the shell, routing, and auth layers are untouched.
- **Clear extension path**: Stage 2/3 are explicitly deferred, so the first
  PR is not weighed down by speculative API.

## 13. Appendix: Example default-theme manifest

```json
{
  "id": "default",
  "name": "QwenPaw Default",
  "version": "1.0.0",
  "mode": "auto",
  "tokens": {
    "colorPrimary": "#FF7F16"
  }
}
```

Matches the current hard-coded `colorPrimary` in
`console/src/App.tsx:180` — this is the migration foothold for the whole
system.
