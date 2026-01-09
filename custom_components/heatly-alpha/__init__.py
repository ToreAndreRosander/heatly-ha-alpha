from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .api_client import HeatlyApiClient
from .const import (
    DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH,
    CONF_OUTDOOR_SENSOR, CONF_API_URL, DEFAULT_API_URL, SCAN_INTERVAL_SECONDS
)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Setter opp Heatly via GUI."""
    room_id = entry.data[CONF_ROOM_ID]
    sensor_id = entry.data[CONF_TEMP_SENSOR]
    outdoor_sensor_id = entry.data.get(CONF_OUTDOOR_SENSOR)
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    
    api_client = HeatlyApiClient(room_id, api_url)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client

    # Function to send sensor data to API
    async def send_sensor_update():
        """Send current sensor data to API."""
        state = hass.states.get(sensor_id)
        if state and state.state not in ["unknown", "unavailable"]:
            temp = float(state.state)
            
            # Get outdoor temperature if configured
            outdoor_temp = None
            if outdoor_sensor_id:
                outdoor_state = hass.states.get(outdoor_sensor_id)
                if outdoor_state and outdoor_state.state not in ["unknown", "unavailable"]:
                    try:
                        outdoor_temp = float(outdoor_state.state)
                    except (ValueError, TypeError):
                        pass
            
            response = await api_client.send_sensor_data(temp, outdoor_temp)
            
            # Find thermostat entity and update with response
            component = hass.data[DOMAIN].get("thermostat_entity")
            if component and response:
                await component.update_from_response(response)

    # Send sensor data immediately on state change
    async def sensor_changed(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ["unknown", "unavailable"]:
            await send_sensor_update()

    async_track_state_change_event(hass, [sensor_id], sensor_changed)
    
    # Also send sensor data every SCAN_INTERVAL_SECONDS (minimum every minute)
    async def periodic_update(now):
        """Send periodic sensor updates."""
        await send_sensor_update()
    
    async_track_time_interval(
        hass,
        periodic_update,
        timedelta(seconds=SCAN_INTERVAL_SECONDS)
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True

