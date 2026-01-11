from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .api_client import HeatlyApiClient
from .const import (
    DOMAIN, CONF_ROOM_ID, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH, CONF_HEATER_SWITCHES,
    CONF_OUTDOOR_SENSOR, CONF_API_URL, DEFAULT_API_URL, SCAN_INTERVAL_SECONDS
)
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Lar HA sette opp integrasjonen."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Setter opp Heatly via GUI og starter loopen."""
    room_id = entry.data[CONF_ROOM_ID]
    sensor_id = entry.data[CONF_TEMP_SENSOR]
    outdoor_sensor_id = entry.data.get(CONF_OUTDOOR_SENSOR)
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    
    api_client = HeatlyApiClient(room_id, api_url)
    
    # 1. Opprett lagringsplass i HA
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api_client,
        "thermostat": None  # Denne fylles av climate.py senere
    }

    # 2. Definer funksjonen som sender data til skyen og oppdaterer termostat
    async def send_sensor_update():
        """Send current sensor data to API and update thermostat."""
        state = hass.states.get(sensor_id)
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                temp = float(state.state)
            except ValueError:
                return 
            
            outdoor_temp = None
            if outdoor_sensor_id:
                outdoor_state = hass.states.get(outdoor_sensor_id)
                if outdoor_state and outdoor_state.state not in ["unknown", "unavailable"]:
                    try:
                        outdoor_temp = float(outdoor_state.state)
                    except (ValueError, TypeError):
                        pass
            
            # Get thermostat reference
            data_store = hass.data[DOMAIN].get(entry.entry_id)
            if not data_store:
                return
            
            thermostat = data_store.get("thermostat")
            if not thermostat:
                return
            
            # If in AUTO mode, send to API and get control commands
            from homeassistant.components.climate import HVACMode
            if thermostat.hvac_mode == HVACMode.AUTO:
                try:
                    response = await api_client.send_sensor_data(temp, outdoor_temp)
                    if response:
                        await thermostat.update_from_response(response)
                    else:
                        _LOGGER.warning("No response from API - thermostat may switch to failsafe")
                except Exception as e:
                    _LOGGER.error(f"API error: {e}")
            
            # If in HEAT mode (local control), run local update
            elif thermostat.hvac_mode == HVACMode.HEAT:
                await thermostat.async_update()

    # 3. Lytt på endringer i temperatur
    async def sensor_changed(event):
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ["unknown", "unavailable"]:
            await send_sensor_update()

    async_track_state_change_event(hass, [sensor_id], sensor_changed)
    
    # 4. Kjør periodisk sjekk også (hvert minutt)
    async def periodic_update(now):
        await send_sensor_update()
    
    async_track_time_interval(
        hass,
        periodic_update,
        timedelta(seconds=SCAN_INTERVAL_SECONDS)
    )

    # 5. Fortell HA at vi har en klimaanordning (climate.py)
    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True