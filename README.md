# Oklyn Local (lecture seule) — POC

Intégration Home Assistant **custom, locale et en lecture seule** pour un boîtier
piscine **Oklyn** connecté en Wi-Fi sur le réseau local.

Elle interroge directement le boîtier en HTTP (port 80), **sans passer par le
cloud Oklyn**, et expose les mesures sous forme de `sensor` / `binary_sensor`.

> ⚠️ **Preuve de concept.** Cette version ne pilote **rien** : pas de commande
> pompe, AUX, AUX2, ni de modification Wi-Fi. Aucun `PUT`/`POST` n'est émis.
> Le décodage de certains champs est une **hypothèse** à confirmer.

## Endpoints interrogés

| Méthode | URL                       | Usage                         |
| ------- | ------------------------- | ----------------------------- |
| `GET`   | `http://<IP>/api/info`    | infos techniques du boîtier   |
| `GET`   | `http://<IP>/api/data`    | mesures brutes                |

## Installation (HACS — dépôt personnalisé)

1. HACS → menu ⋮ → **Dépôts personnalisés**
2. URL du dépôt + catégorie **Intégration**
3. Installer **Oklyn Local**, redémarrer Home Assistant
4. **Paramètres → Appareils & services → Ajouter une intégration → Oklyn Local**
5. Saisir l'IP du boîtier (ex. `192.168.0.42`)

Installation manuelle : copier `custom_components/oklyn_local/` dans
`/config/custom_components/` puis redémarrer.

## Entités

### Mesures principales (`/api/data`)
| Entité                              | Source        | Conversion |
| ----------------------------------- | ------------- | ---------- |
| `sensor.…_temperature_eau`          | `EAU`         | `/ 100` °C |
| `sensor.…_temperature_air`          | `AIR`         | `/ 100` °C |
| `sensor.…_ph` (corrigé)             | `PH1` + `APH` | `(PH1 + APH) / 100` |
| `sensor.…_ph_sonde` (brut sonde)    | `PH1`         | `PH1 / 100` |
| `sensor.…_redox` (corrigé)          | `ORP` + `ARX` | `(ORP + ARX) / 10` mV |
| `sensor.…_redox_sonde` (brut sonde) | `ORP`         | `ORP / 10` mV |
| `sensor.…_offset_ph` *(désactivé)*  | `APH`         | `/ 100` (correction appliquée) |
| `sensor.…_offset_redox` *(désact.)* | `ARX`         | `/ 10` mV (correction appliquée) |

> **pH / Redox** : deux entités chacun — la valeur **lue par la sonde** (brute)
> et la valeur **corrigée** par l'offset interne du boîtier (`APH` / `ARX`,
> corrections **additives**). La valeur corrigée est celle affichée par Oklyn.
> La corrigée passe indisponible si la correction (`APH`/`ARX`) manque.

### Pompe & AUX1 (décodés depuis le champ `SC1` de `/api/data`)
| Entité | Source | Détail |
| --- | --- | --- |
| `binary_sensor.…_pompe` | `SC1` bit 14 | pompe en marche (débit réel) |
| `sensor.…_pompe_mode` | `SC1` bits 19/20 | `auto` / `manuel` |
| `binary_sensor.…_aux1` | `SC1` bit 22 | sortie AUX1 ; **nom + type** configurables (lumière / chauffage / électrolyseur / personnalisé → icône + device_class) |

> **AUX2 n'est pas exposé en local** par le firmware (asymétrie confirmée : AUX2
> ON ne modifie aucun champ de `/api/data`). Aucun capteur AUX2 local n'est donc
> possible — il faut passer par le cloud. De même, le **mode** AUX
> (interrupteur/régulateur) et les **consignes** de régulation (pH, redox) ne
> sont pas remontés en local.

### Diagnostic boîtier (`/api/info`)
`wifi_signal` (dBm), `memory_free` (octets), `version`, `core_version`,
`sdk_version`, et binary sensors `service_granted` (`granted`),
`key_valid` (`key`), `config_valid` (`valid`).

### Capteurs bruts (`/api/data`, désactivés par défaut)
`HSN, TIM, SC1, BOX, OQT, PQT, HPN, SPN, SC2, ECM, APH, ARX, AMG, ATA, ATE`
— exposés tels quels pour analyse. À activer dans l'UI au besoin.

## Décodage — hypothèses

Les facteurs de conversion sont centralisés dans
[`const.py`](custom_components/oklyn_local/const.py) (`DATA_DIVIDE`) pour être
faciles à corriger. Les champs inconnus ne sont **pas** surinterprétés : ils
restent bruts.

## Comportement / erreurs

- Polling HTTP simple, timeout **5 s**, intervalle par défaut **30 s**
  (configurable : 15/30/60/120/300 s via les options).
- `/api/data` en échec → capteurs de mesure indisponibles.
- `/api/info` en échec → capteurs diagnostic indisponibles.
- Les deux en échec → `UpdateFailed` (toutes les entités indisponibles).
- Champ absent → l'entité concernée passe indisponible, sans planter.

## Licence

MIT — voir [LICENSE](LICENSE).
