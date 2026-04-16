##  Overview

The system allows users to:
- Filter data by time and location
- View summary statistics
- Explore paginated tables
- Analyze trends and distributions

##  Design Decisions

- **Backend**: Flask (lightweight, easy to run)
- **Frontend**: Vanilla HTML, CSS, JavaScript
- **REASON**: No need for frontend build tools or Node.js

---

##  Project Structure

1. app.py # Flask backend (API + routes)
2. data_loader.py # Data loading & cleaning logic

3. data/sample_dialysis_facility_data.csv # Sample dataset
4. static/
    index.html # Summary page
    analysis.html # Analysis page
    app.js # Frontend logic
    styles.css # Styling

---

##  Backend APIs

### 1. /api/filters
Returns available filter options:
- Year
- Month
- State

### 2. /api/summary
Returns key metrics:

- "total"
- "avgMortality"
- "minMortality"
- "maxMortality"
- "top10Highest"
- "top10Lowest"

### 3. /api/table

Paginated table data:

-  "data"
-  "page"
-  "pageSize"
-  "total"

### 4. /api/analysis

Aggregated analysis results:
-  monthlyTrend
-  byState
-  byZip
-  distribution
-  ranking

### 5. /api/export

Exports filtered data as CSV.

## Filtering Features

Supported filters:
- year
- month
- state
- zip (prefix match)
- facility (fuzzy search)

## Data Processing

Field Detection
1. Automatically detects CMS-style field names:
Facility name
State
ZIP
Mortality rate
Date
Date Parsing
Converts to standard format
2. Extracts:
Year
Month
3. Data Cleaning:
Invalid values → converted using to_numeric(..., errors="coerce")
Missing values removed
4. ZIP Standardization
Extracts first 5 digits

## Frontend
- `Page 1`: Summary
Filters
Key metrics
Top 10 highest/lowest mortality facilities
Paginated table
- `Page 2`: Analysis
Monthly trend
State comparison
ZIP comparison
Distribution
Ranking table

## Dataset

The dataset is based on CMS Dialysis Facility data.
Note:
Due to API access limitations (HTTP 410 errors), the dataset was downloaded as CSV and included as a sample file.



## In the QuestionE directory:

python app.py

Then open:

Summary: http://127.0.0.1:5000/
Analysis: http://127.0.0.1:5000/analysis
Features Implemented:
- Filtering by multiple conditions
- Summary statistics
- Ranking (Top 10)
- Pagination
- Data aggregation
- Analysis endpoints
- Two frontend pages
- Missing/invalid data handling
- Consistent API response format


