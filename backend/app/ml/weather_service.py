import requests
from typing import Optional

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP = {
    0: ("Clear Sky", "☀️", "Sunny and crisp. Perfect for standard layering."),
    1: ("Mainly Clear", "🌤️", "Bright with occasional soft clouds."),
    2: ("Partly Cloudy", "⛅", "Pleasant partly cloudy weather."),
    3: ("Overcast", "☁️", "Gloomy clouds. Consider an extra layer."),
    45: ("Foggy", "🌫️", "Misty and cool. Wear wind-resistant layers."),
    48: ("Depositing Rime Fog", "🌫️", "Chilly and damp."),
    51: ("Light Drizzle", "🌦️", "Light drizzle. Keep a light waterproof jacket."),
    53: ("Moderate Drizzle", "🌦️", "Continuous damp drizzle. Water-resistant outerwear recommended."),
    55: ("Dense Drizzle", "🌧️", "Wet drizzle. Wear sturdy footwear."),
    61: ("Slight Rain", "🌧️", "Light rain shower. Pair with a jacket and closed shoes."),
    63: ("Moderate Rain", "🌧️", "Rainy day. Water-resistant jacket and leather shoes/boots advised."),
    65: ("Heavy Rain", "⛈️", "Heavy rainfall. Waterproof outerwear and boots recommended."),
    71: ("Slight Snow", "🌨️", "Light snowfall. Warm knitwear, coat, and boots essential."),
    73: ("Moderate Snow", "❄️", "Snowy conditions. Heavy winter coat and warm layers needed."),
    75: ("Heavy Snow", "❄️", "Freezing snowstorm. Maximum warmth items (Level 5)."),
    80: ("Slight Rain Showers", "🌦️", "Passing rain showers."),
    81: ("Moderate Rain Showers", "🌧️", "Sporadic rain showers."),
    82: ("Violent Rain Showers", "⛈️", "Heavy storms. Stay warm and dry."),
    95: ("Thunderstorm", "⚡", "Thunderstorms. Heavy protective layer and solid boots."),
}

def geocode_city(city_name: str) -> Optional[tuple[float, float, str]]:
    """Uses Open-Meteo free geocoding API to resolve city to lat/lon."""
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                lat = float(result["latitude"])
                lon = float(result["longitude"])
                resolved_name = f"{result.get('name')}, {result.get('country', '')}"
                return lat, lon, resolved_name
    except Exception as e:
        print(f"[WeatherService] Geocoding error for '{city_name}': {e}")
    return None

def fetch_weather(lat: float, lon: float, city_label: str = "Local Location") -> dict:
    """
    Fetches real-time weather from Open-Meteo API.
    Does not require any API keys.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
            "timezone": "auto"
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            temp = float(current.get("temperature_2m", 22.0))
            humidity = float(current.get("relative_humidity_2m", 50.0))
            precip = float(current.get("precipitation", 0.0))
            wmo_code = int(current.get("weather_code", 0))

            cond_name, icon, tip = WMO_CODE_MAP.get(wmo_code, ("Fair Weather", "🌤️", "Standard day attire."))

            if temp >= 28.0:
                warmth_rec = "Summer Heat: Wear breathable, lightweight items (Warmth 1-2)."
            elif temp >= 20.0:
                warmth_rec = "Pleasant & Warm: Optimal for casual tees, shirts, and jeans (Warmth 2-3)."
            elif temp >= 14.0:
                warmth_rec = "Mild / Breezy: Consider a light jacket or cardigan (Warmth 2-4)."
            elif temp >= 7.0:
                warmth_rec = "Chilly: Sweaters, warm pants, and sturdy footwear recommended (Warmth 3-5)."
            else:
                warmth_rec = "Cold Winter: Heavy overcoats, thermals, and boots recommended (Warmth 4-5)."

            return {
                "city": city_label,
                "temperature_c": round(temp, 1),
                "humidity_percent": round(humidity, 1),
                "precipitation_mm": round(precip, 1),
                "weather_condition": cond_name,
                "weather_icon": icon,
                "warmth_recommendation": warmth_rec
            }
    except Exception as e:
        print(f"[WeatherService] Weather fetch error: {e}")

    # Fallback default weather
    return {
        "city": city_label,
        "temperature_c": 22.0,
        "humidity_percent": 50.0,
        "precipitation_mm": 0.0,
        "weather_condition": "Pleasant / Sunny",
        "weather_icon": "☀️",
        "warmth_recommendation": "Mild conditions: standard tops and bottoms."
    }

def get_current_weather_context(
    city: Optional[str] = None, 
    lat: Optional[float] = None, 
    lon: Optional[float] = None,
    manual_temp: Optional[float] = None,
    manual_condition: Optional[str] = None
) -> dict:
    """Consolidates weather context from city name, GPS coords, or manual override."""
    if manual_temp is not None:
        cond = manual_condition or "Custom Temperature"
        return {
            "city": city or "Custom Location",
            "temperature_c": float(manual_temp),
            "humidity_percent": 45.0,
            "precipitation_mm": 0.0,
            "weather_condition": cond,
            "weather_icon": "🌡️",
            "warmth_recommendation": f"Manual temperature set to {manual_temp}°C."
        }

    if city:
        geo = geocode_city(city)
        if geo:
            resolved_lat, resolved_lon, resolved_name = geo
            return fetch_weather(resolved_lat, resolved_lon, resolved_name)

    if lat is not None and lon is not None:
        return fetch_weather(lat, lon, f"GPS ({round(lat, 2)}, {round(lon, 2)})")

    # Default location: London / New York fallback or standard 22°C
    return fetch_weather(51.5074, -0.1278, "London, United Kingdom")
