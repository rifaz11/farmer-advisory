import os
import pandas as pd
from typing import Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw')

SCHEMES_FILE = 'schemes.csv'
PEST_FILE = 'crop_pest_solution.csv'
QA_FILE = 'farmer queries with answers.csv'


def load_csv_safe(path: str) -> pd.DataFrame:
	return pd.read_csv(path)


def load_all() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""Load schemes, pests, and Q&A CSVs from data/raw.

	Returns a tuple: (df_schemes, df_pests, df_qa)
	"""
	schemes_path = os.path.join(RAW_DATA_PATH, SCHEMES_FILE)
	pests_path = os.path.join(RAW_DATA_PATH, PEST_FILE)
	qa_path = os.path.join(RAW_DATA_PATH, QA_FILE)

	df_schemes = load_csv_safe(schemes_path)
	df_pests = load_csv_safe(pests_path)
	df_qa = load_csv_safe(qa_path)

	# Normalize column names (strip)
	def normalize(df: pd.DataFrame) -> pd.DataFrame:
		df = df.copy()
		df.columns = [c.strip() for c in df.columns]
		return df

	df_schemes = normalize(df_schemes)
	df_pests = normalize(df_pests)
	df_qa = normalize(df_qa)

	return df_schemes, df_pests, df_qa
