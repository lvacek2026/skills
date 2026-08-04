---
name: iotstack-update
description: Safely apt-upgrade and reboot Debian/Raspberry Pi servers running Docker/IOTstack workloads, one server at a time, with before/after container verification. Use when the user asks to update, upgrade or patch one or more IOT/Docker servers ("aktualizuj servery", "projdi stacky a updatuj", "apt upgrade na všech serverech").
argument-hint: "[host ...]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
effort: high
---

# IOTstack Update Expert

You upgrade Debian / Raspberry Pi OS servers that run Docker workloads, without
losing containers or locking yourself out. The core discipline: **capture a
baseline before touching anything, run the upgrade detached from your SSH
session, then diff reality against the baseline.**

## Input Parameters

- `$ARGUMENTS` — one or more SSH targets (`user@host`, or full `ssh -i key user@host`)

If nothing is provided, look for server definitions in the project's `CLAUDE.md`
or memory files, then confirm the list with the user before starting.

## Non-negotiable rules

1. **One server at a time.** Never fan out upgrades in parallel. If an upgrade
   breaks something, you want exactly one blast radius and a clean cause.
2. **Never run `docker compose up -d` as part of an update.** On long-lived
   stacks the compose file has drifted from the running containers; `up -d` will
   recreate or destroy containers that nobody intended to touch. `apt` upgrading
   `docker-ce` restarts the daemon and the containers come back via their restart
   policy — that is the only container restart an update should cause.
3. **Ask before rebooting and before upgrading Docker.** Both have visible
   consequences (service downtime, daemon restart). Get an explicit yes; do not
   infer it from "update everything".
4. **Check free disk before starting.** A kernel + initramfs upgrade needs
   ~1 GB free on `/`. Servers with small root partitions will fail mid-`dpkg`,
   which is a far worse state than not having started.

## Phase 1 — Reachability and inventory

Probe every target first, before touching any of them, so you know the full
scope and can tell the user what is unreachable.

```bash
for h in "${HOSTS[@]}"; do
  echo "=== $h ==="
  ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=8 "$USER@$h" '
    hostname; . /etc/os-release; echo "$PRETTY_NAME"
    sudo apt-get update -qq >/dev/null 2>&1
    echo "k upgradu: $(apt list --upgradable 2>/dev/null | tail -n +2 | wc -l)"
    apt list --upgradable 2>/dev/null | tail -n +2 | cut -d/ -f1 | tr "\n" " "; echo
    df -h / | tail -1
    ls /var/run/reboot-required 2>/dev/null && echo REBOOT-REQUIRED
  ' 2>&1 | tail -6
done
```

**If a host is unreachable on its LAN IP, try Tailscale before declaring it
down** — `tailscale status` lists the peers and their 100.x addresses. Servers
behind a different LAN are routinely only reachable that way.

Note the count per host. That drives ordering in Phase 2.

## Phase 2 — Order the work

Upgrade in ascending order of risk, so you learn on the cheap servers first:

1. Servers with the fewest packages and no kernel update
2. Ordinary Docker stacks
3. **Production / network-critical servers last** — anything hosting a captive
   portal, VPN concentrator, backup collector, or a GPIO control loop

## Phase 3 — Baseline (per server, before upgrading)

Everything you record here is what you will diff against afterwards.

```bash
ssh ... '
  docker ps --format "{{.Names}}\t{{.Status}}" | sort | tee /tmp/pre-upgrade-containers.txt
  echo "=== restart policies:"
  for c in $(docker ps -q); do
    printf "%s\t%s\n" \
      "$(docker inspect -f "{{.Name}}" $c | tr -d /)" \
      "$(docker inspect -f "{{.HostConfig.RestartPolicy.Name}}" $c)"
  done | sort
  echo "=== networks:"; docker network ls --format "{{.Name}}\t{{.Driver}}"
'
```

**Read the restart policies.** Any container with policy `no` will *not* come
back after a reboot — flag it to the user before rebooting, not after.

For containers on `ipvlan`/`macvlan` networks the host cannot reach them over
IP (that is the point of ipvlan). Capture their listening sockets from the host
via `nsenter` instead:

```bash
for c in <container names>; do
  pid=$(docker inspect -f "{{.State.Pid}}" $c)
  printf "%-28s IP=%-12s %s\n" "$c" \
    "$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $c)" \
    "$(sudo nsenter -t $pid -n ss -tlnu | tail -n +2 | awk '{print $1":"$5}' | sort -u | tr '\n' ' ')"
done
```

Containers using `network_mode: container:<other>` share another container's
namespace and show an empty IP — that is normal, check the namespace owner.

## Phase 4 — Free disk space if needed

If `/` has under ~1.5 GB free:

```bash
sudo apt-get clean
dpkg -l | grep "^ii  linux-image"          # find kernels older than $(uname -r)
sudo apt-get -y purge linux-image-<old>    # never purge the running kernel
sudo apt-get -y autoremove --purge
```

Note that `docker system df` reclaimable space usually lives on a *different*
filesystem than `/`, so pruning images may not help the partition that is full.
Check the mount before suggesting a prune.

## Phase 5 — Run the upgrade detached

The upgrade set routinely includes `openssh-server`, `tailscale` and `systemd`,
any of which can drop your SSH session mid-`dpkg`. **Always detach with
`nohup`** so a dropped connection cannot leave `dpkg` half-finished:

```bash
ssh ... 'sudo sh -c "nohup env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a \
  apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold \
  full-upgrade > /tmp/upgrade.log 2>&1 &"'
```

- `NEEDRESTART_MODE=a` stops needrestart from opening an interactive dialog
- `--force-confdef --force-confold` keeps existing config files (never silently
  overwrite a working `mosquitto.conf` or `daemon.json`)
- `full-upgrade` (not `upgrade`) so held-back kernel/dependency changes go in

Then poll until done, reporting progress to the user:

```bash
for i in $(seq 1 40); do
  sleep 30
  r=$(ssh ... 'pgrep -x apt-get >/dev/null && echo RUNNING || echo DONE; tail -1 /tmp/upgrade.log')
  echo "[$i] $r"
  echo "$r" | grep -q DONE && break
done
```

A Pi with 300+ packages takes 10–20 minutes. Do not give up early and do not
start a second server while one is still running.

## Phase 6 — Verify the upgrade

```bash
grep -cE "^E:" /tmp/upgrade.log        # must be 0
sudo apt-get update -qq
apt list --upgradable | tail -n +2     # must be empty
sudo apt-get -y autoremove --purge
uname -r; ls /boot/vmlinuz* | tail -2  # running vs installed kernel
```

**Packages left over after a successful run are usually phased/held-back
updates** — install them explicitly by name (`apt-get install <pkg>`) rather than
leaving the server half-updated.

If a new kernel is installed but `uname -r` still shows the old one, a reboot is
required regardless of whether `/var/run/reboot-required` exists (it is a
Debian/Ubuntu convention that Raspberry Pi OS does not always create).

## Phase 7 — Reboot safely

Before rebooting a server you can only reach remotely, confirm it will come back:

```bash
for s in tailscaled ssh docker; do echo "$s: $(systemctl is-enabled $s)"; done
ls -d /lib/modules/$(uname -r)           # modules for the running kernel exist
ls /boot/firmware/kernel*.img            # Pi: boot partition intact
```

**Raspberry Pi caveat:** some Pis (typically upgraded in place from an older
image) have *no* `linux-image` package installed at all and boot the kernel from
`/boot/firmware/kernel8.img`. `dpkg -l | grep -c "^ii  linux-image"` returning 0
means apt will never patch that kernel. Reboot is still safe (the boot partition
was untouched), but tell the user — it is a standing security gap.

Reboot and wait, guarding against reconnecting to the *pre-shutdown* system —
compare uptime, not just reachability:

```bash
ssh ... 'sudo systemctl reboot'
sleep 60
for i in $(seq 1 30); do
  r=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no ... '
        up=$(cut -d. -f1 /proc/uptime)
        [ "$up" -lt 3600 ] && { uname -r; uptime -p; docker ps --format "{{.Names}}\t{{.Status}}" | sort; }')
  [ -n "$r" ] && { echo "=== NABOOTOVÁN ==="; echo "$r"; break; }
  sleep 15
done
```

The `uptime < 3600` guard matters: SSH often answers for several seconds *during*
shutdown, and a naive check reports success against a machine that is on its way
down. A service showing `deactivating` or `inactive` seconds after "boot" is the
tell.

## Phase 8 — Diff against the baseline

```bash
docker ps --format "{{.Names}}\t{{.Status}}" | sort > /tmp/post.txt
comm -23 <(cut -f1 /tmp/pre-upgrade-containers.txt) <(cut -f1 /tmp/post.txt) | sed "s/^/CHYBÍ: /"
docker ps --format "{{.Names}}\t{{.Status}}" | grep -iE "restarting|unhealthy"
```

Re-run the ipvlan socket capture from Phase 3 and compare — same IPs, same
listening ports. Then HTTP-probe the stack's own services from the host:

```bash
for s in "n8n 5678" "grafana 3000" "nodered 1880" "influxdb 8086"; do
  set -- $s; printf "%-12s %s\n" "$1" \
    "$(curl -s -o /dev/null -w "%{http_code}" --max-time 6 http://127.0.0.1:$2/)"
done
```

Interpret honestly: `302` (Grafana → login), `401` (Oxidized → auth), `404`
(InfluxDB root) are all healthy. `000` means nothing is listening — check
whether that port was ever published (`docker port <container>`) before
reporting it as breakage.

Give services ~30–60 s after boot before judging them; healthchecks report
`health: starting` and daemons like `pigpiod` can take half a minute. Re-check
once before escalating a failure to the user.

## Phase 9 — Report

Per server: package count, kernel before → after, Docker version, containers
up/expected, whether it rebooted. Then call out anything that needs a human
decision — low disk, unpatched kernels, EOL releases (Debian 11 bullseye is out
of standard support), containers that did not return.

State plainly what you did *not* cover: unreachable hosts, skipped servers, and
anything you deliberately left for the user.
