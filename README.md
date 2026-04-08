# Real-Time Product Recommendation System

This project imports purchase data from the public BigQuery dataset `bigquery-public-data.thelook_ecommerce`, stores it in Neo4j, and generates product recommendations with Cypher.

## Main Flow
- Source data: BigQuery `thelook_ecommerce`
- Graph storage: Neo4j
- Recommendation types: user-based and category-based

## Required Environment Variables
Put these in `.env`:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
GOOGLE_CLOUD_PROJECT=recommendation-system-418420
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
```

If your machine is already authenticated with Google Cloud, `GOOGLE_APPLICATION_CREDENTIALS` may not be needed.

## One Environment Only
Use only `.venv` for this project.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In your IDE, select `.venv\Scripts\python.exe`.

## Import Data From BigQuery
```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --bootstrap-bigquery --project-id neo4j-bigquery-demo --user-id 1
```

Useful flags:
- `--limit 500`
- `--keep-existing-data`

Recommended demo run:
```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --bootstrap-bigquery --project-id neo4j-bigquery-demo --limit 2000 --user-id 1
```

## Recommendation Strategy
- `user-based`: uses shared purchases as the main similarity signal, boosts candidates from categories the user already likes, and fills any missing slots with strong category/popularity fallback picks so sparse samples do not return empty results too often.
- `category-based`: recommends unseen products from the user's strongest category.

## Files Used By The Main Flow
- `src/bigquery_data/fetch_from_bigquery.py`
- `src/bigquery_data/set_up_database_using_bigquery.py`
- `src/database/database_setup.py`
- `src/recommendations/collaborative_filtering.py`
- `src/main.py`

## Notes
- Legacy Fake Store and duplicate BigQuery files were removed from the main flow.
- Dependencies are reduced to the packages needed for BigQuery and Neo4j.
- If Windows feels slow, keep the repo outside OneDrive.

## License
This project is licensed under the [MIT License](src/docs/LICENSE).
