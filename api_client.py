import aiohttp
import async_timeout
import time
import logging
from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)

class HeatlyApiClient:
    def __init__(self, room_id: str):
        self.url = f"{BASE_URL}/api/room/{room_id}"

    async def send_sensor_data(self, temp: float):
        """Sender temperatur og mottar kontroll-instruksjoner."""
        async with aiohttp.ClientSession() as session:
            try:
                async with async_timeout.timeout(10):
                    payload = {"temperature": temp, "timestamp": int(time.time())}
                    async with session.post(f"{self.url}/sensor", json=payload) as resp:
                        return await resp.json() if resp.status == 200 else None
            except Exception as e:
                _LOGGER.error("API feil: %s", e)
                return None