import streamlit as st
import os, sys
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)
from src.data_loader import load_all
from src.retrieval import route_and_search
from src.weather import get_weather_recommendation
from src.i18n import detect_language, to_english, from_english

st.set_page_config(page_title="Agri Assistant (Prototype)", page_icon="🌾", layout="wide")

@st.cache_data(show_spinner=False)
def load_data():
	return load_all()

st.title("🌾 Agri Assistant - Farmer Chatbot (Prototype)")
st.caption("Ask about pests, schemes/subsidies, weather tips, and general agri queries.")

with st.sidebar:
	st.header("About")
	st.write("This is a retrieval-based prototype using three CSV knowledge bases.")
	st.write("Data: `schemes.csv`, `crop_pest_solution.csv`, `farmer queries with answers.csv`")
	st.divider()
	st.subheader("Weather-aware advice")
	st.write("Type a location below to get 7-day weather summary and crop suggestions.")
	location_input = st.text_input("Location (city/village, district, state)", key="weather_location")
	if st.button("Get weather advice", use_container_width=True):
		if location_input:
			try:
				rec = get_weather_recommendation(location_input)
				st.session_state.history.append({"role": "user", "content": f"weather: {location_input}"})
				st.session_state.history.append({"role": "assistant", "content": rec.get("message", "Could not build advice.")})
				st.success("Weather advice added to chat.")
			except Exception as e:
				st.error(f"Failed to fetch weather: {e}")
		else:
			st.warning("Please enter a location.")

# Load data
try:
	df_schemes, df_pests, df_qa = load_data()
except Exception as e:
	st.error(f"Failed to load data: {e}")
	raise

if "history" not in st.session_state:
	st.session_state.history = []

user_query = st.chat_input("Type your question... e.g., Brown planthopper in paddy / मौसम कैसा रहेगा")

chat = st.container()
with chat:
	for turn in st.session_state.history:
		with st.chat_message(turn["role"]):
			st.markdown(turn["content"])

if user_query:
	# Detect input language and translate to English for retrieval
	user_lang = detect_language(user_query)
	query_en = to_english(user_query)
	st.session_state.history.append({"role": "user", "content": user_query})
	with st.spinner("Searching knowledge base..."):
		result = route_and_search(df_schemes, df_pests, df_qa, query_en)

	answer_lines = []
	if result["results"]:
		best = result["results"][0]
		if best["type"] == "pest":
			answer_lines.append(f"**Crop:** {best.get('crop','')}")
			answer_lines.append(f"**Issue:** {best.get('name','')}")
			answer_lines.append(f"**Symptoms:** {best.get('symptoms','')}")
			answer_lines.append(f"**Recommended Solution:** {best.get('solution','')}")
			if best.get("source"):
				answer_lines.append(f"**Source:** {best.get('source')}")
		elif best["type"] == "scheme":
			answer_lines.append(f"**Scheme:** {best.get('scheme','')} ({best.get('acronym','')})")
			answer_lines.append(f"**Objective:** {best.get('objective','')}")
			answer_lines.append(f"**Benefits:** {best.get('benefits','')}")
			answer_lines.append(f"**Beneficiaries:** {best.get('beneficiaries','')}")
			answer_lines.append(f"**Funding:** {best.get('funding','')}")
			if best.get("link"):
				answer_lines.append(f"**Official Link:** {best.get('link')}")
		elif best["type"] == "weather":
			assistant_msg = result["results"][0].get("message", "Couldn't retrieve weather.")
			st.session_state.history.append({"role": "assistant", "content": assistant_msg})
			with st.chat_message("assistant"):
				st.markdown(assistant_msg)
				refs = []
				st.stop()
		else:
			answer_lines.append(best.get("answer", "I couldn't find an exact match, but here are some tips."))
			if best.get("source"):
				answer_lines.append(f"**Source:** {best.get('source')}")

		# Show top-3 as references
		refs = []
		for item in result["results"]:
			label = item.get("type")
			score = int(item.get("score", 0))
			if label == "pest":
				refs.append(f"Pest: {item.get('crop','')} - {item.get('name','')} (score {score})")
			elif label == "scheme":
				refs.append(f"Scheme: {item.get('scheme','')} ({item.get('acronym','')}) (score {score})")
			else:
				refs.append(f"Q&A: {item.get('query','')[:60]} (score {score})")

		# Compose assistant message text in English
		assistant_msg_en = "\n\n".join(answer_lines) if answer_lines else "I couldn't find a good match. Please try rephrasing your question."

		# Translate to user's language if it is not English
		assistant_msg = from_english(assistant_msg_en, user_lang)
		st.session_state.history.append({"role": "assistant", "content": assistant_msg})

		with st.chat_message("assistant"):
			st.markdown(assistant_msg)
			with st.expander("References (top matches)"):
				st.write("\n".join(refs))
