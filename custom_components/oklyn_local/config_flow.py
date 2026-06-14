"""Config flow pour Oklyn Local.

À la création de l'entrée, on vérifie que /api/info répond correctement avant
de créer l'entry. L'IP (ou host) est configurable depuis l'UI.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    OklynLocalClient,
    OklynLocalConnectionError,
    OklynLocalError,
)
from .const import (
    CONF_HOST,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OPT_SCAN_INTERVAL,
    SCAN_INTERVAL_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


class OklynLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gérer le config flow Oklyn Local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            session = async_get_clientsession(self.hass)
            client = OklynLocalClient(session, host)
            try:
                info = await client.async_get_info()
            except OklynLocalConnectionError:
                errors["base"] = "cannot_connect"
            except OklynLocalError:
                errors["base"] = "invalid_response"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Erreur inattendue à la validation Oklyn Local")
                errors["base"] = "unknown"
            else:
                serial = info.get("serial") or info.get("hostname") or host
                await self.async_set_unique_id(str(serial))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.get("hostname") or DEFAULT_NAME,
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return OklynLocalOptionsFlow()


class OklynLocalOptionsFlow(OptionsFlow):
    """Options : intervalle de polling."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        OPT_SCAN_INTERVAL, default=current
                    ): vol.In(SCAN_INTERVAL_OPTIONS),
                }
            ),
        )
