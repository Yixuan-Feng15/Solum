from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "bmw_global_sales_2018-2025.xlsx"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def elasticity_from_changes(group: pd.DataFrame) -> float:
    x = group["price_pct_change"]
    y = group["units_pct_change"]
    if len(group) < 8 or x.nunique() < 2:
        return np.nan
    return float(np.polyfit(x, y, 1)[0])


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["Year", "Month", "Region", "Model"], as_index=False)
        .agg(
            Units_Sold=("Units_Sold", "sum"),
            Avg_Price_EUR=("Avg_Price_EUR", "mean"),
            GDP_Growth=("GDP_Growth", "mean"),
        ).sort_values(["Model", "Region", "Year", "Month"]))

    monthly["price_pct_change"] = monthly.groupby(["Model", "Region"])["Avg_Price_EUR"].pct_change()
    monthly["units_pct_change"] = monthly.groupby(["Model", "Region"])["Units_Sold"].pct_change()
    monthly = monthly.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["price_pct_change", "units_pct_change"]
    )

    q1, q2 = monthly["GDP_Growth"].quantile([1 / 3, 2 / 3])
    monthly["GDP_Bucket"] = pd.cut(
        monthly["GDP_Growth"],
        bins=[-np.inf, q1, q2, np.inf],
        labels=["Low", "Medium", "High"],
        include_lowest=True,)
    return monthly


def save_plots(overall: pd.Series, by_bucket: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    overall.sort_values().plot(kind="bar", ax=ax, color="#2c7fb8")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Overall Price Elasticity by Model")
    ax.set_ylabel("Elasticity (slope of unit change vs price change)")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "overall_price_elasticity.png", dpi=200)
    plt.close(fig)

    pivoted = by_bucket.pivot(index="Model", columns="GDP_Bucket", values="elasticity")
    fig, ax = plt.subplots(figsize=(10, 5))
    pivoted.plot(kind="bar", ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Price Elasticity by GDP Bucket")
    ax.set_ylabel("Elasticity")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "elasticity_by_gdp_bucket.png", dpi=200)
    plt.close(fig)


def main() -> None:
    df = pd.read_excel(DATA_PATH)
    prepared = prepare_data(df)

    overall = (
        prepared.groupby("Model", group_keys=False)[["price_pct_change", "units_pct_change"]]
        .apply(elasticity_from_changes)
        .sort_values()
    )
    by_bucket = (
        prepared.groupby(["GDP_Bucket", "Model"], group_keys=False, observed=False)[
            ["price_pct_change", "units_pct_change"]
        ]
        .apply(elasticity_from_changes)
        .reset_index(name="elasticity")
    )

    save_plots(overall, by_bucket)
    overall.rename("elasticity").reset_index().to_csv(
        OUTPUT_DIR / "overall_elasticity.csv", index=False
    )
    by_bucket.to_csv(OUTPUT_DIR / "elasticity_by_gdp_bucket.csv", index=False)

    print("Overall elasticity")
    print(overall.to_string())
    print("\nBy GDP bucket")
    print(by_bucket.sort_values(["GDP_Bucket", "elasticity"]).to_string(index=False))


if __name__ == "__main__":
    main()
