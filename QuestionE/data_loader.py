from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_PATH = DATA_DIR / "DFC_FACILITY.csv"


DATE_CANDIDATES = [
    "SMR Date",
    "report_date",
    "REPORT_DATE",
    "Date",
    "date",
    "MEASURE_DATE",
]

FACILITY_CANDIDATES = ["facility_name", "PROVNAME", "Facility Name"]
STATE_CANDIDATES = ["state", "STATE", "State"]
ZIP_CANDIDATES = ["zip", "ZIP", "ZIP Code", "ZIP_CD"]
MORTALITY_CANDIDATES = ["mortality_rate", "SMR_RATE_F_MED", "Mortality Rate (Facility)"]


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def parse_date_column(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()

    # CMS date fields such as "01Jan2021-31Dec2024" are date ranges.
    # Use the end date so Year/Month reflect the latest period in the metric.
    end_dates = text.where(~text.str.contains("-", na=False), text.str.split("-").str[-1])
    parsed = pd.to_datetime(end_dates, format="%d%b%Y", errors="coerce")

    if parsed.notna().any():
        return parsed

    return pd.to_datetime(series, errors="coerce")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    facility_col = pick_column(df, FACILITY_CANDIDATES)
    state_col = pick_column(df, STATE_CANDIDATES)
    zip_col = pick_column(df, ZIP_CANDIDATES)
    mortality_col = pick_column(df, MORTALITY_CANDIDATES)
    date_col = pick_column(df, DATE_CANDIDATES)

    if not all([facility_col, state_col, zip_col, mortality_col]):
        raise ValueError(
            "Dataset is missing one of the required columns for facility, state, zip, or mortality."
        )

    normalized = pd.DataFrame(
        {
            "facility_name": df[facility_col].astype(str).fillna(""),
            "state": df[state_col].astype(str).fillna(""),
            "zip": df[zip_col].astype(str).str.extract(r"(\d{5})", expand=False).fillna(""),
            "mortality_rate": pd.to_numeric(df[mortality_col], errors="coerce"),
        }
    )

    if date_col:
        dates = parse_date_column(df[date_col])
        normalized["year"] = dates.dt.year
        normalized["month"] = dates.dt.month
        normalized["report_date"] = dates.dt.strftime("%Y-%m-%d")
    else:
        normalized["year"] = pd.to_numeric(df.get("year"), errors="coerce")
        normalized["month"] = pd.to_numeric(df.get("month"), errors="coerce")
        normalized["report_date"] = None

    normalized = normalized.dropna(subset=["mortality_rate", "year", "month"]).copy()
    normalized["year"] = normalized["year"].astype(int)
    normalized["month"] = normalized["month"].astype(int)
    normalized["mortality_rate"] = normalized["mortality_rate"].astype(float)
    return normalized.sort_values(["year", "month", "state", "facility_name"]).reset_index(drop=True)


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    csv_path = path or DEFAULT_PATH
    df = pd.read_csv(csv_path)
    return normalize_columns(df)
