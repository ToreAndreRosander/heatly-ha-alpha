import logging
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH, 
    CONF_HEATER_SWITCHES, CONF_OUTDOOR_SENSOR, CONF_API_URL, 
    CONF_COLD_TOLERANCE, CONF_HOT_TOLERANCE,
    DEFAULT_API_URL, DEFAULT_COLD_TOLERANCE, DEFAULT_HOT_TOLERANCE
)
import voluptuous as vol
from homeassistant.helpers import selector

_LOGGER = logging.getLogger(__name__)

class HeatlyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer onboarding-prosessen for Heatly."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Heatly: async_step_user called")
        
        if user_input is not None:
            # Convert single heater to list for backward compatibility
            if CONF_HEATER_SWITCH in user_input and CONF_HEATER_SWITCHES not in user_input:
                user_input[CONF_HEATER_SWITCHES] = [user_input[CONF_HEATER_SWITCH]]
                del user_input[CONF_HEATER_SWITCH]
            
            return self.async_create_entry(
                title=f"Heatly {user_input[CONF_ROOM_ID]}", 
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required(CONF_ROOM_ID): str,
            vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Required(CONF_HEATER_SWITCHES): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch", "input_boolean", "light"],
                    multiple=True
                )
            ),
            vol.Optional(CONF_OUTDOOR_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
            vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_COLD_TOLERANCE): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=5.0)
            ),
            vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_HOT_TOLERANCE): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=5.0)
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HeatlyOptionsFlow(config_entry)


class HeatlyOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Heatly integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            return self.async_create_entry(title="", data=user_input)

        # Get current values
        current_data = self.config_entry.data
        
        options_schema = vol.Schema({
            vol.Optional(
                CONF_COLD_TOLERANCE,
                default=current_data.get(CONF_COLD_TOLERANCE, DEFAULT_COLD_TOLERANCE)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
            vol.Optional(
                CONF_HOT_TOLERANCE,
                default=current_data.get(CONF_HOT_TOLERANCE, DEFAULT_HOT_TOLERANCE)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
            vol.Optional(
                CONF_API_URL,
                default=current_data.get(CONF_API_URL, DEFAULT_API_URL)
            ): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )