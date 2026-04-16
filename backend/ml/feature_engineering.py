from __future__ import annotations

from statistics import mean

from app.trigger_utils import compute_trigger_payouts


def _normalize_forecast_input(forecast_data):
    if isinstance(forecast_data, dict):
        return [forecast_data]
    return list(forecast_data or [])


def _compute_streak(trigger_flags: list[bool]) -> int:
    longest = 0
    current = 0

    for flag in trigger_flags:
        if flag:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def summarize_forecast(forecast_data) -> dict[str, float]:
    rows = _normalize_forecast_input(forecast_data)
    if not rows:
        return {
            "avg_temp": 0.0,
            "max_temp": 0.0,
            "total_rain": 0.0,
            "max_rain": 0.0,
            "trigger_days": 0.0,
            "avg_payout_pct": 0.0,
            "temp_variance": 0.0,
            "rain_variance": 0.0,
            "consecutive_trigger_days": 0.0,
        }

    temps: list[float] = []
    rains: list[float] = []
    trigger_percentages: list[int] = []
    trigger_flags: list[bool] = []

    for row in rows:
        rain = float(row.get("rain", row.get("rain_mm", 0.0)) or 0.0)
        temp = float(row.get("temperature", row.get("temp", 0.0)) or 0.0)
        aqi = float(row.get("aqi", 0.0) or 0.0)

        rain_pct, aqi_pct, heat_pct = compute_trigger_payouts(rain, aqi, temp)
        day_pct = max(rain_pct, aqi_pct, heat_pct)

        temps.append(temp)
        rains.append(rain)
        trigger_percentages.append(day_pct)
        trigger_flags.append(day_pct > 0)

    avg_temp = mean(temps)
    max_temp = max(temps)
    total_rain = sum(rains)
    max_rain = max(rains)
    trigger_days = sum(1 for pct in trigger_percentages if pct > 0)
    avg_payout_pct = mean(trigger_percentages)
    temp_variance = max_temp - min(temps)
    rain_variance = max_rain - min(rains)
    consecutive_trigger_days = _compute_streak(trigger_flags)

    return {
        "avg_temp": float(avg_temp),
        "max_temp": float(max_temp),
        "total_rain": float(total_rain),
        "max_rain": float(max_rain),
        "trigger_days": float(trigger_days),
        "avg_payout_pct": float(avg_payout_pct),
        "temp_variance": float(temp_variance),
        "rain_variance": float(rain_variance),
        "consecutive_trigger_days": float(consecutive_trigger_days),
    }


def build_features(forecast_data) -> list[float]:
    summary = summarize_forecast(forecast_data)
    return [
        summary["avg_temp"],
        summary["max_temp"],
        summary["total_rain"],
        summary["max_rain"],
        summary["trigger_days"],
        summary["avg_payout_pct"],
        summary["temp_variance"],
        summary["rain_variance"],
        summary["consecutive_trigger_days"],
    ]
