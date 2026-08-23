from fastapi import APIRouter, Query
from typing import Optional
from app.ml.weather_service import get_current_weather_context, geocode_city

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/current")
def get_weather(
    city: Optional[str] = Query(None, description="City name (e.g., 'New York', 'Mumbai', 'London')"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude")
):
    """Fetches real-time weather conditions from Open-Meteo."""
    return get_current_weather_context(city=city, lat=lat, lon=lon)

@router.get("/search-city")
def search_city(query: str = Query(..., min_length=2)):
    """Geocoding search for city autocomplete."""
    geo = geocode_city(query)
    if geo:
        lat, lon, name = geo
        return {"found": True, "city": name, "latitude": lat, "longitude": lon}
    return {"found": False, "message": "City not found"}
