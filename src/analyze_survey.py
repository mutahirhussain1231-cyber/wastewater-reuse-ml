"""
analyze_survey.py - analyses the Google Forms survey.

Input : survey/responses.csv   (Google Sheets -> File -> Download -> CSV)
Output: results/tables/survey_*.csv, results/figures/survey_*.png,
        results/survey_summary.txt  (all key numbers for the paper)

How to run
  python src/analyze_survey.py
  python src/analyze_survey.py path/to/another_file.csv   (optional)

The script finds questions by the code at the start of each question title
("C1.", "P1." ... "Q12."), so keep those codes in your Google Form.
"""
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from config import FIGURES_DIR, ROOT, SURVEY_DIR, TABLES_DIR

INFILE = SURVEY_DIR / "responses.csv"
SUMMARY = ROOT / "results" / "survey_summary.txt"
lines = []  # collected text for the summary file


def say(text=""):
    print(text)
    lines.append(text)


# ---------------------------------------------------------------------------
# Helpers to find columns
# ---------------------------------------------------------------------------
def col(df, code):
    """Single column whose title starts with e.g. 'Q7.'"""
    hits = [c for c in df.columns if c.strip().startswith(code + " ") or c.strip().startswith(code + ".")
            or re.match(rf"^\s*{re.escape(code)}\.", c)]
    hits = [c for c in hits if "[" not in c]
    return hits[0] if hits else None


def grid(df, code):
    """All grid columns 'Q5. ... [row]' -> dict {row label: column}"""
    out = {}
    for c in df.columns:
        if re.match(rf"^\s*{re.escape(code)}\.", c) and "[" in c:
            out[c[c.rfind("[") + 1:c.rfind("]")].strip()] = c
    return out


def to_score(s):
    """'4', '4 - Agree', 4.0 -> 4 ; anything else -> NaN"""
    return pd.to_numeric(s.astype(str).str.extract(r"(\d)")[0], errors="coerce")


def cronbach_alpha(items: pd.DataFrame) -> float:
    items = items.dropna()
    k = items.shape[1]
    if k < 2 or len(items) < 3:
        return float("nan")
    var_sum = items.var(axis=0, ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    return float(k / (k - 1) * (1 - var_sum / total_var))


def freq_table(series, name):
    t = series.value_counts(dropna=True).rename("n").to_frame()
    t["percent"] = (100 * t["n"] / t["n"].sum()).round(1)
    t.index.name = name
    return t


def ci95(x):
    x = x.dropna()
    if len(x) < 2:
        return np.nan
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))


def stacked_bars(data: pd.DataFrame, categories, colors, title, fname, xlabel="Percent of respondents"):
    """data: rows = items, columns = categories (counts)."""
    pct = data[categories].div(data[categories].sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(pct) + 1.5))
    left = np.zeros(len(pct))
    labels = ["\n".join(textwrap.wrap(i, 38)) for i in pct.index]
    for cat, colr in zip(categories, colors):
        ax.barh(labels, pct[cat], left=left, color=colr, label=str(cat), edgecolor="white")
        for y, (l, v) in enumerate(zip(left, pct[cat])):
            if v >= 7:
                ax.text(l + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=7)
        left += pct[cat].values
    ax.set_xlim(0, 100)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.invert_yaxis()
    ax.legend(ncol=len(categories), bbox_to_anchor=(0.5, -0.18), loc="upper center", fontsize=7, frameon=False)
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / fname, dpi=200)
    plt.close(fig)


LIKERT_COLORS = ["#c53030", "#ed8936", "#e2e8f0", "#68d391", "#2f855a"]
CONCERN_COLORS = ["#2f855a", "#68d391", "#e2e8f0", "#ed8936", "#c53030"]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else INFILE
    df = pd.read_csv(path)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9})

    say("SURVEY ANALYSIS SUMMARY")
    say("=" * 60)
    say(f"Rows in file: {len(df)}")

    # 1. Keep consenting adults only ----------------------------------------
    c1 = col(df, "C1")
    if c1:
        df = df[df[c1].astype(str).str.lower().str.startswith("yes")]
    df = df.reset_index(drop=True)
    n = len(df)
    say(f"Valid responses (consent given): n = {n}")
    if n < 30:
        say("NOTE: fewer than 30 responses - treat statistical tests as preliminary.")

    # 2. Profile table -------------------------------------------------------
    prof = []
    for code, name in [("P1", "Age group"), ("P2", "Gender"), ("P3", "Education"),
                       ("P4", "Field"), ("P5", "Residence"), ("P6", "Province/region")]:
        c = col(df, code)
        if c:
            t = freq_table(df[c], "category").reset_index()
            t.insert(0, "characteristic", name)
            prof.append(t)
    if prof:
        pd.concat(prof).to_csv(TABLES_DIR / "survey_table1_profile.csv", index=False)

    # 3. Frequencies of single-choice questions ------------------------------
    freq = []
    for code in ["Q1", "Q3", "Q4", "Q7", "Q8", "Q12"]:
        c = col(df, code)
        if c:
            t = freq_table(df[c], "answer").reset_index()
            t.insert(0, "question", code)
            freq.append(t)
            say(f"\n{code}: " + "; ".join(f"{a} {p}%" for a, p in zip(t['answer'], t['percent'])))
    if freq:
        pd.concat(freq).to_csv(TABLES_DIR / "survey_table2_frequencies.csv", index=False)

    # 4. Scores ---------------------------------------------------------------
    q5, q6, q11 = grid(df, "Q5"), grid(df, "Q6"), grid(df, "Q11")
    will = pd.DataFrame({k: to_score(df[v]) for k, v in q5.items()})
    conc = pd.DataFrame({k: to_score(df[v]) for k, v in q6.items()})
    df["willingness_index"] = will.mean(axis=1) if not will.empty else np.nan
    df["concern_index"] = conc.mean(axis=1) if not conc.empty else np.nan
    for code, newname in [("Q2", "knowledge"), ("Q9", "disgust"), ("Q10", "transparency")]:
        c = col(df, code)
        df[newname] = to_score(df[c]) if c else np.nan
    aw = pd.Series(0, index=df.index, dtype=float)
    if col(df, "Q1"):
        aw += df[col(df, "Q1")].astype(str).str.contains("know what it means", case=False).astype(int)
    if col(df, "Q3"):
        aw += (~df[col(df, "Q3")].astype(str).str.contains("don't know|dont know", case=False)).astype(int)
    if col(df, "Q4"):
        aw += df[col(df, "Q4")].astype(str).str.lower().str.startswith("yes").astype(int)
    df["awareness_score"] = aw

    # 5. Willingness ladder (Q5) ----------------------------------------------
    if not will.empty:
        lad = pd.DataFrame({
            "use": will.columns,
            "mean": will.mean().values,
            "ci95": [ci95(will[c]) for c in will.columns],
            "percent_willing_(4-5)": [(100 * (will[c] >= 4).sum() / will[c].notna().sum()).round(1) for c in will.columns],
        }).sort_values("mean", ascending=False)
        lad.round(2).to_csv(TABLES_DIR / "survey_table3_willingness_ladder.csv", index=False)
        counts = pd.DataFrame({k: will[k].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0) for k in lad["use"]}).T
        stacked_bars(counts, [1, 2, 3, 4, 5], LIKERT_COLORS,
                     "Willingness to use treated wastewater (1 = not at all, 5 = completely)",
                     "survey_fig1_willingness.png")
        a5 = cronbach_alpha(will)
        say(f"\nWillingness ladder (mean 1-5, most to least accepted):")
        for _, r in lad.iterrows():
            say(f"  {r['use']}: mean {r['mean']:.2f} ± {r['ci95']:.2f}; {r['percent_willing_(4-5)']}% willing")
        say(f"Cronbach's alpha, willingness items (Q5): {a5:.2f}")

    # 6. Concerns (Q6) ----------------------------------------------------------
    if not conc.empty:
        ct = pd.DataFrame({"concern": conc.columns, "mean": conc.mean().values,
                           "percent_concerned_(4-5)": [(100 * (conc[c] >= 4).sum() / conc[c].notna().sum()).round(1)
                                                      for c in conc.columns]}).sort_values("mean", ascending=False)
        ct.round(2).to_csv(TABLES_DIR / "survey_table4_concerns.csv", index=False)
        counts = pd.DataFrame({k: conc[k].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0) for k in ct["concern"]}).T
        stacked_bars(counts, [1, 2, 3, 4, 5], CONCERN_COLORS,
                     "Level of concern (1 = not concerned, 5 = extremely concerned)", "survey_fig2_concerns.png")
        say("\nConcerns (mean 1-5): " + "; ".join(f"{r['concern']} {r['mean']:.2f}" for _, r in ct.iterrows()))
        say(f"Cronbach's alpha, concern items (Q6): {cronbach_alpha(conc):.2f}")

    # 7. Recovered products (Q11) ---------------------------------------------
    if q11:
        cats = ["Would accept", "Not sure", "Would not accept"]
        counts = pd.DataFrame({k: df[v].value_counts().reindex(cats, fill_value=0) for k, v in q11.items()}).T
        counts.to_csv(TABLES_DIR / "survey_table5_recovered_products.csv")
        stacked_bars(counts, cats, ["#2f855a", "#e2e8f0", "#c53030"],
                     "Acceptance of products recovered from wastewater", "survey_fig3_products.png")
        pct = (100 * counts["Would accept"] / counts.sum(axis=1)).round(1)
        say("\nWould accept: " + "; ".join(f"{k} {v}%" for k, v in pct.items()))

    # 8. Correlations with the willingness index --------------------------------
    rows = []
    for var in ["knowledge", "awareness_score", "concern_index", "disgust", "transparency"]:
        d = df[["willingness_index", var]].dropna()
        if len(d) >= 5 and d[var].nunique() > 1:
            rho, p = stats.spearmanr(d["willingness_index"], d[var])
            rows.append({"variable": var, "n": len(d), "spearman_rho": round(rho, 3), "p_value": round(p, 4)})
    if rows:
        cor = pd.DataFrame(rows)
        cor.to_csv(TABLES_DIR / "survey_table6_correlations.csv", index=False)
        say("\nSpearman correlation with willingness index:")
        for _, r in cor.iterrows():
            say(f"  {r['variable']}: rho = {r['spearman_rho']}, p = {r['p_value']} (n = {r['n']})")

    # 9. Group differences in willingness ---------------------------------------
    rows = []
    for code, name in [("P2", "Gender"), ("P3", "Education"), ("P5", "Residence"), ("P1", "Age group")]:
        c = col(df, code)
        if not c:
            continue
        groups = {g: d["willingness_index"].dropna() for g, d in df.groupby(c)
                  if g != "Prefer not to say" and d["willingness_index"].notna().sum() >= 3}
        if len(groups) < 2:
            continue
        if len(groups) == 2:
            a, b = list(groups.values())
            stat, p = stats.mannwhitneyu(a, b)
            test = "Mann-Whitney U"
        else:
            stat, p = stats.kruskal(*groups.values())
            test = "Kruskal-Wallis H"
        medians = "; ".join(f"{g}: {v.median():.2f} (n={len(v)})" for g, v in groups.items())
        rows.append({"factor": name, "test": test, "statistic": round(stat, 3), "p_value": round(p, 4),
                     "group_medians": medians})
    if rows:
        gd = pd.DataFrame(rows)
        gd.to_csv(TABLES_DIR / "survey_table7_group_differences.csv", index=False)
        say("\nWillingness by group:")
        for _, r in gd.iterrows():
            say(f"  {r['factor']}: {r['test']} = {r['statistic']}, p = {r['p_value']} | {r['group_medians']}")

    # 10. Chi-square: eating vegetables (Q7) vs profile/awareness ---------------
    rows = []
    q7 = col(df, "Q7")
    if q7:
        for code, name in [("P3", "Education"), ("P5", "Residence"), ("P2", "Gender"), ("Q4", "Knew untreated water is used")]:
            c = col(df, code)
            if not c:
                continue
            tab = pd.crosstab(df[c], df[q7])
            if tab.shape[0] < 2 or tab.shape[1] < 2:
                continue
            chi2, p, dof, exp = stats.chi2_contingency(tab)
            v = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
            rows.append({"Q7_vs": name, "chi2": round(chi2, 3), "df": dof, "p_value": round(p, 4),
                         "cramers_V": round(v, 3),
                         "cells_expected_below_5_%": round(100 * (exp < 5).mean(), 1)})
            tab.to_csv(TABLES_DIR / f"survey_crosstab_Q7_{code}.csv")
    if rows:
        ch = pd.DataFrame(rows)
        ch.to_csv(TABLES_DIR / "survey_table8_chisquare.csv", index=False)
        say("\nChi-square tests (Q7 'eat vegetables irrigated with treated water'):")
        for _, r in ch.iterrows():
            flag = "  [caution: many small expected counts]" if r["cells_expected_below_5_%"] > 20 else ""
            say(f"  vs {r['Q7_vs']}: chi2 = {r['chi2']}, df = {r['df']}, p = {r['p_value']}, V = {r['cramers_V']}{flag}")

    df.to_csv(TABLES_DIR / "survey_scored_responses.csv", index=False)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSummary saved to {SUMMARY}")
    print("SURVEY ANALYSIS DONE")


if __name__ == "__main__":
    main()
