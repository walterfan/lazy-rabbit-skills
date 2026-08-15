---
name: lazy-tls-doctor
description: >-
  Diagnose HTTPS/TLS certificate verification failures and assign blame to the
  server, the trust store, an intercepting proxy, or DNS. Use when the user hits
  certificate verify failed, unable to get local issuer certificate,
  CERTIFICATE_VERIFY_FAILED, SSLCertVerificationError, self signed certificate
  in certificate chain, hostname mismatch, x509 certificate signed by unknown
  authority, ERR_CERT_AUTHORITY_INVALID, PKIX path building failed, curl error
  60, or says "browser works but my code fails", "works locally but not in
  Docker/CI", "should I set verify=False". Also use for corporate proxy TLS
  interception (Zscaler, Netskope, Palo Alto, mitmproxy), missing intermediate
  certificates, CA bundle and trust store problems, and DNS-induced certificate
  mismatches. Triggers: 证书报错, 证书校验失败, 证书链, 中间证书, 代理劫持,
  信任库, 抓包代理. Prefer this over general network troubleshooting whenever
  certificates, TLS, or HTTPS trust is involved.
license: CC-BY-NC-ND-4.0
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - tls
  - ssl
  - certificate
  - openssl
  - proxy
  - mitm
  - dns
  - troubleshooting
category: ops-tools
platforms:
  - codex
  - claude-code
  - cursor
  - opencode
visibility: public
source: >-
  https://www.fanyamin.com/dig-nslookup-and-proxy-cert-failure.html
  https://www.fanyamin.com/2026-04-22-python-ssl-unable-to-get-local-issuer-certificate.html
---

# lazy-tls-doctor

Turn a red `certificate verify failed` into a specific verdict: **who is at fault, and what to change.**

Most people respond to this error by disabling verification. That makes the message disappear and quietly removes server authentication — the half of HTTPS that stops someone impersonating the server. This skill finds the actual cause instead, in a fixed order that avoids the usual wild-goose chases.

The method comes from two field write-ups:
[nslookup vs dig and proxy-induced cert failure](https://www.fanyamin.com/dig-nslookup-and-proxy-cert-failure.html) and
[unable to get local issuer certificate](https://www.fanyamin.com/2026-04-22-python-ssl-unable-to-get-local-issuer-certificate.html).

## Core principle

> Read the **issuer**, not the subject. The name on the certificate is usually correct — the question is who signed it, and whether the client can walk that signature back to a root it trusts.

Four causes produce nearly identical error text, and each needs a different fix:

| Cause | Tell-tale sign | Who fixes it |
|---|---|---|
| Proxy interception | Issuer is a company or security-vendor name | Trust store — install the proxy CA |
| Missing intermediate | Chain length 1, issuer is a real public CA | Server — serve fullchain |
| Untrusted private CA | Chain ends in an unknown self-signed root | Trust store — install that root |
| Wrong host reached | Hostname mismatch, valid cert for another name | DNS or routing |

Guessing between these is what turns a two-hour fix into a two-day one.

## Contract

- **scope_in**: diagnosing TLS/HTTPS certificate verification failures from a client's point of view; certificate chain inspection; trust store and CA bundle problems; corporate proxy / MITM interception detection; missing intermediate certificates; hostname mismatch; expired certificates; DNS cross-checks *when a certificate symptom points at reaching the wrong host*; per-runtime CA configuration (Python, Node, Go, Java, curl, git, Docker, JVM); reproducing interception locally for teaching or testing.
- **scope_out**: issuing or renewing certificates; ACME/Let's Encrypt automation; configuring a server's TLS stack beyond "serve the full chain"; cipher suite, TLS version, or protocol negotiation tuning; mTLS client-certificate authentication design; certificate transparency and revocation policy; general network reachability with no TLS symptom (use `lazy-network-doctor`); intercepting traffic the user is not authorised to intercept.
- **Preconditions**: shell access; `openssl` installed (the script says so if missing); the failing hostname and port are known; for full diagnosis, the ability to run commands *in the environment that is actually failing* — a laptop result does not speak for a container.
- **Postconditions**: the response names one primary cause with a confidence level; states which side must change (server, trust store, DNS, or client config); gives the exact command evidence behind the verdict; supplies a runtime-specific fix; and never proposes disabling verification as the resolution.

## Execution

### Phase 0: Classify the request

Pick one mode:

- `diagnose` — a specific host is failing and the cause is unknown (default)
- `explain` — the user pasted an error and wants to understand it
- `chain` — inspect what a server actually sends
- `trust` — "browser works, code fails" / container / CI trust store problems
- `dns` — certificate names a different host than expected
- `lab` — reproduce interception locally to learn or demo

If the user only pasted an error string, start with `explain`, then offer `diagnose`.

### Phase 1: Get the evidence

Entry: a hostname (and port) is known.

```bash
python3 scripts/tls_doctor.py diagnose api.example.com
```

This runs the whole ordered method: chain inspection, verification, DNS cross-check, trust store survey, and a verdict. Useful variants:

```bash
# Suspect a specific interception CA — this is the conclusive test
python3 scripts/tls_doctor.py diagnose api.example.com --proxy-ca /path/to/corp-ca.pem

# Behind an explicit proxy
python3 scripts/tls_doctor.py diagnose api.example.com --proxy 10.0.0.1:8080

# Compare resolvers when a hostname mismatch shows up
python3 scripts/tls_doctor.py diagnose api.example.com --resolver 8.8.8.8

# Machine-readable, for CI gates
python3 scripts/tls_doctor.py diagnose api.example.com --json
```

Exit codes: `0` verification succeeded, `1` verification failed, `2` tooling problem.

Exit criteria: a verdict with a blame target.
On fail (script unusable): fall back to the raw commands in [references/command-playbook.md](references/command-playbook.md) and interpret manually.

### Phase 2: Confirm the verdict before acting

Do not stop at the label — confirm it, because the fixes are mutually exclusive.

**If `intercepted`:** the issuer names a company or security vendor. Confirm with `--proxy-ca`: if that CA verifies the chain, the proxy signed it, full stop. Then the work is trust-store configuration, not server changes.

**If `incomplete-chain`:** the server sent leaf-only but the issuer is a public CA. Confirm by fetching the intermediate and verifying offline:

```bash
openssl verify -untrusted intermediate.pem leaf.pem
```

Fix on the server (`fullchain.pem`, not `cert.pem`). This one fix serves every client, so prefer it over patching each caller.

**If `hostname-mismatch`:** the certificate is real but for another name. Move to DNS — you are probably reaching a different host than intended:

```bash
python3 scripts/tls_doctor.py dns api.example.com --resolver 8.8.8.8
```

Check `/etc/hosts` explicitly. Both `dig` and `nslookup` bypass it while your application does not, so they can disagree with the program. The script reports this as `hosts_override`.

**If `untrusted-root` / `self-signed`:** decide deliberately whether that CA should be trusted. If yes, install it. If you cannot identify who owns it, treat interception as a live possibility and escalate rather than trusting it.

### Phase 3: Fix on the correct side

Entry: verdict confirmed.

Priority order, because it minimises total work and risk:

1. **Server-side** (missing intermediate, expired cert) — one fix helps every client.
2. **Trust store** (proxy CA, private root) — install the CA where the failing runtime looks.
3. **Explicit CA file** (short-term) — pass the CA to the one caller that needs it.
4. **Disabling verification** — not a fix. Acceptable only for a throwaway local reproduction, never committed.

Runtimes read different trust stores, which is exactly why a browser succeeds while code fails:

```bash
python3 scripts/tls_doctor.py truststore
```

Per-runtime commands are in [references/runtime-trust-stores.md](references/runtime-trust-stores.md).

### Phase 4: Report

Use this shape:

```
Symptom  : the error and where it appears
Evidence : chain length, issuer, verify code, DNS/trust-store findings
Verdict  : one primary cause + confidence
Blame    : server | trust store | DNS | client config
Fix      : the specific change, on the side that owns it
Verify   : the command that should now succeed
```

Keep the evidence compact — the issuer line and verify code usually carry the whole argument.

### Resilience

- **openssl missing** → say so and give the install command; do not silently degrade to a weaker check.
- **dig missing** → the DNS comparison still reports the application view via `getaddrinfo`; note the reduced coverage.
- **Host unreachable** → stop and report a network problem. Do not speculate about certificates when no certificate was received.
- **Ambiguous issuer** (unknown private CA, could be corporate or hostile) → report `medium` confidence, state both readings, and ask the user to identify the CA owner before installing it.
- **Diagnosis run in the wrong environment** → if the user reports a container/CI failure but ran the check on a laptop, flag that the result may not transfer and ask them to re-run inside the failing environment.

## Verification

### Hard gates

| Gate | Condition | On fail |
|---|---|---|
| Evidence before verdict | Every claim traces to command output shown to the user | Re-run the command and quote it; never assert a cause from intuition |
| Single primary cause | Exactly one cause is named, with confidence | If genuinely ambiguous, say so explicitly and give the disambiguating command |
| Blame is actionable | Verdict names which side must change | Re-examine chain length + issuer; those two decide it |
| No insecure fix | `verify=False`, `-k`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `InsecureSkipVerify` never proposed as the resolution | Replace with the trust-store fix; mention insecure flags only as labelled temporary reproduction |
| Right environment | Diagnosis ran where the failure happens | Warn that laptop results do not speak for containers/CI |

### Soft gates

| Gate | Condition | On fail |
|---|---|---|
| Runtime-specific fix | Fix matches the user's actual stack | Give the generic fix and ask which runtime |
| Verification step | A command is offered to confirm the fix worked | Add the re-run command |
| Hostname check honoured | Name validation was part of the check | Note that `s_client` skips it without `-verify_hostname` |
| Brevity | Evidence is summarised, not dumped wholesale | Trim to issuer, chain length, verify code |

### Correctness notes worth preserving

These are easy to get wrong and were verified against live hosts while building this skill:

- `openssl s_client` **does not validate the hostname by default.** `-servername` only sends SNI. Without `-verify_hostname`, a certificate issued for an unrelated host still prints `Verify return code: 0 (ok)`. The bundled script always passes it, which is why it agrees with curl and browsers.
- `dig` **returns exit code 0 on NXDOMAIN.** It reports success for "the query completed", not "a record exists". Test the output, not the exit status.
- `openssl s_client` prints `CONNECTED` and even `Verification: OK` when the handshake produced no certificate at all. Treat "no peer certificate available" as a connection failure, not a passing check.

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---|---|---|
| Verdict says trust store, but installing the CA does not help | The application reads a different bundle than the one updated | Run `truststore`; check `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `NODE_EXTRA_CA_CERTS`, and container images separately |
| "Fixed" by disabling verification, breaks again later | Root cause never addressed; authentication silently off | Re-diagnose; treat the earlier change as an open security issue |
| Diagnosis says OK, application still fails | Checked from the wrong environment or with a different trust store | Re-run inside the failing container/CI job |
| Called interception, was actually a missing intermediate | Judged on the error code alone | Chain length + whether the issuer is a public CA is the discriminator |
| Chain looks fine but the name is wrong | Reached a different host than intended | Compare resolvers and `/etc/hosts`; both DNS tools bypass the hosts file |
| Endless certificate debugging on a dead port | Nothing is listening or the port is not TLS | Confirm reachability first; `no-connection` means stop |

### Boundary examples

- **Only an error string, no host**: explain the error and the likely causes, then ask for the hostname to diagnose. Do not guess a verdict.
- **Internal host unreachable from here**: give the exact commands to run inside the failing environment and explain how to read the output; do not diagnose remotely by assumption.
- **Self-signed certificate in a dev environment**: report it plainly and ask whether it is intended before recommending anything.
- **User asks to intercept traffic they do not own**: refuse; the lab exists for local reproduction on hosts the user controls.
- **Edge of scope**: request mixes cert failure with general packet-level debugging → handle the certificate half, hand the rest to `lazy-network-doctor`.
- **Out of scope**: "renew my certificate" or "set up ACME" → say it is out of scope and point to the CA's own tooling.

### Improvement triggers

- A verdict is wrong more than occasionally → revisit the classifier's issuer heuristics in `scripts/tls_doctor.py`.
- A new interception vendor appears in the field → add it to `INTERCEPTOR_HINTS`.
- Users repeatedly ask about a runtime not covered → extend `references/runtime-trust-stores.md`.
- OpenSSL output format changes across a major version → re-check the chain parser against the new format.

## Resources

- [references/command-playbook.md](references/command-playbook.md) — raw commands, error-code table, and how to read chain output when the script is unavailable
- [references/runtime-trust-stores.md](references/runtime-trust-stores.md) — where each runtime looks for CAs, and how to install one properly
- `scripts/tls_doctor.py` — `diagnose`, `chain`, `verify`, `dns`, `truststore`, `lab`
