from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from .const import DOMAIN, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH

async def async_setup_entry(hass, entry, async_add_entities):
    """Setter opp termostaten basert på config flow-data."""
    config = entry.data
    # Hent API-klienten fra den nye strukturen
    api_client = hass.data[DOMAIN][entry.entry_id]

    # not sure why changed from this:
    # api_client = hass.data[DOMAIN][entry.entry_id]["api"]
    
    thermostat = HeatlyThermostat(hass, api_client, config)
    # Store thermostat entity reference for __init__.py to use
    hass.data[DOMAIN]["thermostat_entity"] = thermostat
    async_add_entities([thermostat])

class HeatlyThermostat(ClimateEntity):
    """Representasjon av en Heatly-styrt termostat."""

    def __init__(self, hass, api_client, config, entry_id):
        self.hass = hass
        self._api = api_client
        self._sensor_id = config[CONF_TEMP_SENSOR]
        self._switch_id = config[CONF_HEATER_SWITCH]
        self._entry_id = entry_id
        
        self._attr_name = f"Heatly {config['room_id']}"
        self._attr_unique_id = f"heatly_{config['room_id']}"
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature = 20.0
        self._attr_min_temp = 5.0
        self._attr_max_temp = 35.0
        self._attr_extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    async def update_from_response(self, response):
        """Kalles fra __init__.py når API har svart."""
        if not response:
            return

        # Oppdater fysisk ovn
        heater_state = response.get("heater_state", "off")
        await self._set_heater_state(heater_state)
        
        # Oppdater status i HA
        self._attr_hvac_mode = HVACMode.HEAT if heater_state == "on" else HVACMode.OFF
        
        # Lagre AI-data (trajectory) for grafer
        self._attr_extra_state_attributes = {
            "trajectory": response.get("trajectory", []),
            "strategy": response.get("strategy", {}),
            "prediction_age": response.get("prediction_age_seconds", 0)
        }
        self.async_write_ha_state()
        
    @property
    def current_temperature(self):
        state = self.hass.states.get(self._sensor_id)
        if state and state.state not in ["unknown", "unavailable"]:
            return float(state.state)
        return None

    async def async_set_temperature(self, **kwargs):
        """Bruker endrer temp i kortet."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp:
            self._attr_target_temperature = temp
            self.async_write_ha_state()
            # Her bør du sende den nye temperaturen til API-et ditt også, hvis API-et støtter det
            # await self._api.set_target_temp(temp)

    async def async_set_hvac_mode(self, hvac_mode):
        """Bruker skrur av/på i kortet."""
        self._attr_hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            await self._set_heater_state("off")
        self.async_write_ha_state()

    async def _set_heater_state(self, state: str):
        """Skrur den fysiske bryteren av eller på."""
        service = "turn_on" if state == "on" else "turn_off"
        # Håndterer switch, input_boolean, light etc.
        domain = self._switch_id.split(".")[0] 
        await self.hass.services.async_call(
            domain, 
            service, 
            {"entity_id": self._switch_id},
            blocking=False
        )