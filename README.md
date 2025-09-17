# Agri Assistant - Farmer Chatbot (Prototype)

A simple retrieval-based chatbot over three CSV datasets:
- `data/raw/schemes.csv`
- `data/raw/crop_pest_solution.csv`
- `data/raw/farmer queries with answers.csv`

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

From the project root:
```bash
streamlit run app.py
```
## Deploy on Streamlit Community Cloud

1. Push this repo (with `app.py`, `requirements.txt`, `src/`, and `data/raw/` CSVs) to GitHub.
2. The repo includes `runtime.txt` (Python 3.12) and `.streamlit/config.toml` for cloud defaults.
3. On streamlit.io → "Deploy an app" → pick your repo/branch → `app.py` → Deploy.
4. Optional secrets (if you use the farmer AI): add `OPENAI_API_KEY` in Manage app → Secrets.


Then open the local URL shown in the console.

## How it works
- Loads the three CSVs with `src/data_loader.py`.
- Classifies intent (pest, scheme, weather, general) and does fuzzy retrieval with `src/retrieval.py`.
- Displays a chat UI via Streamlit in `app.py`.

## Notes
- This is a prototype using simple fuzzy matching (no embeddings).
- Ensure CSV headers match exactly those provided in the repo.
