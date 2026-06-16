# Oklyn Local for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/ADNPolymerase/ha-oklyn-local)
[![GitHub Release](https://badgen.net/github/release/ADNPolymerase/ha-oklyn-local)](https://github.com/ADNPolymerase/ha-oklyn-local/releases)
[![Validate](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml/badge.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/adnpolymerase)

<a href="https://buymeacoffee.com/adnpolymerase" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" alt="Buy Me A Coffee" height="60"></a>

**Local, read-only** Home Assistant integration for the **Oklyn** pool
controller. It polls the controller directly over your LAN (HTTP, port 80) —
**no cloud, no account, no token** — and exposes the measurements as
`sensor` / `binary_sensor` entities.

> 🇫🇷 [Lire en français](README.fr.md)

> ⚠️ **Proof of concept — read-only.** This integration never sends a command:
> no pump / AUX control, no Wi-Fi config, no `PUT`/`POST`. It only reads
> `http://<ip>/api/info` and `http://<ip>/api/data`. Some fields are decoded
> from real-world testing; a few remain **unknown** — see
> [Help wanted](#help-wanted-decode-the-unknown-fields) below.

> ☁️ **Need control (pump, auxiliaries)?** The Oklyn controller can only be
> *commanded* through the cloud. Use the companion cloud integration
> [ADNPolymerase/ha-oklyn](https://github.com/ADNPolymerase/ha-oklyn) for that.
> This project is for fast, cloud-independent **reading**.

---

## Features

- **pH** — corrected (`(PH1 + APH) / 100`) and raw probe value
- **RedOx / ORP** — corrected (`(ORP + ARX) / 10`, mV) and raw probe value
- **Water** and **air** temperature (°C)
- **Pump**: running state + mode (`auto` / `manuel`), decoded from the `SC1` status word
- **Auxiliary 1**: output state, with configurable name & type (light / heating / electrolyzer / custom)
- **Diagnostics**: Wi-Fi signal, free memory, firmware/core/SDK versions, service/key/config flags
- **Raw fields** exposed (disabled by default) for further analysis
- Corrected sensors (pH, RedOx, water/air temperature) expose `raw_*` / `offset_*` /
  `corrected` as state attributes for full traceability
- Full UI configuration — `oklyn.local` (mDNS) or IP, plus polling interval, no YAML
- Short HTTP timeout, configurable polling (15 / 30 / 60 / 120 / 300 s)
- Robust to the controller's intermittent empty responses (built-in retries)
- English and French translations

---

## Installation via HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/ADNPolymerase/ha-oklyn-local` with category **Integration**.
4. Search for **Oklyn Local** and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **Oklyn Local**.
7. Enter the controller's host: either its mDNS name `oklyn.local`, or its IP address (e.g. `192.168.1.100`).

> 💡 **Tip:** `oklyn.local` works out of the box on most home networks (mDNS).
> If your network doesn't resolve `.local` names (some routers / VLANs / Docker
> setups don't), assign a static IP (DHCP reservation) to the controller instead
> so the address never changes between reboots.

## Manual installation

1. Copy the `custom_components/oklyn_local/` folder into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant, then add the integration as above.

---

## Local discovery / mDNS

The Oklyn controller advertises its local HTTP service through mDNS/zeroconf:

```text
_http._tcp.local → oklyn.local:80
```

Confirmed via:

```bash
dns-sd -B _http._tcp local        # → oklyn
dns-sd -L oklyn _http._tcp local  # → oklyn.local.:80
```

Confirmed local endpoints (both work with the mDNS name or the IP):

```text
GET http://oklyn.local/api/info
GET http://oklyn.local/api/data
```

If `.local` resolution doesn't work on your network (some routers / VLANs /
Docker networks don't support mDNS), use the device's IP address instead — the
config flow accepts either.

---

## Endpoints used

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `http://<host>/api/info` | controller technical info |
| `GET` | `http://<host>/api/data` | raw measurements + status word |

The local HTTP server is a **diagnostic + Wi-Fi provisioning portal**. It exposes
**no command endpoint** — pump/AUX control is cloud-only by design.

---

## Network findings

Local scans against a real controller (firmware `436`) showed:

```text
$ nmap -Pn -T4 --top-ports 1000 <ip>
PORT   STATE SERVICE
80/tcp open  http
```

- **TCP 80 open** — the local HTTP API documented here.
- **No MQTT** (1883 / 8883), **no HTTPS** (443), **no alt-HTTP** (8080 / 8000) —
  all closed/filtered.
- **No CoAP** (UDP 5683) — closed.
- **UDP 5353 open** — mDNS / zeroconf (see [Local discovery](#local-discovery--mdns) above).
- MAC vendor prefix resolves to **Espressif** — the controller is ESP-based.
- All other scanned TCP/UDP ports were filtered or closed — no other local
  service was found.

No local command endpoint for the pump, AUX1 or AUX2 was found (see
[Reverse engineering notes](#reverse-engineering-notes) below for the full list
of paths tried). Commands appear to be cloud-only: traffic captures show the
controller calling `iot.oklyn.fr` (CNAME `esp.api.oklyn.fr`). This is mentioned
here for diagnostic purposes only — **this integration never talks to that
domain**.

---

## Entities

### Measurements (`/api/data`)
| Entity | Source | Conversion |
| --- | --- | --- |
| `sensor.…_ph` | `PH1` + `APH` | `(PH1 + APH) / 100` (corrected) |
| `sensor.…_ph_sonde` | `PH1` | `PH1 / 100` (raw probe, disabled by default) |
| `sensor.…_redox` | `ORP` + `ARX` | `(ORP + ARX) / 10` mV (corrected) |
| `sensor.…_redox_sonde` | `ORP` | `ORP / 10` mV (raw probe, disabled by default) |
| `sensor.…_temperature_eau` | `EAU` + `ATE` | `(EAU + ATE) / 100` °C (corrected) |
| `sensor.…_temperature_eau_sonde` | `EAU` | `EAU / 100` °C (raw probe, disabled by default) |
| `sensor.…_temperature_air` | `AIR` + `ATA` | `(AIR + ATA) / 100` °C (corrected) |
| `sensor.…_temperature_air_sonde` | `AIR` | `AIR / 100` °C (raw probe, disabled by default) |

> `APH` / `ARX` / `ATA` / `ATE` are **additive probe corrections** applied by the
> controller. Corrected sensors match what the Oklyn app shows.
> Validated: `ATE = 100` = +1.0 °C, `ATA = -40` = −0.4 °C (field-tested 2026-06-15).
>
> The 4 corrected sensors (`ph`, `redox`, `temperature_eau`, `temperature_air`)
> also expose `raw_<field>`, `offset_<field>` and `corrected` as **state
> attributes**, so the full calculation stays visible without extra entities.

### Pump & Auxiliary 1 (decoded from `SC1`)
| Entity | Source | Detail |
| --- | --- | --- |
| `binary_sensor.…_pompe` | `SC1` bit 14 | pump running (real flow) |
| `sensor.…_pompe_mode` | `SC1` bits 19/20 | `auto` / `manuel` |
| `binary_sensor.…_aux1` | `SC1` bit 22 | AUX1 output; **name + type** configurable |

### Diagnostics (`/api/info`)
Wi-Fi signal (dBm), free memory (bytes), `version`, `core_version`, `sdk_version`,
and binary sensors `service_granted`, `key_valid`, `config_valid`.

### Raw fields (`/api/data`, disabled by default)
`HSN, TIM, SC1, BOX, OQT, PQT, HPN, SPN, SC2, ECM, APH, ARX, AMG, ATA, ATE` — exposed
as-is for analysis. Enable per field in the entity settings.

---

## Options

**Settings → Devices & Services → Oklyn Local → Configure**

| Option | Default | Description |
| --- | --- | --- |
| Polling interval | 30 s | 15 / 30 / 60 / 120 / 300 s |
| AUX1 name | Auxiliaire 1 | Friendly name for the AUX1 binary sensor |
| AUX1 type | custom | `light` / `heating` / `electrolyzer` / `custom` → icon + device_class |

---

## What is local vs cloud-only

Field-testing shows a clear split: `/api/data` exposes **real-time physical measurements + calibration corrections + relay states**. Everything else (programs, setpoints, configuration) lives on the Oklyn cloud servers only.

| Parameter | Local `/api/data` |
|---|---|
| AUX1 ON/OFF | ✅ `SC1` bit 22 |
| Pump ON/OFF/auto | ✅ `SC1` bits 14/19/20 |
| pH probe correction (`APH`) | ✅ field `APH` |
| RedOx probe correction (`ARX`) | ✅ field `ARX` |
| Water temp correction (`ATE`) | ✅ field `ATE` |
| Air temp correction (`ATA`) | ✅ field `ATA` |
| Disinfection type (chlorine/salt) | ❌ cloud only |
| Pool volume | ❌ cloud only |
| Frost protection setpoint | ❌ cloud only |
| Filtration mode (auto / fixed) | ❌ cloud only |
| Regulation setpoints (pH, RedOx) | ❌ cloud only |
| AUX2 state | ❌ not exposed locally (firmware) |

---

## The `SC1` status word

`SC1` is a 32-bit status field. Confirmed bits (field-tested):

| Bit | Mask | Meaning |
| --- | --- | --- |
| 14 | `0x4000` | pump running |
| 19 | `0x80000` | manual command **ON** (transient override) |
| 20 | `0x100000` | manual command **OFF** (transient override) |
| 21 + 27 | `0x200000` + `0x8000000` | pump running in **auto** mode |
| 22 | `0x400000` | **AUX1** output |

`SC1 = 0` means idle (pump off, in auto). Manual override bits (19/20) are transient
and clear after a few minutes back to auto.

---

## Help wanted: decode the unknown fields

This is the fun part. Several fields are **not yet understood**, and Oklyn provides
no public documentation. If you own an Oklyn controller, **you can help map them** —
purely by reading, never by sending commands.

### Still unknown

| Field / bit | Current guess | What we need |
| --- | --- | --- |
| `HSN` | hardware serial (= `serial`) | confirm on other units |
| `TIM` | Unix timestamp of the snapshot | confirm |
| `OQT` / `PQT` | ORP / pH measurement quality (%) | confirm scale |
| `BOX` | controller internal temperature (°C, probable) | confirm vs ambient |
| `HPN` / `SPN` | constant here (2 / 10) — pump count? program? | values on other setups |
| `ECM`, `SC2`, `AMG` | unknown | any correlation you observe |
| **AUX2** | **not exposed locally** (firmware) | confirm on other firmware versions |
| `SC1` bits 0–13, 15–18, 23–26, 28–31 | unused/unknown | any bit that toggles |
| Other unlisted `/api/data` keys | — | report them |

### How to contribute a reading

1. **Grab a snapshot** (replace the IP):
   ```bash
   curl -s http://IP_OKLYN/api/data
   curl -s http://IP_OKLYN/api/info   # mask mac/ssid/serial before sharing
   ```
   `/api/data` sometimes returns an empty body — just retry a few times.
2. **Change one thing** on your controller (e.g. turn AUX2 on, switch pump to
   manual, change a regulation setpoint) and grab a snapshot **before and after**.
3. **Open an issue** with: the two snapshots, what you changed, your controller
   model and firmware (`version` / `core_version` from `/api/info`), and the value
   shown in the Oklyn app if relevant.

   → [Open a "field decode" issue](https://github.com/ADNPolymerase/ha-oklyn-local/issues/new)

A single bit that flips when you toggle something is often all it takes to map a
new feature. Findings are credited in the changelog. 🙏

> ⚠️ Before sharing `/api/info`, redact `mac`, `ssid` and `serial`.

---

## Error handling

- Short HTTP timeout (5 s); polling default 30 s (configurable).
- `/api/data` fails → measurement / pump / AUX entities become unavailable.
- `/api/info` fails → diagnostic entities become unavailable.
- Both fail → `UpdateFailed` (all entities unavailable).
- A missing field never crashes — the affected entity just goes unavailable.
- The controller often returns an **empty HTTP 200** on `/api/data`; the client
  retries a few times per cycle to smooth this out.

---

## Read-only limitation

**This integration is read-only.** It does not and cannot currently:

- control the filtration pump;
- control AUX1;
- control AUX2;
- change Oklyn schedules / regulation setpoints;
- change Wi-Fi settings;
- replace the Oklyn cloud for any command.

It will never send `POST`/`PUT` to the controller (including `/wifi-try`), and
performs no aggressive scanning beyond the documented `GET` requests.

## Known limitations (local API)

- **No local command endpoint was found** — see [Reverse engineering notes](#reverse-engineering-notes).
- **AUX2 state is not currently exposed** in `/api/data` — turning it on changes
  no field. Use the cloud integration for AUX2.
- **AUX mode** (switch vs regulator) and **regulation setpoints** (pH, RedOx) are
  not exposed locally — cloud/config only.
- The cloud/API is still required for native Oklyn commands.
- Single device per host.

---

## Reverse engineering notes

These paths were tried against a real controller (firmware `436`) and all
returned `404 Not Found` (including `OPTIONS`). Recorded here so others don't
have to repeat the same tests:

```text
/api/status        /api/last_values    /api/pump           /api/aux
/api/aux2           /api/relay          /api/relays          /api/ph
/api/orp            /api/measure        /api/measures        /api/config
/api/device         /api/schedules      /api/errors           /api/alerts
/status  /data  /pump  /aux  /aux2  /relay  /relays  /ph  /orp  /measure  /measures
```

The controller's own local web UI (`http://oklyn.local/`) only references:

```text
/api/info  /api/wifi  /wifi-scan  /wifi-try
```

Its HTML/JS contains no route referencing `pump`, `aux`, `aux2`, `relay`,
`pompe`, `filtration`, `gpio` or `output` — confirming the local server only
serves diagnostics + Wi-Fi provisioning, not control. If you find a working
command endpoint on a different firmware version, please
[open an issue](https://github.com/ADNPolymerase/ha-oklyn-local/issues/new) —
don't add it to this integration without discussion (see
[Read-only limitation](#read-only-limitation) above).

---

## Summary

Oklyn exposes useful local measurement data over HTTP. The controller can be
discovered as `oklyn.local` through mDNS. Only TCP port 80 and UDP port 5353
were found open locally. No local command endpoint for the pump, AUX1 or AUX2
has been found so far. **This integration is therefore intentionally
read-only.**

---

## Contributing

Issues and pull requests welcome at
<https://github.com/ADNPolymerase/ha-oklyn-local/issues>. Field-decode reports
(see [Help wanted](#help-wanted-decode-the-unknown-fields)) are especially valuable.

## License

MIT — see [LICENSE](LICENSE).
