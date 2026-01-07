import voluptuous as f
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH

class HeatlyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer onboarding-prosessen for Heatly."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"Heatly {user_input[CONF_ROOM_ID]}", data=user_input)

        # Skjemaet brukeren ser i HA
        data_schema = f.Schema({
            f.Required(CONF_ROOM_ID): str,
            f.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            f.Required(CONF_HEATER_SWITCH): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch", "light", "outlet"])
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)