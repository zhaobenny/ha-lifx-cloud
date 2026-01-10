"""LIFX Cloud API client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp

from .const import API_BASE_URL, DEFAULT_TIMEOUT


class LifxCloudAPIError(Exception):
    """Base exception for LIFX Cloud API errors."""


class LifxCloudAuthError(LifxCloudAPIError):
    """Authentication error."""


class LifxCloudConnectionError(LifxCloudAPIError):
    """Connection error."""


@dataclass
class LifxLight:
    """Representation of a LIFX light from the API."""

    id: str
    uuid: str
    label: str
    connected: bool
    power: str
    brightness: float
    color: dict[str, Any]
    group: dict[str, str]
    location: dict[str, str]
    product: dict[str, Any]
    last_seen: str
    seconds_since_seen: int

    @property
    def is_on(self) -> bool:
        """Return if the light is on."""
        return self.power == "on"

    @property
    def hue(self) -> float:
        """Return the hue (0-360)."""
        return self.color.get("hue", 0)

    @property
    def saturation(self) -> float:
        """Return the saturation (0-1)."""
        return self.color.get("saturation", 0)

    @property
    def kelvin(self) -> int:
        """Return the color temperature in Kelvin."""
        return self.color.get("kelvin", 3500)

    @property
    def supports_color(self) -> bool:
        """Return if the light supports color."""
        capabilities = self.product.get("capabilities", {})
        return capabilities.get("has_color", False)

    @property
    def supports_temperature(self) -> bool:
        """Return if the light supports color temperature."""
        capabilities = self.product.get("capabilities", {})
        return capabilities.get("has_variable_color_temp", False)

    @property
    def min_kelvin(self) -> int:
        """Return minimum color temperature."""
        capabilities = self.product.get("capabilities", {})
        return capabilities.get("min_kelvin", 2500)

    @property
    def max_kelvin(self) -> int:
        """Return maximum color temperature."""
        capabilities = self.product.get("capabilities", {})
        return capabilities.get("max_kelvin", 9000)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LifxLight:
        """Create a LifxLight from API response data."""
        return cls(
            id=data["id"],
            uuid=data.get("uuid", data["id"]),
            label=data["label"],
            connected=data.get("connected", False),
            power=data.get("power", "off"),
            brightness=data.get("brightness", 0),
            color=data.get("color", {}),
            group=data.get("group", {}),
            location=data.get("location", {}),
            product=data.get("product", {}),
            last_seen=data.get("last_seen", ""),
            seconds_since_seen=data.get("seconds_since_seen", 0),
        )


class LifxCloudAPI:
    """Client for the LIFX Cloud API."""

    def __init__(self, token: str, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the API client."""
        self._token = token
        self._session = session
        self._owned_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owned_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()

    def _headers(self) -> dict[str, str]:
        """Return headers for API requests."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{endpoint}"

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with session.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=data,
                ) as response:
                    if response.status == 401:
                        raise LifxCloudAuthError("Invalid access token")
                    if response.status == 403:
                        raise LifxCloudAuthError("Access forbidden")

                    if response.status == 207:
                        # Multi-status response for set_state
                        return await response.json()

                    if response.status >= 400:
                        text = await response.text()
                        raise LifxCloudAPIError(
                            f"API error {response.status}: {text}"
                        )

                    if response.status == 202:
                        # Fast mode - no body
                        return None

                    return await response.json()

        except asyncio.TimeoutError as err:
            raise LifxCloudConnectionError("Request timed out") from err
        except aiohttp.ClientError as err:
            raise LifxCloudConnectionError(f"Connection error: {err}") from err

    async def list_lights(self, selector: str = "all") -> list[LifxLight]:
        """List all lights."""
        data = await self._request("GET", f"/lights/{selector}")
        return [LifxLight.from_dict(light) for light in data]

    async def validate_token(self) -> bool:
        """Validate the API token by listing lights."""
        try:
            await self.list_lights()
            return True
        except LifxCloudAuthError:
            return False

    async def set_state(
        self,
        selector: str,
        power: str | None = None,
        color: str | None = None,
        brightness: float | None = None,
        duration: float = 1.0,
        infrared: float | None = None,
        fast: bool = False,
    ) -> Any:
        """Set the state of lights."""
        data: dict[str, Any] = {"duration": duration}

        if power is not None:
            data["power"] = power
        if color is not None:
            data["color"] = color
        if brightness is not None:
            data["brightness"] = brightness
        if infrared is not None:
            data["infrared"] = infrared
        if fast:
            data["fast"] = True

        return await self._request("PUT", f"/lights/{selector}/state", data)

    async def toggle_power(
        self,
        selector: str,
        duration: float = 1.0,
    ) -> Any:
        """Toggle the power of lights."""
        return await self._request(
            "POST",
            f"/lights/{selector}/toggle",
            {"duration": duration},
        )

    async def breathe_effect(
        self,
        selector: str,
        color: str,
        period: float = 1.0,
        cycles: float = 1.0,
        persist: bool = False,
        power_on: bool = True,
        peak: float = 0.5,
    ) -> Any:
        """Perform a breathe effect."""
        return await self._request(
            "POST",
            f"/lights/{selector}/effects/breathe",
            {
                "color": color,
                "period": period,
                "cycles": cycles,
                "persist": persist,
                "power_on": power_on,
                "peak": peak,
            },
        )

    async def pulse_effect(
        self,
        selector: str,
        color: str,
        period: float = 1.0,
        cycles: float = 1.0,
        persist: bool = False,
        power_on: bool = True,
    ) -> Any:
        """Perform a pulse effect."""
        return await self._request(
            "POST",
            f"/lights/{selector}/effects/pulse",
            {
                "color": color,
                "period": period,
                "cycles": cycles,
                "persist": persist,
                "power_on": power_on,
            },
        )
