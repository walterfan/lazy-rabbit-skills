#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Small network helper for local interface, DNS, port, and firewall diagnostics."""

from __future__ import annotations

import argparse
import platform
import shutil
import socket
import subprocess
from collections.abc import Iterable, Sequence


SHORTCUTS = [
    ("Show OS and tool availability", "python3 skills/lazy-network-doctor/scripts/network_doctor.py env"),
    ("Show local default IP", "python3 skills/lazy-network-doctor/scripts/network_doctor.py local-ip"),
    ("Show default route", "python3 skills/lazy-network-doctor/scripts/network_doctor.py default-route"),
    ("Show listening ports", "python3 skills/lazy-network-doctor/scripts/network_doctor.py listeners"),
    ("Show process using port 8080", "python3 skills/lazy-network-doctor/scripts/network_doctor.py port-owner --port 8080"),
    ("Resolve hostname", "python3 skills/lazy-network-doctor/scripts/network_doctor.py resolve --host example.com"),
    ("Test TCP connectivity", "python3 skills/lazy-network-doctor/scripts/network_doctor.py tcp-check --host example.com --port 443"),
    ("Inspect firewall tools", "python3 skills/lazy-network-doctor/scripts/network_doctor.py firewall"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Network helper for teaching and basic local diagnostics."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("shortcuts", help="Show common helper shortcuts")
    subparsers.add_parser("env", help="Show OS and command availability")
    subparsers.add_parser("local-ip", help="Show the local IP chosen for the default route")
    subparsers.add_parser("default-route", help="Show the default route")
    subparsers.add_parser("listeners", help="Show listening ports and owning processes when possible")

    port_owner = subparsers.add_parser("port-owner", help="Show which process owns a port")
    port_owner.add_argument("--port", required=True, type=int, help="TCP or UDP port to inspect")

    resolve = subparsers.add_parser("resolve", help="Resolve a hostname with the system resolver")
    resolve.add_argument("--host", required=True, help="Hostname to resolve")

    tcp = subparsers.add_parser("tcp-check", help="Test whether a host and port are reachable over TCP")
    tcp.add_argument("--host", required=True, help="Target hostname or IP")
    tcp.add_argument("--port", required=True, type=int, help="Target TCP port")
    tcp.add_argument("--timeout", type=float, default=3.0, help="Connect timeout in seconds")

    subparsers.add_parser("firewall", help="Show available firewall tooling and safe inspection commands")
    return parser.parse_args()


def markdown_table(columns: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    rendered = list(rows)
    if not rendered:
        return "_No rows returned._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(escape_cell(value) for value in row) + " |"
        for row in rendered
    ]
    return "\n".join([header, separator, *body])


def escape_cell(value: object) -> str:
    if value is None:
        text = "NULL"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def print_result(columns: Sequence[str], rows: Sequence[Sequence[object]], note: str | None = None) -> None:
    print("## Result")
    print(markdown_table(columns, rows))
    if note:
        print()
        print(note)


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def available_commands() -> list[tuple[str, str]]:
    names = [
        "ifconfig",
        "ip",
        "route",
        "netstat",
        "ss",
        "lsof",
        "nslookup",
        "dig",
        "nc",
        "ping",
        "traceroute",
        "ufw",
        "iptables",
        "nft",
        "pfctl",
    ]
    return [(name, shutil.which(name) or "missing") for name in names]


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def extract_interface_from_route(output: str) -> str | None:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("interface:"):
            return stripped.split(":", 1)[1].strip()
        parts = stripped.split()
        if parts[:1] == ["default"] and len(parts) >= 5:
            return parts[4]
        if parts[:1] == ["default"] and len(parts) >= 3:
            return parts[-1]
    return None


def get_interface_ipv4(interface: str) -> str | None:
    if command_exists("ifconfig"):
        rc, stdout, _ = run_command(["ifconfig", interface])
        if rc == 0:
            for line in stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("inet ") and "127.0.0.1" not in stripped:
                    parts = stripped.split()
                    if len(parts) >= 2:
                        return parts[1]
    if command_exists("ip"):
        rc, stdout, _ = run_command(["ip", "-4", "addr", "show", "dev", interface])
        if rc == 0:
            for line in stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("inet "):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        return parts[1].split("/", 1)[0]
    return None


def hostname_ipv4() -> str | None:
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return None
    for info in infos:
        address = info[4][0]
        if not address.startswith("127."):
            return address
    return None


def any_non_loopback_ipv4() -> str | None:
    if command_exists("ifconfig"):
        rc, stdout, _ = run_command(["ifconfig"])
        if rc == 0:
            for line in stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("inet "):
                    parts = stripped.split()
                    if len(parts) >= 2 and not parts[1].startswith("127."):
                        return parts[1]
    if command_exists("ip"):
        rc, stdout, _ = run_command(["ip", "-4", "addr"])
        if rc == 0:
            for line in stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("inet "):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        address = parts[1].split("/", 1)[0]
                        if not address.startswith("127."):
                            return address
    return None


def get_local_default_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        route_output, _ = get_default_route_output()
        interface = extract_interface_from_route(route_output)
        if interface:
            address = get_interface_ipv4(interface)
            if address:
                return address
        address = hostname_ipv4()
        if address:
            return address
        address = any_non_loopback_ipv4()
        if address:
            return address
        return "unknown"
    finally:
        sock.close()


def get_default_route_output() -> tuple[str, str]:
    system = platform.system()
    if system == "Darwin" and command_exists("route"):
        rc, stdout, stderr = run_command(["route", "-n", "get", "default"])
        return stdout if rc == 0 else stderr, "route -n get default"
    if command_exists("ip"):
        rc, stdout, stderr = run_command(["ip", "route", "show", "default"])
        return stdout if rc == 0 else stderr, "ip route show default"
    if command_exists("route"):
        rc, stdout, stderr = run_command(["route", "-n"])
        return stdout if rc == 0 else stderr, "route -n"
    return "No route command available.", "none"


def get_listener_output() -> tuple[str, str]:
    if command_exists("lsof"):
        rc, stdout, stderr = run_command(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"])
        return stdout if rc == 0 else stderr, "lsof -nP -iTCP -sTCP:LISTEN"
    if command_exists("ss"):
        rc, stdout, stderr = run_command(["ss", "-lntp"])
        return stdout if rc == 0 else stderr, "ss -lntp"
    if command_exists("netstat"):
        rc, stdout, stderr = run_command(["netstat", "-an"])
        return stdout if rc == 0 else stderr, "netstat -an"
    return "No listener-inspection command available.", "none"


def get_port_owner_output(port: int) -> tuple[str, str]:
    port_text = str(port)
    if command_exists("lsof"):
        rc, stdout, stderr = run_command(["lsof", "-nP", "-i", f":{port_text}"])
        return stdout if rc == 0 and stdout else stderr or "No matching process found.", f"lsof -nP -i :{port_text}"
    if command_exists("ss"):
        rc, stdout, stderr = run_command(["ss", "-lntp"])
        if rc == 0:
            filtered = "\n".join(line for line in stdout.splitlines() if f":{port_text}" in line)
            return filtered or "No matching process found.", "ss -lntp"
        return stderr, "ss -lntp"
    if command_exists("netstat"):
        rc, stdout, stderr = run_command(["netstat", "-an"])
        if rc == 0:
            filtered = "\n".join(line for line in stdout.splitlines() if f".{port_text} " in line or f":{port_text} " in line)
            return filtered or "No matching socket found.", "netstat -an"
        return stderr, "netstat -an"
    return "No port-inspection command available.", "none"


def resolve_host(host: str) -> list[tuple[object, ...]]:
    seen: set[tuple[str, str]] = set()
    rows: list[tuple[object, ...]] = []
    resolver_error = False
    for family, family_name in ((socket.AF_INET, "A"), (socket.AF_INET6, "AAAA")):
        try:
            infos = socket.getaddrinfo(host, None, family, socket.SOCK_STREAM)
        except socket.gaierror as exc:
            rows.append((family_name, "error", str(exc)))
            resolver_error = True
            continue
        for info in infos:
            address = info[4][0]
            key = (family_name, address)
            if key in seen:
                continue
            seen.add(key)
            rows.append((family_name, "ok", address))
    if resolver_error and command_exists("dig"):
        for record_type in ("A", "AAAA"):
            rc, stdout, stderr = run_command(["dig", "+short", host, record_type])
            if rc == 0 and stdout:
                for line in stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    key = (record_type, line)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append((record_type, "ok", line))
            elif rc != 0 and stderr:
                rows.append((record_type, "dig_error", stderr))
    elif resolver_error and command_exists("nslookup"):
        rc, stdout, stderr = run_command(["nslookup", host])
        if rc == 0 and stdout:
            rows.append(("nslookup", "ok", stdout))
        elif stderr:
            rows.append(("nslookup", "error", stderr))
    return rows


def tcp_check(host: str, port: int, timeout: float) -> tuple[str, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "reachable", f"TCP connect to {host}:{port} succeeded."
    except OSError as exc:
        return "unreachable", str(exc)


def firewall_rows() -> list[tuple[object, ...]]:
    system = platform.system()
    rows: list[tuple[object, ...]] = []
    if command_exists("ufw"):
        rows.append(("ufw", "available", "sudo ufw status verbose"))
    else:
        rows.append(("ufw", "missing", "not in PATH"))
    if command_exists("iptables"):
        rows.append(("iptables", "available", "sudo iptables -L -n -v"))
    else:
        rows.append(("iptables", "missing", "not in PATH"))
    if command_exists("nft"):
        rows.append(("nft", "available", "sudo nft list ruleset"))
    else:
        rows.append(("nft", "missing", "not in PATH"))
    if system == "Darwin" or command_exists("pfctl"):
        rows.append(("pf", "available" if command_exists("pfctl") else "missing", "sudo pfctl -sr"))
    return rows


def main() -> None:
    args = parse_args()

    if args.command == "shortcuts":
        print_result(["task", "command"], SHORTCUTS)
        return

    if args.command == "env":
        rows = [("os", platform.system(), platform.release()), ("python", platform.python_version(), "runtime")]
        for name, path in available_commands():
            rows.append((name, "available" if path != "missing" else "missing", path))
        print_result(["item", "status", "detail"], rows)
        return

    if args.command == "local-ip":
        ip_address = get_local_default_ip()
        print_result(["item", "value"], [("local_default_ip", ip_address)])
        return

    if args.command == "default-route":
        output, command = get_default_route_output()
        print_result(["command", "output"], [(command, output or "No output.")])
        return

    if args.command == "listeners":
        output, command = get_listener_output()
        print_result(["command", "output"], [(command, output or "No output.")])
        return

    if args.command == "port-owner":
        output, command = get_port_owner_output(args.port)
        print_result(["command", "output"], [(command, output or "No output.")])
        return

    if args.command == "resolve":
        rows = resolve_host(args.host)
        print_result(["record_type", "status", "value"], rows)
        return

    if args.command == "tcp-check":
        status, detail = tcp_check(args.host, args.port, args.timeout)
        print_result(["host", "port", "status", "detail"], [(args.host, args.port, status, detail)])
        return

    if args.command == "firewall":
        print_result(["tool", "status", "inspect_command"], firewall_rows())
        print()
        print("## Notes")
        print("- Inspect before changing rules.")
        print("- `ufw`, `iptables`, and `nft` are Linux-focused; `pf` is common on macOS and BSD-style systems.")
        print("- Application firewalls and packet filters can both matter.")
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
