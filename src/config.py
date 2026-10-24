"""
config.py - one place for every setting used in the project.

You normally never need to edit this file. If you do, change only the
values on the right-hand side of the "=" signs.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Folders (worked out automatically from where this file lives)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = ROOT / "data" / "raw" / "water-treatment.data"
CLEAN_DATA = ROOT / "data" / "processed" / "wwtp_clean.csv"
MODELS_DIR = ROOT / "models"
FIGURES_DIR = ROOT / "results" / "figures"
TABLES_DIR = ROOT / "results" / "tables"
SURVEY_DIR = ROOT / "survey"

# ---------------------------------------------------------------------------
# The 39 columns of the UCI "Water Treatment Plant" file, in order.
# The file has no header row, so we supply the names ourselves.
# E = input to plant, P = input to primary settler,
# D = input to secondary settler, S = output (effluent),
# RD = removal performance (%).
# ---------------------------------------------------------------------------
COLUMNS = [
    "DATE",
    "Q-E", "ZN-E", "PH-E", "DBO-E", "DQO-E", "SS-E", "SSV-E", "SED-E", "COND-E",
    "PH-P", "DBO-P", "SS-P", "SSV-P", "SED-P", "COND-P",
    "PH-D", "DBO-D", "DQO-D", "SS-D", "SSV-D", "SED-D", "COND-D",
    "PH-S", "DBO-S", "DQO-S", "SS-S", "SSV-S", "SED-S", "COND-S",
    "RD-DBO-P", "RD-SS-P", "RD-SED-P", "RD-DBO-S", "RD-DQO-S",
    "RD-DBO-G", "RD-DQO-G", "RD-SS-G", "RD-SED-G",
]

# Plain-English names used in figures, tables and the app.
LABELS = {
    "Q-E": "Inflow to plant (m3/day)",
    "ZN-E": "Zinc in inflow (mg/L)",
    "PH-E": "pH of inflow",
    "DBO-E": "BOD of inflow (mg/L)",
    "DQO-E": "COD of inflow (mg/L)",
    "SS-E": "Suspended solids in inflow (mg/L)",
    "SSV-E": "Volatile suspended solids in inflow (mg/L)",
    "SED-E": "Sediments in inflow (mL/L)",
    "COND-E": "Conductivity of inflow (uS/cm)",
    "PH-P": "pH entering primary settler",
    "DBO-P": "BOD entering primary settler (mg/L)",
    "SS-P": "Suspended solids entering primary settler (mg/L)",
    "SSV-P": "Volatile suspended solids entering primary settler (mg/L)",
    "SED-P": "Sediments entering primary settler (mL/L)",
    "COND-P": "Conductivity entering primary settler (uS/cm)",
    "PH-D": "pH entering secondary settler",
    "DBO-D": "BOD entering secondary settler (mg/L)",
    "DQO-D": "COD entering secondary settler (mg/L)",
    "SS-D": "Suspended solids entering secondary settler (mg/L)",
    "SSV-D": "Volatile suspended solids entering secondary settler (mg/L)",
    "SED-D": "Sediments entering secondary settler (mL/L)",
    "COND-D": "Conductivity entering secondary settler (uS/cm)",
    "DBO-S": "Effluent BOD (mg/L)",
    "DQO-S": "Effluent COD (mg/L)",
    "SS-S": "Effluent suspended solids (mg/L)",
}

# Inputs the model is allowed to see: everything measured BEFORE the
# final effluent (stages E, P and D). Effluent (S) and removal-rate (RD)
# columns are excluded because they are calculated from the answer itself
# ("data leakage").
# Removal-rate columns (RD-...) are also left out: they are derived values,
# not direct measurements.
FEATURES = [c for c in COLUMNS if c.endswith(("-E", "-P", "-D")) and not c.startswith("RD-")]

# Recent effluent results (previous recorded day and average of the previous
# 3 recorded days) are added as inputs - see features.py.
LAG_LABELS = {
    "DBO-S_last": "Effluent BOD, most recent result (mg/L)",
    "DBO-S_avg3": "Effluent BOD, average of last 3 results (mg/L)",
    "DQO-S_last": "Effluent COD, most recent result (mg/L)",
    "DQO-S_avg3": "Effluent COD, average of last 3 results (mg/L)",
    "SS-S_last": "Effluent TSS, most recent result (mg/L)",
    "SS-S_avg3": "Effluent TSS, average of last 3 results (mg/L)",
}
LABELS.update(LAG_LABELS)
MODEL_FEATURES = FEATURES + list(LAG_LABELS)

# What the models predict (one model per target).
TARGETS = {
    "DBO-S": "Effluent BOD",
    "DQO-S": "Effluent COD",
    "SS-S": "Effluent TSS",
}

# Share of the most recent days kept aside for the final test.
TEST_FRACTION = 0.20
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Quality limits used by the app (mg/L, pH unitless).
# Sources:
#  - NEQS / Punjab EQS / Sindh EQS for municipal & liquid industrial
#    effluents, discharge to inland waters: BOD5 80, COD 150, TSS 200, pH 6-9.
#  - US EPA (2012) Guidelines for Water Reuse, agricultural reuse:
#    processed food & non-food crops: BOD <= 30, TSS <= 30, pH 6-9;
#    food crops eaten raw: BOD <= 10, TSS <= 5 (if TSS used instead of turbidity).
# ---------------------------------------------------------------------------
LIMITS = {
    "Discharge to inland waters (Pakistan EQS)": {"DBO-S": 80, "DQO-S": 150, "SS-S": 200, "pH": (6.0, 9.0)},
    "Irrigation of non-food / processed crops (US EPA 2012)": {"DBO-S": 30, "SS-S": 30, "pH": (6.0, 9.0)},
    "Irrigation of food crops eaten raw (US EPA 2012)": {"DBO-S": 10, "SS-S": 5, "pH": (6.0, 9.0)},
}
