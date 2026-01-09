import aiohttp
import async_timeout
import time
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

class HeatlyApiClient:
    def __init__(self, room_id: str, api_url: str):
        self.room_id = room_id
        self.base_url = api_url.rstrip('/')
        self.url = f"{self.base_url}/api/room/{room_id}"

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
                    
                    async with session.post(f"{self.url}/sensor", json=payload) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        else:
                            _LOGGER.warning(f"API returned status {resp.status}")
                            return None
            except asyncio.TimeoutError:
                _LOGGER.error(f"API timeout for room {self.room_id}")
                return None
            except Exception as e:
                _LOGGER.error(f"API error for room {self.room_id}: %s", e)
                return None