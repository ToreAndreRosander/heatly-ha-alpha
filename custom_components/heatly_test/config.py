"""
Heatly Home Assistant Plugin Configuration

Central configuration file for timing parameters and other easily configurable settings.
This makes it easier to adjust parameters during pilot testing.
"""

# Scan and Schedule Configuration
SCAN_INTERVAL_SECONDS = 60  # Send sensor data every 60 seconds
SCHEDULE_CACHE_SECONDS = 600  # 10 minutes - cache schedules from API
MIN_SWITCH_INTERVAL_SECONDS = 60  # Minimum time between heater state changes

# Tolerance Configuration
DEFAULT_COLD_TOLERANCE = 0.5  # Degrees C below target to turn on heater
DEFAULT_HOT_TOLERANCE = 0.5  # Degrees C above target to turn off heater
