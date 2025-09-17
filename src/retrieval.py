import re
from typing import Dict, List, Tuple
import pandas as pd
try:
	from rapidfuzz import fuzz as _rf_fuzz
	def _similarity(a: str, b: str) -> int:
		return int(_rf_fuzz.token_set_ratio(a, b))
except Exception:
	from difflib import SequenceMatcher
	def _similarity(a: str, b: str) -> int:
		return int(SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio() * 100)
from .weather import get_weather_recommendation

Intent = str

INTENT_PATTERNS: List[Tuple[Intent, re.Pattern]] = [
	("pest", re.compile(r"\b(pest|disease|insect|mite|borer|blight|rot|weevil|aphid|thrips|wilt|virus|fungus|fungal|bacteria|bacterial)\b", re.I)),
	("scheme", re.compile(r"\b(scheme|subsidy|pm[- ]?kisan|pm[- ]?kusum|kcc|loan|support|grant|policy|benefit)\b", re.I)),
	("weather", re.compile(r"\b(weather|rain|monsoon|flood|drought|hail|storm|wind|heat|temperature|forecast)\b", re.I)),
]


def detect_intent(query: str) -> Intent:
	for intent, pattern in INTENT_PATTERNS:
		if pattern.search(query or ""):
			return intent
	return "general"


def search_pests(df_pests: pd.DataFrame, query: str, top_k: int = 3) -> List[Dict]:
	candidates = []
	for _, row in df_pests.iterrows():
		text = " ".join([str(row.get(col, "")) for col in ["Crop", "Pest/Disease", "Symptoms", "Recommended Solution", "Source", "Language Hint"]])
		score = _similarity(query, text)
		candidates.append((score, row))
	candidates.sort(key=lambda x: x[0], reverse=True)
	results: List[Dict] = []
	for score, row in candidates[:top_k]:
		results.append({
			"type": "pest",
			"score": float(score),
			"crop": row.get("Crop", ""),
			"name": row.get("Pest/Disease", ""),
			"symptoms": row.get("Symptoms", ""),
			"solution": row.get("Recommended Solution", ""),
			"source": row.get("Source", ""),
		})
	return results


def search_schemes(df_schemes: pd.DataFrame, query: str, top_k: int = 3) -> List[Dict]:
	candidates = []
	for _, row in df_schemes.iterrows():
		text = " ".join([str(row.get(col, "")) for col in ["Scheme Name", "Acronym", "Nodal Ministry/Department", "Primary Objective", "Key Features & Benefits", "Target Beneficiaries", "Funding Structure", "Official Link"]])
		score = _similarity(query, text)
		candidates.append((score, row))
	candidates.sort(key=lambda x: x[0], reverse=True)
	results: List[Dict] = []
	for score, row in candidates[:top_k]:
		results.append({
			"type": "scheme",
			"score": float(score),
			"scheme": row.get("Scheme Name", ""),
			"acronym": row.get("Acronym", ""),
			"objective": row.get("Primary Objective", ""),
			"benefits": row.get("Key Features & Benefits", ""),
			"beneficiaries": row.get("Target Beneficiaries", ""),
			"funding": row.get("Funding Structure", ""),
			"link": row.get("Official Link", ""),
		})
	return results


def search_qa(df_qa: pd.DataFrame, query: str, top_k: int = 3) -> List[Dict]:
	candidates = []
	for _, row in df_qa.iterrows():
		text = " ".join([str(row.get(col, "")) for col in ["Query", "Category", "Answer", "Source"]])
		score = _similarity(query, text)
		candidates.append((score, row))
	candidates.sort(key=lambda x: x[0], reverse=True)
	results: List[Dict] = []
	for score, row in candidates[:top_k]:
		results.append({
			"type": "qa",
			"score": float(score),
			"query": row.get("Query", ""),
			"category": row.get("Category", ""),
			"answer": row.get("Answer", ""),
			"source": row.get("Source", ""),
		})
	return results


def route_and_search(df_schemes: pd.DataFrame, df_pests: pd.DataFrame, df_qa: pd.DataFrame, query: str) -> Dict:
	intent = detect_intent(query)
	if intent == "pest":
		results = search_pests(df_pests, query)
	elif intent == "scheme":
		results = search_schemes(df_schemes, query)
	elif intent == "weather":
		# For weather-related queries, let the UI pass a location using a simple marker syntax like
		# "weather: <location>" e.g., "weather: Pune". If not provided, just return generic weather Q&A results.
		location = None
		if ":" in (query or ""):
			parts = query.split(":", 1)
			if parts and len(parts) == 2:
				location = parts[1].strip()
		if location:
			try:
				rec = get_weather_recommendation(location)
				results = [rec]
			except Exception:
				results = search_qa(df_qa, query)
		else:
			results = search_qa(df_qa, query)
	else:
		qa = search_qa(df_qa, query)
		schemes = search_schemes(df_schemes, query)
		pests = search_pests(df_pests, query)
		results = sorted(qa + schemes + pests, key=lambda x: x["score"], reverse=True)[:3]
	return {"intent": intent, "results": results}
