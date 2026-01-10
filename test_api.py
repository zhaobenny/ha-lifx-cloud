"""Test script for LIFX Cloud API."""

import asyncio
import os
import sys

# Add the custom_components to the path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

from custom_components.lifx_cloud.api import LifxCloudAPI, LifxCloudAPIError


async def main() -> None:
    """Test the LIFX Cloud API."""
    load_dotenv()

    token = os.getenv("LIFX_TOKEN")
    if not token:
        print("Error: LIFX_TOKEN not found in .env file")
        return

    print("Testing LIFX Cloud API...")
    print("-" * 50)

    api = LifxCloudAPI(token)

    try:
        # List all lights
        print("\n1. Listing all lights:")
        lights = await api.list_lights()

        if not lights:
            print("   No lights found!")
        else:
            for light in lights:
                print(f"\n   Light: {light.label}")
                print(f"   - ID: {light.id}")
                print(f"   - Connected: {light.connected}")
                print(f"   - Power: {light.power}")
                print(f"   - Brightness: {light.brightness:.0%}")
                print(f"   - Color: H={light.hue:.0f}, S={light.saturation:.0%}, K={light.kelvin}")
                print(f"   - Product: {light.product.get('name', 'Unknown')}")
                print(f"   - Location: {light.location.get('name', 'Unknown')}")
                print(f"   - Group: {light.group.get('name', 'Unknown')}")
                print(f"   - Supports Color: {light.supports_color}")
                print(f"   - Supports Temp: {light.supports_temperature}")
                if light.supports_temperature:
                    print(f"   - Kelvin Range: {light.min_kelvin}-{light.max_kelvin}")

        # Test toggling power if there are lights
        if lights:
            print("\n2. API connection successful!")
            print(f"   Found {len(lights)} light(s)")

    except LifxCloudAPIError as err:
        print(f"Error: {err}")
    finally:
        await api.close()

    print("\n" + "-" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
