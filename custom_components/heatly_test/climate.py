from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .api_client import HeatlyApiClient
from .const import (
    DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH,
    CONF_OUTDOOR_SENSOR, CONF_API_URL, DEFAULT_API_URL, SCAN_INTERVAL_SECONDS
)
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Setter opp Heatly via GUI."""
    room_id = entry.data[CONF_ROOM_ID]
    sensor_id = entry.data[CONF_TEMP_SENSOR]
    outdoor_sensor_id = entry.data.get(CONF_OUTDOOR_SENSOR)
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    
    api_client = HeatlyApiClient(room_id, api_url)
    
    # Opprett lagringsplass
    hass.data.setdefault(DOMAIN, {})
    # Vi lagrer både API og plass til termostaten (som fylles av climate.py)
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api_client,
        "thermostat": None 
    }

    async def send_sensor_update():
        """Send current sensor data to API."""
        state = hass.states.get(sensor_id)
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                temp = float(state.state)
            except ValueError:
                return # Ikke krasj hvis temp ikke er et tall
            
            outdoor_temp = None
            if outdoor_sensor_id:
                outdoor_state = hass.states.get(outdoor_sensor_id)
                if outdoor_state and outdoor_state.state not in ["unknown", "unavailable"]:
                    try:
                        outdoor_temp = float(outdoor_state.state)
                    except (ValueError, TypeError):
                        pass
            
            # Send data til API
            try:
                response = await api_client.send_sensor_data(temp, outdoor_temp)
            except Exception as e:
                _LOGGER.error(f"Feil ved sending av data til API: {e}")
                return

            # Oppdater termostaten hvis den er klar
            data_store = hass.data[DOMAIN].get(entry.entry_id)
            if data_store:
                thermostat = data_store.get("thermostat")
                if thermostat and response:
                    await thermostat.update_from_response(response)
                elif not thermostat:
                    _LOGGER.debug("Termostat-enhet er ikke klar ennå, venter...")

    async def sensor_changed(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ["unknown", "unavailable"]:
            await send_sensor_update()

    async_track_state_change_event(hass, [sensor_id], sensor_changed)
    
    async def periodic_update(now):
        await send_sensor_update()
    
    async_track_time_interval(
        hass,
        periodic_update,
        timedelta(seconds=SCAN_INTERVAL_SECONDS)
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True