from __future__ import annotations

import asyncio
import os
import re
import time
from typing import Literal
from urllib.parse import quote

import requests
from dotenv import load_dotenv

from .config import get_settings

load_dotenv()

_RAIN_URL = "https://api.open-meteo.com/v1/forecast"
_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_REVERSE_GEOCODE_URL = "https://nominatim.openstreetmap.org/reverse"
_AQI_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
_AQI_IN_URL = "https://www.aqi.in/in/dashboard/{country}/{state}/{city}"

_CACHE_TTL_COORDS_SECONDS = 600.0
_CACHE_TTL_RAIN_SECONDS = 45.0
_CACHE_TTL_AQI_SECONDS = 90.0
_CACHE_TTL_AQI_IN_URL_SECONDS = 21600.0

_coords_cache: dict[str, tuple[float, tuple[float, float]]] = {}
_rain_cache: dict[str, tuple[float, float]] = {}
_aqi_cache: dict[str, tuple[float, float]] = {}
_aqi_in_url_cache: dict[str, tuple[float, str]] = {}


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


def _cache_get(cache: dict[str, tuple[float, object]], key: str) -> object | None:
    entry = cache.get(key)
    if not entry:
        return None

    expires_at, value = entry
    if time.monotonic() >= expires_at:
        cache.pop(key, None)
        return None

    return value


def _cache_set(cache: dict[str, tuple[float, object]], key: str, value: object, ttl_seconds: float) -> None:
    cache[key] = (time.monotonic() + ttl_seconds, value)


def _lat_lon_cache_key(lat: float, lon: float, precision: int = 3) -> str:
    return f"{round(float(lat), precision)}:{round(float(lon), precision)}"


def _slugify(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _reverse_geocode(lat: float, lon: float, timeout: float = 5.0) -> dict | None:
    try:
        response = requests.get(
            _REVERSE_GEOCODE_URL,
            params={
                "format": "jsonv2",
                "lat": float(lat),
                "lon": float(lon),
                "zoom": 10,
                "addressdetails": 1,
            },
            headers={"User-Agent": "GuardGig/1.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _build_aqi_in_url(location: str | None = None, lat: float | None = None, lon: float | None = None, timeout: float = 5.0) -> str | None:
    if lat is None or lon is None:
        return None

    cache_key = _lat_lon_cache_key(lat, lon)
    cached_url = _cache_get(_aqi_in_url_cache, cache_key)
    if isinstance(cached_url, str):
        return cached_url

    details = _reverse_geocode(lat, lon, timeout=timeout)
    if not details:
        return None

    address = details.get("address") or {}
    country_code = str(address.get("country_code") or "").upper()
    if country_code != "IN":
        return None

    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
        or details.get("name")
        or location
    )
    state = address.get("state") or address.get("state_district")

    if isinstance(city, str) and city.lower().endswith(" corporation") and address.get("state_district"):
        city = address.get("state_district")

    if not city or not state:
        return None

    aqi_in_url = _AQI_IN_URL.format(
        country=quote(_slugify(details.get("country") or "india")),
        state=quote(_slugify(state)),
        city=quote(_slugify(city)),
    )
    _cache_set(_aqi_in_url_cache, cache_key, aqi_in_url, _CACHE_TTL_AQI_IN_URL_SECONDS)
    return aqi_in_url


def _parse_aqi_in_value(page_text: str) -> float | None:
    patterns = (
        r"Live AQI\s*([0-9]+(?:\.[0-9]+)?)\s*AQI \(US\)",
        r"current real-time AQI \(US\) level.*? is\s*([0-9]+(?:\.[0-9]+)?)\s*\(",
        r"\bAQI\s*([0-9]+(?:\.[0-9]+)?)AQI \(US\)Air Quality is",
    )

    for pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _safe_float(match.group(1), 0.0)

    return None


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

    cache_key = location.strip().lower()
    cached_coordinates = _cache_get(_coords_cache, cache_key)
    if isinstance(cached_coordinates, tuple) and len(cached_coordinates) == 2:
        return float(cached_coordinates[0]), float(cached_coordinates[1])

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
        coordinates = float(first.get("latitude")), float(first.get("longitude"))
        _cache_set(_coords_cache, cache_key, coordinates, _CACHE_TTL_COORDS_SECONDS)
        return coordinates
    except (TypeError, ValueError):
        return None


def get_rain(lat: float, lon: float) -> float:
    cache_key = _lat_lon_cache_key(lat, lon)
    cached_rain = _cache_get(_rain_cache, cache_key)
    if isinstance(cached_rain, float):
        return cached_rain

    url = f"{_RAIN_URL}?latitude={lat}&longitude={lon}&hourly=rain"

    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        rain = data["hourly"]["rain"][0]
    except Exception:
        rain = 0

    rain_value = _safe_float(rain, 0.0)
    _cache_set(_rain_cache, cache_key, rain_value, _CACHE_TTL_RAIN_SECONDS)
    return rain_value


def get_aqi(location: str | None = None, lat: float | None = None, lon: float | None = None) -> float:
    if lat is not None and lon is not None:
        cache_key = _lat_lon_cache_key(lat, lon)
        cached_aqi = _cache_get(_aqi_cache, cache_key)
        if isinstance(cached_aqi, float):
            return cached_aqi

    aqi_in_url = _build_aqi_in_url(location=location, lat=lat, lon=lon)
    if aqi_in_url:
        try:
            res = requests.get(aqi_in_url, timeout=5)
            res.raise_for_status()
            parsed_aqi = _parse_aqi_in_value(res.text)
            if parsed_aqi is not None:
                if lat is not None and lon is not None:
                    _cache_set(_aqi_cache, _lat_lon_cache_key(lat, lon), parsed_aqi, _CACHE_TTL_AQI_SECONDS)
                return parsed_aqi
        except Exception:
            pass

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return 0.0

    if lat is None or lon is None:
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

    aqi_value = float(mapping.get(aqi_index, 0))
    _cache_set(_aqi_cache, _lat_lon_cache_key(lat, lon), aqi_value, _CACHE_TTL_AQI_SECONDS)
    return aqi_value


def check_trigger(rain: float, aqi: float) -> dict:
    """
    Evaluate rain and AQI against industry-standard parametric insurance thresholds.
    Returns tiered payout percentages based on severity.
    If multiple triggers fire, selects the one with highest payout percentage.
    
    Returns:
        {
            "triggered": bool,
            "trigger_type": "rain" | "aqi",
            "severity": "moderate" | "high" | "extreme",
            "payout_percentage": int (0, 30, 60, 100),
            "rain": float,
            "aqi": float
        }
    """
    rain_trigger = None
    rain_payout = 0
    
    # Rain thresholds (mm)
    if rain >= 150:
        rain_trigger = {"trigger_type": "rain", "severity": "extreme", "payout_percentage": 100}
        rain_payout = 100
    elif rain >= 100:
        rain_trigger = {"trigger_type": "rain", "severity": "high", "payout_percentage": 60}
        rain_payout = 60
    elif rain >= 50:
        rain_trigger = {"trigger_type": "rain", "severity": "moderate", "payout_percentage": 30}
        rain_payout = 30
    
    aqi_trigger = None
    aqi_payout = 0
    
    # AQI thresholds
    if aqi >= 500:
        aqi_trigger = {"trigger_type": "aqi", "severity": "extreme", "payout_percentage": 100}
        aqi_payout = 100
    elif aqi >= 400:
        aqi_trigger = {"trigger_type": "aqi", "severity": "high", "payout_percentage": 60}
        aqi_payout = 60
    elif aqi >= 300:
        aqi_trigger = {"trigger_type": "aqi", "severity": "moderate", "payout_percentage": 30}
        aqi_payout = 30
    
    # No trigger
    if not rain_trigger and not aqi_trigger:
        return {
            "triggered": False,
            "rain": rain,
            "aqi": aqi
        }
    
    # Multiple triggers: choose higher payout percentage
    if rain_trigger and aqi_trigger:
        if rain_payout >= aqi_payout:
            selected = rain_trigger
        else:
            selected = aqi_trigger
    elif rain_trigger:
        selected = rain_trigger
    else:
        selected = aqi_trigger
    
    return {
        "triggered": True,
        "trigger_type": selected["trigger_type"],
        "severity": selected["severity"],
        "payout_percentage": selected["payout_percentage"],
        "rain": rain,
        "aqi": aqi
    }


async def fetch_rain_mm(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    timeout: float = 5.0,
) -> float:
    settings = get_settings()
    if settings.demo_mode:
        return 75.0

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
    settings = get_settings()
    if settings.demo_mode:
        return 320.0

    coordinates = resolve_coordinates(location=location, lat=lat, lon=lon, timeout=timeout)
    if coordinates is None:
        return 0.0

    return await asyncio.to_thread(get_aqi, location, coordinates[0], coordinates[1])


async def fetch_trigger_snapshot(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    timeout: float = 5.0,
) -> tuple[float, float]:
    rain, aqi = await asyncio.gather(
        fetch_rain_mm(location=location, lat=lat, lon=lon, timeout=timeout),
        fetch_aqi(location=location, lat=lat, lon=lon, timeout=timeout),
    )
    return rain, aqi


def evaluate_rain_trigger(rain_mm: float) -> Literal["none", "partial", "full"]:
    if rain_mm >= 100:
        return "full"
    if rain_mm >= 60:
        return "partial"
    return "none"
