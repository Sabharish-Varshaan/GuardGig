from typing import Literal

import httpx


async def _fetch_json(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


async def fetch_rain_mm(location: str, timeout: float = 8.0) -> float:
    url = f"https://wttr.in/{location}?format=j1"
    async with httpx.AsyncClient(timeout=timeout) as client:
        data = await _fetch_json(client, url)
    current = data.get("current_condition", [{}])[0]
    return float(current.get("precipMM", 0.0))


async def fetch_aqi(location: str, timeout: float = 8.0) -> float | None:
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    async with httpx.AsyncClient(timeout=timeout) as client:
        geo_data = await _fetch_json(client, geocode_url, params={"name": location, "count": 1})
        results = geo_data.get("results") or []
        if not results:
            return None

        latitude = results[0].get("latitude")
        longitude = results[0].get("longitude")
        if latitude is None or longitude is None:
            return None

        aqi_data = await _fetch_json(
            client,
            air_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "us_aqi",
                "timezone": "UTC",
            },
        )

    hourly = aqi_data.get("hourly", {})
    aqi_values = hourly.get("us_aqi") or []
    for value in reversed(aqi_values):
        if value is not None:
            return float(value)

    return None


def evaluate_rain_trigger(rain_mm: float) -> Literal["none", "partial", "full"]:
    if rain_mm >= 100:
        return "full"
    if rain_mm >= 60:
        return "partial"
    return "none"
