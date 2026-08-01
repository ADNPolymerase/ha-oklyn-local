<p align="center">
  <img src="https://raw.githubusercontent.com/ADNPolymerase/ha-oklyn/main/custom_components/oklyn/brand/logo.png" alt="Oklyn" height="80">
</p>

# Oklyn Local for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub Release](https://badgen.net/github/release/ADNPolymerase/ha-oklyn-local)](https://github.com/ADNPolymerase/ha-oklyn-local/releases)
[![Validate](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml/badge.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/adnpolymerase)

<a href="https://buymeacoffee.com/adnpolymerase" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" alt="Buy Me A Coffee" height="60"></a>
<a href="https://adnpolymerase.github.io/HA/" target="_blank"><img src="https://raw.githubusercontent.com/ADNPolymerase/HA/main/assets/site-button.svg" alt="Link to my github.io for my other projects" height="60"></a>

**Local, read-only** Home Assistant integration for the **Oklyn** pool
controller. It polls the controller directly over your LAN (HTTP, port 80) —
**no cloud, no account, no token** — and exposes the measurements as
`sensor` / `binary_sensor` entities.

> 🇫🇷 [Lire en français](README.fr.md)

> ⚠️ **Proof of concept — read-only.** This integration never sends a command:
> no pump / AUX control, no Wi-Fi config, no `PUT`/`POST`. It only reads
> `http://<ip>/api/info` and `http://<ip>/api/data`. The field decoding has been
> **validated by Oklyn** (June 2026) — see
> [Field confirmations](#help-wanted-decode-the-unknown-fields) below.

> ☁️ **Need control (pump, auxiliaries)?** The Oklyn controller can only be
> *commanded* through the cloud. Use the companion cloud integration
> [ADNPolymerase/ha-oklyn](https://github.com/ADNPolymerase/ha-oklyn) for that.
> This project is for fast, cloud-independent **reading**.

---

## Features

- **pH, RedOx/ORP, water & air temperature** — corrected values (probe + controller offset), with `raw_*` / `offset_*` / `corrected` attributes for full traceability, plus raw probe sensors (disabled by default).
- **Salt** (salt pool models, g/L, `ECM / 1000`) — disabled by default.
- **Pump** (running state + `auto` / `manuel` mode) and **Auxiliaries 1 & 2** (configurable name & type), decoded from the `SC1` status word.
- **Diagnostics**: Wi-Fi signal, free memory, firmware versions, service/key/config flags — and **raw fields** (disabled by default) for analysis.
- **Router linking**: the MAC address is registered in HA, linking the device to your router integration (Livebox, Freebox, UniFi…).
- Full UI configuration (`oklyn.local` or IP), configurable polling (15–300 s), built-in retries, **last known good cache** with a `Dernière mesure boîtier` staleness sensor.
- English, French and Russian translations.

---

## Installation (HACS)

Available directly in HACS — no custom repository needed.

1. Open **HACS**, search for **Oklyn Local** and download it.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration** → **Oklyn Local**, then enter the controller's host: `oklyn.local` (mDNS) or its IP.

> 💡 If your network doesn't resolve `.local` names (some routers / VLANs / Docker setups), use a static IP (DHCP reservation) instead.

As a custom repository: HACS → **⋮** → **Custom repositories** → `https://github.com/ADNPolymerase/ha-oklyn-local`, category **Integration**.

Manual alternative: copy `custom_components/oklyn_local/` into `config/custom_components/`, restart, then add the integration.

---

## Local API

The controller advertises itself via mDNS (`_http._tcp.local → oklyn.local:80`) and exposes two endpoints:

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `http://<host>/api/info` | controller technical info |
| `GET` | `http://<host>/api/data` | raw measurements + status word |

The local HTTP server is a **diagnostic + Wi-Fi provisioning portal** — it exposes **no command endpoint**; pump/AUX control is cloud-only by design. Network scans (firmware `436`) found only TCP 80 and UDP 5353 (mDNS) open — no MQTT, HTTPS, alt-HTTP or CoAP. The controller is ESP-based (Espressif MAC prefix), and traffic captures show commands go through `iot.oklyn.fr` — **this integration never talks to that domain**.

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

### Pump, Auxiliary 1 & Auxiliary 2 (decoded from `SC1`)
| Entity | Source | Detail |
| --- | --- | --- |
| `binary_sensor.…_pompe` | `SC1` bit 14 | pump running (real flow) |
| `sensor.…_pompe_mode` | `SC1` bits 19/20 | `auto` / `manuel` |
| `binary_sensor.…_aux1` | `SC1` bit 22 | AUX1 output; **name + type** configurable |
| `binary_sensor.…_aux2` | `SC1` bit 23 | AUX2 output; **name + type** configurable — confirmed field-tested 2026-06-18 (kurtenweb) |

### Diagnostics (`/api/info` + `/api/data`)
Wi-Fi signal (dBm), free memory (bytes), `version`, `core_version`, `sdk_version`,
and binary sensors `service_granted`, `key_valid`, `config_valid`.

`sensor.…_derniere_mesure` — timestamp of the controller's last internal snapshot
(`TIM` field, ~5 min refresh cycle). Stays frozen when the cache is being served,
making stale data easy to spot.

### Raw fields (`/api/data`, disabled by default)
`HSN, TIM, SC1, BOX, OQT, PQT, HPN, SPN, SC2, APH, ARX, AMG, ATA, ATE` — exposed
as-is for analysis. Enable per field in the entity settings.
(`ECM` is no longer a raw field — it is the decoded **Sel** sensor.)
Note: `OQT`/`PQT` contain data but are not used by Oklyn firmware; `AMG` is the salt probe correction.

---

## Options

**Settings → Devices & Services → Oklyn Local → Configure**

| Option | Default | Description |
| --- | --- | --- |
| Polling interval | 30 s | 15 / 30 / 60 / 120 / 300 s — shown as a dropdown with the current value pre-selected |
| AUX1 name | Auxiliaire 1 | Friendly name for the AUX1 binary sensor |
| AUX1 type | custom | `light` / `heating` / `electrolyzer` / `custom` → icon + device_class |
| AUX2 name | Auxiliaire 2 | Friendly name for the AUX2 binary sensor |
| AUX2 type | custom | `light` / `heating` / `electrolyzer` / `custom` → icon + device_class |

---

## What is local vs cloud-only

Field-testing shows a clear split: `/api/data` exposes **real-time physical measurements + calibration corrections + relay states**. Everything else (programs, setpoints, configuration) lives on the Oklyn cloud servers only.

| Parameter | Local `/api/data` |
|---|---|
| AUX1 ON/OFF | ✅ `SC1` bit 22 |
| AUX2 ON/OFF | ✅ `SC1` bit 23 — confirmed field-tested 2026-06-18 |
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
| 23 | `0x800000` | **AUX2** output — confirmed field-tested 2026-06-18 (kurtenweb) |

`SC1 = 0` means idle (pump off, in auto). Manual override bits (19/20) are transient
and clear after a few minutes back to auto.

> ⚠️ **AUX2 propagation delay (~2 min):** the controller takes ~2 minutes to update SC1 bit 23 after a cloud command changes AUX2 (firmware limitation — the register lags the relay). A cloud ON shorter than ~2 min is never seen locally. Ideas for a workaround are welcome via issues.

---

## Help wanted: decode the unknown fields

This is the fun part. Several fields are **not yet understood**, and Oklyn provides
no public documentation. If you own an Oklyn controller, **you can help map them** —
purely by reading, never by sending commands.

### Confirmed by Oklyn (2026-06-29)

| Field | Status | Detail |
| --- | --- | --- |
| `OQT` / `PQT` | ✅ **Not used** | Contain data but are not used by the firmware (confirmed by Oklyn). |
| `AMG` | ✅ **Salt probe correction** | Additive correction for the salt probe — same logic as `APH` / `ARX` / `ATE` / `ATA`. |
| `SC2`, `HPN`, `SPN` | ✅ **Decoding confirmed correct** | Exact semantics not documented, but the integration's handling is validated. |
| **Regulator mode (AUX)** | ✅ **Electrolyzer only** | Activates the AUX relay when RedOx < setpoint AND the pump is running. Not suitable for a dosing pump. |

### Still unknown

| Field / bit | Current guess | What we need |
| --- | --- | --- |
| `HSN` | hardware serial (= `serial`) | confirm on other units |
| `TIM` | Unix timestamp of the snapshot (local time, no UTC offset) | confirm on other timezones |
| `BOX` | controller internal temperature (°C, probable) | confirm vs ambient |
| `SC1` bits 0–13, 15–18, 24–26, 28–31 | unused/unknown | any bit that toggles |
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

On failure, the last known values are served from cache (entities stay available); the cache expires after **3 × polling interval**, beyond which entities go unavailable rather than serve stale state. Empty HTTP 200 responses (frequent on `/api/data`) are retried within the cycle; when the controller comes back after a dropout, an extra poll fires 1 s later. On cache use, the `Dernière mesure boîtier` sensor freezes, making stale data visible. A missing field never crashes — the entity just goes unavailable.

---

## Read-only limitation

**This integration is read-only.** It cannot control the pump or auxiliaries, change schedules, setpoints or Wi-Fi settings — no local command endpoint exists (see [Reverse engineering notes](#reverse-engineering-notes)), and it will never send `POST`/`PUT` to the controller. AUX mode (switch vs regulator) and regulation setpoints are cloud-only; the cloud integration remains required for commands. Single device per host.

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

Its HTML/JS contains no route referencing `pump`, `aux`, `relay`, `filtration`, `gpio` or `output` — confirming the local server only serves diagnostics + Wi-Fi provisioning. If you find a working command endpoint on another firmware, please [open an issue](https://github.com/ADNPolymerase/ha-oklyn-local/issues/new) rather than adding it without discussion.

---

## Contributing

Issues and pull requests welcome at
<https://github.com/ADNPolymerase/ha-oklyn-local/issues>. Field-decode reports
(see [Help wanted](#help-wanted-decode-the-unknown-fields)) are especially valuable.

## License

MIT — see [LICENSE](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE).
