from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "bmw_global_sales_2018-2025.xlsx"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def build_views(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly_region = (
        df.groupby(["Region", "Month"], as_index=False)
        .agg(
            Units_Sold=("Units_Sold", "sum"),
            Revenue_EUR=("Revenue_EUR", "sum"),
            GDP_Growth=("GDP_Growth", "mean"),
            Fuel_Price_Index=("Fuel_Price_Index", "mean"),
        )
        .sort_values(["Region", "Month"])
    )

    year_month_region = (
        df.groupby(["Year", "Month", "Region"], as_index=False)
        .agg(
            Units_Sold=("Units_Sold", "sum"),
            Revenue_EUR=("Revenue_EUR", "sum"),
            GDP_Growth=("GDP_Growth", "mean"),
            Fuel_Price_Index=("Fuel_Price_Index", "mean"),
        )
        .sort_values(["Region", "Year", "Month"])
    )

    return monthly_region, year_month_region


def region_summary(monthly_region: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region, monthly_group in monthly_region.groupby("Region"):
        panel_group = panel[panel["Region"] == region]
        rows.append(
            {
                "Region": region,
                "units_peak_month": int(monthly_group.loc[monthly_group["Units_Sold"].idxmax(), "Month"]),
                "units_trough_month": int(monthly_group.loc[monthly_group["Units_Sold"].idxmin(), "Month"]),
                "revenue_peak_month": int(monthly_group.loc[monthly_group["Revenue_EUR"].idxmax(), "Month"]),
                "revenue_trough_month": int(monthly_group.loc[monthly_group["Revenue_EUR"].idxmin(), "Month"]),
                "units_seasonality_cv": monthly_group["Units_Sold"].std() / monthly_group["Units_Sold"].mean(),
                "revenue_seasonality_cv": monthly_group["Revenue_EUR"].std() / monthly_group["Revenue_EUR"].mean(),
                "units_corr_gdp": panel_group["Units_Sold"].corr(panel_group["GDP_Growth"]),
                "units_corr_fuel": panel_group["Units_Sold"].corr(panel_group["Fuel_Price_Index"]),
                "revenue_corr_gdp": panel_group["Revenue_EUR"].corr(panel_group["GDP_Growth"]),
                "revenue_corr_fuel": panel_group["Revenue_EUR"].corr(panel_group["Fuel_Price_Index"]),
            }
        )
    return pd.DataFrame(rows)


def save_plots(monthly_region: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(11, 10), sharex=True)
    for region, group in monthly_region.groupby("Region"):
        axes[0].plot(group["Month"], group["Units_Sold"], marker="o", label=region)
        axes[1].plot(group["Month"], group["Revenue_EUR"], marker="o", label=region)

    axes[0].set_title("Monthly Units Sold by Region")
    axes[0].set_ylabel("Units Sold")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].set_title("Monthly Revenue by Region")
    axes[1].set_xlabel("Month")
    axes[1].set_ylabel("Revenue (EUR)")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "monthly_sales_and_revenue.png", dpi=200)
    plt.close(fig)


def main() -> None:
    df = pd.read_excel(DATA_PATH)
    monthly_region, panel = build_views(df)
    summary = region_summary(monthly_region, panel)
    save_plots(monthly_region)
    monthly_region.to_csv(OUTPUT_DIR / "monthly_region_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "question_c_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
