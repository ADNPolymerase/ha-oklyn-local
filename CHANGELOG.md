# Changelog

## 0.1.8b1 (beta)

- **Beta** : new `binary_sensor` AUX2 (`Auxiliaire 2`), decoded from SC1 bit 23.
  Confirmed by field test 2026-06-18 (kurtenweb, SC1 diff = 2²³ = 8 388 608
  on AUX2 ON→OFF toggle). Awaiting confirmation on a second installation.
  To verify: enable the entity and compare its state with the physical AUX2 relay.

## 0.1.7

- New sensor `Sel` (`sensor.oklyn_sel`, g/L): decoded from the `ECM` field
  (`ECM / 1000`), confirmed field-tested 2026-06-18 (ECM=2404 → 2.4 g/L).
  Disabled by default — enable it in HA for salt pool models.
- `ECM` removed from raw diagnostic fields (now a proper decoded sensor).

## 0.1.6

- Device registry: the controller's MAC address is now registered via
  `CONNECTION_NETWORK_MAC` — HA automatically links the device to the router
  integration (Livebox, Freebox, UniFi, etc.).

## 0.1.5

- Resilience: coordinator caches last known good data — entities stay available
  with the most recently received values on polling failure instead of going
  unavailable. A warning is logged with the last `TIM` timestamp.
- New diagnostic sensor `Dernière mesure boîtier` (enabled by default): exposes
  the `TIM` field as an HA timestamp — frozen value = cache in use.

## 0.1.4

- Resilience: coordinator now caches last known good data. On polling failure,
  entities stay available with the most recently received values instead of going
  unavailable. A warning is logged with the last `TIM` timestamp.
- New diagnostic sensor `derniere_mesure` (enabled by default): exposes the `TIM`
  field as a proper HA timestamp, showing exactly when the controller last refreshed
  its snapshot — useful to spot stale data at a glance.

## 0.1.3

- Decoded `ATA` / `ATE` as additive air/water temperature corrections (field-tested
  2026-06-15: `ATE = 100` = +1.0 °C, `ATA = -40` = −0.4 °C).
- Temperature sensors now expose the **corrected value** (principal) using
  `(EAU + ATE) / 100` and `(AIR + ATA) / 100`, matching the Oklyn app display.
- Added `temperature_eau_sonde` / `temperature_air_sonde` (raw probe, disabled by default).
- Added `temperature_boitier` diagnostic sensor (`BOX` field, probable controller
  internal temperature in °C, disabled by default).
- Added `offset_temp_eau` / `offset_temp_air` diagnostic sensors (`ATE` / `ATA`).
- Removed real IP from docs; replaced with `IP_OKLYN` placeholder + DHCP reservation tip.

## 0.1.2

- Robustness: `/api/data` retries within a polling cycle to absorb the
  controller's intermittent empty `HTTP 200` responses (fewer `unavailable` blips).
- Docs: full English README with badges, `SC1` bit map, and a **Help wanted**
  section calling for community field-decode reports; French translation
  (`README.fr.md`); GitHub issue template for decode submissions.

## 0.1.1

- Decode the `SC1` status word into entities:
  - `binary_sensor.…_pompe` (pump running, bit 14)
  - `sensor.…_pompe_mode` (auto / manuel, bits 19/20)
  - `binary_sensor.…_aux1` (AUX1 output, bit 22) with configurable name & type
- Validated against the cloud integration (measurements match to ±0.01).

## 0.1.0

- Initial read-only POC: local polling of `/api/info` and `/api/data`.
- Sensors: corrected & raw pH/RedOx, water/air temperature, diagnostics,
  raw fields; binary sensors for service/key/config flags.
- Config flow (IP + polling interval).
