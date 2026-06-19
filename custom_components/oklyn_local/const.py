"""Constants for the Oklyn Local (read-only) integration.

POC LECTURE SEULE — interroge directement le boîtier Oklyn sur le réseau
local (http://IP/api/info et http://IP/api/data), sans passer par le cloud.

Aucune commande n'est envoyée au boîtier : ni pompe, ni AUX/AUX2, ni Wi-Fi.

Le décodage des champs /api/data ci-dessous est une HYPOTHÈSE de test,
volontairement centralisé ici pour être facile à modifier au fur et à mesure
que les valeurs réelles se confirment.
"""
from __future__ import annotations

DOMAIN = "oklyn_local"

DEFAULT_NAME = "Oklyn Local"

# Réseau --------------------------------------------------------------------
CONF_HOST = "host"
DEFAULT_TIMEOUT = 5  # secondes — timeout HTTP court
DEFAULT_SCAN_INTERVAL = 30  # secondes

# Le boîtier renvoie fréquemment un corps VIDE avec un HTTP 200 sur /api/data.
# On réessaie plusieurs fois dans le même cycle de polling pour lisser ces blips.
HTTP_RETRIES = 4
HTTP_RETRY_DELAY = 0.3  # secondes entre deux tentatives (réduit : moins de dead time)

# Cache TTL : au-delà de N × scan_interval secondes sans donnée fraîche,
# le coordinateur cesse de servir le cache et passe les entités en unavailable.
# Évite de prolonger un état périmé (ex. AUX resté ON après une coupure HTTP).
CACHE_TTL_FACTOR = 3  # → TTL = 3 × scan_interval

OPT_SCAN_INTERVAL = "scan_interval"
SCAN_INTERVAL_OPTIONS = [15, 30, 60, 120, 300]

# Options AUX1 -------------------------------------------------------------
# Le boîtier n'expose en local QUE l'état de sortie d'AUX1 (bit 22 de SC1).
# Le mode (interrupteur/régulateur) et le type ne sont PAS exposés → on les
# laisse configurer dans l'UI pour adapter nom/icône/device_class.
# AUX2 n'est pas remonté en local du tout (asymétrie firmware).
OPT_AUX1_NAME = "aux1_name"
OPT_AUX1_TYPE = "aux1_type"
DEFAULT_AUX1_NAME = "Auxiliaire 1"

OPT_AUX2_NAME = "aux2_name"
OPT_AUX2_TYPE = "aux2_type"
DEFAULT_AUX2_NAME = "Auxiliaire 2"

AUX1_TYPE_LIGHT = "light"
AUX1_TYPE_HEATING = "heating"
AUX1_TYPE_ELECTROLYZER = "electrolyzer"
AUX1_TYPE_CUSTOM = "custom"
AUX1_TYPES = [
    AUX1_TYPE_LIGHT,
    AUX1_TYPE_HEATING,
    AUX1_TYPE_ELECTROLYZER,
    AUX1_TYPE_CUSTOM,
]
DEFAULT_AUX1_TYPE = AUX1_TYPE_CUSTOM
DEFAULT_AUX2_TYPE = AUX1_TYPE_CUSTOM

# Décodage du champ SC1 (bitfield d'état) — confirmé terrain 2026-06-15.
# Référence : memory oklyn-local-sc1-decode.
SC1_PUMP_RUNNING = 14    # pompe tourne (débit réel)
SC1_MANUAL_ON = 19       # commande manuelle ON (transitoire)
SC1_MANUAL_OFF = 20      # commande manuelle OFF (transitoire)
SC1_AUTO_A = 21          # marche en mode auto
SC1_AUTO_B = 27          # marche en mode auto (2e bit)
SC1_AUX1 = 22            # sortie relais AUX1 (indépendante de la pompe)
SC1_AUX2 = 23            # sortie relais AUX2 — confirmé terrain 2026-06-18 (kurtenweb)

# Endpoints locaux connus ---------------------------------------------------
ENDPOINT_INFO = "/api/info"
ENDPOINT_DATA = "/api/data"

# Device info ---------------------------------------------------------------
MANUFACTURER = "Oklyn"
MODEL = "Oklyn Pool Controller (local)"

# Champs /api/data : facteur de conversion connu / supposé ------------------
# value = raw / factor  (factor = 1 → valeur brute)
#
# pH et Redox ont DEUX valeurs :
#   - lecture sonde brute : PH1 / 100      et  ORP / 10
#   - valeur corrigée     : (PH1 + APH)/100 et (ORP + ARX)/10
# APH et ARX sont des corrections ADDITIVES (offset interne du boîtier),
# dans la même échelle que PH1 / ORP.
DATA_DIVIDE = {
    "AIR": 100,   # température air (°C)
    "EAU": 100,   # température eau (°C)
    "ORP": 10,    # redox (mV)
    "PH1": 100,   # pH
    "APH": 100,   # correction pH (additive, même échelle que PH1)
    "ARX": 10,    # correction redox mV (additive, même échelle que ORP)
    "ATA": 100,   # correction temp air (additive, °C) — confirmé 2026-06-15
    "ATE": 100,   # correction temp eau (additive, °C) — confirmé 2026-06-15
    "BOX": 1,     # température interne boîtier (°C, entier) — probable
    "ECM": 1000,  # concentration sel (g/L) — confirmé 2026-06-18 (ECM=2404 → 2,4 g/L)
}
