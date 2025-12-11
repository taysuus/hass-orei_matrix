from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Orei HDMI Matrix outputs as buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    config = data["config"]
    zones = config.get("zones", [])
    entities = [
        OreiMatrixOutputButton(client, coordinator, config, f"{zone_name} next source", idx, entry.entry_id)
        for idx, zone_name in enumerate(zones, start=1)
    ]

    async_add_entities(entities)


class OreiMatrixOutputButton(CoordinatorEntity, ButtonEntity):
    """Represents one HDMI matrix output as a button to cycle sources."""

    def __init__(self, client, coordinator, config, name, output_id, entry_id) -> None:
        super().__init__(coordinator)
        sources = config.get("sources", [])
        self._client = client
        self._config = config
        self._attr_name = name
        self._output_id = output_id
        self._sources = sources
        self._current = None
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{config.get('host')}_{output_id}_next_source"

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

    @callback
    def _handle_coordinator_update(self):
        outputs = self.coordinator.data.get("outputs")
        if not outputs:
            return
        self._current = outputs[self._output_id]
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._current == None:
            _LOGGER.warning("Current input is unknown; cannot change source for %s", self.name)
            return

        input_id = (self._current % len(self._sources)) + 1
        source = self._sources[input_id - 1]
        await self._client.set_output_source(input_id, self._output_id)
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Switched %s to %s", self.name, source)