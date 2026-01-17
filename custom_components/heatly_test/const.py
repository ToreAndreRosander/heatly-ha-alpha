DOMAIN = "heatly_test"
CONF_ROOM_ID = "room_id"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HEATER_SWITCH = "heater_switch"
CONF_HEATER_SWITCHES = "heater_switches"  # Multiple heaters support
CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_API_URL = "api_url"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HOT_TOLERANCE = "hot_tolerance"
DEFAULT_API_URL = "http://localhost:5364"

# Import timing configuration from config module
from .config import (
    DEFAULT_COLD_TOLERANCE,
    DEFAULT_HOT_TOLERANCE,
    SCAN_INTERVAL_SECONDS,
    SCHEDULE_CACHE_SECONDS,
    MIN_SWITCH_INTERVAL_SECONDS
)