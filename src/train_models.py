"""
train_models.py - STEP 2 of the machine-learning pipeline.

For each effluent target (BOD, COD, TSS) it:
  1. Splits the days in time order: first 80 % = training, last 20 % = test
     (the model never sees the "future" while learning).
  2. Compares six models with 5-fold time-series cross-validation:
       - Baseline     (always predicts the training median)
       - Last result  (predicts the most recent effluent result)
       - Ridge        (linear regression with regularisation)
       - RandomForest
       - XGBoost
       - Ensemble     (average of Ridge, random forest and XGBoost)
     Inputs = plant readings of the day + recent effluent results
     (features.py). Ridge, random forest and XGBoost work on log-scaled
     values, which stops a few extreme days from dominating.
  3. Refits every model on the full training period and scores it on the
     untouched test period (R2, MAE, RMSE).
  4. Keeps the LEARNING model (not a benchmark) with the lowest
     cross-validated MAE as the "best" model,
     saves it to models/, and draws the figures for the paper.

How to run
  python src/train_models.py
"""
import json
import warnings

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.compose import TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from xgboost import XGBRegressor

from config import (CLEAN_DATA, FIGURES_DIR, LABELS, LIMITS, MODEL_FEATURES,
                    MODELS_DIR, RANDOM_STATE, TABLES_DIR, TARGETS,
                    TEST_FRACTION)
from features import LastResult, add_recent_effluent, log1p_clip

FEATURES = MODEL_FEATURES

warnings.filterwarnings("ignore")


def log_model(estimator, scale=False):
    """fill missing -> log(1+x) inputs -> (scale) -> model, trained on log(1+y)."""
    steps = [("impute", SimpleImputer(strategy="median")),
             ("log", FunctionTransformer(log1p_clip))]
    if scale:
        steps.append(("scale", StandardScaler()))
    steps.append(("model", estimator))
    return TransformedTargetRegressor(regressor=Pipeline(steps), func=np.log1p, inverse_func=np.expm1)


def make_models(target: str) -> dict:
    """The six models compared for one target."""
    last_col = FEATURES.index(f"{target}_last")
    models = {
        "Baseline (median)": Pipeline([("impute", SimpleImputer(strategy="median")),
                                       ("model", DummyRegressor(strategy="median"))]),
        "Last result": LastResult(column=last_col),
        "Ridge regression": log_model(Ridge(alpha=10.0), scale=True),
        "Random forest": log_model(RandomForestRegressor(
            n_estimators=400, min_samples_leaf=5, max_features=0.33,
            random_state=RANDOM_STATE, n_jobs=-1)),
        "XGBoost": log_model(XGBRegressor(
            n_estimators=300, learning_rate=0.03, max_depth=2, subsample=0.8,
            colsample_bytree=0.7, min_child_weight=5, reg_lambda=5.0,
            objective="reg:absoluteerror", random_state=RANDOM_STATE, n_jobs=-1)),
    }
    models["Ensemble (average)"] = VotingRegressor([
        ("ridge", models["Ridge regression"]), ("forest", models["Random forest"]),
        ("xgb", models["XGBoost"])])
    return models


BENCHMARKS = ("Baseline (median)", "Last result")


def scores(y_true, y_pred) -> dict:
    return {
        "R2": r2_score(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def plot_observed_vs_predicted(target, y_test, pred, model_name, r2):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.scatter(y_test, pred, s=12, alpha=0.7, color="#2b6cb0")
    lo, hi = float(min(y_test.min(), pred.min())), float(max(y_test.max(), pred.max()))
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="Perfect prediction")
    ax.set_xlabel(f"Observed {TARGETS[target]} (mg/L)")
    ax.set_ylabel(f"Predicted {TARGETS[target]} (mg/L)")
    ax.set_title(f"{TARGETS[target]}: {model_name}\nTest R² = {r2:.2f}")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"fig_obs_vs_pred_{target}.png", dpi=150)
    plt.close(fig)


def plot_timeseries(target, dates, y_test, pred, model_name):
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(dates, y_test, lw=1, label="Observed", color="#1a202c")
    ax.plot(dates, pred, lw=1, label=f"Predicted ({model_name})", color="#dd6b20")
    ax.set_ylabel(f"{TARGETS[target]} (mg/L)")
    ax.set_title(f"{TARGETS[target]} in the test period")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"fig_test_timeseries_{target}.png", dpi=150)
    plt.close(fig)


def plot_importance(target, model, X_test, y_test, model_name):
    result = permutation_importance(model, X_test, y_test, n_repeats=20,
                                    random_state=RANDOM_STATE, scoring="neg_mean_absolute_error")
    imp = pd.Series(result.importances_mean, index=FEATURES).sort_values().tail(10)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh([LABELS.get(c, c) for c in imp.index], imp.values, color="#2f855a")
    ax.set_xlabel("Increase in MAE when the input is shuffled (mg/L)")
    ax.set_title(f"Top 10 inputs for {TARGETS[target]}\n(model: {model_name})")
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"fig_importance_{target}.png", dpi=150)
    plt.close(fig)
    return imp.sort_values(ascending=False)


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CLEAN_DATA, parse_dates=["DATE"]).sort_values("DATE")
    df = add_recent_effluent(df)
    metadata = {"features": FEATURES, "targets": {}, "feature_stats": {}}
    for c in FEATURES:
        s = df[c].dropna()
        metadata["feature_stats"][c] = {
            "label": LABELS.get(c, c), "median": float(s.median()),
            "min": float(s.min()), "max": float(s.max()),
        }

    all_rows = []
    for target in TARGETS:
        data = df.dropna(subset=[target])
        n_test = int(round(len(data) * TEST_FRACTION))
        train, test = data.iloc[:-n_test], data.iloc[-n_test:]
        X_train, y_train = train[FEATURES], train[target]
        X_test, y_test = test[FEATURES], test[target]

        cv = TimeSeriesSplit(n_splits=5)
        fitted, test_preds = {}, {}
        for name, model in make_models(target).items():
            cvres = cross_validate(model, X_train, y_train, cv=cv,
                                   scoring=("r2", "neg_mean_absolute_error",
                                            "neg_root_mean_squared_error"))
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            s = scores(y_test, pred)
            all_rows.append({
                "target": TARGETS[target], "model": name,
                "n_train_days": len(train), "n_test_days": len(test),
                "CV_R2_mean": cvres["test_r2"].mean(),
                "CV_MAE_mean": -cvres["test_neg_mean_absolute_error"].mean(),
                "CV_MAE_sd": cvres["test_neg_mean_absolute_error"].std(),
                "CV_RMSE_mean": -cvres["test_neg_root_mean_squared_error"].mean(),
                "Test_R2": s["R2"], "Test_MAE": s["MAE"], "Test_RMSE": s["RMSE"],
            })
            fitted[name], test_preds[name] = model, pred
            print(f"{TARGETS[target]:<14} {name:<18} CV MAE={all_rows[-1]['CV_MAE_mean']:.2f}  "
                  f"Test R2={s['R2']:.2f}  Test MAE={s['MAE']:.2f}")

        # Best model = learning model with the lowest cross-validated MAE
        # (chosen without looking at the test set; benchmarks are for comparison only)
        rows_t = [r for r in all_rows if r["target"] == TARGETS[target]]
        best = min([r for r in rows_t if r["model"] not in BENCHMARKS], key=lambda r: r["CV_MAE_mean"])
        best_name = best["model"]
        best_model = fitted[best_name]
        pred = test_preds[best_name]

        plot_observed_vs_predicted(target, y_test, pred, best_name, best["Test_R2"])
        plot_timeseries(target, test["DATE"], y_test, pred, best_name)
        imp = plot_importance(target, best_model, X_test, y_test, best_name)

        # Refit the chosen model on ALL days for use in the app
        final_model = make_models(target)[best_name].fit(data[FEATURES], data[target])
        joblib.dump(final_model, MODELS_DIR / f"model_{target}.joblib")

        metadata["targets"][target] = {
            "name": TARGETS[target], "best_model": best_name,
            "test_R2": round(best["Test_R2"], 3), "test_MAE": round(best["Test_MAE"], 2),
            "test_RMSE": round(best["Test_RMSE"], 2), "cv_MAE": round(best["CV_MAE_mean"], 2),
            "n_days": len(data), "top_inputs": list(imp.index[:5]),
        }

    results = pd.DataFrame(all_rows)
    results.round(3).to_csv(TABLES_DIR / "table2_model_comparison.csv", index=False)

    # Compliance check on the test period with the best models:
    # does "predicted pass/fail" agree with "observed pass/fail"?
    comp_rows = []
    for standard, lim in LIMITS.items():
        for target in TARGETS:
            if target not in lim:
                continue
            data = df.dropna(subset=[target])
            n_test = int(round(len(data) * TEST_FRACTION))
            train, test = data.iloc[:-n_test], data.iloc[-n_test:]
            name = metadata["targets"][target]["best_model"]
            m = make_models(target)[name].fit(train[FEATURES], train[target])
            obs_pass = test[target] <= lim[target]
            pred_pass = m.predict(test[FEATURES]) <= lim[target]
            comp_rows.append({
                "standard": standard, "parameter": TARGETS[target],
                "limit_mg_L": lim[target], "observed_pass_rate_%": round(100 * obs_pass.mean(), 1),
                "agreement_%": round(100 * (obs_pass == pred_pass).mean(), 1),
            })
    pd.DataFrame(comp_rows).to_csv(TABLES_DIR / "table3_compliance_agreement.csv", index=False)

    with open(MODELS_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nBest model per target:")
    for t, m in metadata["targets"].items():
        print(f"  {m['name']:<14} -> {m['best_model']}  (test R2 {m['test_R2']}, MAE {m['test_MAE']} mg/L)")
    print("\nModels saved to:", MODELS_DIR)
    print("STEP 2 DONE")


if __name__ == "__main__":
    main()
