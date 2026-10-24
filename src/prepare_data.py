"""
prepare_data.py - STEP 1 of the machine-learning pipeline.

What it does
  1. Reads the raw UCI file  data/raw/water-treatment.data
  2. Names the 39 columns, turns "?" into proper "missing" values
  3. Converts the day code (e.g. "D-1/3/90") into a real date and sorts by date
  4. Saves a clean CSV          data/processed/wwtp_clean.csv
  5. Saves summary tables       results/tables/
  6. Saves exploration figures  results/figures/

How to run (from the project folder, with the virtual environment active)
  python src/prepare_data.py
"""
import sys

import matplotlib
matplotlib.use("Agg")  # draw figures to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import (CLEAN_DATA, COLUMNS, FEATURES, FIGURES_DIR, LABELS,
                    RAW_DATA, TABLES_DIR, TARGETS)


def load_raw(path=RAW_DATA) -> pd.DataFrame:
    """Read the raw file whether it has a header row or not."""
    if not path.exists():
        sys.exit(
            f"\nERROR: raw data file not found at:\n  {path}\n"
            "Download it from https://archive.ics.uci.edu/dataset/106/water+treatment+plant\n"
            "unzip it, and put 'water-treatment.data' inside the data/raw folder.\n"
        )
    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    has_header = not first_line.strip().upper().startswith("D-")
    df = pd.read_csv(
        path,
        header=0 if has_header else None,
        names=COLUMNS,
        na_values=["?", "", " "],
        skipinitialspace=True,
    )
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # "D-1/3/90" -> 1 March 1990 (day/month/year)
    df["DATE"] = pd.to_datetime(
        df["DATE"].astype(str).str.replace("D-", "", regex=False).str.strip(),
        format="%d/%m/%y", errors="coerce",
    )
    num_cols = [c for c in COLUMNS if c != "DATE"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)
    # Physically impossible values (negative concentrations) -> missing
    for c in num_cols:
        if not c.startswith("PH"):
            df.loc[df[c] < 0, c] = np.nan
    return df


def save_tables(df: pd.DataFrame) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cols = FEATURES + list(TARGETS)
    desc = df[cols].describe().T[["count", "mean", "std", "min", "50%", "max"]]
    desc = desc.rename(columns={"50%": "median"})
    desc.insert(0, "variable", [LABELS.get(c, c) for c in desc.index])
    desc.round(2).to_csv(TABLES_DIR / "table1_descriptive_statistics.csv")

    miss = df[cols].isna().sum().rename("missing_values").to_frame()
    miss["percent"] = (100 * miss["missing_values"] / len(df)).round(1)
    miss.to_csv(TABLES_DIR / "table_missing_values.csv")


def save_figures(df: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 150, "font.size": 9})

    # Figure: effluent quality over time
    fig, axes = plt.subplots(len(TARGETS), 1, figsize=(7, 6), sharex=True)
    for ax, t in zip(axes, TARGETS):
        ax.plot(df["DATE"], df[t], lw=0.8, color="#2b6cb0")
        ax.set_ylabel(LABELS[t].replace("Effluent ", ""), fontsize=8)
        ax.grid(alpha=0.3)
    axes[0].set_title("Daily effluent quality of the studied plant")
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_effluent_timeseries.png")
    plt.close(fig)

    # Figure: correlation of every input with each effluent target
    corr = df[FEATURES + list(TARGETS)].corr(method="spearman").loc[FEATURES, list(TARGETS)]
    fig, ax = plt.subplots(figsize=(5, 8))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(TARGETS)), [TARGETS[t] for t in TARGETS], rotation=30, ha="right")
    ax.set_yticks(range(len(FEATURES)), FEATURES)
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, label="Spearman correlation")
    ax.set_title("Correlation of plant inputs with effluent quality")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_correlation_heatmap.png")
    plt.close(fig)


def main() -> None:
    raw = load_raw()
    df = clean(raw)
    CLEAN_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_DATA, index=False)
    save_tables(df)
    save_figures(df)
    print(f"Rows read: {len(raw)}   rows kept: {len(df)}")
    print(f"Date range: {df['DATE'].min().date()} to {df['DATE'].max().date()}")
    print(f"Clean data saved to: {CLEAN_DATA}")
    print("Tables saved to:", TABLES_DIR)
    print("Figures saved to:", FIGURES_DIR)
    print("STEP 1 DONE")


if __name__ == "__main__":
    main()
