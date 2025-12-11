from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    config = data["config"]

    async_add_entities([OreiMatrixPowerSwitch(client, coordinator, config, entry.entry_id)])


class OreiMatrixPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Switch for Orei HDMI Matrix power."""

    def __init__(self, client, coordinator, config, entry_id) -> None:
        super().__init__(coordinator)
        self._client = client
        self._config = config
        self._entry_id = entry_id
        self._attr_name = f"{config.get('host', 'Orei Matrix')} Power"
        self._attr_unique_id = f"{DOMAIN}_{config.get('host')}_power"

    @property
    def device_info(self):
        """Device info for grouping and model-based naming."""
        model = self.coordinator.data.get("type", "Unknown")
        name = f"Orei {model}" if model != "Unknown" else "Orei HDMI Matrix"
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": name,
            "manufacturer": "Orei",
            "model": model,
            "configuration_url": f"http://{self._config.get('host')}",
        }

    @property
    def is_on(self):
        return self.coordinator.data.get("power")

    async def async_turn_on(self, **kwargs):
        await self._client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.set_power(False)
        await self.coordinator.async_request_refresh()