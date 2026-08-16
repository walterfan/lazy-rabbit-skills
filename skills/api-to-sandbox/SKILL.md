---
name: api-to-sandbox
description: >-
  Use when you need to give a tutorial/notebook a safe, ready-to-run backend to
  execute against — generate a guarded sandbox scaffold from an OpenAPI spec:
  the three guardrails (timeout, resource caps, network egress allowlist) with
  the allowlist auto-derived from the spec's hosts, an env/OAuth2 auth scaffold
  that never hardcodes secrets, a hardened non-root Dockerfile, a run.sh that
  actually enforces the limits, and a golden-path first call. The runtime
  provider of the living-tutorial skill family (feeds tutorial-to-notebook and
  code-tutor).
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - sandbox
  - openapi
  - security
  - developer-experience
  - containers
category: dev-tools
use_cases:
  - "Scaffold a guarded sandbox from an OpenAPI spec"
  - "Derive a network egress allowlist from an API's server hosts"
  - "Generate an env/OAuth2 auth setup with no hardcoded secrets"
  - "Produce a hardened, non-root Dockerfile + enforced run.sh for a tutorial box"
platforms:
  - claude-code
  - docker
visibility: public
---

# api-to-sandbox

Turn "打开就能用" from a promise into a safe reality. Given an API spec, generate
the box a learner runs tutorial code in — pre-wired with auth and, crucially,
**fenced in** so it can't hang the host, burn resources, or become someone's free
crypto miner.

This is the runtime half of the living-tutorial family. `tutorial-to-notebook`
writes the cells; this skill provides the guarded environment those cells execute
in; `code-tutor` may run a candidate fix — but only safe inside *this* sandbox.

> The article's rule, made concrete: a sandbox without **timeout + resource caps
> + network allowlist** is not a convenience, it is a liability. These three are
> not optional. This skill generates them by default and refuses to pretend a
> bare container is a sandbox.

## What it generates

Into an output directory:

| File | Purpose |
|---|---|
| `sandbox.config.yaml` | The guardrails: timeout, cpu/mem/disk caps, **default-deny** egress allowlist (auto-filled from the spec's hosts), read-only root, non-root user, dropped caps, ephemeral lifecycle |
| `run.sh` | Maps that config to real `docker run` flags — so the limits are *enforced*, not just documented |
| `Dockerfile` | Minimal `python:slim`, non-root user, no secrets baked in |
| `sandbox_setup.py` | Client init + auth from env/OAuth2 + the golden-path first call |
| `requirements.txt` | Just what the golden path needs |

## Ask First (only if it changes the output)

- **Auth reality**: does the sandbox get an OAuth2-injected token, or will the
  learner paste their own key at runtime? (Both are fine; neither is hardcoded.)
- **Resource envelope** if the defaults (30s / 1 CPU / 512Mi / 256Mi disk) don't
  fit the API's real needs (e.g. large file processing).
- **Golden-path operation** if the spec is large — which single call should the
  first run make?

If the spec is small and self-evident, infer and proceed.

## Workflow

### 1. Generate the scaffold

From the skill root (OpenAPI must be JSON — convert YAML first with
`yq -o=json eval spec.yaml > spec.json`):

```bash
python scripts/gen_sandbox.py <openapi.json> --out ./sandbox
# choose the first call explicitly:
python scripts/gen_sandbox.py <openapi.json> --out ./sandbox --operation createTranscription
# override the envelope:
python scripts/gen_sandbox.py <openapi.json> --out ./sandbox --memory 1Gi --timeout 60
```

The generator, without ever calling the API:

- derives the **egress allowlist** from `servers[].url` and any OAuth2
  token/authorization URLs (so auth still works under default-deny);
- picks the **auth scheme** (oauth2 > http bearer > apiKey) and writes an
  env-based snippet — **no secret in the code**;
- picks a **golden-path** operation (the requested opId, else the simplest GET);
- **warns** on `http://` servers and missing hosts.

### 2. Fill the real details

The scaffold is a correct skeleton; make it real:

- Replace golden-path path/query placeholders with real values (or a sandbox
  fixture, like a bundled `sample.wav`).
- Confirm the auth env var name matches what your OAuth broker injects
  (`ACCESS_TOKEN` / `API_KEY`).
- If the allowlist is empty (no `servers` in the spec), fill it by hand — do not
  ship a default-allow sandbox.

### 3. Wire enforcement (the part people skip)

Read `references/sandbox-security.md`. The config only protects anyone if the
runtime enforces it:

- Create the locked-down network once (`docker network create --internal ...`
  plus firewall rules limited to the allowlisted hosts).
- Use the generated `run.sh` (it sets `--cpus --memory --pids-limit --read-only
  --tmpfs --cap-drop ALL --security-opt no-new-privileges --user 1000` and wraps
  the process in `timeout`).
- Keep the container **ephemeral** — destroy it after the session.

### 4. Validate

Run the checks in Verification. Confirm the generated Python parses, the
Dockerfile builds (if Docker is available), and the config's allowlist is
non-empty and default-deny.

## Security (this skill's whole reason to exist)

- **The three guardrails are mandatory**: timeout, resource caps, network
  egress allowlist. Never generate or bless a sandbox missing any of them.
- **Default-deny egress.** Allow only the API's own hosts (+ OAuth endpoints).
- **No secret in code or image.** Auth is env/OAuth2 injected at run time and
  rotatable. If a spec embeds an example key, drop it and warn.
- **HTTPS only.** Warn and fix any `http://` server.
- **Non-root, read-only root, dropped caps, no-new-privileges, ephemeral.** These
  are defaults, not upsells.
- The generator itself never calls the API or executes generated code.

## Verification

Block delivery until:

- `sandbox.config.yaml` has a non-empty, **default-deny** egress allowlist.
- All three guardrails (timeout, cpu/mem, network) are present.
- `sandbox_setup.py` parses (`python -m py_compile`) and contains **no** literal
  secret (only `os.environ[...]`).
- The Dockerfile runs as a non-root user and bakes in no token.
- `run.sh` enforces the caps that `sandbox.config.yaml` declares (they agree).
- Any `http://` server was flagged and switched to https.

Warn, but still deliver:

- Spec had no `servers` → allowlist must be filled by hand (say so loudly).
- No securityScheme found → auth left as a TODO from env (say so).
- Docker not available to test the build (structural checks only).

## Delivery Summary

- Output dir and files written.
- API title, chosen auth kind, egress allowlist hosts.
- Golden-path operation chosen.
- Any warnings (http servers, empty allowlist, embedded example secrets removed).
- Whether the image was actually built or only structurally checked.

## Skill Family

- **`tutorial-to-notebook`** writes the cells; this sandbox is where they run.
  Keep the auth env-var name consistent between the two.
- **`code-tutor`** may execute a candidate fix — only ever inside this guarded
  box, and only for safe/idempotent actions.
- **`tour-builder`** is the UI-page counterpart (interactive guidance instead of
  a code runtime).

## Resources

- Generator: `scripts/gen_sandbox.py`
- Enforcement + threat notes: `references/sandbox-security.md`
- Templates: `templates/` (config, run.sh, Dockerfile, setup)

<!-- last_updated: 2026-07-31 -->
<!-- maintained-by: walter.fan -->
