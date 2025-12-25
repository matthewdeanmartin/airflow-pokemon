import pendulum
import pandas as pd
import sqlite3
import re
from typing import List, Dict, Any
from airflow.decorators import dag, task
from airflow.models.baseoperator import Chain
from pathlib import Path

# --- Configuration ---
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_films"
DB_PATH = "pokemon_movies.db"  # This will be created in your AIRFLOW_HOME or current dir


@dag(
    dag_id="pokemon_movie_loader",
    schedule="@daily",  # Check for new movies once a day
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["pokemon", "scraping"],
)
def pokemon_dag():
    @task()
    def scrape_wikipedia() -> List[Dict[str, Any]]:
        """
        Downloads the Pokemon movie table from Wikipedia and cleans it.
        """
        print(f"Scraping {WIKI_URL}...")

        # pandas read_html automatically finds tables.
        # The Pokemon movie table is usually the first or second 'wikitable' on the page.
        dfs = pd.read_html(WIKI_URL, match="Title")

        if not dfs:
            raise ValueError("Could not find a table with 'Title' in it.")

        # Select the first matching table
        df = dfs[0]

        # Simple cleaning: ensure we have columns like 'Title', 'Release date'
        # Wikipedia headers can be multi-level, let's flatten or pick key columns.
        # Note: The table structure changes, so we grab likely columns by checking content.

        # Let's standardize column names for our DB
        clean_movies = []

        for _, row in df.iterrows():
            # Depending on the table format, 'Title' might be the English title
            # We try to extract the English title and Year

            # Helper to safely get string
            def get_val(col_name):
                val = row.get(col_name, '')
                if pd.isna(val): return None
                return str(val).strip()

            # Wikipedia column names often have footnotes like "Title[a]"
            # We look for columns that contain "English title" or just "Title"
            title_col = next((c for c in df.columns if "English title" in str(c) or "Title" in str(c)), None)
            release_col = next((c for c in df.columns if "release" in str(c).lower()), None)

            if title_col and release_col:
                title = get_val(title_col)
                release_date = get_val(release_col)

                # Basic validation: ensure we have a title and it looks like a movie row
                if title and release_date:
                    clean_movies.append({
                        "title": title,
                        "release_date": release_date,
                        "source_url": WIKI_URL
                    })

        print(f"Found {len(clean_movies)} movies.")
        return clean_movies

    @task()
    def load_to_sqlite(movies: List[Dict[str, Any]]):
        """
        Upserts movie data into SQLite. Detects new movies via 'ON CONFLICT'.
        """
        if not movies:
            print("No movies to load.")
            return

        print(f"Connecting to database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Create Table if not exists
        # We enforce a UNIQUE constraint on 'title' to handle the 'detecting new movies' logic
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS pokemon_movies
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           title
                           TEXT
                           UNIQUE,
                           release_date
                           TEXT,
                           source_url
                           TEXT,
                           last_updated
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       """)

        # 2. Upsert Logic (ON CONFLICT)
        # If the movie Title exists, we update the release_date and last_updated.
        # If it doesn't, we insert it.
        upsert_sql = """
                     INSERT INTO pokemon_movies (title, release_date, source_url, last_updated)
                     VALUES (:title, :release_date, :source_url, CURRENT_TIMESTAMP) ON CONFLICT(title) DO \
                     UPDATE SET
                         release_date = excluded.release_date, \
                         last_updated = CURRENT_TIMESTAMP \
                     """

        cursor.executemany(upsert_sql, movies)
        conn.commit()

        print(f"Processed {len(movies)} records successfully.")
        conn.close()

    # Define the workflow
    movie_data = scrape_wikipedia()
    load_to_sqlite(movie_data)


# Instantiate the DAG
pokemon_dag()