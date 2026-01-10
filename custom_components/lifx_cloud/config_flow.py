"""Config flow for LIFX Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN

from .api import LifxCloudAPI, LifxCloudAuthError, LifxCloudConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LifxCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LIFX Cloud."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_ACCESS_TOKEN]

            api = LifxCloudAPI(token)
            try:
                lights = await api.list_lights()
                await api.close()

                # Use the first light's location as a unique identifier
                # or fall back to a hash of the token
                if lights:
                    unique_id = lights[0].location.get("id", token[:16])
                else:
                    unique_id = token[:16]

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="LIFX Cloud",
                    data={CONF_ACCESS_TOKEN: token},
                )

            except LifxCloudAuthError:
                errors["base"] = "invalid_auth"
            except LifxCloudConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): str,
                }
            ),
            errors=errors,
        )
