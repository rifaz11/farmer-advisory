import pandas as pd
import os

# Define the absolute path to your project's root folder
# This makes the path reliable no matter where the script is run from.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw')

def load_all_data():
    """
    Loads all three datasets into separate Pandas DataFrames.
    """
    print("Loading datasets...")

    try:
        # Load the Pest and Disease Knowledge Base with the correct file name
        df_pests = pd.read_csv(os.path.join(RAW_DATA_PATH, 'crop_pest_solution.xls - crop_pest.csv'))

        # Load the General Q&A Knowledge Base with the correct file name
        df_queries = pd.read_csv(os.path.join(RAW_DATA_PATH, 'farmer queries with answers.xls - queries with answers.csv'))

        # Load the Schemes and Subsidies Knowledge Base with the correct file name
        df_schemes = pd.read_csv(os.path.join(RAW_DATA_PATH, 'schemes.xlsx - Sheet1.csv'))

        print("All datasets loaded successfully!")

        return df_pests, df_queries, df_schemes

    except FileNotFoundError as e:
        print(f"\nError: A file was not found. Please ensure all three CSV files are in the 'data/raw' folder and that their names are correct. Details: {e}")
        return None, None, None
    except pd.errors.ParserError as e:
        print(f"\nError: Could not parse a CSV file. Check for formatting issues. Details: {e}")
        return None, None, None

if __name__ == '__main__':
    df_pests, df_queries, df_schemes = load_all_data()

    if df_pests is not None:
        print("\n--- PEST DATA (df_pests) ---")
        df_pests.info()
        print("\nFirst 5 rows of df_pests:")
        print(df_pests.head().to_markdown(index=False, numalign="left", stralign="left"))

        print("\n--- GENERAL QUERIES DATA (df_queries) ---")
        df_queries.info()
        print("\nFirst 5 rows of df_queries:")
        print(df_queries.head().to_markdown(index=False, numalign="left", stralign="left"))

        print("\n--- SCHEMES DATA (df_schemes) ---")
        df_schemes.info()
        print("\nFirst 5 rows of df_schemes:")
        print(df_schemes.head().to_markdown(index=False, numalign="left", stralign="left"))