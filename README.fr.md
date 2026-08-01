# Oklyn Local pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub Release](https://badgen.net/github/release/ADNPolymerase/ha-oklyn-local)](https://github.com/ADNPolymerase/ha-oklyn-local/releases)
[![Validate](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml/badge.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/actions/workflows/validate.yml)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/adnpolymerase)

<a href="https://buymeacoffee.com/adnpolymerase" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" alt="Buy Me A Coffee" height="60"></a>
<a href="https://adnpolymerase.github.io/HA/" target="_blank"><img src="https://raw.githubusercontent.com/ADNPolymerase/HA/main/assets/site-button.svg" alt="Link to my github.io for my other projects" height="60"></a>

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

- **pH, RedOx/ORP, températures eau et air** — valeurs corrigées (sonde + offset boîtier), avec attributs `raw_*` / `offset_*` / `corrected` pour une traçabilité complète, plus les capteurs sonde bruts (désactivés par défaut).
- **Sel** (piscines au sel, g/L, `ECM / 1000`) — désactivé par défaut.
- **Pompe** (état de marche + mode `auto` / `manuel`) et **Auxiliaires 1 et 2** (nom & type configurables), décodés du mot d'état `SC1`.
- **Diagnostic** : signal Wi-Fi, mémoire libre, versions firmware, indicateurs service/clef/config — et **champs bruts** (désactivés par défaut) pour analyse.
- **Liaison routeur** : l'adresse MAC est enregistrée dans HA, qui fait le lien avec ton intégration routeur (Livebox, Freebox, UniFi…).
- Configuration UI complète (`oklyn.local` ou IP), polling configurable (15–300 s), retries intégrés, **cache des dernières valeurs connues** avec capteur `Dernière mesure boîtier`.
- Traductions française, anglaise et russe.

---

## Installation (HACS)

Disponible directement dans HACS — aucun dépôt personnalisé à ajouter.

1. Ouvre **HACS**, recherche **Oklyn Local** et télécharge-le.
2. Redémarre Home Assistant.
3. **Paramètres → Appareils et services → Ajouter une intégration** → **Oklyn Local**, puis saisis l'hôte du boîtier : `oklyn.local` (mDNS) ou son IP.

> 💡 Si ton réseau ne résout pas les noms `.local` (certains routeurs / VLAN / configs Docker), utilise plutôt une IP fixe (réservation DHCP).

Alternative manuelle : copie `custom_components/oklyn_local/` dans `config/custom_components/`, redémarre, puis ajoute l'intégration.

---

## API locale

Le boîtier s'annonce via mDNS (`_http._tcp.local → oklyn.local:80`) et expose deux endpoints :

| Méthode | URL | Usage |
| --- | --- | --- |
| `GET` | `http://<host>/api/info` | infos techniques du boîtier |
| `GET` | `http://<host>/api/data` | mesures brutes + mot d'état |

Le serveur HTTP local est un **portail diagnostic + provisioning Wi-Fi** — il n'expose **aucun endpoint de commande** ; le pilotage pompe/AUX est cloud uniquement. Les scans réseau (firmware `436`) n'ont trouvé que TCP 80 et UDP 5353 (mDNS) ouverts — pas de MQTT, HTTPS, HTTP alternatif ni CoAP. Le boîtier est basé ESP (préfixe MAC Espressif), et les captures de trafic montrent que les commandes passent par `iot.oklyn.fr` — **cette intégration ne contacte jamais ce domaine**.

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
>
> Les 4 capteurs corrigés (`ph`, `redox`, `temperature_eau`, `temperature_air`)
> exposent aussi `raw_<champ>`, `offset_<champ>` et `corrected` en **attributs
> d'état**, pour garder le calcul complet visible sans entités supplémentaires.

### Pompe, Auxiliaire 1 & Auxiliaire 2 (décodés depuis `SC1`)
| Entité | Source | Détail |
| --- | --- | --- |
| `binary_sensor.…_pompe` | `SC1` bit 14 | pompe en marche (débit réel) |
| `sensor.…_pompe_mode` | `SC1` bits 19/20 | `auto` / `manuel` |
| `binary_sensor.…_aux1` | `SC1` bit 22 | sortie AUX1 ; **nom + type** configurables |
| `binary_sensor.…_aux2` | `SC1` bit 23 | sortie AUX2 ; **nom + type** configurables — confirmé terrain 2026-06-18 (kurtenweb) |

### Diagnostic (`/api/info` + `/api/data`)
Signal Wi-Fi (dBm), mémoire libre (octets), `version`, `core_version`, `sdk_version`,
et binary sensors `service_granted`, `key_valid`, `config_valid`.

`sensor.…_derniere_mesure` — horodatage du dernier snapshot interne du boîtier
(champ `TIM`, cycle de rafraîchissement ~5 min). Se fige quand le cache est servi,
rendant les données périmées immédiatement visibles.

### Champs bruts (`/api/data`, désactivés par défaut)
`HSN, TIM, SC1, BOX, OQT, PQT, HPN, SPN, SC2, APH, ARX, AMG, ATA, ATE` — exposés
tels quels pour analyse. À activer champ par champ.
(`ECM` n'est plus un champ brut — c'est désormais le capteur **Sel** décodé.)

---

## Options

**Paramètres → Appareils et services → Oklyn Local → Configurer**

| Option | Défaut | Description |
| --- | --- | --- |
| Intervalle de polling | 30 s | 15 / 30 / 60 / 120 / 300 s — affiché comme dropdown avec la valeur courante pré-sélectionnée |
| Nom AUX1 | Auxiliaire 1 | Nom du binary sensor AUX1 |
| Type AUX1 | custom | `light` / `heating` / `electrolyzer` / `custom` → icône + device_class |
| Nom AUX2 | Auxiliaire 2 | Nom du binary sensor AUX2 |
| Type AUX2 | custom | `light` / `heating` / `electrolyzer` / `custom` → icône + device_class |

---

## Ce qui est local vs cloud uniquement

Les tests terrain montrent une séparation nette : `/api/data` expose les **mesures physiques temps réel + corrections de calibration + état des relais**. Tout le reste (programmes, consignes, configuration) vit uniquement sur les serveurs cloud Oklyn.

| Paramètre | Local `/api/data` |
|---|---|
| AUX1 ON/OFF | ✅ `SC1` bit 22 |
| AUX2 ON/OFF | ✅ `SC1` bit 23 — confirmé terrain 2026-06-18 |
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
| 23 | `0x800000` | sortie **AUX2** — confirmé terrain 2026-06-18 (kurtenweb) |

`SC1 = 0` = repos (pompe arrêtée, en auto). Les bits d'override manuel (19/20) sont
transitoires et s'effacent au bout de quelques minutes (retour auto).

> ⚠️ **Délai de propagation AUX2 (~2 min) :** le boîtier met ~2 minutes à mettre à jour le bit 23 de SC1 après une commande cloud sur AUX2 (limitation firmware — le registre est en retard sur le relais). Un ON cloud de moins de ~2 min n'est jamais vu localement. Les pistes de contournement sont bienvenues via les issues.

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
| `TIM` | timestamp Unix du snapshot (heure locale, sans offset UTC) | confirmer sur d'autres fuseaux |
| `OQT` / `PQT` | qualité de mesure ORP / pH (%) | confirmer l'échelle |
| `BOX` | température interne boîtier (°C, probable) | confirmer vs ambiant |
| `HPN` / `SPN` | constants ici (2 / 10) — nb pompes ? programme ? | valeurs sur d'autres installs |
| `SC2`, `AMG` | inconnus | toute corrélation observée |
| `SC1` bits 0–13, 15–18, 24–26, 28–31 | inutilisés/inconnus | tout bit qui bascule |
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

En cas d'échec, les dernières valeurs connues sont servies depuis le cache (les entités restent disponibles) ; le cache expire après **3 × l'intervalle de polling**, au-delà les entités passent indisponibles plutôt que de servir un état périmé. Les HTTP 200 vides (fréquents sur `/api/data`) sont réessayés dans le cycle ; à la sortie d'une coupure, un poll supplémentaire part 1 s plus tard. En cas d'utilisation du cache, le capteur `Dernière mesure boîtier` se fige, rendant les données périmées visibles. Un champ absent ne plante jamais — l'entité passe juste indisponible.

---

## Limitation lecture seule

**Cette intégration est en lecture seule.** Elle ne peut pas piloter la pompe ou les auxiliaires, ni modifier programmes, consignes ou Wi-Fi — aucun endpoint de commande local n'existe (voir [Notes de reverse engineering](#notes-de-reverse-engineering)), et elle n'envoie jamais de `POST`/`PUT` au boîtier. Le mode AUX (interrupteur vs régulateur) et les consignes de régulation sont cloud uniquement ; l'intégration cloud reste nécessaire pour les commandes. Un seul appareil par hôte.

---

## Notes de reverse engineering

Ces chemins ont été testés sur un boîtier réel (firmware `436`) et renvoient
tous `404 Not Found` (y compris en `OPTIONS`). Listés ici pour éviter à
d'autres de refaire les mêmes tests :

```text
/api/status        /api/last_values    /api/pump           /api/aux
/api/aux2           /api/relay          /api/relays          /api/ph
/api/orp            /api/measure        /api/measures        /api/config
/api/device         /api/schedules      /api/errors           /api/alerts
/status  /data  /pump  /aux  /aux2  /relay  /relays  /ph  /orp  /measure  /measures
```

La page web locale du boîtier (`http://oklyn.local/`) ne référence que :

```text
/api/info  /api/wifi  /wifi-scan  /wifi-try
```

Son HTML/JS ne contient aucune route faisant référence à `pump`, `aux`, `relay`, `filtration`, `gpio` ou `output` — le serveur local ne sert que le diagnostic + le provisioning Wi-Fi. Si tu trouves un endpoint de commande fonctionnel sur un autre firmware, merci d'[ouvrir une issue](https://github.com/ADNPolymerase/ha-oklyn-local/issues/new) plutôt que de l'ajouter sans discussion.

---

## Contribuer

Issues et pull requests bienvenues sur
<https://github.com/ADNPolymerase/ha-oklyn-local/issues>. Les relevés de décodage
(voir [Appel à l'aide](#appel-à-laide--décoder-les-champs-inconnus)) sont
particulièrement précieux.

## Licence

MIT — voir [LICENSE](https://github.com/ADNPolymerase/ha-oklyn-local/blob/main/LICENSE).
