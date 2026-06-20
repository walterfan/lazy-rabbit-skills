# Network Command Reference

Use this file when the user wants deeper explanation of command families or when the main skill needs quick examples without bloating `SKILL.md`.

## Interfaces and IPs

### Linux

```bash
ip addr
ip route
ip route show default
```

### macOS / BSD-style

```bash
ifconfig
route -n get default
```

## Ports and processes

### Show listening sockets

```bash
lsof -nP -iTCP -sTCP:LISTEN
ss -lntp
netstat -an
```

### Find who owns one port

```bash
lsof -nP -i :8080
ss -lntp '( sport = :8080 )'
```

## DNS

```bash
nslookup example.com
dig example.com A
dig example.com AAAA
dig example.com MX
dig @8.8.8.8 example.com A
```

## TCP checks

```bash
nc -vz example.com 443
nc -vz 127.0.0.1 3000
```

## Firewalls

### ufw

```bash
sudo ufw status verbose
sudo ufw status numbered
```

### iptables

```bash
sudo iptables -L -n -v
sudo iptables -S
```

### nftables

```bash
sudo nft list ruleset
```

### macOS pf

```bash
sudo pfctl -sr
sudo pfctl -sa
```
