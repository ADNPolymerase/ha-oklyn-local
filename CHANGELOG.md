# Changelog

## 0.1.9b1 (beta)

- **Re-poll immédiat après coupure HTTP** : dès que le boîtier redevient
  joignable après une série de corps vides, un re-poll est déclenché 1 s plus
  tard — évite de servir le cache périmé pendant tout un cycle de 15 s.
- **Cache TTL** : le cache est limité à 3 × intervalle (45 s par défaut).
  Au-delà, les entités passent en unavailable au lieu de prolonger un état
  périmé (ex. AUX affiché ON pendant 5 min après une coupure).
- **Retry delay 0.3 s** (était 1.0 s) : la récupération après un corps vide
  prend 1.2 s max au lieu de 4 s.

## 0.1.9

- **AUX2** : sortie relais AUX2 (SC1 bit 23) — entité `binary_sensor` confirmée terrain
  (kurtenweb + JD, 2026-06-18/19). Nom et type configurables dans les options (Lumière /
  Chauffage / Électrolyseur / Autre), identique à AUX1.
- **Fix** : options — intervalle et type AUX affiché comme dropdown (`SelectSelector`),
  valeur courante pré-sélectionnée à la réouverture.
- **Fix** : `Dernière mesure boîtier` affichait l'heure 2h dans le futur — le boîtier
  stocke TIM en heure locale sans offset UTC ; corrigé en réinterprétant dans le fuseau HA.
- **Sel** : capteur `sensor.oklyn_sel` (g/L, désactivé par défaut) — champ ECM / 1000,
  pour piscines au sel uniquement.
- **MAC** : adresse MAC enregistrée dans le device registry — HA lie automatiquement le
  boîtier à l'intégration routeur (Livebox, Freebox, UniFi…).

## 0.1.8b3 (beta)

- **Fix** : intervalle d'interrogation affiché comme dropdown (SelectSelector)
  — la valeur courante est maintenant pré-sélectionnée à la réouverture des options.
- **Fix** : type AUX1 affiché comme dropdown (SelectSelector) avec libellés lisibles.
- **Nouveauté** : AUX2 entièrement configurable dans les options — nom et type
  (Lumière / Chauffage / Électrolyseur / Autre), identique à AUX1.

## 0.1.8b2 (beta)

- **Fix** : l'intervalle d'interrogation dans les options sautait / ne se sauvegardait pas
  (`vol.Coerce(int)` ajouté — HA renvoie la valeur en string depuis le formulaire).
- **Fix** : `Dernière mesure boîtier` affichait l'heure 2h dans le futur.
  Le boîtier stocke TIM en heure locale (France) sans offset UTC ;
  la conversion réinterprète maintenant la valeur comme heure locale
  puis la convertit en vrai UTC (basé sur le fuseau HA configuré).

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
