"""Tests for the LIFX Cloud API client."""

import json

import pytest
from aioresponses import aioresponses

from custom_components.lifx_cloud.api import (
    LifxCloudAPI,
    LifxCloudAPIError,
    LifxCloudAuthError,
    LifxCloudConnectionError,
    LifxLight,
)
from custom_components.lifx_cloud.const import API_BASE_URL

from .conftest import MOCK_LIGHT_DATA, MOCK_TOKEN


class TestLifxLight:
    """Tests for LifxLight dataclass."""

    def test_from_dict(self) -> None:
        """Test creating LifxLight from dictionary."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA)

        assert light.id == "d073d55b6334"
        assert light.label == "Test Light"
        assert light.connected is True
        assert light.power == "on"
        assert light.brightness == 0.8

    def test_is_on(self) -> None:
        """Test is_on property."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA)
        assert light.is_on is True

        off_data = {**MOCK_LIGHT_DATA, "power": "off"}
        light_off = LifxLight.from_dict(off_data)
        assert light_off.is_on is False

    def test_color_properties(self) -> None:
        """Test color-related properties."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA)

        assert light.hue == 120
        assert light.saturation == 0.5
        assert light.kelvin == 3500

    def test_capability_properties(self) -> None:
        """Test capability properties."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA)

        assert light.supports_color is True
        assert light.supports_temperature is True
        assert light.min_kelvin == 2500
        assert light.max_kelvin == 9000

    def test_missing_capabilities(self) -> None:
        """Test with missing capabilities."""
        data = {**MOCK_LIGHT_DATA, "product": {}}
        light = LifxLight.from_dict(data)

        assert light.supports_color is False
        assert light.supports_temperature is False
        assert light.min_kelvin == 2500  # default
        assert light.max_kelvin == 9000  # default


class TestLifxCloudAPI:
    """Tests for LifxCloudAPI client."""

    @pytest.mark.asyncio
    async def test_list_lights_success(self) -> None:
        """Test listing lights successfully."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                payload=[MOCK_LIGHT_DATA],
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            lights = await api.list_lights()
            await api.close()

            assert len(lights) == 1
            assert lights[0].id == "d073d55b6334"
            assert lights[0].label == "Test Light"

    @pytest.mark.asyncio
    async def test_auth_error(self) -> None:
        """Test authentication error handling."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                status=401,
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            with pytest.raises(LifxCloudAuthError, match="Invalid access token"):
                await api.list_lights()
            await api.close()

    @pytest.mark.asyncio
    async def test_forbidden_error(self) -> None:
        """Test forbidden error handling."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                status=403,
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            with pytest.raises(LifxCloudAuthError, match="Access forbidden"):
                await api.list_lights()
            await api.close()

    @pytest.mark.asyncio
    async def test_api_error(self) -> None:
        """Test generic API error handling."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                status=500,
                body="Internal Server Error",
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            with pytest.raises(LifxCloudAPIError, match="API error 500"):
                await api.list_lights()
            await api.close()

    @pytest.mark.asyncio
    async def test_validate_token_success(self) -> None:
        """Test token validation success."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                payload=[MOCK_LIGHT_DATA],
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.validate_token()
            await api.close()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_failure(self) -> None:
        """Test token validation failure."""
        with aioresponses() as m:
            m.get(
                f"{API_BASE_URL}/lights/all",
                status=401,
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.validate_token()
            await api.close()

            assert result is False

    @pytest.mark.asyncio
    async def test_set_state(self) -> None:
        """Test setting light state."""
        with aioresponses() as m:
            m.put(
                f"{API_BASE_URL}/lights/id:test/state",
                status=207,
                payload={"results": [{"status": "ok"}]},
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.set_state(
                selector="id:test",
                power="on",
                brightness=0.5,
                color="kelvin:3000",
                duration=1.0,
            )
            await api.close()

            assert result["results"][0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_fast_mode_response(self) -> None:
        """Test fast mode returns None."""
        with aioresponses() as m:
            m.put(
                f"{API_BASE_URL}/lights/id:test/state",
                status=202,
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.set_state(
                selector="id:test",
                power="on",
                fast=True,
            )
            await api.close()

            assert result is None

    @pytest.mark.asyncio
    async def test_toggle_power(self) -> None:
        """Test toggling power."""
        with aioresponses() as m:
            m.post(
                f"{API_BASE_URL}/lights/id:test/toggle",
                status=207,
                payload={"results": [{"status": "ok"}]},
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.toggle_power(selector="id:test")
            await api.close()

            assert result["results"][0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_breathe_effect(self) -> None:
        """Test breathe effect."""
        with aioresponses() as m:
            m.post(
                f"{API_BASE_URL}/lights/id:test/effects/breathe",
                status=207,
                payload={"results": [{"status": "ok"}]},
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.breathe_effect(
                selector="id:test",
                color="red",
            )
            await api.close()

            assert result["results"][0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_pulse_effect(self) -> None:
        """Test pulse effect."""
        with aioresponses() as m:
            m.post(
                f"{API_BASE_URL}/lights/id:test/effects/pulse",
                status=207,
                payload={"results": [{"status": "ok"}]},
            )

            api = LifxCloudAPI(MOCK_TOKEN)
            result = await api.pulse_effect(
                selector="id:test",
                color="blue",
            )
            await api.close()

            assert result["results"][0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_close_session(self) -> None:
        """Test closing the session."""
        api = LifxCloudAPI(MOCK_TOKEN)
        # Create a session first
        await api._get_session()
        assert api._session is not None

        await api.close()
        assert api._session.closed

    def test_headers(self) -> None:
        """Test that correct headers are generated."""
        api = LifxCloudAPI(MOCK_TOKEN)
        headers = api._headers()

        assert headers["Authorization"] == f"Bearer {MOCK_TOKEN}"
        assert headers["Content-Type"] == "application/json"
