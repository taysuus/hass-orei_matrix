from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector

from .const import DOMAIN


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
            vol.Required("host"): str,
            vol.Optional("port", default=23): int,
            vol.Optional(
                "sources",
                default=[]
            ): selector({"text": {"multiple": True}}),
            vol.Optional(
                "zones",
                default=[]
            ): selector({"text": {"multiple": True}}),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )