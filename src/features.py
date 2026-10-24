"""
features.py - shared helpers used by BOTH train_models.py and app.py.

Two ideas live here:
  1. "Recent effluent" inputs: the plant's most recent effluent results
     (previous recorded day, and the average of the previous 3 recorded days).
     Effluent quality changes slowly, so recent results carry real information.
  2. Log scaling: wastewater measurements are skewed (a few extreme days),
     so values are transformed with log(1 + x) before modelling.

Keep these functions here (not inside a script), so the saved models can be
loaded again by the app.
"""
import numpy as np
import pandas as pd

EFFLUENT = ["DBO-S", "DQO-S", "SS-S"]
LAG_FEATURES = [f"{t}_{k}" for t in EFFLUENT for k in ("last", "avg3")]


def add_recent_effluent(df: pd.DataFrame) -> pd.DataFrame:
    """Add, for every day, the previous recorded effluent result and the
    average of the previous 3 recorded results (today's value is NOT used)."""
    df = df.sort_values("DATE").copy()
    for t in EFFLUENT:
        previous = df[t].shift(1)
        df[f"{t}_last"] = previous.ffill()
        df[f"{t}_avg3"] = previous.rolling(3, min_periods=1).mean()
    return df


def log1p_clip(X):
    """log(1 + x) with negative values clipped to 0."""
    return np.log1p(np.clip(np.asarray(X, dtype=float), 0, None))


from sklearn.base import BaseEstimator, RegressorMixin  # noqa: E402


class LastResult(BaseEstimator, RegressorMixin):
    """Benchmark 'model': predicts that today's effluent equals the most
    recent recorded result (column given by `column`)."""

    def __init__(self, column=0):
        self.column = column

    def fit(self, X, y):
        self.fallback_ = float(np.nanmedian(np.asarray(y, dtype=float)))
        return self

    def predict(self, X):
        v = np.asarray(X, dtype=float)[:, self.column]
        return np.where(np.isnan(v), self.fallback_, v)
