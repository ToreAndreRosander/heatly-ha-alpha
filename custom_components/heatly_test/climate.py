from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.helpers.restore_state import RestoreEntity
from .const import (
    DOMAIN, CONF_TEMP_SENSOR, CONF_HEATER_SWITCH, CONF_HEATER_SWITCHES,
    CONF_COLD_TOLERANCE, CONF_HOT_TOLERANCE, DEFAULT_COLD_TOLERANCE, 
    DEFAULT_HOT_TOLERANCE, MIN_SWITCH_INTERVAL_SECONDS
)
import logging
import time

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Kalles automatisk av __init__.py for å lage termostaten."""
    config = entry.data
    entry_id = entry.entry_id
    
    # Hent API-klienten som __init__.py lagret
    if DOMAIN not in hass.data or entry_id not in hass.data[DOMAIN]:
        return

    api_client = hass.data[DOMAIN][entry_id]["api"]
    
    thermostat = HeatlyThermostat(hass, api_client, config, entry_id)
    
    # VIKTIG: Gi beskjed tilbake til __init__.py om at termostaten er klar
    hass.data[DOMAIN][entry_id]["thermostat"] = thermostat
    
    async_add_entities([thermostat])

class HeatlyThermostat(ClimateEntity, RestoreEntity):
    """Hybrid thermostat that can operate in Smart (AUTO) or Dumb (HEAT) mode."""

    def __init__(self, hass, api_client, config, entry_id):
        self.hass = hass
        self._api = api_client
        self._sensor_id = config[CONF_TEMP_SENSOR]
        
        # Support multiple heaters - backward compatible with single heater
        if CONF_HEATER_SWITCHES in config:
            self._heater_ids = config[CONF_HEATER_SWITCHES]
        elif CONF_HEATER_SWITCH in config:
            self._heater_ids = [config[CONF_HEATER_SWITCH]]
        else:
            self._heater_ids = []
        
        self._entry_id = entry_id
        
        # Hysteresis parameters for local control
        self._cold_tolerance = config.get(CONF_COLD_TOLERANCE, DEFAULT_COLD_TOLERANCE)
        self._hot_tolerance = config.get(CONF_HOT_TOLERANCE, DEFAULT_HOT_TOLERANCE)
        
        self._attr_name = f"Heatly {config.get('room_id', 'Unknown')}"
        self._attr_unique_id = f"heatly_{config.get('room_id', 'unknown')}"
        
        # Support both AUTO (Heatly/Smart) and HEAT (Local/Dumb) modes
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
        
        # Support target temperature range for MPC scheduling
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.PRESET_MODE
        )
        
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature = 20.0
        self._attr_min_temp = 5.0
        self._attr_max_temp = 35.0
        self._attr_hvac_mode = HVACMode.AUTO  # Default to smart mode
        self._attr_preset_mode = None
        self._attr_preset_modes = []  # Will be populated from API
        self._attr_extra_state_attributes = {}
        
        # State for local controller
        self._local_heater_state = False
        self._api_available = True
        self._last_api_success = None
        self._last_switch_time = 0  # Prevent rapid switching

    async def async_added_to_hass(self):
        """Restore state when entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state is not None:
            # Restore HVAC mode
            if last_state.state in [mode.value for mode in self._attr_hvac_modes]:
                self._attr_hvac_mode = HVACMode(last_state.state)
            
            # Restore target temperature
            if last_state.attributes.get(ATTR_TEMPERATURE):
                self._attr_target_temperature = float(last_state.attributes[ATTR_TEMPERATURE])
            
            # Restore preset mode
            if last_state.attributes.get("preset_mode"):
                self._attr_preset_mode = last_state.attributes["preset_mode"]
            
            _LOGGER.info(
                f"Restored state for {self._attr_name}: "
                f"mode={self._attr_hvac_mode}, temp={self._attr_target_temperature}, "
                f"preset={self._attr_preset_mode}"
            )
        
        # Fetch available schedules from API to populate preset modes
        try:
            schedules = await self._api.get_available_schedules()
            if schedules:
                self._attr_preset_modes = list(schedules.keys())
                _LOGGER.info(f"Loaded {len(self._attr_preset_modes)} schedule presets")
            else:
                _LOGGER.warning("No schedules available from API - preset modes will be empty")
                self._attr_preset_modes = []
        except Exception as e:
            _LOGGER.warning(f"Could not load schedules from API: {e}. Preset modes will be unavailable.")
            self._attr_preset_modes = []

    async def update_from_response(self, response):
        """Mottar ordre fra API (via __init__.py) - only used in AUTO mode."""
        if not response:
            self._api_available = False
            return

        try:
            self._api_available = True
            self._last_api_success = time.time()
            
            heater_state = response.get("heater_state", "off")
            
            # Only apply API commands if in AUTO mode
            if self._attr_hvac_mode == HVACMode.AUTO:
                await self._set_heater_state(heater_state == "on")
            
            self._attr_extra_state_attributes = {
                "trajectory": response.get("trajectory", []),
                "strategy": response.get("strategy", {}),
                "prediction_age": response.get("prediction_age_seconds", 0),
                "control_mode": "smart" if self._attr_hvac_mode == HVACMode.AUTO else "local",
                "api_available": self._api_available
            }
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Feil i termostat oppdatering: {e}")
            self._api_available = False

    async def async_update(self):
        """Periodic update - implements the control logic fork."""
        current_temp = self.current_temperature
        
        if current_temp is None:
            return
        
        # Branch based on HVAC mode
        if self._attr_hvac_mode == HVACMode.AUTO:
            # Smart mode - API controls (handled via update_from_response)
            # Just update attributes
            self._attr_extra_state_attributes["control_mode"] = "smart"
        elif self._attr_hvac_mode == HVACMode.HEAT:
            # Dumb mode - local bang-bang controller
            await self._run_local_controller(current_temp)
        elif self._attr_hvac_mode == HVACMode.OFF:
            # Off mode - ensure heaters are off
            if self._local_heater_state:
                await self._set_heater_state(False)
        
        self.async_write_ha_state()

    async def _run_local_controller(self, current_temp: float):
        """Run local bang-bang controller with hysteresis."""
        target = self._attr_target_temperature
        
        # Prevent rapid switching - enforce minimum time between state changes
        now = time.time()
        time_since_last_switch = now - self._last_switch_time
        
        # Hysteresis logic to prevent short cycling
        should_turn_on = current_temp <= target - self._cold_tolerance
        should_turn_off = current_temp >= target + self._hot_tolerance
        
        if should_turn_on and not self._local_heater_state:
            # Too cold - turn on heater (if minimum interval has passed)
            if time_since_last_switch >= MIN_SWITCH_INTERVAL_SECONDS:
                _LOGGER.debug(
                    f"Local controller: turning ON (temp={current_temp:.1f}°C, "
                    f"target={target:.1f}°C, threshold={target - self._cold_tolerance:.1f}°C)"
                )
                await self._set_heater_state(True)
                self._last_switch_time = now
            else:
                _LOGGER.debug(
                    f"Local controller: delaying turn ON for {MIN_SWITCH_INTERVAL_SECONDS - time_since_last_switch:.0f}s "
                    f"to prevent rapid cycling"
                )
        elif should_turn_off and self._local_heater_state:
            # Too hot - turn off heater (if minimum interval has passed)
            if time_since_last_switch >= MIN_SWITCH_INTERVAL_SECONDS:
                _LOGGER.debug(
                    f"Local controller: turning OFF (temp={current_temp:.1f}°C, "
                    f"target={target:.1f}°C, threshold={target + self._hot_tolerance:.1f}°C)"
                )
                await self._set_heater_state(False)
                self._last_switch_time = now
            else:
                _LOGGER.debug(
                    f"Local controller: delaying turn OFF for {MIN_SWITCH_INTERVAL_SECONDS - time_since_last_switch:.0f}s "
                    f"to prevent rapid cycling"
                )
        # else: within deadband, maintain current state
        
        self._attr_extra_state_attributes = {
            "control_mode": "local",
            "target_temperature": target,
            "cold_threshold": target - self._cold_tolerance,
            "hot_threshold": target + self._hot_tolerance,
            "heater_state": "on" if self._local_heater_state else "off",
            "time_since_last_switch": int(time_since_last_switch)
        }

    @property
    def current_temperature(self):
        state = self.hass.states.get(self._sensor_id)
        if state and state.state not in ["unknown", "unavailable", None]:
            try:
                return float(state.state)
            except ValueError:
                pass
        return None

    async def async_set_temperature(self, **kwargs):
        """Set target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp:
            self._attr_target_temperature = temp
            
            # If in HEAT mode, immediately run local controller
            if self._attr_hvac_mode == HVACMode.HEAT:
                current_temp = self.current_temperature
                if current_temp is not None:
                    await self._run_local_controller(current_temp)
            
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode - switching between Smart (AUTO) and Local (HEAT) control."""
        old_mode = self._attr_hvac_mode
        self._attr_hvac_mode = hvac_mode
        
        _LOGGER.info(f"HVAC mode changed from {old_mode} to {hvac_mode}")
        
        if hvac_mode == HVACMode.OFF:
            # Turn off all heaters
            await self._set_heater_state(False)
        elif hvac_mode == HVACMode.HEAT:
            # Switch to local control - run controller immediately
            current_temp = self.current_temperature
            if current_temp is not None:
                await self._run_local_controller(current_temp)
        elif hvac_mode == HVACMode.AUTO:
            # Switch to smart mode - will be controlled by API
            _LOGGER.info("Switched to AUTO mode - waiting for API control")
        
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str):
        """Set preset mode (schedule selection)."""
        if preset_mode not in self._attr_preset_modes:
            _LOGGER.warning(f"Invalid preset mode: {preset_mode}")
            return
        
        self._attr_preset_mode = preset_mode
        
        # Update schedule via API
        success = await self._api.update_room_schedule(preset_mode)
        if success:
            _LOGGER.info(f"Successfully changed schedule to {preset_mode}")
        else:
            _LOGGER.error(f"Failed to update schedule to {preset_mode}")
        
        self.async_write_ha_state()

    async def _set_heater_state(self, state: bool):
        """Set heater state for all configured heaters."""
        self._local_heater_state = state
        
        for heater_id in self._heater_ids:
            domain = heater_id.split(".")[0]
            try:
                if domain == "climate":
                    # Climate entities use set_hvac_mode instead of turn_on/turn_off
                    hvac_mode = "heat" if state else "off"
                    await self.hass.services.async_call(
                        "climate",
                        "set_hvac_mode",
                        {"entity_id": heater_id, "hvac_mode": hvac_mode},
                        blocking=False
                    )
                    _LOGGER.debug(f"Set {heater_id} to hvac_mode={hvac_mode}")
                else:
                    # Switch, input_boolean, light use turn_on/turn_off
                    service = "turn_on" if state else "turn_off"
                    await self.hass.services.async_call(
                        domain, 
                        service, 
                        {"entity_id": heater_id},
                        blocking=False
                    )
                    _LOGGER.debug(f"Called {service} on {heater_id}")
            except Exception as e:
                _LOGGER.error(f"Failed to control {heater_id}: {e}")