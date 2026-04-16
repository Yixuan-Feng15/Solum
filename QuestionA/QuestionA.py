from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "bmw_global_sales_2018-2025.xlsx"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def build_region_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    annual = (df.groupby(["Year", "Region"], as_index=False)
        .agg(
            BEV_Share=("BEV_Share", "mean"),
            Units_Sold=("Units_Sold", "sum"),
            Revenue_EUR=("Revenue_EUR", "sum"),
        ).sort_values(["Region", "Year"]))

    rows = []
    for region, group in annual.groupby("Region"):
        rows.append({
                "Region": region,
                "corr_bev_units": group["BEV_Share"].corr(group["Units_Sold"]),
                "corr_bev_revenue": group["BEV_Share"].corr(group["Revenue_EUR"]),
                "bev_2018": group["BEV_Share"].iloc[0],
                "bev_2025": group["BEV_Share"].iloc[-1],
                "absolute_bev_change": group["BEV_Share"].iloc[-1] - group["BEV_Share"].iloc[0],
                "bev_trend_slope_per_year": group["BEV_Share"].diff().mean(),
            })

    return annual, pd.DataFrame(rows).sort_values("absolute_bev_change", ascending=False)


def save_plots(annual: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    for region, group in annual.groupby("Region"):
        axes[0].plot(group["Year"], group["BEV_Share"], marker="o", label=region)
        axes[1].plot(group["Year"], group["Units_Sold"], marker="o", label=region)

    axes[0].set_title("BEV Share Trend by Region")
    axes[0].set_ylabel("Average BEV Share")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].set_title("Units Sold Trend by Region")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Units Sold")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "bev_and_units_trend.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    for ax, (region, group) in zip(axes.flatten(), annual.groupby("Region")):
        ax.scatter(group["BEV_Share"], group["Revenue_EUR"], s=50)
        for _, row in group.iterrows():
            ax.annotate(int(row["Year"]), (row["BEV_Share"], row["Revenue_EUR"]), fontsize=8)
        ax.set_title(region)
        ax.set_xlabel("BEV Share")
        ax.set_ylabel("Revenue (EUR)")
        ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "bev_vs_revenue_by_region.png", dpi=200)
    plt.close(fig)


def main() -> None:
    df = pd.read_excel(DATA_PATH)
    annual, summary = build_region_summary(df)
    save_plots(annual)
    annual.to_csv(OUTPUT_DIR / "annual_region_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "question_a_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
