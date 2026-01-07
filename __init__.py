from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from .api_client import HeatlyApiClient
from .const import DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR

async def async_setup_entry(hass: HomeAssistant, entry):
    """Setter opp Heatly via GUI."""
    room_id = entry.data[CONF_ROOM_ID]
    sensor_id = entry.data[CONF_TEMP_SENSOR]
    
    api_client = HeatlyApiClient(room_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client

    # Lytt på sensoren og oppdater API-et/ovnen umiddelbart
    async def sensor_changed(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ["unknown", "unavailable"]:
            response = await api_client.send_sensor_data(float(new_state.state))
            
            # Finn termostaten i HA og dytt inn de nye dataene
            component = hass.data[DOMAIN].get("thermostat_entity")
            if component and response:
                await component.update_from_response(response)

    async_track_state_change_event(hass, [sensor_id], sensor_changed)

    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True

