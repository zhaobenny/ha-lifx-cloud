"""Fixtures for LIFX Cloud tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lifx_cloud.api import LifxLight

MOCK_TOKEN = "test_token_12345"

MOCK_LIGHT_DATA = {
    "id": "d073d55b6334",
    "uuid": "02345678-1234-1234-1234-123456789abc",
    "label": "Test Light",
    "connected": True,
    "power": "on",
    "brightness": 0.8,
    "color": {
        "hue": 120,
        "saturation": 0.5,
        "kelvin": 3500,
    },
    "group": {
        "id": "group123",
        "name": "Living Room",
    },
    "location": {
        "id": "location123",
        "name": "Home",
    },
    "product": {
        "name": "LIFX Color",
        "capabilities": {
            "has_color": True,
            "has_variable_color_temp": True,
            "has_ir": False,
            "has_multizone": False,
            "min_kelvin": 2500,
            "max_kelvin": 9000,
        },
    },
    "last_seen": "2024-01-01T00:00:00Z",
    "seconds_since_seen": 0,
}

MOCK_LIGHT_DATA_TEMP_ONLY = {
    **MOCK_LIGHT_DATA,
    "id": "d073d55b6335",
    "label": "Temp Only Light",
    "product": {
        "name": "LIFX Mini Day and Dusk",
        "capabilities": {
            "has_color": False,
            "has_variable_color_temp": True,
            "has_ir": False,
            "has_multizone": False,
            "min_kelvin": 1500,
            "max_kelvin": 4000,
        },
    },
}


@pytest.fixture
def mock_light() -> LifxLight:
    """Return a mock LifxLight object."""
    return LifxLight.from_dict(MOCK_LIGHT_DATA)


@pytest.fixture
def mock_light_temp_only() -> LifxLight:
    """Return a mock temperature-only LifxLight object."""
    return LifxLight.from_dict(MOCK_LIGHT_DATA_TEMP_ONLY)


@pytest.fixture
def mock_api() -> Generator[AsyncMock, None, None]:
    """Return a mocked LifxCloudAPI."""
    with patch(
        "custom_components.lifx_cloud.api.LifxCloudAPI", autospec=True
    ) as mock:
        api = mock.return_value
        api.list_lights = AsyncMock(
            return_value=[LifxLight.from_dict(MOCK_LIGHT_DATA)]
        )
        api.set_state = AsyncMock(return_value={"results": [{"status": "ok"}]})
        api.toggle_power = AsyncMock(return_value={"results": [{"status": "ok"}]})
        api.breathe_effect = AsyncMock(return_value={"results": [{"status": "ok"}]})
        api.pulse_effect = AsyncMock(return_value={"results": [{"status": "ok"}]})
        api.validate_token = AsyncMock(return_value=True)
        api.close = AsyncMock()
        yield api
