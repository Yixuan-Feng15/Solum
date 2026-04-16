from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from data_loader import load_dataset


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
DATASET = load_dataset()


def dataset_metadata(df):
    years = sorted(df["year"].dropna().astype(int).unique().tolist())
    months = sorted(df["month"].dropna().astype(int).unique().tolist())
    is_single_period = len(df[["year", "month"]].drop_duplicates()) == 1
    latest_year = years[-1] if years else None
    latest_month = months[-1] if months else None
    return {
        "sourceFile": "data/DFC_FACILITY.csv",
        "recordCount": int(len(df)),
        "years": years,
        "months": months,
        "singlePeriod": is_single_period,
        "derivedDateField": "SMR Date",
        "dateRule": "Use the end date of the CMS SMR Date range as year/month for filtering.",
        "latestPeriod": f"{latest_year}-{latest_month:02d}" if latest_year and latest_month else None,
    }


DATASET_META = dataset_metadata(DATASET)


def apply_filters(df, args):
    filtered = df.copy()

    year = args.get("year")
    month = args.get("month")
    state = args.get("state")
    zip_code = args.get("zip")
    facility = args.get("facility")

    if year:
        filtered = filtered[filtered["year"] == int(year)]
    if month:
        filtered = filtered[filtered["month"] == int(month)]
    if state:
        filtered = filtered[filtered["state"].str.upper() == state.upper()]
    if zip_code:
        filtered = filtered[filtered["zip"].astype(str).str.startswith(str(zip_code))]
    if facility:
        filtered = filtered[filtered["facility_name"].str.contains(facility, case=False, na=False)]

    return filtered


def serialize_rows(df):
    records = df.copy()
    records["mortality_rate"] = records["mortality_rate"].round(4)
    return records.to_dict(orient="records")


def csv_filename(args) -> str:
    parts = ["mortality_export"]
    for key in ["year", "month", "state", "zip"]:
        value = args.get(key)
        if value:
            parts.append(f"{key}-{value}")
    return "_".join(parts) + ".csv"


@app.get("/api/filters")
def filters():
    return jsonify(
        {
            "years": DATASET_META["years"],
            "months": DATASET_META["months"],
            "states": sorted(DATASET["state"].dropna().astype(str).unique().tolist()),
            "dataset": DATASET_META,
        }
    )


@app.get("/api/summary")
def summary():
    filtered = apply_filters(DATASET, request.args)
    ranked = filtered.sort_values("mortality_rate")
    payload = {
        "total": int(len(filtered)),
        "avgMortality": round(float(filtered["mortality_rate"].mean()), 4) if len(filtered) else None,
        "minMortality": round(float(filtered["mortality_rate"].min()), 4) if len(filtered) else None,
        "maxMortality": round(float(filtered["mortality_rate"].max()), 4) if len(filtered) else None,
        "top10Highest": serialize_rows(ranked.tail(10).sort_values("mortality_rate", ascending=False)),
        "top10Lowest": serialize_rows(ranked.head(10)),
    }
    return jsonify(payload)


@app.get("/api/table")
def table():
    filtered = apply_filters(DATASET, request.args).sort_values(
        ["mortality_rate", "facility_name"], ascending=[False, True]
    )
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("pageSize", 10)), 1), 100)
    start = (page - 1) * page_size
    end = start + page_size

    return jsonify(
        {
            "data": serialize_rows(filtered.iloc[start:end]),
            "page": page,
            "pageSize": page_size,
            "total": int(len(filtered)),
        }
    )


@app.get("/api/analysis")
def analysis():
    filtered = apply_filters(DATASET, request.args)

    monthly_trend = (
        filtered.groupby(["year", "month"], as_index=False)["mortality_rate"]
        .mean()
        .sort_values(["year", "month"])
    )
    by_state = (
        filtered.groupby("state")["mortality_rate"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avgMortality", "count": "count"})
        .sort_values("avgMortality", ascending=False)
    )
    by_zip = (
        filtered.groupby("zip")["mortality_rate"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avgMortality", "count": "count"})
        .sort_values("avgMortality", ascending=False)
        .head(20)
    )
    distribution = (
        filtered.assign(bucket=filtered["mortality_rate"].round(1))
        .groupby("bucket", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("bucket")
    )
    ranking = filtered.sort_values("mortality_rate", ascending=False).head(25)

    return jsonify(
        {
            "monthlyTrend": monthly_trend.to_dict(orient="records"),
            "byState": by_state.to_dict(orient="records"),
            "byZip": by_zip.to_dict(orient="records"),
            "distribution": distribution.to_dict(orient="records"),
            "ranking": serialize_rows(ranking),
        }
    )


@app.get("/api/export")
def export_csv():
    filtered = apply_filters(DATASET, request.args).sort_values(
        ["year", "month", "state", "facility_name"]
    )
    csv_data = filtered.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{csv_filename(request.args)}"'},
    )


@app.get("/")
def root():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/analysis")
def analysis_page():
    return send_from_directory(STATIC_DIR, "analysis.html")


if __name__ == "__main__":
    app.run(debug=True)
