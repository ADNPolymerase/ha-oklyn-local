# Oklyn Local pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/ADNPolymerase/ha-oklyn-local)
[![GitHub Release](https://badgen.net/github/release/ADNPolymerase/ha-oklyn-local)](https://github.com/ADNPolymerase/ha-oklyn-local/releases)
[![Validate](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml/badge.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/adnpolymerase)

<a href="https://buymeacoffee.com/adnpolymerase" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" alt="Buy Me A Coffee" height="60"></a>

Intégration Home Assistant **locale et en lecture seule** pour le boîtier piscine
**Oklyn**. Elle interroge le boîtier directement sur le réseau local (HTTP, port 80)
— **sans cloud, sans compte, sans token** — et expose les mesures sous forme de
`sensor` / `binary_sensor`.

> 🇬🇧 [Read in English](README.md)

> ⚠️ **Preuve de concept — lecture seule.** Cette intégration n'envoie jamais de
> commande : pas de pilotage pompe / AUX, pas de config Wi-Fi, aucun `PUT`/`POST`.
> Elle lit uniquement `http://<ip>/api/info` et `http://<ip>/api/data`. Certains
> champs sont décodés par des tests terrain ; quelques-uns restent **inconnus** —
> voir [Appel à l'aide](#appel-à-laide--décoder-les-champs-inconnus).

> ☁️ **Besoin de piloter (pompe, auxiliaires) ?** Le boîtier Oklyn ne se *commande*
> que via le cloud. Utilise l'intégration cloud compagnon
> [ADNPolymerase/ha-oklyn](https://github.com/ADNPolymerase/ha-oklyn) pour ça. Ce
> projet-ci sert à **lire** rapidement, sans dépendre du cloud.

---

## Fonctionnalités

- **pH** — corrigé (`(PH1 + APH) / 100`) et valeur brute sonde
- **RedOx / ORP** — corrigé (`(ORP + ARX) / 10`, mV) et valeur brute sonde
- Température **eau** et **air** (°C)
- **Pompe** : état de marche + mode (`auto` / `manuel`), décodés du mot d'état `SC1`
- **Auxiliaire 1** : état de sortie, avec nom & type configurables (lumière / chauffage / électrolyseur / personnalisé)
- **Diagnostic** : signal Wi-Fi, mémoire libre, versions firmware/core/SDK, indicateurs service/clef/config
- **Champs bruts** exposés (désactivés par défaut) pour analyse
- Configuration UI complète — IP et intervalle de polling, pas de YAML
- Timeout HTTP court, polling configurable (15 / 30 / 60 / 120 / 300 s)
- Robuste aux réponses vides intermittentes du boîtier (retries intégrés)
- Traductions française et anglaise

---

## Installation via HACS

1. Dans Home Assistant, ouvre **HACS → Intégrations**.
2. Menu **⋮** → **Dépôts personnalisés**.
3. Ajoute `https://github.com/ADNPolymerase/ha-oklyn-local` en catégorie **Intégration**.
4. Cherche **Oklyn Local** et clique **Télécharger**.
5. Redémarre Home Assistant.
6. **Paramètres → Appareils et services → Ajouter une intégration → Oklyn Local**.
7. Saisis l'IP du boîtier (ex. `192.168.1.100`).

> 💡 **Conseil :** assigne une IP fixe (réservation DHCP) à ton boîtier Oklyn dans ton routeur pour que l'adresse ne change pas entre les redémarrages.

## Installation manuelle

1. Copie le dossier `custom_components/oklyn_local/` dans
   `config/custom_components/`.
2. Redémarre Home Assistant, puis ajoute l'intégration comme ci-dessus.

---

## Endpoints utilisés

| Méthode | URL | Usage |
| --- | --- | --- |
| `GET` | `http://<ip>/api/info` | infos techniques du boîtier |
| `GET` | `http://<ip>/api/data` | mesures brutes + mot d'état |

Le serveur HTTP local est un **portail diagnostic + provisioning Wi-Fi**. Il n'expose
**aucun endpoint de commande** — le pilotage pompe/AUX est cloud uniquement.

---

## Entités

### Mesures (`/api/data`)
| Entité | Source | Conversion |
| --- | --- | --- |
| `sensor.…_ph` | `PH1` + `APH` | `(PH1 + APH) / 100` (corrigé) |
| `sensor.…_ph_sonde` | `PH1` | `PH1 / 100` (sonde brute, désactivé par défaut) |
| `sensor.…_redox` | `ORP` + `ARX` | `(ORP + ARX) / 10` mV (corrigé) |
| `sensor.…_redox_sonde` | `ORP` | `ORP / 10` mV (sonde brute, désactivé par défaut) |
| `sensor.…_temperature_eau` | `EAU` + `ATE` | `(EAU + ATE) / 100` °C (corrigé) |
| `sensor.…_temperature_eau_sonde` | `EAU` | `EAU / 100` °C (sonde brute, désactivé par défaut) |
| `sensor.…_temperature_air` | `AIR` + `ATA` | `(AIR + ATA) / 100` °C (corrigé) |
| `sensor.…_temperature_air_sonde` | `AIR` | `AIR / 100` °C (sonde brute, désactivé par défaut) |

> `APH` / `ARX` / `ATA` / `ATE` sont des **corrections additives de sonde** appliquées par le boîtier.
> Les capteurs corrigés reproduisent ce qu'affiche l'app Oklyn.
> Validé terrain : `ATE = 100` = +1,0 °C, `ATA = -40` = −0,4 °C (2026-06-15).

### Pompe & Auxiliaire 1 (décodés depuis `SC1`)
| Entité | Source | Détail |
| --- | --- | --- |
| `binary_sensor.…_pompe` | `SC1` bit 14 | pompe en marche (débit réel) |
| `sensor.…_pompe_mode` | `SC1` bits 19/20 | `auto` / `manuel` |
| `binary_sensor.…_aux1` | `SC1` bit 22 | sortie AUX1 ; **nom + type** configurables |

### Diagnostic (`/api/info`)
Signal Wi-Fi (dBm), mémoire libre (octets), `version`, `core_version`, `sdk_version`,
et binary sensors `service_granted`, `key_valid`, `config_valid`.

### Champs bruts (`/api/data`, désactivés par défaut)
`HSN, TIM, SC1, BOX, OQT, PQT, HPN, SPN, SC2, ECM, APH, ARX, AMG, ATA, ATE` — exposés
tels quels pour analyse. À activer champ par champ.

---

## Options

**Paramètres → Appareils et services → Oklyn Local → Configurer**

| Option | Défaut | Description |
| --- | --- | --- |
| Intervalle de polling | 30 s | 15 / 30 / 60 / 120 / 300 s |
| Nom AUX1 | Auxiliaire 1 | Nom du binary sensor AUX1 |
| Type AUX1 | custom | `light` / `heating` / `electrolyzer` / `custom` → icône + device_class |

---

## Ce qui est local vs cloud uniquement

Les tests terrain montrent une séparation nette : `/api/data` expose les **mesures physiques temps réel + corrections de calibration + état des relais**. Tout le reste (programmes, consignes, configuration) vit uniquement sur les serveurs cloud Oklyn.

| Paramètre | Local `/api/data` |
|---|---|
| AUX1 ON/OFF | ✅ `SC1` bit 22 |
| Pompe ON/OFF/auto | ✅ `SC1` bits 14/19/20 |
| Correction sonde pH (`APH`) | ✅ champ `APH` |
| Correction sonde RedOx (`ARX`) | ✅ champ `ARX` |
| Correction temp eau (`ATE`) | ✅ champ `ATE` |
| Correction temp air (`ATA`) | ✅ champ `ATA` |
| Type de désinfection (chlore/sel) | ❌ cloud uniquement |
| Volume du bassin | ❌ cloud uniquement |
| Consigne hors-gel | ❌ cloud uniquement |
| Mode filtration (auto / fixe) | ❌ cloud uniquement |
| Consignes de régulation (pH, RedOx) | ❌ cloud uniquement |
| État AUX2 | ❌ non exposé en local (firmware) |

---

## Le mot d'état `SC1`

`SC1` est un champ d'état 32 bits. Bits confirmés (testés terrain) :

| Bit | Masque | Signification |
| --- | --- | --- |
| 14 | `0x4000` | pompe en marche |
| 19 | `0x80000` | commande manuelle **ON** (override transitoire) |
| 20 | `0x100000` | commande manuelle **OFF** (override transitoire) |
| 21 + 27 | `0x200000` + `0x8000000` | pompe en marche en mode **auto** |
| 22 | `0x400000` | sortie **AUX1** |

`SC1 = 0` = repos (pompe arrêtée, en auto). Les bits d'override manuel (19/20) sont
transitoires et s'effacent au bout de quelques minutes (retour auto).

---

## Appel à l'aide : décoder les champs inconnus

C'est la partie intéressante. Plusieurs champs **ne sont pas encore compris**, et
Oklyn ne fournit aucune documentation publique. Si tu possèdes un boîtier Oklyn,
**tu peux aider à les cartographier** — uniquement en lisant, jamais en envoyant de
commande.

### Encore inconnus

| Champ / bit | Hypothèse actuelle | Ce qu'il nous faut |
| --- | --- | --- |
| `HSN` | numéro de série (= `serial`) | confirmer sur d'autres unités |
| `TIM` | timestamp Unix du snapshot | confirmer |
| `OQT` / `PQT` | qualité de mesure ORP / pH (%) | confirmer l'échelle |
| `BOX` | température interne boîtier (°C, probable) | confirmer vs ambiant |
| `HPN` / `SPN` | constants ici (2 / 10) — nb pompes ? programme ? | valeurs sur d'autres installs |
| `ECM`, `SC2`, `AMG` | inconnus | toute corrélation observée |
| **AUX2** | **non exposé en local** (firmware) | confirmer sur d'autres versions firmware |
| `SC1` bits 0–13, 15–18, 23–26, 28–31 | inutilisés/inconnus | tout bit qui bascule |
| Autres clés `/api/data` non listées | — | les signaler |

### Comment contribuer un relevé

1. **Prends un snapshot** (remplace l'IP) :
   ```bash
   curl -s http://IP_OKLYN/api/data
   curl -s http://IP_OKLYN/api/info   # masque mac/ssid/serial avant de partager
   ```
   `/api/data` renvoie parfois un corps vide — réessaie quelques fois.
2. **Change une seule chose** sur ton boîtier (ex. allumer AUX2, passer la pompe en
   manuel, modifier une consigne de régulation) et prends un snapshot **avant et après**.
3. **Ouvre une issue** avec : les deux snapshots, ce que tu as changé, le modèle et
   le firmware de ton boîtier (`version` / `core_version` de `/api/info`), et la
   valeur affichée dans l'app Oklyn le cas échéant.

   → [Ouvrir une issue « field decode »](https://github.com/ADNPolymerase/ha-oklyn-local/issues/new)

Un seul bit qui bascule quand tu actionnes quelque chose suffit souvent à mapper une
nouvelle fonction. Les contributions sont créditées dans le changelog. 🙏

> ⚠️ Avant de partager `/api/info`, masque `mac`, `ssid` et `serial`.

---

## Gestion des erreurs

- Timeout HTTP court (5 s) ; polling 30 s par défaut (configurable).
- `/api/data` échoue → capteurs mesure / pompe / AUX indisponibles.
- `/api/info` échoue → capteurs diagnostic indisponibles.
- Les deux échouent → `UpdateFailed` (toutes les entités indisponibles).
- Un champ absent ne plante jamais — l'entité concernée passe indisponible.
- Le boîtier renvoie souvent un **HTTP 200 vide** sur `/api/data` ; le client
  réessaie plusieurs fois par cycle pour lisser ces blips.

---

## Limites connues (API locale)

- **AUX2 non exposé en local** — l'allumer ne change aucun champ. Utilise
  l'intégration cloud pour AUX2.
- Le **mode AUX** (interrupteur vs régulateur) et les **consignes de régulation**
  (pH, RedOx) ne sont pas exposés en local — cloud/config uniquement.
- Pas de pilotage pompe/AUX — lecture seule par conception.
- Un seul appareil par IP.

---

## Contribuer

Issues et pull requests bienvenues sur
<https://github.com/ADNPolymerase/ha-oklyn-local/issues>. Les relevés de décodage
(voir [Appel à l'aide](#appel-à-laide--décoder-les-champs-inconnus)) sont
particulièrement précieux.

## Licence

MIT — voir [LICENSE](LICENSE).
