import aiohttp
import async_timeout
import time
import logging
import asyncio
from .const import SCHEDULE_CACHE_SECONDS

_LOGGER = logging.getLogger(__name__)

class HeatlyApiClient:
    def __init__(self, room_id: str, api_url: str, api_key: str = None):
        self.room_id = room_id
        self.base_url = api_url.rstrip('/')
        self.url = f"{self.base_url}/api/room/{room_id}"
        self.api_key = api_key
        self._available_schedules = None
        self._last_schedule_fetch = 0

    async def send_sensor_data(self, temp: float, outdoor_temp: float = None):
        """Sender temperatur og mottar kontroll-instruksjoner."""
        async with aiohttp.ClientSession() as session:
            try:
                async with async_timeout.timeout(10):
                    payload = {
                        "temperature": temp,
                        "timestamp": int(time.time())
                    }
                    if outdoor_temp is not None:
                        payload["outdoor_temp"] = outdoor_temp
                    
                    # Prepare headers with API key if available
                    headers = {'Content-Type': 'application/json'}
                    if self.api_key:
                        headers['X-Heatly-User-API-Key'] = self.api_key
                    
                    async with session.post(f"{self.url}/sensor", json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 401 or resp.status == 403:
                            _LOGGER.error(
                                f"Authentication failed for room '{self.room_id}'. "
                                f"Please check your API key. Status: {resp.status}"
                            )
                            return None
                        elif resp.status == 404:
                            _LOGGER.error(
                                f"Room '{self.room_id}' not found in API. "
                                f"Please ensure room exists in heatly-api database. "
                                f"URL: {self.url}/sensor"
                            )
                            return None
                        else:
                            _LOGGER.warning(
                                f"API returned status {resp.status} for room '{self.room_id}'. "
                                f"URL: {self.url}/sensor"
                            )
                            return None
            except asyncio.TimeoutError:
                _LOGGER.error(f"API timeout for room {self.room_id}")
                return None
            except Exception as e:
                _LOGGER.error(f"API error for room {self.room_id}: %s", e)
                return None

    async def get_available_schedules(self):
        """Fetch available schedules from API. Cached for 5 minutes."""
        now = time.time()
        if self._available_schedules and (now - self._last_schedule_fetch) < SCHEDULE_CACHE_SECONDS:
            return self._available_schedules
        
        async with aiohttp.ClientSession() as session:
            try:
                async with async_timeout.timeout(10):
                    async with session.get(f"{self.base_url}/api/schedules") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            schedules = data.get("schedules", {})
                            if schedules:
                                self._available_schedules = schedules
                                self._last_schedule_fetch = now
                                return self._available_schedules
                            else:
                                _LOGGER.warning("API returned empty schedules")
                                return None
                        else:
                            _LOGGER.warning(f"Failed to fetch schedules: status {resp.status}")
                            return None
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout fetching schedules from API")
                return None
            except Exception as e:
                _LOGGER.error(f"Error fetching schedules: {e}")
                return None

    async def update_room_schedule(self, schedule_name: str):
        """Update the active schedule for the room."""
        # Validate input - check for None, empty string, or whitespace-only
        if not schedule_name or not schedule_name.strip():
            _LOGGER.error(
                f"Cannot update schedule for room {self.room_id}: "
                f"schedule_name is {'None' if schedule_name is None else 'empty or whitespace'}"
            )
            return False
            
        async with aiohttp.ClientSession() as session:
            try:
                async with async_timeout.timeout(10):
                    payload = {"active_schedule": schedule_name.strip()}
                    async with session.post(f"{self.url}/schedule", json=payload) as resp:
                        if resp.status == 200:
                            _LOGGER.info(
                                f"Successfully updated schedule to '{schedule_name.strip()}' for room {self.room_id}"
                            )
                            return True
                        elif resp.status == 404:
                            _LOGGER.error(
                                f"Room '{self.room_id}' not found when updating schedule. "
                                f"Please ensure room exists in heatly-api database. "
                                f"URL: {self.url}/schedule"
                            )
                            return False
                        else:
                            _LOGGER.warning(
                                f"Failed to update schedule for room '{self.room_id}': status {resp.status}. "
                                f"URL: {self.url}/schedule"
                            )
                            return False
            except asyncio.TimeoutError:
                _LOGGER.error(f"Timeout updating schedule for room {self.room_id}")
                return False
            except Exception as e:
                _LOGGER.error(f"Error updating schedule for room {self.room_id}: {e}")
                return False