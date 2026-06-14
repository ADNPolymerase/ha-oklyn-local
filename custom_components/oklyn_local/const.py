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

OPT_SCAN_INTERVAL = "scan_interval"
SCAN_INTERVAL_OPTIONS = [15, 30, 60, 120, 300]

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
}
