---
name: lazy-network-doctor
description: >-
  Diagnose and teach local network troubleshooting from natural-language
  requests. Use when the user mentions network issues, connectivity, DNS, IP,
  ports, firewall, iptables, ufw, ifconfig, ip, netstat, ss, lsof, nslookup,
  dig, nc, ping, traceroute, route, or wants to know which process is using
  which port. This skill should help inspect local IP and routes, map ports to
  processes, explain common network tools, and guide firewall diagnosis on
  Linux or macOS.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - network
  - troubleshooting
  - dns
  - ports
  - firewall
  - iptables
  - ufw
  - ifconfig
  - netstat
  - nc
category: ops-tools
use_cases:
  - "what is my local default IP"
  - "which process is listening on this port"
  - "teach me how to use netstat, dig, nslookup, and nc"
  - "debug a DNS or TCP connectivity problem"
  - "explain ufw, iptables, or firewall troubleshooting"
platforms:
  - codex
  - claude-code
  - cursor
visibility: public
---

# lazy-network-doctor

Turn vague networking pain into a concrete checklist: identify the symptom, inspect local state, test one layer at a time, then explain what the output means.

## Contract

- **scope_in**: local network troubleshooting; IP/interface discovery; default route checks; DNS lookup checks; TCP connectivity checks; mapping ports to processes; command teaching for `ifconfig`, `ip`, `netstat`, `ss`, `lsof`, `nslookup`, `dig`, `nc`, `ping`, `traceroute`, `route`; firewall diagnosis for `ufw`, `iptables`, `nft`, and macOS `pf`
- **scope_out**: router or cloud-network changes that cannot be inspected from the local machine; destructive firewall changes without explicit user approval; packet capture deep-dives unless the user asks for `tcpdump` or Wireshark-level work
- **Preconditions**: shell access is available; the target host, port, interface, or symptom is known or can be inferred; commands may differ by OS, so prefer detection over assumptions
- **Postconditions**: the response states the symptom being checked, shows the exact commands used or recommended, explains the output in plain language, and makes any privileged or destructive firewall step explicit

## Workflow

### Phase 0: Classify the symptom

- Pick one primary mode:
  - `teach`: explain networking tools and how to use them
  - `local-state`: find local IPs, interfaces, routes, listeners, and owning processes
  - `dns`: resolve a hostname and compare resolvers or record types
  - `tcp`: test whether a host and port are reachable
  - `firewall`: inspect filtering tools and rules
  - `full-diagnose`: step through local state → DNS → route → TCP reachability → firewall
- If the user only says “network issue”, start with `full-diagnose`.

### Phase 1: Inspect local state first

Use the bundled helper:

```bash
python3 skills/lazy-network-doctor/scripts/network_doctor.py env
python3 skills/lazy-network-doctor/scripts/network_doctor.py local-ip
python3 skills/lazy-network-doctor/scripts/network_doctor.py default-route
python3 skills/lazy-network-doctor/scripts/network_doctor.py listeners
python3 skills/lazy-network-doctor/scripts/network_doctor.py port-owner --port 8080
```

Default order:

1. Identify the OS and available networking commands.
2. Identify the local IP and default route.
3. Check whether the expected port is listening locally.
4. Map the port back to the owning process.

### Phase 2: Check the failing layer explicitly

#### DNS

```bash
python3 skills/lazy-network-doctor/scripts/network_doctor.py resolve --host example.com
```

Also teach direct tools when useful:

```bash
nslookup example.com
dig example.com A
dig example.com AAAA
dig example.com MX
```

#### TCP reachability

```bash
python3 skills/lazy-network-doctor/scripts/network_doctor.py tcp-check --host example.com --port 443
nc -vz example.com 443
```

#### Firewall

```bash
python3 skills/lazy-network-doctor/scripts/network_doctor.py firewall
```

Then branch by platform:

- Linux with `ufw`: inspect status and numbered rules before changing anything.
- Linux with `iptables` or `nft`: inspect policy and current chains/rules first.
- macOS: inspect `pfctl` state and remember the application firewall is separate from packet filter rules.

### Phase 3: Teach the command and the interpretation

When the user is learning, answer in this shape:

1. `What it does`
2. `Common command forms`
3. `How to read the output`
4. `When to use it instead of something else`

Example distinctions:

- `ifconfig` or `ip addr`: interfaces and IP addresses
- `netstat`, `ss`, or `lsof`: sockets, listeners, and owners
- `nslookup` or `dig`: DNS
- `nc`: quick TCP/UDP testing

### Phase 4: Response format

For non-trivial troubleshooting, use:

1. `Symptom`: what is being checked
2. `Command`: exact command or helper invocation
3. `Result`: compact output summary
4. `Meaning`: what the result implies
5. `Next check`: the next layer to inspect

## Shortcuts

### Helper commands

| Task | Command |
|------|---------|
| Show available shortcuts | `python3 skills/lazy-network-doctor/scripts/network_doctor.py shortcuts` |
| Show OS and command availability | `python3 skills/lazy-network-doctor/scripts/network_doctor.py env` |
| Show local default IP | `python3 skills/lazy-network-doctor/scripts/network_doctor.py local-ip` |
| Show default route | `python3 skills/lazy-network-doctor/scripts/network_doctor.py default-route` |
| Show listening ports | `python3 skills/lazy-network-doctor/scripts/network_doctor.py listeners` |
| Show process using a port | `python3 skills/lazy-network-doctor/scripts/network_doctor.py port-owner --port 8080` |
| Resolve hostname | `python3 skills/lazy-network-doctor/scripts/network_doctor.py resolve --host example.com` |
| Test TCP reachability | `python3 skills/lazy-network-doctor/scripts/network_doctor.py tcp-check --host example.com --port 443` |
| Show firewall tool status | `python3 skills/lazy-network-doctor/scripts/network_doctor.py firewall` |

### Core command shortcuts

| Task | Command |
|------|---------|
| Show interfaces on Linux | `ip addr` |
| Show interfaces on macOS / older Unix | `ifconfig` |
| Show default route on Linux | `ip route show default` |
| Show default route on macOS | `route -n get default` |
| Show listeners with owners | `lsof -nP -iTCP -sTCP:LISTEN` |
| Show listeners on Linux | `ss -lntp` |
| Show listeners with netstat | `netstat -an` |
| Show port owner | `lsof -nP -i :8080` |
| Resolve host with nslookup | `nslookup example.com` |
| Resolve host with dig | `dig example.com A` |
| Test TCP port with nc | `nc -vz example.com 443` |
| Show ufw rules | `sudo ufw status verbose` |
| Show iptables rules | `sudo iptables -L -n -v` |
| Show nftables rules | `sudo nft list ruleset` |
| Show pf status on macOS | `sudo pfctl -sr` |

## Tool guidance

### `ifconfig` vs `ip`

- Prefer `ip addr` and `ip route` on modern Linux.
- Use `ifconfig` on macOS and on systems where `ip` is unavailable.
- Teach both when the user may work across platforms.

### `netstat` vs `ss` vs `lsof`

- Prefer `ss` on Linux for socket state and listening ports.
- Prefer `lsof` when the user asks which process owns a port.
- Use `netstat` when `ss` is missing or the user specifically asks for it.

### `nslookup` vs `dig`

- `nslookup` is quick and simple.
- `dig` is better for precise record-type checks and more detailed DNS output.

### `nc`

- Use `nc -vz host port` for a fast TCP reachability check.
- Explain that “succeeded” proves the TCP connect worked, but not that the higher-level protocol is healthy.

## Firewall guidance

### `ufw`

- Inspect first:
  - `sudo ufw status verbose`
  - `sudo ufw status numbered`
- Common safe reasoning:
  - confirm whether `ufw` is active
  - confirm whether the target port/protocol is allowed
  - confirm direction and interface assumptions

### `iptables` / `nft`

- Inspect first:
  - `sudo iptables -L -n -v`
  - `sudo nft list ruleset`
- Pay attention to:
  - default policy
  - packet/byte counters
  - chain order
  - whether NAT and filter tables are both relevant

### macOS `pf`

- Inspect with:
  - `sudo pfctl -sr`
  - `sudo pfctl -sa`
- Remember:
  - `pf` packet filter rules are not the same thing as the macOS application firewall
  - diagnosing one does not prove the other is open

## Verification

### Hard gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| Layered diagnosis | The answer identifies whether the issue is local state, DNS, route, TCP, or firewall | Reframe around layers before giving commands |
| Exact commands shown | The answer includes runnable commands or helper invocations | Add the exact commands |
| Port ownership is process-aware | Port questions use `lsof`, `ss`, or equivalent owner-aware tooling | Re-run with owner-aware tooling |
| Firewall safety | Inspection is separated from change commands | Remove implied write steps unless explicitly requested |

### Soft gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| Cross-platform awareness | Linux vs macOS command differences are noted when relevant | Add platform note |
| Output interpretation | Raw command output is explained | Add a plain-language explanation |
| Least-privilege posture | `sudo` is only suggested where inspection truly needs it | Replace with non-privileged check when possible |

## Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| “Port is open” but app still fails | TCP connect succeeded but protocol or app layer is broken | Test with the app protocol, not just `nc` |
| No process shown for port | Wrong tool or insufficient privilege | Use `lsof` or `ss -p`, add `sudo` only if required |
| Wrong local IP reported | Multiple interfaces or VPN changed the route | Check default route and interface-specific addresses |
| DNS looks fine from one tool only | Resolver, cache, or record-type mismatch | Compare `nslookup`, `dig`, and system resolver behavior |
| Firewall rule seems right but traffic still fails | Wrong direction, interface, chain order, or another firewall layer | Inspect counters, default policy, and alternate firewall tools |

## Boundary examples

- **User**: "What is my local default IP?"  
  Use `local-ip` and `default-route`, then explain that the chosen IP is route-dependent.
- **User**: "Which process is using 3000?"  
  Use `port-owner --port 3000` or `lsof -nP -i :3000`.
- **User**: "Teach me dig, nslookup, and nc."  
  Explain what each tool is for, show the common command forms, and compare when to choose one over another.
- **User**: "My service is not reachable from another machine."  
  Check local listener, bound address, firewall, local route, then remote TCP reachability assumptions.

## Additional resources

- Command reference: [references/command-reference.md](references/command-reference.md)
