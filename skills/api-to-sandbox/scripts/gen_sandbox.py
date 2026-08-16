#!/usr/bin/env python3
"""Generate a GUARDED sandbox scaffold from an OpenAPI spec.

Turns "here is an API" into "here is a safe box a learner can run code in":

  * sandbox.config.yaml  -- the three guardrails from the article (timeout,
    resource caps, network egress allowlist) plus extra hardening, with the
    allowlist auto-derived from the spec's server hosts;
  * run.sh               -- maps that config to real `docker run` flags, so the
    guardrails are actually enforced, not just documented;
  * Dockerfile           -- minimal, non-root, hardened base image;
  * sandbox_setup.py     -- client init that reads auth from env / OAuth2
    injection (never a hardcoded secret), derived from the spec's securitySchemes;
  * requirements.txt.

Deterministic. Reads the spec, never calls the API. OpenAPI **JSON** in (convert
YAML first, e.g. with `yq -o=json`). Stdlib only.

Usage:
    python gen_sandbox.py openapi.json --out ./sandbox
    python gen_sandbox.py openapi.json --out ./sandbox --operation createTranscription
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"

# Secure-by-default resource envelope. Deliberately small; the point is a
# guardrail, not a workload.
DEFAULTS = {
    "timeout_seconds": 30,
    "cpus": "1",
    "memory": "512Mi",
    "disk": "256Mi",
}


def load_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(
            f"error: could not parse {path} as JSON ({e}).\n"
            "OpenAPI YAML is not supported directly — convert first, e.g.:\n"
            "    yq -o=json eval openapi.yaml > openapi.json",
            file=sys.stderr,
        )
        raise SystemExit(2)


def server_hosts(spec: dict) -> tuple[list[str], list[str]]:
    """Return (allowlist_hosts, warnings) from spec servers + oauth token URLs."""
    hosts: list[str] = []
    warnings: list[str] = []
    for srv in spec.get("servers", []) or []:
        url = srv.get("url", "")
        if not url:
            continue
        p = urlparse(url if "//" in url else "https://" + url)
        if p.scheme == "http":
            warnings.append(f"server {url!r} uses http:// — force https for the sandbox.")
        if p.hostname:
            hosts.append(p.hostname)
    # OAuth2 token/authorization endpoints must also be reachable.
    for scheme in (spec.get("components", {}).get("securitySchemes", {}) or {}).values():
        for flow in (scheme.get("flows", {}) or {}).values():
            for key in ("tokenUrl", "authorizationUrl", "refreshUrl"):
                u = flow.get(key)
                if u:
                    h = urlparse(u).hostname
                    if h:
                        hosts.append(h)
    # de-dup, preserve order
    seen: set[str] = set()
    ordered = [h for h in hosts if not (h in seen or seen.add(h))]
    if not ordered:
        warnings.append("no server host found in spec — set the egress allowlist manually.")
    return ordered, warnings


def pick_auth(spec: dict) -> dict:
    """Choose an auth scheme and describe how to wire it from env / OAuth2."""
    schemes = spec.get("components", {}).get("securitySchemes", {}) or {}
    # preference: oauth2 > http bearer > apiKey > none
    def rank(s: dict) -> int:
        t = s.get("type")
        if t == "oauth2":
            return 0
        if t == "http" and s.get("scheme") == "bearer":
            return 1
        if t == "apiKey":
            return 2
        return 3

    if not schemes:
        return {"kind": "none"}
    name, scheme = min(schemes.items(), key=lambda kv: rank(kv[1]))
    t = scheme.get("type")
    if t == "oauth2":
        token_url = ""
        for flow in (scheme.get("flows", {}) or {}).values():
            token_url = flow.get("tokenUrl") or token_url
        return {"kind": "oauth2", "name": name, "token_url": token_url}
    if t == "http" and scheme.get("scheme") == "bearer":
        return {"kind": "bearer", "name": name}
    if t == "apiKey":
        return {"kind": "apikey", "name": name,
                "in": scheme.get("in", "header"), "param": scheme.get("name", "X-API-Key")}
    return {"kind": "other", "name": name, "type": t}


def auth_snippet(auth: dict) -> str:
    if auth["kind"] == "oauth2":
        return (
            "# Auth: OAuth2. The sandbox injects a short-lived token after the\n"
            "# learner clicks \"Connect account\". NEVER hardcode a token here.\n"
            f"# (token endpoint: {auth.get('token_url') or 'see API docs'})\n"
            "ACCESS_TOKEN = os.environ[\"ACCESS_TOKEN\"]\n"
            "auth_headers = {\"Authorization\": f\"Bearer {ACCESS_TOKEN}\"}"
        )
    if auth["kind"] == "bearer":
        return (
            "# Auth: HTTP Bearer. Token comes from the environment, not the code.\n"
            "ACCESS_TOKEN = os.environ[\"ACCESS_TOKEN\"]\n"
            "auth_headers = {\"Authorization\": f\"Bearer {ACCESS_TOKEN}\"}"
        )
    if auth["kind"] == "apikey":
        where = auth.get("in", "header")
        param = auth.get("param", "X-API-Key")
        if where == "header":
            return (
                "# Auth: API key in a header. Key comes from the environment.\n"
                "API_KEY = os.environ[\"API_KEY\"]\n"
                f"auth_headers = {{\"{param}\": API_KEY}}"
            )
        return (
            f"# Auth: API key in {where} '{param}'. Key comes from the environment.\n"
            "API_KEY = os.environ[\"API_KEY\"]\n"
            "auth_headers = {}  # attach API_KEY as a query param on each request"
        )
    return (
        "# No security scheme found in the spec. If the API needs auth, wire it\n"
        "# from os.environ / OAuth2 — never hardcode a secret.\n"
        "auth_headers = {}"
    )


def pick_operation(spec: dict, wanted: str | None) -> dict | None:
    """Pick a golden-path operation: the requested opId, else a simple GET."""
    candidates = []
    for path, item in (spec.get("paths", {}) or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            if not isinstance(op, dict):
                continue
            candidates.append({
                "path": path,
                "method": method.upper(),
                "operationId": op.get("operationId", ""),
                "required_params": [
                    p.get("name") for p in op.get("parameters", []) or []
                    if p.get("required")
                ],
            })
    if not candidates:
        return None
    if wanted:
        for c in candidates:
            if c["operationId"] == wanted:
                return c
        print(f"warning: operation {wanted!r} not found; using a default.", file=sys.stderr)
    # prefer a GET with the fewest required params
    gets = [c for c in candidates if c["method"] == "GET"]
    pool = gets or candidates
    return min(pool, key=lambda c: len(c["required_params"]))


def golden_path_snippet(spec: dict, op: dict | None) -> str:
    base = ""
    for srv in spec.get("servers", []) or []:
        base = srv.get("url", "")
        break
    base = base or "https://api.example.com"
    if op is None:
        return (
            f'BASE = "{base}"\n'
            "# No operation found in the spec; add your first call here.\n"
            "# r = requests.get(f\"{BASE}/...\", headers=auth_headers, timeout=10)\n"
        )
    params = "".join(f'\n    # required: {p}' for p in op["required_params"])
    method = op["method"].lower()
    return (
        f'BASE = "{base}"\n'
        f'# Golden path: {op["method"]} {op["path"]}'
        f'{" (" + op["operationId"] + ")" if op["operationId"] else ""}{params}\n'
        f'r = requests.{method}(f"{{BASE}}{op["path"]}", headers=auth_headers, timeout=10)\n'
        "r.raise_for_status()\n"
        "print(r.json())\n"
    )


def render(template: str, **kw) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for k, v in kw.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="OpenAPI spec as JSON")
    ap.add_argument("--out", required=True, help="Output directory for the sandbox scaffold")
    ap.add_argument("--operation", help="operationId to use as the golden path")
    ap.add_argument("--timeout", type=int, default=DEFAULTS["timeout_seconds"])
    ap.add_argument("--memory", default=DEFAULTS["memory"])
    ap.add_argument("--cpus", default=DEFAULTS["cpus"])
    ap.add_argument("--disk", default=DEFAULTS["disk"])
    args = ap.parse_args(argv)

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        print(f"error: spec not found: {spec_path}", file=sys.stderr)
        return 2
    spec = load_spec(spec_path)

    title = spec.get("info", {}).get("title", "API")
    hosts, warnings = server_hosts(spec)
    auth = pick_auth(spec)
    op = pick_operation(spec, args.operation)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    allowlist_yaml = "\n".join(f"      - {h}" for h in hosts) or "      # - api.example.com  # set me"
    run_hosts = ",".join(hosts) or "api.example.com"

    (out / "sandbox.config.yaml").write_text(render(
        "sandbox.config.yaml.tmpl",
        title=title, timeout=args.timeout, cpus=args.cpus,
        memory=args.memory, disk=args.disk, allowlist=allowlist_yaml,
    ), encoding="utf-8")
    (out / "sandbox_setup.py").write_text(render(
        "sandbox_setup.py.tmpl",
        title=title, auth_snippet=auth_snippet(auth),
        golden_path=golden_path_snippet(spec, op),
    ), encoding="utf-8")
    (out / "Dockerfile").write_text(render("Dockerfile.tmpl", title=title), encoding="utf-8")
    (out / "run.sh").write_text(render(
        "run.sh.tmpl", timeout=args.timeout, cpus=args.cpus,
        memory=args.memory, run_hosts=run_hosts,
    ), encoding="utf-8")
    (out / "requirements.txt").write_text("requests>=2.31\n", encoding="utf-8")

    print(f"sandbox scaffold written to {out}/")
    print(f"  API: {title}")
    print(f"  auth: {auth['kind']}")
    print(f"  egress allowlist: {', '.join(hosts) or '(none — set manually)'}")
    print(f"  golden path: {op['method'] + ' ' + op['path'] if op else '(none found)'}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
