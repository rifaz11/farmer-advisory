import datetime
from typing import Dict, List, Optional, Tuple

import requests


GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_location(location_query: str) -> Optional[Dict]:
	"""Resolve a location name to coordinates using Open-Meteo geocoding API.

	Returns a dict with latitude, longitude, name, admin1, country or None if not found.
	"""
	if not location_query:
		return None
	params = {
		"name": location_query,
		"count": 1,
		"language": "en",
		"format": "json",
	}
	resp = requests.get(GEOCODE_URL, params=params, timeout=10)
	resp.raise_for_status()
	data = resp.json() or {}
	results = data.get("results") or []
	if not results:
		return None
	place = results[0]
	return {
		"latitude": place.get("latitude"),
		"longitude": place.get("longitude"),
		"name": place.get("name"),
		"admin1": place.get("admin1"),
		"country": place.get("country"),
	}


def fetch_forecast(latitude: float, longitude: float) -> Dict:
	"""Fetch 7-day daily forecast for temperature and precipitation."""
	params = {
		"latitude": latitude,
		"longitude": longitude,
		"daily": [
			"temperature_2m_max",
			"temperature_2m_min",
			"precipitation_sum",
			"windspeed_10m_max",
		],
		"timezone": "auto",
		"forecast_days": 7,
	}
	resp = requests.get(FORECAST_URL, params=params, timeout=10)
	resp.raise_for_status()
	return resp.json() or {}


def summarize_forecast(forecast: Dict) -> Dict:
	"""Compute simple aggregates from the daily forecast."""
	daily = (forecast or {}).get("daily") or {}
	def avg(values: List[float]) -> Optional[float]:
		vals = [v for v in (values or []) if isinstance(v, (int, float))]
		return round(sum(vals) / len(vals), 1) if vals else None

	avg_tmax = avg(daily.get("temperature_2m_max"))
	avg_tmin = avg(daily.get("temperature_2m_min"))
	rain_total = round(sum(daily.get("precipitation_sum") or []), 1) if daily.get("precipitation_sum") else None
	wind_max_avg = avg(daily.get("windspeed_10m_max"))

	return {
		"avg_temp_max_c": avg_tmax,
		"avg_temp_min_c": avg_tmin,
		"total_rain_mm": rain_total,
		"avg_wind_max_kmh": wind_max_avg,
	}


def recommend_crops(summary: Dict, month: Optional[int] = None) -> List[Dict]:
	"""Very simple heuristic crop recommendations by Indian season and weather.

	- Kharif (Jun-Oct): rain-fed crops; high rain favors rice, moderate favors maize/soybean/groundnut
	- Rabi (Nov-Mar): wheat, mustard, chickpea prefer cool temps and low rain
	- Zaid (Apr-May): short-duration vegetables and melons in warm temps
	"""
	if month is None:
		month = datetime.date.today().month

	season = "kharif" if month in [6, 7, 8, 9, 10] else ("rabi" if month in [11, 12, 1, 2, 3] else "zaid")
	avg_tmax = summary.get("avg_temp_max_c") or 0
	avg_tmin = summary.get("avg_temp_min_c") or 0
	rain_total = summary.get("total_rain_mm") or 0

	recs: List[Dict] = []
	if season == "kharif":
		if rain_total >= 150:
			recs.append({"crop": "Rice (Paddy)", "why": "High expected rainfall suits transplanted paddy"})
		if 80 <= rain_total <= 180:
			recs.append({"crop": "Maize", "why": "Moderate rain with warm temps suits maize"})
			recs.append({"crop": "Soybean", "why": "Warm and moderately wet conditions"})
			recs.append({"crop": "Groundnut", "why": "Requires warm climate and moderate rainfall"})
		if rain_total < 80:
			recs.append({"crop": "Millets (Pearl/foxtail)", "why": "Drought-tolerant for low rainfall"})
	elif season == "rabi":
		# Cool season crops favor lower max temps and cool nights with low rainfall
		if avg_tmax <= 30 and 5 <= avg_tmin <= 15 and rain_total < 50:
			recs.append({"crop": "Wheat", "why": "Cool season with low rainfall suits wheat"})
		if 15 <= avg_tmin <= 20 and rain_total < 60:
			recs.append({"crop": "Mustard", "why": "Cool-dry conditions favorable"})
		if 10 <= avg_tmin <= 20 and rain_total < 60:
			recs.append({"crop": "Chickpea (Gram)", "why": "Thrives in cool, relatively dry weather"})
	else:  # zaid
		if avg_tmax >= 30 and rain_total < 80:
			recs.append({"crop": "Watermelon/Muskmelon", "why": "Warm short-season fruits fit zaid"})
			recs.append({"crop": "Cucumber & Gourds", "why": "Short duration, warm season"})
		if rain_total >= 60:
			recs.append({"crop": "Vegetables (Okra, chilli)", "why": "Warm temps with some rain"})

	# Deduplicate by crop keeping first rationale
	seen = set()
	unique_recs: List[Dict] = []
	for r in recs:
		c = r.get("crop")
		if c and c not in seen:
			seen.add(c)
			unique_recs.append(r)
	return unique_recs[:6]


def build_advice_message(place: Dict, summary: Dict, recs: List[Dict]) -> str:
	parts: List[str] = []
	loc_label = ", ".join([p for p in [place.get("name"), place.get("admin1"), place.get("country")] if p]) if place else "your area"
	parts.append(f"**Location:** {loc_label}")
	if summary.get("avg_temp_max_c") is not None and summary.get("avg_temp_min_c") is not None:
		parts.append(f"**Next 7 days temp (avg max/min):** {summary['avg_temp_max_c']}°C / {summary['avg_temp_min_c']}°C")
	if summary.get("total_rain_mm") is not None:
		parts.append(f"**Expected total rainfall (7d):** {summary['total_rain_mm']} mm")
	if summary.get("avg_wind_max_kmh") is not None:
		parts.append(f"**Avg daily max wind:** {summary['avg_wind_max_kmh']} km/h")
	if recs:
		parts.append("\n**Suggested crops (heuristic):**")
		for r in recs:
			parts.append(f"- {r['crop']}: {r['why']}")
	return "\n".join(parts)


def get_weather_recommendation(location_query: str) -> Dict:
	"""High-level: geocode, fetch forecast, summarize, recommend, and return a structured result."""
	place = geocode_location(location_query)
	if not place:
		return {
			"type": "weather",
			"score": 100.0,
			"error": f"Could not find location: {location_query}",
		}
	forecast = fetch_forecast(place["latitude"], place["longitude"])
	summary = summarize_forecast(forecast)
	recs = recommend_crops(summary)
	message = build_advice_message(place, summary, recs)
	return {
		"type": "weather",
		"score": 100.0,
		"location": place,
		"summary": summary,
		"recommendations": recs,
		"message": message,
	}


