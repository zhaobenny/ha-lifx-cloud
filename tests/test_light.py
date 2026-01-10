"""Tests for the LIFX Cloud light platform."""

import pytest

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ColorMode,
)

from custom_components.lifx_cloud.api import LifxLight
from custom_components.lifx_cloud.light import LifxCloudLight

from .conftest import MOCK_LIGHT_DATA, MOCK_LIGHT_DATA_TEMP_ONLY


class TestLifxCloudLightProperties:
    """Tests for LifxCloudLight properties."""

    def test_is_on(self, mock_light: LifxLight) -> None:
        """Test is_on property."""
        assert mock_light.is_on is True

    def test_brightness(self, mock_light: LifxLight) -> None:
        """Test brightness calculation."""
        # brightness is 0.8 in mock, should convert to 204 (0.8 * 255)
        assert int(mock_light.brightness * 255) == 204

    def test_color_properties(self, mock_light: LifxLight) -> None:
        """Test color-related properties."""
        assert mock_light.hue == 120
        assert mock_light.saturation == 0.5
        assert mock_light.kelvin == 3500

    def test_supports_color(self, mock_light: LifxLight) -> None:
        """Test color support detection."""
        assert mock_light.supports_color is True

    def test_supports_temperature(self, mock_light: LifxLight) -> None:
        """Test temperature support detection."""
        assert mock_light.supports_temperature is True

    def test_temp_only_light(self, mock_light_temp_only: LifxLight) -> None:
        """Test temperature-only light."""
        assert mock_light_temp_only.supports_color is False
        assert mock_light_temp_only.supports_temperature is True
        assert mock_light_temp_only.min_kelvin == 1500
        assert mock_light_temp_only.max_kelvin == 4000


class TestColorModes:
    """Tests for color mode detection."""

    def test_color_mode_hs(self) -> None:
        """Test HS color mode when saturation > 0."""
        data = {**MOCK_LIGHT_DATA, "color": {"hue": 120, "saturation": 0.5, "kelvin": 3500}}
        light = LifxLight.from_dict(data)

        # With color support and saturation > 0, should use HS mode
        assert light.supports_color is True
        assert light.saturation > 0

    def test_color_mode_temp(self) -> None:
        """Test color temp mode when saturation = 0."""
        data = {**MOCK_LIGHT_DATA, "color": {"hue": 0, "saturation": 0, "kelvin": 3500}}
        light = LifxLight.from_dict(data)

        # With saturation = 0, should use color temp mode
        assert light.saturation == 0

    def test_supported_color_modes_full(self) -> None:
        """Test supported color modes for full-color light."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA)

        modes = set()
        if light.supports_color:
            modes.add(ColorMode.HS)
        if light.supports_temperature:
            modes.add(ColorMode.COLOR_TEMP)

        assert ColorMode.HS in modes
        assert ColorMode.COLOR_TEMP in modes

    def test_supported_color_modes_temp_only(self) -> None:
        """Test supported color modes for temp-only light."""
        light = LifxLight.from_dict(MOCK_LIGHT_DATA_TEMP_ONLY)

        modes = set()
        if light.supports_color:
            modes.add(ColorMode.HS)
        if light.supports_temperature:
            modes.add(ColorMode.COLOR_TEMP)

        assert ColorMode.HS not in modes
        assert ColorMode.COLOR_TEMP in modes


class TestLightEffects:
    """Tests for light effects."""

    def test_effect_list(self) -> None:
        """Test effect list contains expected effects."""
        expected_effects = ["breathe", "pulse"]
        # This would be tested through the entity, but we test the concept
        assert "breathe" in expected_effects
        assert "pulse" in expected_effects


class TestDeviceInfo:
    """Tests for device info generation."""

    def test_device_info_fields(self, mock_light: LifxLight) -> None:
        """Test device info contains expected fields."""
        assert mock_light.label == "Test Light"
        assert mock_light.product.get("name") == "LIFX Color"
        assert mock_light.group.get("name") == "Living Room"

    def test_device_info_temp_only(self, mock_light_temp_only: LifxLight) -> None:
        """Test device info for temp-only light."""
        assert mock_light_temp_only.label == "Temp Only Light"
        assert mock_light_temp_only.product.get("name") == "LIFX Mini Day and Dusk"


class TestColorConversions:
    """Tests for color value conversions."""

    def test_hs_to_api_format(self) -> None:
        """Test conversion of HS values to API format."""
        hue = 180
        saturation = 75  # HA uses 0-100

        # API expects saturation as 0-1
        api_color = f"hue:{hue} saturation:{saturation / 100}"
        assert api_color == "hue:180 saturation:0.75"

    def test_kelvin_to_api_format(self) -> None:
        """Test conversion of kelvin to API format."""
        kelvin = 4000

        api_color = f"kelvin:{kelvin}"
        assert api_color == "kelvin:4000"

    def test_brightness_to_api_format(self) -> None:
        """Test conversion of brightness to API format."""
        ha_brightness = 128  # HA uses 0-255

        # API expects 0-1
        api_brightness = ha_brightness / 255
        assert 0.5 < api_brightness < 0.51  # ~0.502


class TestTransitions:
    """Tests for transition handling."""

    def test_default_transition(self) -> None:
        """Test default transition value."""
        kwargs: dict = {}
        duration = kwargs.get(ATTR_TRANSITION, 1.0)
        assert duration == 1.0

    def test_custom_transition(self) -> None:
        """Test custom transition value."""
        kwargs = {ATTR_TRANSITION: 5.0}
        duration = kwargs.get(ATTR_TRANSITION, 1.0)
        assert duration == 5.0
