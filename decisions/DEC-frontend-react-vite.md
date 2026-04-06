# DEC-frontend-react-vite

**Status**: Approved  
**Decision Type**: Technology  
**Made By**: human-decided  
**Date**: 2026-04-06

## Decision

The LeanDeep 6.0 frontend uses **React + TypeScript + Vite** as its technology stack. The frontend is a separate application in `3-code/frontend/`, with a Vite dev server proxying API calls to FastAPI (port 8420). Production builds output static assets served by FastAPI or deployed independently.

## Context

The v6.0 UI requires complex interactive features:
- Bidirectional marker-narrative linking (click narrative -> highlight markers, click marker -> show narratives)
- Dynamic narrative tabs with state management
- Real-time text highlighting with confidence-based coloring
- Searchable/filterable marker library sidebar
- Responsive design with WCAG AA accessibility

The existing frontend (`api/static/*.html`) uses inline vanilla JS. While functional for simpler UIs (playground, resonanzraum), the v6.0 interactive visualization requires component-based state management that vanilla JS handles poorly at scale.

## Stack

- **React 18+** — component model, hooks for state management
- **TypeScript** — type safety, IDE support
- **Vite** — fast dev server, HMR, production bundler
- **Location**: `3-code/frontend/`
- **Dev proxy**: Vite proxies `/v1/*` and `/api/*` to `http://localhost:8420`
- **Production**: `npm run build` outputs to `dist/`, served by FastAPI or CDN

## Alternatives Considered

1. **Vanilla JS (extend existing)** — matches current pattern, zero build tooling. Rejected: state management for narrative-marker linking would be brittle and hard to maintain.
2. **Vue/Svelte** — viable but React has larger ecosystem and team familiarity assumed.

## Consequences

**Positive**:
- Clean component architecture for complex UI state
- TypeScript catches errors at build time
- Vite provides fast dev iteration (HMR)
- Large ecosystem for accessibility, testing, animation

**Negative**:
- New build pipeline (Node.js required in dev environment)
- Deployment must include build step (Docker, CI/CD)
- More files and abstractions than inline HTML

## Enforcement

- Frontend code lives in `3-code/frontend/`, not `api/static/`
- All new UI features use React components
- Existing `api/static/*.html` pages remain as legacy (not migrated unless needed)

## Traceability

- REQ-USA-interactive-visualization
- TASK-interactive-visualization-ui (decomposed into subtasks)
