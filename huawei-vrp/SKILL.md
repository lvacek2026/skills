---
name: huawei-vrp
description: >
  Expert on Huawei CloudEngine S57xx and S67xx series network devices (VRP – Versatile Routing Platform).
  Use this skill whenever the user mentions Huawei switch, CloudEngine, VRP, S5700, S5731, S5735,
  S6700, S6730, iStack, Eth-Trunk, or requests VLAN configuration, Trunk port, LACP, STP, MSTP,
  SSH access, port diagnostics, analysis of `display` command output, or any other task
  related to management or configuration of Huawei switches. Skill ensures correct VRP syntax,
  best practices and proper use of networking terminology.
---

# Huawei VRP – CloudEngine S57xx / S67xx Expert Skill

## Role and Context

You are an expert on Huawei network devices, specifically **CloudEngine S57xx** (S5700, S5731, S5735)
and **S67xx** (S6700, S6730) series switches running **VRP (Versatile Routing Platform)**.

---

## 1. Basic VRP Syntax Rules

```
system-view          ← enter configuration mode
quit                 ← go one level up
return               ← return to user-view
display ...          ← show status (NEVER use "show"!)
save                 ← permanently save configuration to vrpcfg.zip
```

> ⚠️ **Always remind the user to run `save`** after every configuration change.
> Without saving, configuration will be lost after a restart.

---

## 2. Port Types on S57xx/S67xx

| Label                 | Description                          |
|-----------------------|--------------------------------------|
| `GigabitEthernet`     | 1G port (e.g. GE0/0/1)              |
| `XGigabitEthernet`    | 10G port (e.g. XGE0/0/1)            |
| `MultiGigabitEthernet`| 2.5G/5G/10G (selected models)        |
| `40GE` / `100GE`      | Uplink ports on S6730 etc.           |

**Abbreviated commands:**
- `GigabitEthernet 0/0/1` → can be shortened to `gi 0/0/1`
- `XGigabitEthernet 0/0/1` → `xgi 0/0/1`

---

## 3. VLAN Configuration

```bash
system-view
vlan batch 10 20 30         # create multiple VLANs at once
vlan 10
 description Management
quit
```

---

## 4. Port Configuration – Access, Trunk, Hybrid

### Access port
```bash
interface GigabitEthernet 0/0/1
 port link-type access
 port default vlan 10
 description PC-Office
quit
```

### Trunk port
```bash
interface GigabitEthernet 0/0/24
 port link-type trunk
 port trunk pvid vlan 1
 port trunk allow-pass vlan 10 20 30
 description Uplink-SW02
quit
```

### Hybrid port (typical for Huawei)
```bash
interface GigabitEthernet 0/0/5
 port link-type hybrid
 port hybrid pvid vlan 10
 port hybrid tagged vlan 20 30       # tagged VLANs
 port hybrid untagged vlan 10        # untagged for access traffic
quit
```

---

## 5. Eth-Trunk (LACP)

```bash
interface Eth-Trunk 1
 trunkport GigabitEthernet 0/0/23
 trunkport GigabitEthernet 0/0/24
 mode lacp-static                    # recommended mode
 max active-linknumber 2
 description Uplink-LACP-to-Core
 port link-type trunk
 port trunk allow-pass vlan 10 20 30
quit
```

> Verify: `display eth-trunk 1`

---

## 6. iStack – Stacking

```bash
# On each switch in the stack:
system-view
stack slot 0 priority 200           # higher = master (0–255)
stack slot 0 domain 10              # same domain ID for the entire stack

# Stack ports (physical):
interface stack-port 0/1
 port interface XGigabitEthernet 0/0/27 enable
quit
```

> Verify: `display stack` | `display stack topology`

---

## 7. STP / MSTP

```bash
system-view
stp mode mstp
stp region-configuration
 region-name COMPANY-REGION
 instance 1 vlan 10 20
 instance 2 vlan 30 40
 active region-configuration
quit
stp instance 1 priority 4096        # root bridge for instance 1
stp enable
```

> Verify: `display stp brief` | `display stp instance 1`

---

## 8. SSH Access – Complete Setup

```bash
system-view

# 1. RSA keys (required for SSH)
rsa local-key-pair create
# Enter key length: recommended 2048

# 2. Local user
aaa
 local-user admin password irreversible-cipher SecurePass123!
 local-user admin service-type ssh
 local-user admin privilege level 15
quit

# 3. VTY lines
user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh
 idle-timeout 10 0
quit

# 4. Enable SSH server
stelnet server enable

# 5. STELNET user assignment (optional)
ssh user admin authentication-type password
```

> ⚠️ Don't forget: `save`
> Verify: `display ssh server status` | `display ssh user-information`

---

## 9. Analyzing `display` Command Output

When the user pastes output of a `display` command, automatically perform:

### Port diagnostics (`display interface GEx/x/x`)
Look for:
- **CRC errors** – cabling or SFP module issues
- **Input/Output errors** – physical layer, faulty cable
- **Duplex mismatch** – check `Duplex` (half vs. full)
- **Speed mismatch** – auto-negotiation problem
- **Discards (Inbound/Outbound)** – buffer overload / QoS issue

### STP diagnostics (`display stp brief`)
Look for:
- **DISCARDING** state – blocked port (normal for non-root ports)
- **Unexpected DISCARDING** on uplink → check priority/root bridge

### Eth-Trunk diagnostics (`display eth-trunk X`)
Look for:
- Inactive member links → check LACP mode on the other side
- Speed mismatch within the trunk

---

## 10. Useful Diagnostic Commands

```plaintext
display version                          # VRP and HW version
display device                           # card/port overview
display ip interface brief               # IP addresses
display vlan summary                     # VLAN overview
display mac-address                      # MAC table
display interface brief                  # status of all ports
display interface GigabitEthernet 0/0/1  # detailed port statistics
display stp brief                        # STP status on ports
display eth-trunk 1                      # Eth-Trunk status
display stack                            # iStack status
display cpu-usage                        # CPU utilization
display memory-usage                     # memory usage
display logbuffer                        # system log
display current-configuration            # current configuration
```

---

## 11. New Switch Template (Quick-Start)

See `references/quickstart-template.md` for a complete basic configuration template for a new switch
(hostname, NTP, SNMP, management VLAN, SSH, logging).

---

## Notes and Best Practices

1. **Always save** after configuration: `save` → confirm with `y`
2. **Test port** before production deployment: `display interface Gx/x/x`
3. **Prefer LACP** over static trunk – detects link failures
4. **iStack domain ID** must be identical across the entire stack
5. **SSH instead of Telnet** – Telnet transmits passwords in plain text
6. For complex scenarios (BGP, OSPF, QoS, ACL) ask for specific requirements
