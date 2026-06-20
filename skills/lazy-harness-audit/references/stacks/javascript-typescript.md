# JavaScript / TypeScript Stack Checklist

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

**Markers**: `package.json`, `tsconfig.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, framework configs (`vite.config.*`, `next.config.*`, `nuxt.config.*`, `vue.config.*`).

**Verification surfaces** (rubric §2):
- `package.json` scripts: `test`, `lint`, `typecheck`, `build`, `check`, `e2e`.
- Test runners: `vitest`, `jest`, `mocha`, `playwright`, `cypress`.
- Type: `tsc --noEmit`, `vue-tsc`, `astro check`.
- Lint/format: `eslint`, `biome`, `prettier`.

**Architecture fitness** (rubric §3):
- `dependency-cruiser`, `eslint-plugin-boundaries`, `eslint-plugin-import` rules for layering.
- Public API surface: `.d.ts` exports, `api-extractor`, `publint`.

**Behavior harness** (rubric §4):
- Component/UI tests (`@testing-library/*`), visual regression (`storybook` + `chromatic`, `playwright` snapshots).
- E2E flows under `e2e/` or `tests/e2e/`.

**Safety tooling** (rubric §5):
- `npm audit`, `pnpm audit`, `osv-scanner`, Snyk.
- CSP / lockfile policy, secret scanning, supply-chain pinning (`npm ci`, integrity hashes).

**Priority notes**:
- Distinguish "frontend" from "Node service" — both are JS/TS but have different behavior harness expectations (browser flows vs HTTP/CLI flows).
