from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Orei HDMI Matrix outputs as media players."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    config = data["config"]
    zones = config.get("zones", [])
    entities = [
        OreiMatrixOutputMediaPlayer(client, coordinator, config, zone_name, idx, entry.entry_id)
        for idx, zone_name in enumerate(zones, start=1)
    ]

    async_add_entities(entities)


class OreiMatrixOutputMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Represents one HDMI matrix output as a media player source selector."""

    _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE \
                                | MediaPlayerEntityFeature.TURN_OFF \
                                | MediaPlayerEntityFeature.TURN_ON

    def __init__(self, client, coordinator, config, name, output_id, entry_id) -> None:
        super().__init__(coordinator)
        sources = config.get("sources", [])
        self._client = client
        self._config = config
        self._attr_name = name
        self._output_id = output_id
        self._sources = sources
        self._attr_source_list = sources
        self._attr_source = None
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{config.get('host')}_{output_id}"

    @property
    def available(self):
        """Entity availability based on matrix power."""
        return bool(self.coordinator.data.get("power"))

    @property
    def state(self):
        """Entity state is 'on' when matrix powered."""
        return STATE_ON if self.available else STATE_OFF

    async def async_turn_on(self):
        if not self.available:
            return
        outputs = self.coordinator.data.get("outputs")
        if not outputs:
            return
        src_id = outputs[self._output_id]
        await self._client.set_cec_in(src_id, "on")
        self.async_write_ha_state()

    async def async_turn_off(self):
        if not self.available:
            return
        outputs = self.coordinator.data.get("outputs")
        if not outputs:
            return
        src_id = outputs[self._output_id]
        await self._client.set_cec_in(src_id, "off")
        self.async_write_ha_state()

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
        if not self.available:
            return
        outputs = self.coordinator.data.get("outputs")
        if not outputs:
            return
        src_id = outputs[self._output_id]
        if src_id and 1 <= src_id <= len(self._sources):
            self._attr_source = self._sources[src_id - 1]
            self.async_write_ha_state()

    async def async_select_source(self, source):
        """Change active source for this output."""
        if not self.available:
            _LOGGER.warning("Matrix is off; cannot change source for %s", self.name)
            return
        if source not in self._sources:
            _LOGGER.warning("Unknown source %s for %s", source, self.name)
            return
        input_id = self._sources.index(source) + 1
        await self._client.set_output_source(input_id, self._output_id)
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Switched %s to %s", self.name, source)