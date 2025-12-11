from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging

from .const import DOMAIN
from .coordinator import OreiMatrixClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "media_player", "select", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    client = OreiMatrixClient(entry.data["host"], entry.data.get("port", 23))
    type_str = await client.get_type()

    async def async_update_data():
        try:
            power = await client.get_power()
            outputs = await client.get_output_sources()
            return {
                "power": power,
                "type": type_str,
                "outputs": outputs
            }
        except Exception as err:
            _LOGGER.error("Update failed: %s", err)
            raise UpdateFailed(err)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="orei_matrix",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30)
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "config": entry.data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    async def handle_refresh_service(call: ServiceCall):
        """Handle manual refresh of all states."""
        await coordinator.async_request_refresh()

    # Register the service
    hass.services.async_register(
        DOMAIN,
        "refresh",
        handle_refresh_service,
        schema=None,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded