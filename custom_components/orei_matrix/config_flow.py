from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_SOURCES, CONF_ZONES, CONF_CEC_ON_SOURCE_SELECT


class OreiMatrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Orei HDMI Matrix config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Orei HDMI Matrix ({user_input.get('host')})",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=23): int,
            vol.Optional(
                CONF_SOURCES,
                default=[]
            ): selector({"text": {"multiple": True}}),
            vol.Optional(
                CONF_ZONES,
                default=[]
            ): selector({"text": {"multiple": True}}),
            vol.Optional(
                CONF_CEC_ON_SOURCE_SELECT,
                default=False
            ): bool,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )