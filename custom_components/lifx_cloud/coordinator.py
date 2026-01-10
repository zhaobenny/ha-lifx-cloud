"""Data coordinator for LIFX Cloud integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LifxCloudAPI, LifxCloudAPIError, LifxLight
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class LifxCloudCoordinator(DataUpdateCoordinator[dict[str, LifxLight]]):
    """Coordinator to manage LIFX Cloud data."""

    def __init__(self, hass: HomeAssistant, api: LifxCloudAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, LifxLight]:
        """Fetch data from API."""
        try:
            lights = await self.api.list_lights()
            return {light.id: light for light in lights}
        except LifxCloudAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
