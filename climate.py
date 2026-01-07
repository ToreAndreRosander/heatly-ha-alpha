from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from .const import DOMAIN, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH

async def async_setup_entry(hass, entry, async_add_entities):
    """Setter opp termostaten basert på config flow-data."""
    config = entry.data
    api_client = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeatlyThermostat(hass, api_client, config)])

class HeatlyThermostat(ClimateEntity):
    """Representasjon av en Heatly-styrt termostat."""

    def __init__(self, hass, api_client, config):
        self.hass = hass
        self._api = api_client
        self._sensor_id = config[CONF_TEMP_SENSOR]
        self._switch_id = config[CONF_HEATER_SWITCH]
        self._attr_name = f"Heatly {config['room_id']}"
        self._attr_unique_id = f"heatly_{config['room_id']}"
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature = 20.0
        self._attr_extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        """Returnerer metadata som trajectory og strategi til HA."""
        return self._attr_extra_state_attributes

    async def update_from_response(self, response):
        """Oppdaterer termostaten med data fra API-responsen."""
        if not response:
            return

        # Lagre heater_state og sett fysisk bryter
        heater_state = response.get("heater_state", "off")
        await self._set_heater_state(heater_state)

        # Lagre rådata for grafen i attributter
        self._attr_extra_state_attributes = {
            "trajectory": response.get("trajectory", []),
            "strategy": response.get("strategy", {}),
            "prediction_age": response.get("prediction_age_seconds", 0)
        }
        self.async_write_ha_state()
        
    def current_temperature(self):
        """Henter temperatur fra den valgte sensoren."""
        state = self.hass.states.get(self._sensor_id)
        return float(state.state) if state and state.state not in ["unknown", "unavailable"] else None

    async def async_set_temperature(self, **kwargs):
        """Brukeren endret temperatur manuelt (kan sendes til skyen senere)."""
        self._attr_target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Skru termostaten av eller på."""
        self._attr_hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            await self._set_heater_state("off")
        self.async_write_ha_state()

    async def _set_heater_state(self, state: str):
        """Fysisk styring av valgt varmekilde."""
        service = "turn_on" if state == "on" else "turn_off"
        domain = self._switch_id.split(".")[0]
        await self.hass.services.async_call(domain, service, {"entity_id": self._switch_id})