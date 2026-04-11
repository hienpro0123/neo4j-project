# Neo4j + BigQuery Recommendation Project

## Setup

### 1. Clone the project
```powershell
git clone <your-repo-url>
cd neo4j-prj
```

### 2. Create a virtual environment
```powershell
py -3 -m venv .venv
```

### 3. Activate the virtual environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure `.env`

Create a `.env` file in the project root:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=credentials/key.json
```

Notes:
- `NEO4J_URI` can also be your Neo4j Aura connection string.
- `GOOGLE_APPLICATION_CREDENTIALS` should point to your BigQuery service account JSON file.

## Run the project

### Option 1. Import data from BigQuery and run recommendations
```powershell
$env:PYTHONPATH="."
python -m src.main --bootstrap-bigquery --project-id your-gcp-project-id --limit 2000 --user-id 1
```

### Option 2. Run recommendations only
```powershell
$env:PYTHONPATH="."
python -m src.main --user-id 1
```

### Option 3. Run the Streamlit app
```powershell
streamlit run app.py
```

## Quick start

```powershell
git clone <your-repo-url>
cd neo4j-prj
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env`, then run:

```powershell
$env:PYTHONPATH="."
python -m src.main --bootstrap-bigquery --project-id your-gcp-project-id --limit 2000 --user-id 1
```

## Google Cloud Setup (BigQuery)

### 1. Enable BigQuery API
- Open Google Cloud Console
- Select your project
- Enable `BigQuery API`

### 2. Create Service Account
- Go to `IAM & Admin` -> `Service Accounts`
- Click `Create Service Account`

### 3. Assign Role
- Grant this role:
  - `BigQuery Admin`

### 4. Create JSON Key
- Open the service account
- Go to `Keys`
- Click `Add Key` -> `Create new key` -> `JSON`

### 5. Place the key file
- Save the downloaded file as:

```powershell
credentials\key.json
```

### 6. Update `.env`
```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=credentials/key.json
```
