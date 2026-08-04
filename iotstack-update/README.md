# iotstack-update

Safe `apt` upgrades and reboots for Debian / Raspberry Pi OS servers running
Docker or IOTstack workloads. Goes server by server, records what was running
before, runs the upgrade detached from the SSH session, and verifies every
container came back afterwards.

Companion to [iotstack-install](../iotstack-install/) — that one builds the
stack, this one keeps it patched.

## Install

```bash
npx skills add https://github.com/lvacek2026/skills --skill iotstack-update -g
```

## Usage

```
/iotstack-update claudeIA@10.0.72.222 claudeIA@172.22.155.245
```

Or invoke without arguments — the skill reads the server list from the project's
`CLAUDE.md` / memory and confirms it with you before starting.

## What It Does

1. **Reachability sweep** — probes every target up front, falls back to Tailscale for hosts unreachable on their LAN IP, and reports the pending package count per server
2. **Risk ordering** — upgrades the cheapest servers first, production and network-critical ones (captive portal, VPN, GPIO control) last
3. **Baseline capture** — running containers, restart policies, Docker networks, plus `nsenter` socket capture for `ipvlan`/`macvlan` containers the host cannot reach by IP
4. **Disk headroom** — purges superseded kernels and apt cache when `/` is tight, before `dpkg` can fail mid-transaction
5. **Detached upgrade** — `nohup` + `NEEDRESTART_MODE=a` + `--force-confold`, so an `openssh-server`/`tailscale`/`systemd` upgrade cannot break the run by dropping the session
6. **Verification** — zero `E:` lines, zero packages left (held-back ones installed explicitly), running vs installed kernel
7. **Safe reboot** — confirms `tailscaled`/`ssh`/`docker` are enabled and the boot partition is intact first, then waits on *uptime*, not mere reachability
8. **Post-reboot diff** — missing containers, restarting/unhealthy states, ipvlan IPs and ports vs baseline, HTTP probes of stack services
9. **Honest report** — per-server table plus standing issues that need a human decision

## Hard rules it follows

- One server at a time — never parallel
- Never `docker compose up -d` during an update (drifted compose files destroy running containers)
- Always ask before rebooting and before upgrading `docker-ce`
- Never overwrite config files silently (`--force-confdef --force-confold`)

## Gotchas it knows about

- SSH answers for seconds *during* shutdown — a naive post-reboot check reports success against a dying machine
- Raspberry Pis upgraded in place can have **no `linux-image` package at all** and boot from `/boot/firmware/kernel8.img`, so apt never patches the kernel
- `docker system df` reclaimable space usually sits on a different filesystem than the full `/`
- HTTP `302`/`401`/`404` from stack services are healthy responses, not failures
- Containers using `network_mode: container:<other>` legitimately report an empty IP
