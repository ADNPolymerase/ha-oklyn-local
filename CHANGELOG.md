# Changelog

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
