from typing import Optional

try:
	from deep_translator import GoogleTranslator  # type: ignore
	_HAS_TRANSLATOR = True
except Exception:
	GoogleTranslator = None  # type: ignore
	_HAS_TRANSLATOR = False


def detect_language(text: str) -> str:
	"""Return ISO code like 'hi' or 'en'. Defaults to 'en' on failure."""
	try:
		if not text:
			return "en"
		# Heuristic: GoogleTranslator has no detect; keep simple checks
		# If contains many Devanagari chars, assume Hindi
		devanagari = sum(1 for ch in text if '\u0900' <= ch <= '\u097F')
		return "hi" if devanagari >= max(3, len(text) // 10) else "en"
	except Exception:
		return "en"


def to_english(text: str) -> str:
	"""Translate input to English if not already English. Falls back to original on errors."""
	try:
		if not text:
			return text
		lang = detect_language(text)
		if lang.startswith("en"):
			return text
		if _HAS_TRANSLATOR:
			return GoogleTranslator(source="auto", target="en").translate(text) or text
		return text
	except Exception:
		return text


def from_english(text: str, target_lang: str) -> str:
	"""Translate English text to target_lang. If target is English or error, return original."""
	try:
		if not text:
			return text
		if not target_lang or target_lang.startswith("en"):
			return text
		if _HAS_TRANSLATOR:
			return GoogleTranslator(source="en", target=target_lang).translate(text) or text
		return text
	except Exception:
		return text


