# Web App

This folder now contains the rebuilt React web shell for:

- tenants,
- landlords,
- agencies,
- admins/reviewers.

Current scope in the first web slice:

- Vite-based app scaffold,
- session-aware auth wiring against `/api/v1/auth`,
- public and protected route skeletons,
- internal operations and security placeholder surfaces,
- design system and layout shell for future feature pages.

Notes:

- The app is intentionally foundation-first and still uses placeholder feature pages where full product flows are not yet built.
- The local workspace Node runtime is older than the intended long-term frontend runtime, so this slice is verified with source-level syntax checks and repo tests rather than a full Vite build.
