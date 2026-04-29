---
name: huawei-olt-manager
description: Expert na automatizaci jednotek Huawei SmartAX MA5683T OLT (verze V800R015C00) přes SSH. Použij tento skill vždy, když uživatel zmíní MA5683T, MA5680T, SmartAX OLT, GPON OLT, optickou síť (FTTH/FTTB), provisioning ONT/ONU, autorizaci ONT, GEM port, service-port, SCUN kartu, GPBD/GPFD desku, nebo požádá o diagnostiku optiky (DDM, Rx/Tx Power), konfiguraci VLAN/native-vlan na ONT, vytvoření line/srv profilu, čtení `display ont autofind`, `display board`, `display ont optical-info`, řešení interaktivních Y/N dotazů v CLI Huawei OLT, deaktivaci stránkování (`scroll`, `screen-length`), nebo cokoliv kolem správy Huawei GPON OLT verze R015. Skill řeší specifická omezení V800R015C00, deterministický workflow pro nasazení nové ONT, parsing výstupů a bezpečné ukončování konfiguračních relací.
---

# Huawei MA5683T (V800R015C00) – SSH Automation Playbook

Tento skill definuje deterministické postupy pro ovládání jednotek Huawei
SmartAX MA5683T přes SSH. Verze firmwaru **V800R015C00** má specifická omezení
v CLI (nestabilní `screen-length`, asynchronní alarmy, povinná interaktivní
potvrzení), která tento skill ošetřuje. Cílem je, aby Claude generoval
posloupnosti příkazů, které **nezamrznou parser**, **nezpůsobí výpadek služby**
a **vrátí strukturovaný výstup**, ze kterého lze dále stavět.

Pokud uživatel popisuje úkol kolem MA5683T, předpokládej tento postup. Pokud
máš pochybnost (jiná verze firmwaru, jiná řada – např. MA5800), zeptej se
před prvním zápisem do konfigurace.

## 1. Příprava SSH relace (kritický krok)

Při každém novém SSH připojení proveď tyto kroky v daném pořadí. Bez nich
hrozí, že automatizovaný klient zamrzne na čekání na `--More--` prompt nebo
na asynchronní hlášku o alarmu.

1. **Vstup do privilegovaného režimu**
   - `enable`
   - `config`

2. **Deaktivace stránkování**
   - V R015 příkaz `screen-length 0 temporary` často selhává nebo neaplikuje
     se na všechny `display` výstupy.
   - Použij `scroll 512` – nastaví maximální možný buffer řádků bez přerušení
     promptem `--More--`.
   - Pokud `scroll 512` skončí chybou *Unrecognized command*, přepadni na
     `screen-length 0 temporary` a explicitně testuj na krátkém příkazu
     (`display version`).

3. **Vypnutí "smart" interaktivity**
   - `undo smart` – zjednoduší výstup pro parsing (vypne nápovědu při chybě
     a podobné konverzační prvky).

4. **Potlačení asynchronních alarmů**
   - `undo alarm output all` – zabrání tomu, aby do středu výstupu přišla
     hláška typu `LOS detected on F/S/P 0/3/12`, která rozbije stavový
     automat parseru.

> **Proč:** R015 sériově serializuje terminálový výstup. Jakýkoliv `--More--`
> nebo asynchronní alarm vloží do streamu netušený obsah a stejnou trasu
> sdílí jak konfigurační, tak event log.

## 2. Zpracování interaktivních dotazů (Y/N)

Huawei OLT u rizikových operací (uložení, smazání, reboot, aktivace
rogue-ONT detekce, hromadná deaktivace portů) vyžaduje interaktivní
potvrzení.

- **Vzor dotazu:** `Are you sure to continue? (y/n)[n]:`
  (přesný formát se mírně liší podle příkazu, někdy `( y/n)`, někdy `[Y/N]`)
- **Reakce:** detekuj substring `(y/n)` (case-insensitive) a odešli `y\n`.
- **Bezpečnostní pojistka:** pokud prompt obsahuje slovo `delete`, `clear`,
  `reset` nebo `reboot`, vyžaduj explicitní potvrzení uživatele předtím,
  než pošleš `y` – nikdy to nedělej "potichu" v rámci bulk skriptu.

## 3. Workflow: Provisioning nové ONT

Deterministický workflow pro přidání nového zákazníka. Předpokládej, že
existují předem připravené `ont-lineprofile` a `ont-srvprofile` (nebo se
zeptej, jaké ID použít).

### Krok 1 – Vyhledání neautorizovaných jednotek

```
display ont autofind all
```

Z výstupu extrahuj pro každou nalezenou ONT:

- `F/S/P` – Frame/Slot/Port
- `SN` – sériové číslo (formát `HWTC` + 8 hex znaků nebo vendor SN)
- `Equipment ID` (volitelně, pomáhá s identifikací modelu)

### Krok 2 – Autorizace ONT

Vstup do GPON rozhraní pro daný slot:

```
interface gpon 0/<slot>
```

Přidání ONT:

```
ont add <port> <ont-id> sn-auth <SN> omci \
    ont-lineprofile-id <line-profile-id> \
    ont-srvprofile-id <srv-profile-id>
```

> **Tip pro R015:** v servisním profilu doporuč `ont-port eth adaptive`,
> aby se systém přizpůsobil počtu ETH portů na konkrétním modelu ONT
> (HG8245, HG8145, EG8145 atd.). Bez `adaptive` může profil odmítnout
> přiřazení ONT s jiným počtem portů, než je v profilu pevně definováno.

### Krok 3 – Konfigurace služeb (L2 bridge / Trunk)

Stále v `interface gpon 0/<slot>` nastav nativní VLAN na ETH portu ONT:

```
ont port native-vlan <port> <ont-id> eth 1 vlan <vlan-id>
```

Opusť `interface` mode (`quit`) a vytvoř service-port (mapuje GEM port
do core VLAN):

```
service-port vlan <vlan-id> gpon 0/<slot>/<port> \
    ont <ont-id> gemport <gem-id> \
    multi-service user-vlan <vlan-id> \
    tag-transform translate
```

> **Proč `tag-transform translate`:** R015 ve výchozím stavu předává
> tag tak, jak ho viděl. Pro čisté oddělení zákaznických VLAN doporuč
> `translate` – tag se přepíše podle service-portu a nedojde k úniku
> uživatelské VLAN do core sítě.

## 4. Workflow: Diagnostika a monitoring

### Diagnostika optiky (DDM)

```
display ont optical-info <port> <ont-id>
```

**Vyhodnocení Rx/Tx Power:**

| Hodnota | Interpretace |
|---|---|
| ONT Rx Power `-8 dBm` až `-27 dBm` | normální provoz |
| ONT Rx Power `< -27 dBm` | hraniční / podezření na ztráty na trase |
| ONT Rx Power `< -28 dBm` | trasa je mimo specifikaci, vyhledat svar/spojku |
| OLT Rx Power (od ONT k OLT) `-8` až `-28 dBm` | normální provoz |
| Tx Power ONT pod `0 dBm` | možný degradovaný laser ONT |

> **Pozn.:** přesné prahy závisí na použitém SFP modulu a třídě GPON
> (Class B+, C+). Pokud uživatel uvádí netypické hodnoty, ověř třídu modulu
> v `display port info <slot>/<port>`.

### Stav hardwaru

- **Desky:** `display board 0`
  - hledej stav `Normal`
  - `Failed`, `Mismatch`, `Offline` → nutný zásah (typicky reseat / RMA)
- **Zátěž SCUN karty (řídicí):** `display cpu 0/7`
  (slot 7 je ve standardním osazení MA5683T pozice řídicí karty SCUN/SCUL;
  pokud je řídicí karta v jiném slotu, uprav)
- **Teplota / napájení:** `display temperature` resp. `display power 0`

## 5. Ukončení práce a uložení

Změny v Huawei OLT nejsou perzistentní, dokud nedojde k explicitnímu
uložení. Po dokončení libovolné konfigurační operace:

```
save
```

OLT se zeptá `Are you sure to save the data? (y/n)[n]:` – odpověz `y`.

Volitelně před odhlášením:

```
quit
quit
```

(první `quit` z `config` mode, druhý ukončí terminálovou relaci).

## 6. Onboarding nového uživatele a SSH RSA klíče

### Krok 6.1 — Import RSA peer-public-key

V `MA5683T(config)#` (R015) nebo `MA5603T(config)#` (R018):

```
rsa peer-public-key <KEY_NAME>
public-key-code begin
<PKCS#1 hex wrapped na 64 znaků, 9 řádků pro 2048-bit klíč>
public-key-code end
peer-public-key end
display rsa peer-public-key brief
```

**Pravidla pro klíč:**
- VRP/MA56xx přijímá **PKCS#1 raw** (`SEQUENCE { modulus, publicExponent }`),
  začíná `3082010a` (2048-bit). NE X.509 (`30820122`).
- Maximum **2048-bit** (4096 nezvládá).
- Wrap na **64 znaků** per řádek (CLI buffer ~520).
- Konverze z OpenSSH `.pub` na PKCS#1 hex:
  ```bash
  ssh-keygen -e -m PKCS8 -f key.pub > k.pem
  openssl rsa -pubin -in k.pem -RSAPublicKey_out -outform DER \
    | od -An -tx1 | tr -d ' \n' | fold -w 64
  ```
- MA5603T R018 (a MA5683T R015) ukládají interně bez leading 0x00 — `display rsa peer-public-key name X` ukazuje `30820109` místo `3082010a`. To je OK, klíč funguje.

### Krok 6.2 — Vytvoření CLI uživatele (interaktivní wizard)

V privilege mode (`MA5683T#` / `MA5603T#`):

```
terminal user name
```

Wizard se postupně ptá (ověřeno na R018 V800R018C10, MA5603T):

| Prompt | Odpověď |
|---|---|
| `User Name(length<6,15>)` | `n8n_backup` (6-15 chars) |
| `User Password(length<6,15>)` | silné heslo, **6-15 chars max** |
| `Confirm Password(length<6,15>)` | znovu heslo |
| `User profile name(<=15 chars)[root]` | ENTER (default `root`) |
| `User's Level: 1. Common User 2. Operator` | `1` (Common User stačí pro read-only) |
| `Permitted Reenter Number(0--20)` | `5` (max současných session) |
| `User's Appended Info(<=30 chars)` | ENTER (volitelný popis) |
| `Adding user successfully. Repeat? (y/n)[n]` | `n` (nebo `y` pro dalšího user) |

R015 wizard je podobný, ale může mít jiné pořadí promptů.

### Krok 6.3 — Mapping SSH user na RSA klíč

V config view:

```
ssh user <USER> authentication-type <TYPE>
ssh user <USER> assign rsa-key <KEY_NAME>
```

Auth-type možnosti (R018):
- `rsa` — pouze RSA klíč (production)
- `password` — pouze heslo
- `password-publickey` — OBOJÍ (heslo I klíč musí prošlo)
- `all` — heslo NEBO RSA (víc tolerantní pro debugging)

**Pozn.:** Hláška "Authentication type is set, and will be in effect next time" znamená že nastavení se aplikuje na **další** session.

### Krok 6.4 — Save

```
save
```

Auto-save může běžet (viz `display autosave`), ale manual save zajistí persistence okamžitě. Save vyžaduje pár sekund (zapisuje na obě SCUN karty).

### Známý problém — Oxidized + net-ssh padding error (R018)

Při použití **Ruby net-ssh** (Oxidized 0.36.0) proti MA5603T V800R018C10:

```
Net::SSH::Exception: padding error, need <random_huge_number> block 16
```

Příčina: net-ssh decryption inkompatibilita s SSH stack na R018. **OpenSSH klient z téhož hostu se stejným klíčem funguje** (`Authenticated using publickey`). Není to problem klíče ani konfigurace OLT.

Test že problém je na klient straně:
```bash
docker exec -u oxidized oxidized ssh -i /home/oxidized/.ssh/key \
  -o KexAlgorithms=diffie-hellman-group14-sha1 \
  -o Ciphers=aes256-ctr -o HostKeyAlgorithms=ssh-rsa \
  -o PubkeyAcceptedAlgorithms=ssh-rsa \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  user@OLT_IP
# → "Authenticated using publickey" = SSH server OK, problém v Oxidized net-ssh
```

Workarounds:
1. **Per-node SSH options** v Oxidized (cipher/MAC override pro tento OLT, group config)
2. **Upgrade Oxidized** na novější verzi (sledovat changelog na opravy net-ssh)
3. **External SSH wrapper** — Oxidized custom input plugin volající `ssh` CLI místo net-ssh
4. Akceptovat failure dokud nevyřešeno (workaround #1 je nejbližší k vyzkoušení)

### Připojení s jinými blokujícími faktory

Pokud SSH connection padá s `Connection reset by peer` (nikoli auth fail):

- Zkontroluj `display sysman ip-refuse ssh` — refuse ACL?
- Zkontroluj `display sysman ip-access ssh` — allow-list ACL? (prázdný = všechno povolené)
- Zkontroluj `display sysman firewall ssh` — firewall enabled?
- Zkontroluj `display ssh server session` — počet aktivních session (limit 22 globálně, per-user dle `Permitted Reenter Number`)

R018 má interní anti-bruteforce mechanismus (po opakovaných failed auth z téhož source IP může TCP-resetovat nové connecty), ale display příkaz pro něj nezná. Cooldown 10-30 min.

## 7. Technické limity pro skripty

- **Oprávnění:** všechny konfigurační operace vyžadují uživatele s
  `Privilege Level 3` (administrator). Pro pouhý read-only monitoring
  stačí Level 1.
- **Souběžnost:** MA5683T podporuje **maximálně 22 současných SSH
  relací**. Při návrhu hromadných nástrojů počítej s frontou a re-try
  s exponential backoff – při překročení limitu vrací OLT
  `% Failure: connection refused`.
- **Authentication timeout:** výchozí hodnota je **60 s**. Pokud běží
  pomalé `display` (např. `display service-port all` na plně osazeném
  šasi), zvyš timeout na klientské straně, jinak hrozí předčasné
  odpojení uprostřed výstupu.
- **Rate limit příkazů:** R015 nemá tvrdý rate limit, ale rychlé
  posílání desítek `service-port` definic může zaplnit interní
  buffer; mezi příkazy nech alespoň 50–100 ms.

## 7. Doporučený výstupní formát

Když uživatel požádá o diagnostiku nebo provisioning, vrať odpověď
v této struktuře (přizpůsob obsahu):

```
1) Co budu dělat: <jedna věta>
2) Posloupnost příkazů: <očíslovaný blok kódu>
3) Očekávaný výstup: <jak má vypadat zdravý stav>
4) Co dělat při chybě: <konkrétní fallback>
```

Tento formát uživateli šetří kontextové přepínání mezi vysvětlením
a copy-paste do konzole.

## 8. Antipattern – co NEDĚLAT

- Neposílat `reboot` ani `reset` desky bez explicitního potvrzení od
  uživatele – výpadek může postihnout stovky účastníků.
- Nepoužívat `undo service-port <index>` bez ověření, co na indexu skutečně
  je (`display service-port port <slot>/<port>`).
- Neprovádět `save` v půli rozpracované konfigurace, pokud si nejsi jist –
  uloží se i nedokončené změny.
- Neopírat se o `screen-length 0 temporary` jako jediný nástroj proti
  stránkování – v R015 je nespolehlivý (viz sekce 1).
