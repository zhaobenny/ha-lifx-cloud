"""Light platform for LIFX Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LifxLight
from .const import DOMAIN
from .coordinator import LifxCloudCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LIFX Cloud lights from a config entry."""
    coordinator: LifxCloudCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        LifxCloudLight(coordinator, light_id)
        for light_id in coordinator.data
    ]

    async_add_entities(entities)


class LifxCloudLight(CoordinatorEntity[LifxCloudCoordinator], LightEntity):
    """Representation of a LIFX light via Cloud API."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = LightEntityFeature.TRANSITION | LightEntityFeature.EFFECT

    def __init__(
        self,
        coordinator: LifxCloudCoordinator,
        light_id: str,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._light_id = light_id
        self._attr_unique_id = light_id

    @property
    def _light(self) -> LifxLight | None:
        """Return the light data."""
        return self.coordinator.data.get(self._light_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._light is not None and self._light.connected

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        light = self._light
        if light is None:
            return DeviceInfo(identifiers={(DOMAIN, self._light_id)})

        return DeviceInfo(
            identifiers={(DOMAIN, light.id)},
            name=light.label,
            manufacturer="LIFX",
            model=light.product.get("name", "Unknown"),
            sw_version=str(light.product.get("capabilities", {}).get("min_ext_mz", "")),
            suggested_area=light.group.get("name"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return if the light is on."""
        if self._light is None:
            return None
        return self._light.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness (0-255)."""
        if self._light is None:
            return None
        return int(self._light.brightness * 255)

    @property
    def color_mode(self) -> ColorMode | None:
        """Return the current color mode."""
        if self._light is None:
            return None

        if self._light.supports_color and self._light.saturation > 0:
            return ColorMode.HS
        if self._light.supports_temperature:
            return ColorMode.COLOR_TEMP
        return ColorMode.BRIGHTNESS

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return the supported color modes."""
        if self._light is None:
            return {ColorMode.BRIGHTNESS}

        modes: set[ColorMode] = set()
        if self._light.supports_color:
            modes.add(ColorMode.HS)
        if self._light.supports_temperature:
            modes.add(ColorMode.COLOR_TEMP)
        if not modes:
            modes.add(ColorMode.BRIGHTNESS)
        return modes

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the HS color."""
        if self._light is None:
            return None
        return (self._light.hue, self._light.saturation * 100)

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature in Kelvin."""
        if self._light is None:
            return None
        return self._light.kelvin

    @property
    def min_color_temp_kelvin(self) -> int:
        """Return the minimum color temperature."""
        if self._light is None:
            return 2500
        return self._light.min_kelvin

    @property
    def max_color_temp_kelvin(self) -> int:
        """Return the maximum color temperature."""
        if self._light is None:
            return 9000
        return self._light.max_kelvin

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported effects."""
        return ["breathe", "pulse"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        light = self._light
        if light is None:
            return

        duration = kwargs.get(ATTR_TRANSITION, 1.0)
        color_str: str | None = None
        brightness: float | None = None

        if ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            color_str = f"hue:{hue} saturation:{sat / 100}"
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            color_str = f"kelvin:{kelvin}"

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS] / 255

        await self.coordinator.api.set_state(
            selector=f"id:{self._light_id}",
            power="on",
            color=color_str,
            brightness=brightness,
            duration=duration,
        )

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        duration = kwargs.get(ATTR_TRANSITION, 1.0)

        await self.coordinator.api.set_state(
            selector=f"id:{self._light_id}",
            power="off",
            duration=duration,
        )

        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
