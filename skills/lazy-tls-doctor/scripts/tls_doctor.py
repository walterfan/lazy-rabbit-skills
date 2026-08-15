#!/usr/bin/env python3
"""tls_doctor.py — diagnose HTTPS certificate verification failures.

Answers one question: WHY does certificate verification fail, and WHOSE fault is it?

Subcommands:
  chain      Inspect the certificate chain a server actually sends
  verify     Verify against a CA bundle (system default or explicit)
  diagnose   Full workflow: chain + verify + DNS + trust store -> verdict
  dns        Compare resolvers to detect hijack/split-horizon DNS
  truststore Show which CA bundle each runtime uses
  lab        Generate a local MITM-proxy lab to reproduce the failure

Exit codes: 0 = verification OK, 1 = verification failed, 2 = tool/usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Any

DEFAULT_TIMEOUT = 10

# OpenSSL X509_V_ERR_* codes worth explaining. Source: openssl/x509_vfy.h
VERIFY_ERRORS: dict[int, dict[str, str]] = {
    10: {
        "name": "certificate has expired",
        "meaning": "A certificate in the chain is past its notAfter date.",
        "blame": "server",
        "fix": "Renew the certificate. Check notAfter on every chain element, not just the leaf.",
    },
    18: {
        "name": "self signed certificate",
        "meaning": "The leaf certificate signed itself; there is no chain at all.",
        "blame": "server-or-trust",
        "fix": "Expected in test environments and on appliances. For production, issue a properly signed cert; to accept deliberately, pin it via an explicit CA file.",
    },
    19: {
        "name": "self signed certificate in certificate chain",
        "meaning": "The chain ends in a self-signed root that is not in your trust store.",
        "blame": "trust",
        "fix": "A private CA is in play. Install that root into the runtime's trust store.",
    },
    20: {
        "name": "unable to get local issuer certificate",
        "meaning": "Cannot find the issuer of some certificate in the chain.",
        "blame": "ambiguous",
        "fix": "Either a proxy is intercepting (unknown issuer) or the server omitted intermediates. Check the issuer name and chain length to tell which.",
    },
    21: {
        "name": "unable to verify the first certificate",
        "meaning": "The leaf cannot be verified because the chain stops too early.",
        "blame": "server",
        "fix": "The server usually sent leaf-only. Serve fullchain.pem instead of cert.pem.",
    },
    62: {
        "name": "hostname mismatch",
        "meaning": "The certificate is valid but not issued for the name you requested.",
        "blame": "dns-or-server",
        "fix": "You may be connecting to the wrong host, or SNI was not sent. Compare DNS answers and check subjectAltName.",
    },
}

# Vendor tokens that strongly suggest a TLS-intercepting middlebox.
INTERCEPTOR_HINTS = [
    "zscaler", "netskope", "palo alto", "paloalto", "fortinet", "fortigate",
    "bluecoat", "blue coat", "symantec web", "forcepoint", "mcafee web",
    "sophos", "sonicwall", "checkpoint", "check point", "cisco umbrella",
    "mitmproxy", "charles", "fiddler", "burp", "proxyman",
    "screenos", "watchguard", "barracuda", "trend micro", "ssl inspection",
    "corporate proxy", "proxy root", "-proxy", "surfeasy",
]

# Well-known public CA organisations. Presence here means "probably not a MITM".
PUBLIC_CA_HINTS = [
    "let's encrypt", "isrg", "digicert", "sectigo", "comodo", "globalsign",
    "godaddy", "entrust", "identrust", "amazon", "google trust", "gts",
    "microsoft", "apple", "baltimore", "verisign", "thawte", "geotrust",
    "rapidssl", "buypass", "zerossl", "certum", "actalis", "quovadis",
    "starfield", "ssl.com", "cloudflare", "wotrus", "trustasia",
]


class ToolError(RuntimeError):
    """A required external tool is missing or misbehaving."""


def _run(cmd: list[str], stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as exc:
        raise ToolError(f"command not found: {cmd[0]}") from exc
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def _require_openssl() -> None:
    if not _have("openssl"):
        raise ToolError(
            "openssl not found. Install it (macOS: brew install openssl; "
            "Debian/Ubuntu: apt install openssl; RHEL: dnf install openssl)."
        )


# --------------------------------------------------------------------------
# certificate chain
# --------------------------------------------------------------------------

@dataclass
class ChainCert:
    depth: int
    subject: str
    issuer: str

    @property
    def self_signed(self) -> bool:
        return self.subject == self.issuer


@dataclass
class ChainResult:
    host: str
    port: int
    servername: str
    connected: bool = False
    certs: list[ChainCert] = field(default_factory=list)
    verify_code: int | None = None
    verify_text: str = ""
    not_before: str = ""
    not_after: str = ""
    sans: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def leaf(self) -> ChainCert | None:
        return self.certs[0] if self.certs else None

    @property
    def root_issuer(self) -> str:
        return self.certs[-1].issuer if self.certs else ""


def _s_client(
    host: str,
    port: int,
    servername: str,
    ca_file: str | None = None,
    proxy: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, str]:
    """Run openssl s_client.

    Note: -servername only *sends* SNI; it does not make openssl check that the
    certificate is valid for that name. -verify_hostname is required for that,
    otherwise a certificate issued for a completely different host still reports
    "Verify return code: 0 (ok)". Browsers and curl always check the name, so
    omitting this would make the tool disagree with them.
    """
    _require_openssl()
    cmd = [
        "openssl", "s_client", "-showcerts",
        "-servername", servername,
        "-verify_hostname", servername,
    ]
    if proxy:
        cmd += ["-proxy", proxy, "-connect", f"{host}:{port}"]
    else:
        cmd += ["-connect", f"{host}:{port}"]
    if ca_file:
        cmd += ["-CAfile", ca_file]
    rc, out, err = _run(cmd, stdin="", timeout=timeout)
    return rc, out + err


def _parse_chain(raw: str) -> tuple[list[ChainCert], int | None, str]:
    certs: list[ChainCert] = []
    # Chain lines look like: " 0 s:CN=host" followed by "   i:C=US, O=CA".
    pending: tuple[int, str] | None = None
    for line in raw.splitlines():
        m_s = re.match(r"\s*(\d+)\s+s:(.*)$", line)
        if m_s:
            pending = (int(m_s.group(1)), m_s.group(2).strip())
            continue
        m_i = re.match(r"\s*i:(.*)$", line)
        if m_i and pending is not None:
            certs.append(ChainCert(depth=pending[0], subject=pending[0] and pending[1] or pending[1], issuer=m_i.group(1).strip()))
            pending = None

    code: int | None = None
    text = ""
    m = re.search(r"Verify return code:\s*(\d+)\s*\((.*?)\)", raw)
    if m:
        code = int(m.group(1))
        text = m.group(2)
    return certs, code, text


def _leaf_details(raw: str) -> tuple[str, str, list[str]]:
    """Extract validity dates and SANs from the first PEM block."""
    m = re.search(
        r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", raw, re.S
    )
    if not m:
        return "", "", []
    pem = m.group(0)
    rc, out, _ = _run(
        ["openssl", "x509", "-noout", "-dates", "-ext", "subjectAltName"], stdin=pem
    )
    if rc != 0:
        return "", "", []
    nb = na = ""
    sans: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("notBefore="):
            nb = line.split("=", 1)[1]
        elif line.startswith("notAfter="):
            na = line.split("=", 1)[1]
        elif line.startswith("DNS:") or ", DNS:" in line:
            sans += [p.strip()[4:] for p in line.split(",") if p.strip().startswith("DNS:")]
    return nb, na, sans


def get_chain(
    host: str,
    port: int = 443,
    servername: str | None = None,
    ca_file: str | None = None,
    proxy: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ChainResult:
    sni = servername or host
    res = ChainResult(host=host, port=port, servername=sni)
    rc, raw = _s_client(host, port, sni, ca_file=ca_file, proxy=proxy, timeout=timeout)

    # openssl prints CONNECTED as soon as the TCP socket opens, and still reports
    # "Verification: OK" when the TLS handshake produced no certificate at all.
    # Treat the exchange as successful only when a peer certificate arrived.
    if "CONNECTED" not in raw or "no peer certificate available" in raw:
        res.error = _connect_error(raw, rc)
        return res

    certs, code, text = _parse_chain(raw)
    if not certs:
        res.error = _connect_error(raw, rc) or "server sent no certificate"
        return res

    res.connected = True
    res.certs, res.verify_code, res.verify_text = certs, code, text
    res.not_before, res.not_after, res.sans = _leaf_details(raw)
    return res


def _connect_error(raw: str, rc: int) -> str:
    if "timeout" in raw.lower() or rc == 124:
        return "connection timed out (host unreachable or port filtered)"
    low = raw.lower()
    if "name or service not known" in low or "nodename nor servname" in low or "getaddrinfo" in low:
        return "hostname could not be resolved (DNS failure)"
    if "connection refused" in low:
        return "connection refused (nothing is listening on that port)"
    if "no peer certificate available" in raw:
        return (
            "TCP connected but the TLS handshake returned no certificate — "
            "the port may not speak TLS, or a middlebox reset the connection"
        )
    for pat in (
        r"connect:(.*)$",
        r"socket:(.*)$",
        r"error:.*:(.*)$",
    ):
        m = re.search(pat, raw, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return f"could not establish TLS connection (openssl exit {rc})"


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

def _looks_like_interceptor(issuer: str) -> str | None:
    low = issuer.lower()
    for hint in INTERCEPTOR_HINTS:
        if hint in low:
            return hint
    return None


def _looks_public(issuer: str) -> bool:
    low = issuer.lower()
    return any(h in low for h in PUBLIC_CA_HINTS)


def classify(chain: ChainResult, proxy_ca_ok: bool | None = None) -> dict[str, Any]:
    """Turn raw chain facts into a blame verdict."""
    if not chain.connected:
        return {
            "verdict": "no-connection",
            "confidence": "high",
            "summary": f"Could not complete a TLS handshake: {chain.error}",
            "blame": "network",
            "next": [
                "Confirm the host and port are reachable (this is a network problem, not a certificate problem).",
                "If a proxy is required, retry with --proxy host:port.",
            ],
        }

    code = chain.verify_code
    issuer = chain.root_issuer
    depth = len(chain.certs)
    vendor = _looks_like_interceptor(issuer)
    public = _looks_public(issuer)

    if code == 0:
        return {
            "verdict": "ok",
            "confidence": "high",
            "summary": "Certificate verification succeeded against the trust store used for this check.",
            "blame": "none",
            "next": [
                "If an application still fails, it is not using this trust store — run the truststore subcommand.",
            ],
        }

    # Explicit proxy CA verified the chain: conclusive interception evidence.
    if proxy_ca_ok:
        return {
            "verdict": "intercepted",
            "confidence": "high",
            "summary": (
                f"A TLS-intercepting proxy is re-signing this connection. Issuer: {issuer!r}. "
                "The supplied proxy CA verified the chain, which proves the proxy signed it."
            ),
            "blame": "trust",
            "next": [
                "Install the proxy CA into the failing runtime's trust store (see truststore subcommand).",
                "Do not disable verification as the fix — that removes server authentication.",
            ],
        }

    if code == 62:
        return {
            "verdict": "hostname-mismatch",
            "confidence": "high",
            "summary": (
                f"The certificate is not valid for {chain.servername!r}. SANs: "
                f"{', '.join(chain.sans) if chain.sans else '(none found)'}."
            ),
            "blame": "dns-or-server",
            "next": [
                "Compare DNS answers across resolvers (dns subcommand) — you may be reaching the wrong host.",
                "Check /etc/hosts, which dig and nslookup both ignore.",
                "Verify the server serves the right certificate for this SNI.",
            ],
        }

    if code == 10:
        return {
            "verdict": "expired",
            "confidence": "high",
            "summary": f"A certificate in the chain has expired (leaf notAfter: {chain.not_after or 'unknown'}).",
            "blame": "server",
            "next": ["Renew the certificate and redeploy the full chain."],
        }

    if vendor:
        return {
            "verdict": "intercepted",
            "confidence": "high",
            "summary": (
                f"Issuer {issuer!r} matches a known interception product ({vendor!r}). "
                "Traffic is being decrypted and re-signed by a middlebox."
            ),
            "blame": "trust",
            "next": [
                "Obtain that CA certificate and install it into the failing runtime's trust store.",
                "Confirm by re-running with --proxy-ca <ca.pem>; verification should flip to OK.",
            ],
        }

    # Leaf-only chain: distinguish missing intermediates from an unknown private CA.
    if code in (20, 21) and depth <= 1:
        if public:
            return {
                "verdict": "incomplete-chain",
                "confidence": "high",
                "summary": (
                    f"The server sent only the leaf certificate, but its issuer {issuer!r} "
                    "is a public CA — the intermediate certificate is missing."
                ),
                "blame": "server",
                "next": [
                    "Fix on the server: serve fullchain.pem (leaf + intermediates), not cert.pem alone.",
                    "This affects every client, so fixing the server beats patching each caller.",
                ],
            }
        return {
            "verdict": "untrusted-issuer",
            "confidence": "medium",
            "summary": (
                f"The server sent a single certificate signed by {issuer!r}, which is not in the trust store "
                "and is not a recognised public CA. This is either a private CA or an interception proxy."
            ),
            "blame": "ambiguous",
            "next": [
                "If that issuer name belongs to your organisation, it is a private CA or proxy — install it.",
                "Re-run with --proxy-ca <ca.pem> to confirm which CA signed this chain.",
            ],
        }

    if code in (20, 21):
        if public:
            return {
                "verdict": "incomplete-chain",
                "confidence": "medium",
                "summary": (
                    f"Chain of {depth} certificate(s) ends at {issuer!r} and does not reach a trusted root. "
                    "An intermediate is likely missing or out of order."
                ),
                "blame": "server",
                "next": [
                    "Rebuild the server chain in leaf -> intermediate -> (optional root) order.",
                    "Verify locally: openssl verify -untrusted intermediate.pem leaf.pem",
                ],
            }
        return {
            "verdict": "untrusted-root",
            "confidence": "medium",
            "summary": f"Chain terminates at {issuer!r}, which the trust store does not recognise.",
            "blame": "trust",
            "next": [
                "Install that root into the runtime's trust store, or pass it explicitly via --ca-file.",
            ],
        }

    if code == 18:
        return {
            "verdict": "self-signed",
            "confidence": "high",
            "summary": (
                f"The server presented a self-signed certificate ({issuer!r}) with no chain above it."
            ),
            "blame": "server-or-trust",
            "next": [
                "Normal for test environments, appliances, and internal tooling.",
                "For production, issue a certificate from a CA the clients already trust.",
                "To accept it deliberately, pin that exact certificate rather than disabling verification.",
            ],
        }

    if code == 19 or (chain.certs and chain.certs[-1].self_signed):
        return {
            "verdict": "untrusted-root",
            "confidence": "medium",
            "summary": f"The chain ends in a self-signed root ({issuer!r}) that is not trusted locally.",
            "blame": "trust",
            "next": [
                "If this root belongs to your organisation, install it into the runtime's trust store.",
                "Otherwise treat it as untrusted — verify explicitly with --ca-file before accepting.",
            ],
        }

    info = VERIFY_ERRORS.get(code or -1)
    return {
        "verdict": "unverified",
        "confidence": "low",
        "summary": (
            f"Verification failed with code {code} ({chain.verify_text or 'unknown'})."
            + (f" {info['meaning']}" if info else "")
        ),
        "blame": info["blame"] if info else "unknown",
        "next": [info["fix"]] if info else ["Inspect the full chain manually with the chain subcommand."],
    }


# --------------------------------------------------------------------------
# DNS
# --------------------------------------------------------------------------

def _dig_short(name: str, server: str | None = None, timeout: int = 5) -> tuple[list[str], str]:
    if not _have("dig"):
        return [], "dig not installed"
    cmd = ["dig", "+short", f"+time={timeout}", "+tries=1"]
    if server:
        cmd.append(f"@{server}")
    cmd += [name, "A"]
    rc, out, err = _run(cmd, timeout=timeout + 5)
    if rc == 9 or "connection timed out" in (out + err):
        return [], f"resolver {server or 'default'} unreachable"
    if rc != 0:
        return [], (err.strip() or f"dig exit {rc}")
    ips = [l.strip() for l in out.splitlines() if re.match(r"^\d+\.\d+\.\d+\.\d+$", l.strip())]
    return ips, ""


def _system_resolve(name: str) -> list[str]:
    """Resolve the way applications do — this DOES consult /etc/hosts."""
    try:
        infos = socket.getaddrinfo(name, None, family=socket.AF_INET)
        return sorted({i[4][0] for i in infos})
    except socket.gaierror as exc:
        return [f"(failed: {exc.strerror or exc})"]


def _hosts_entries(name: str) -> list[str]:
    path = "/etc/hosts"
    found = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                stripped = line.split("#", 1)[0].strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) >= 2 and name in parts[1:]:
                    found.append(stripped)
    except OSError:
        pass
    return found


def dns_report(name: str, resolvers: list[str]) -> dict[str, Any]:
    default_ips, default_err = _dig_short(name)
    rows: list[dict[str, Any]] = [
        {"resolver": "system default", "ips": default_ips, "error": default_err}
    ]
    for r in resolvers:
        ips, err = _dig_short(name, server=r)
        rows.append({"resolver": r, "ips": ips, "error": err})

    sys_ips = _system_resolve(name)
    hosts = _hosts_entries(name)

    answered = [r for r in rows if r["ips"]]
    distinct = {tuple(sorted(r["ips"])) for r in answered}
    inconsistent = len(distinct) > 1

    dns_only = {ip for r in answered for ip in r["ips"]}
    app_only = {ip for ip in sys_ips if not ip.startswith("(")}
    hosts_override = bool(hosts) or (bool(dns_only) and bool(app_only) and not (dns_only & app_only))

    notes = []
    if inconsistent:
        notes.append(
            "Resolvers disagree. Internal DNS override or hijack is likely — the name may point to different hosts depending on where you ask."
        )
    if hosts_override:
        notes.append(
            "The application-level answer differs from DNS, or /etc/hosts has an entry. "
            "dig and nslookup both bypass /etc/hosts; your program does not."
        )
    if not answered:
        notes.append("No resolver returned an A record. The name may not exist in public DNS.")
    if not notes:
        notes.append("Resolvers agree and match the application view.")

    return {
        "name": name,
        "resolvers": rows,
        "application_view": sys_ips,
        "hosts_file_entries": hosts,
        "inconsistent": inconsistent,
        "hosts_override": hosts_override,
        "notes": notes,
    }


# --------------------------------------------------------------------------
# trust stores
# --------------------------------------------------------------------------

def truststore_report() -> dict[str, Any]:
    out: dict[str, Any] = {"openssl": {}, "python": {}, "env": {}, "node": {}, "notes": []}

    if _have("openssl"):
        rc, so, _ = _run(["openssl", "version", "-d"])
        out["openssl"]["dir"] = so.strip() if rc == 0 else "unknown"
        rc, so, _ = _run(["openssl", "version"])
        out["openssl"]["version"] = so.strip() if rc == 0 else "unknown"
    else:
        out["openssl"]["error"] = "openssl not installed"

    paths = ssl.get_default_verify_paths()
    out["python"] = {
        "version": sys.version.split()[0],
        "cafile": paths.cafile,
        "capath": paths.capath,
        "openssl_cafile_env": paths.openssl_cafile_env,
        "openssl_cafile": paths.openssl_cafile,
    }
    try:
        import certifi  # type: ignore

        out["python"]["certifi"] = certifi.where()
    except Exception:
        out["python"]["certifi"] = "(certifi not installed)"

    for var in (
        "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
        "NODE_EXTRA_CA_CERTS", "GIT_SSL_CAINFO", "AWS_CA_BUNDLE",
        "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy",
    ):
        val = os.environ.get(var)
        if val:
            out["env"][var] = val

    if _have("node"):
        rc, so, _ = _run(["node", "-e", "process.stdout.write(process.version)"])
        out["node"]["version"] = so.strip() if rc == 0 else "unknown"
        out["node"]["extra_ca"] = os.environ.get("NODE_EXTRA_CA_CERTS", "(unset)")

    if out["python"].get("certifi", "").startswith("/"):
        out["notes"].append(
            "Python requests uses certifi's bundle, which is separate from the OS trust store. "
            "A CA installed system-wide is invisible to it unless REQUESTS_CA_BUNDLE points there."
        )
    if any(k.lower().endswith("proxy") for k in out["env"]):
        out["notes"].append(
            "Proxy environment variables are set. Traffic may be routed through an intercepting proxy."
        )
    out["notes"].append(
        "Go reads the OS trust store; Node needs NODE_EXTRA_CA_CERTS; Java needs its own truststore. "
        "This is why a browser can succeed while code fails."
    )
    return out


# --------------------------------------------------------------------------
# lab
# --------------------------------------------------------------------------

LAB_SCRIPT = r"""#!/usr/bin/env bash
# Reproduce "proxy breaks certificate verification" locally.
# Creates a fake corporate CA, forges a certificate for TARGET, serves it,
# and shows the exact failure a real intercepting proxy produces.
set -euo pipefail
TARGET="${1:-api.example.com}"
PORT="${2:-4444}"
WORK="$(mktemp -d)"
cd "$WORK"
echo "workdir: $WORK"

openssl req -x509 -newkey rsa:2048 -sha256 -days 30 -nodes \
  -keyout proxyCA.key -out proxyCA.crt \
  -subj "/C=US/O=Acme Corp IT/CN=Acme Corp Proxy Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null

cat > leaf.cnf <<EOF
[req]
distinguished_name = dn
prompt = no
[dn]
CN = $TARGET
[ext]
subjectAltName = DNS:$TARGET
basicConstraints = CA:FALSE
extendedKeyUsage = serverAuth
EOF

openssl req -new -newkey rsa:2048 -nodes \
  -keyout leaf.key -out leaf.csr -config leaf.cnf 2>/dev/null
openssl x509 -req -in leaf.csr -CA proxyCA.crt -CAkey proxyCA.key \
  -CAcreateserial -out leaf.crt -days 30 -sha256 \
  -extfile leaf.cnf -extensions ext 2>/dev/null

openssl s_server -accept "$PORT" -cert leaf.crt -key leaf.key -www -quiet >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

echo
echo "=== 1. What the client sees (the failure) ==="
echo | openssl s_client -connect "127.0.0.1:$PORT" -servername "$TARGET" 2>&1 \
  | grep -E "verify error|subject=|issuer=|Verify return code" || true

echo
echo "=== 2. The issuer names the culprit ==="
echo | openssl s_client -connect "127.0.0.1:$PORT" -servername "$TARGET" 2>&1 \
  | openssl x509 -noout -issuer -subject -dates 2>/dev/null

echo
echo "=== 3. Proof: the proxy CA verifies it (expect code 0) ==="
echo | openssl s_client -connect "127.0.0.1:$PORT" -servername "$TARGET" \
  -CAfile proxyCA.crt 2>&1 | grep -E "Verify return code"

echo
echo "CA kept at: $WORK/proxyCA.crt"
echo "Point tls_doctor at it:  tls_doctor.py diagnose $TARGET --port $PORT --host-override 127.0.0.1 --proxy-ca $WORK/proxyCA.crt"
"""


def write_lab(dest: str | None) -> str:
    path = dest or os.path.join(tempfile.gettempdir(), "tls_mitm_lab.sh")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(LAB_SCRIPT)
    os.chmod(path, 0o755)
    return path


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def _fmt_chain(chain: ChainResult) -> str:
    if not chain.connected:
        return f"  connection failed: {chain.error}"
    if not chain.certs:
        return "  (no certificates parsed)"
    lines = []
    for c in chain.certs:
        lines.append(f"  [{c.depth}] subject: {c.subject}")
        lines.append(f"      issuer : {c.issuer}" + ("   (self-signed)" if c.self_signed else ""))
    lines.append(f"  chain length: {len(chain.certs)}")
    if chain.not_after:
        lines.append(f"  validity: {chain.not_before}  ->  {chain.not_after}")
    if chain.sans:
        shown = ", ".join(chain.sans[:8]) + ("  ..." if len(chain.sans) > 8 else "")
        lines.append(f"  SAN: {shown}")
    lines.append(f"  verify: {chain.verify_code} ({chain.verify_text})")
    return "\n".join(lines)


def _fmt_verdict(v: dict[str, Any]) -> str:
    lines = [
        f"  verdict   : {v['verdict']}  (confidence: {v['confidence']})",
        f"  blame     : {v['blame']}",
        f"  summary   : {v['summary']}",
        "  next steps:",
    ]
    lines += [f"    - {s}" for s in v["next"]]
    return "\n".join(lines)


def _fmt_dns(d: dict[str, Any]) -> str:
    lines = []
    for row in d["resolvers"]:
        val = ", ".join(row["ips"]) if row["ips"] else f"({row['error'] or 'no answer'})"
        lines.append(f"  {row['resolver']:<18} {val}")
    lines.append(f"  {'application view':<18} {', '.join(d['application_view'])}")
    if d["hosts_file_entries"]:
        for e in d["hosts_file_entries"]:
            lines.append(f"  {'/etc/hosts':<18} {e}")
    for n in d["notes"]:
        lines.append(f"  note: {n}")
    return "\n".join(lines)


def _fmt_truststore(t: dict[str, Any]) -> str:
    lines = [
        f"  openssl : {t['openssl'].get('version', t['openssl'].get('error', '?'))}",
        f"            {t['openssl'].get('dir', '')}",
        f"  python  : {t['python']['version']}",
        f"            cafile  = {t['python']['cafile']}",
        f"            capath  = {t['python']['capath']}",
        f"            certifi = {t['python']['certifi']}",
    ]
    if t.get("node", {}).get("version"):
        lines.append(f"  node    : {t['node']['version']}  NODE_EXTRA_CA_CERTS={t['node']['extra_ca']}")
    if t["env"]:
        lines.append("  env overrides:")
        lines += [f"            {k}={v}" for k, v in t["env"].items()]
    else:
        lines.append("  env overrides: (none set)")
    for n in t["notes"]:
        lines.append(f"  note: {n}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_chain(a: argparse.Namespace) -> int:
    target = a.host_override or a.host
    ch = get_chain(target, a.port, servername=a.host, ca_file=a.ca_file, proxy=a.proxy, timeout=a.timeout)
    if a.json:
        print(json.dumps(asdict(ch), indent=2))
    else:
        print(f"\nCertificate chain for {a.host}:{a.port} (SNI: {ch.servername})")
        print(_fmt_chain(ch))
        print()
    return 0 if ch.verify_code == 0 else 1


def cmd_verify(a: argparse.Namespace) -> int:
    target = a.host_override or a.host
    ch = get_chain(target, a.port, servername=a.host, ca_file=a.ca_file, proxy=a.proxy, timeout=a.timeout)
    v = classify(ch)
    if a.json:
        print(json.dumps({"chain": asdict(ch), "verdict": v}, indent=2))
    else:
        print(f"\nVerification for {a.host}:{a.port}"
              + (f" using CA file {a.ca_file}" if a.ca_file else " using default trust store"))
        print(_fmt_chain(ch))
        print()
        print(_fmt_verdict(v))
        print()
    return 0 if ch.verify_code == 0 else 1


def cmd_dns(a: argparse.Namespace) -> int:
    d = dns_report(a.host, a.resolver)
    if a.json:
        print(json.dumps(d, indent=2))
    else:
        print(f"\nDNS comparison for {a.host}")
        print(_fmt_dns(d))
        print()
    return 1 if (d["inconsistent"] or d["hosts_override"]) else 0


def cmd_truststore(a: argparse.Namespace) -> int:
    t = truststore_report()
    if a.json:
        print(json.dumps(t, indent=2))
    else:
        print("\nTrust stores and overrides")
        print(_fmt_truststore(t))
        print()
    return 0


def cmd_lab(a: argparse.Namespace) -> int:
    path = write_lab(a.output)
    print(f"\nMITM lab script written to: {path}")
    print(f"Run it:  bash {path} [target-name] [port]")
    print("It creates a throwaway CA, forges a certificate, serves it, and shows the exact failure.\n")
    return 0


def cmd_diagnose(a: argparse.Namespace) -> int:
    target = a.host_override or a.host
    report: dict[str, Any] = {"host": a.host, "port": a.port}

    chain = get_chain(target, a.port, servername=a.host, ca_file=a.ca_file, proxy=a.proxy, timeout=a.timeout)
    report["chain"] = asdict(chain)

    # If a candidate proxy CA was supplied, test whether it validates the chain.
    proxy_ca_ok: bool | None = None
    if a.proxy_ca and chain.connected:
        probe = get_chain(target, a.port, servername=a.host, ca_file=a.proxy_ca, proxy=a.proxy, timeout=a.timeout)
        proxy_ca_ok = probe.verify_code == 0
        report["proxy_ca_check"] = {"ca_file": a.proxy_ca, "verified": proxy_ca_ok}

    verdict = classify(chain, proxy_ca_ok=proxy_ca_ok)
    report["verdict"] = verdict

    dns: dict[str, Any] | None = None
    if not a.no_dns and not _is_ip(a.host):
        dns = dns_report(a.host, a.resolver)
        report["dns"] = dns

    trust = truststore_report()
    report["truststore"] = trust

    if a.json:
        print(json.dumps(report, indent=2))
        return 0 if chain.verify_code == 0 else 1

    print(f"\n{'=' * 68}")
    print(f"TLS diagnosis: {a.host}:{a.port}")
    print("=" * 68)

    print("\n1. Certificate chain the server sent")
    print(_fmt_chain(chain))

    if "proxy_ca_check" in report:
        ok = report["proxy_ca_check"]["verified"]
        print(f"\n2. Candidate proxy CA ({a.proxy_ca})")
        print(f"  verified the chain: {'YES — this CA signed it' if ok else 'no'}")

    if dns:
        print("\n3. DNS cross-check")
        print(_fmt_dns(dns))

    print("\n4. Trust stores")
    print(_fmt_truststore(trust))

    print("\n" + "-" * 68)
    print("VERDICT")
    print("-" * 68)
    print(_fmt_verdict(verdict))
    print()
    return 0 if chain.verify_code == 0 else 1


def _is_ip(s: str) -> bool:
    try:
        socket.inet_aton(s)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tls_doctor.py",
        description="Diagnose HTTPS certificate verification failures and assign blame.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser, host: bool = True) -> None:
        if host:
            sp.add_argument("host", help="hostname to diagnose (used as SNI)")
            sp.add_argument("--port", type=int, default=443)
            sp.add_argument(
                "--host-override",
                help="connect to this address instead of resolving host (for local labs)",
            )
            sp.add_argument("--ca-file", help="verify against this CA bundle instead of the default")
            sp.add_argument("--proxy", help="connect through HTTP proxy host:port")
            sp.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    sp = sub.add_parser("chain", help="show the certificate chain the server sends")
    common(sp)
    sp.set_defaults(func=cmd_chain)

    sp = sub.add_parser("verify", help="verify the chain and classify the failure")
    common(sp)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("diagnose", help="full workflow: chain + DNS + trust store -> verdict")
    common(sp)
    sp.add_argument("--proxy-ca", help="candidate interception CA to test against")
    sp.add_argument("--resolver", action="append", default=[], help="extra DNS resolver (repeatable)")
    sp.add_argument("--no-dns", action="store_true", help="skip the DNS cross-check")
    sp.set_defaults(func=cmd_diagnose)

    sp = sub.add_parser("dns", help="compare resolvers and the application view")
    sp.add_argument("host")
    sp.add_argument("--resolver", action="append", default=[], help="extra DNS resolver (repeatable)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_dns)

    sp = sub.add_parser("truststore", help="show which CA bundle each runtime uses")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_truststore)

    sp = sub.add_parser("lab", help="write a local MITM reproduction script")
    sp.add_argument("--output", help="path to write the script")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_lab)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
