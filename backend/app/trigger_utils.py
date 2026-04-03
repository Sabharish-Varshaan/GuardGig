from __future__ import annotations

import asyncio
import os
from typing import Literal

import requests
from dotenv import load_dotenv

load_dotenv()

_RAIN_URL = "https://api.open-meteo.com/v1/forecast"
_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_AQI_URL = "http://api.openweathermap.org/data/2.5/air_pollution"


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _request_json(url: str, params: dict | None = None, timeout: float = 5.0) -> dict:
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def resolve_coordinates(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    timeout: float = 5.0,
) -> tuple[float, float] | None:
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (TypeError, ValueError):
            return None

    if not location:
        return None

    data = _request_json(
        _GEOCODE_URL,
        params={"name": location, "count": 1, "language": "en", "format": "json"},
        timeout=timeout,
    )
    results = data.get("results") or []
    if not results:
        return None

    first = results[0]
    try:
        return float(first.get("latitude")), float(first.get("longitude"))
    except (TypeError, ValueError):
        return None


def get_rain(lat: float, lon: float) -> float:
    url = f"{_RAIN_URL}?latitude={lat}&longitude={lon}&hourly=rain"

    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        rain = data["hourly"]["rain"][0]
    except Exception:
        rain = 0

    return _safe_float(rain, 0.0)


def get_aqi(lat: float, lon: float) -> float:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return 0.0

    url = f"{_AQI_URL}?lat={lat}&lon={lon}&appid={api_key}"

    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        aqi_index = int(data["list"][0]["main"]["aqi"])
    except Exception:
        return 0.0

    mapping = {
        1: 50,
        2: 100,
        3: 150,
        4: 300,
        5: 400,
    }

    return float(mapping.get(aqi_index, 0))


def check_trigger(rain: float, aqi: float) -> dict:
    if rain >= 100:
        return {"trigger": True, "type": "rain", "severity": "full"}

    if rain >= 60:
        return {"trigger": True, "type": "rain", "severity": "partial"}

    if aqi >= 400:
        return {"trigger": True, "type": "aqi", "severity": "full"}

    if aqi >= 300:
        return {"trigger": True, "type": "aqi", "severity": "partial"}

    return {"trigger": False}


async def fetch_rain_mm(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    timeout: float = 5.0,
) -> float:
    coordinates = resolve_coordinates(location=location, lat=lat, lon=lon, timeout=timeout)
    if coordinates is None:
        return 0.0

    return await asyncio.to_thread(get_rain, coordinates[0], coordinates[1])


async def fetch_aqi(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    timeout: float = 5.0,
) -> float:
    coordinates = resolve_coordinates(location=location, lat=lat, lon=lon, timeout=timeout)
    if coordinates is None:
        return 0.0

    return await asyncio.to_thread(get_aqi, coordinates[0], coordinates[1])


def evaluate_rain_trigger(rain_mm: float) -> Literal["none", "partial", "full"]:
    if rain_mm >= 100:
        return "full"
    if rain_mm >= 60:
        return "partial"
    return "none"
