"""Spatially validated demand model and SHAP explanations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from site_intelligence.constants import MODEL_FEATURES


@dataclass(frozen=True)
class ModelResult:
    model: RandomForestRegressor
    metrics: dict[str, Any]
    out_of_fold: pd.DataFrame
    fold_metrics: pd.DataFrame


def _model(params: dict[str, Any], seed: int) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=int(params["n_estimators"]),
        min_samples_leaf=int(params["min_samples_leaf"]),
        max_features=float(params["max_features"]),
        random_state=seed,
        n_jobs=-1,
    )


def spatial_cross_validate(
    benchmark: pd.DataFrame,
    *,
    params: dict[str, Any],
    seed: int,
    requested_splits: int,
) -> ModelResult:
    """Fit and evaluate with spatial blocks kept wholly inside a fold."""

    x = benchmark[MODEL_FEATURES].astype(float)
    y = benchmark["annual_sales_try_m"].astype(float)
    groups = benchmark["spatial_block"].astype(str)
    split_count = min(requested_splits, groups.nunique())
    if split_count < 3:
        raise ValueError("Spatial block CV needs at least three unique blocks.")

    predictions = np.full(len(benchmark), np.nan, dtype=float)
    fold_rows = []
    splitter = GroupKFold(n_splits=split_count)
    for fold, (train_index, test_index) in enumerate(splitter.split(x, y, groups), start=1):
        estimator = _model(params, seed + fold)
        estimator.fit(x.iloc[train_index], y.iloc[train_index])
        fold_prediction = estimator.predict(x.iloc[test_index])
        predictions[test_index] = fold_prediction
        actual = y.iloc[test_index]
        fold_rows.append(
            {
                "fold": fold,
                "train_rows": len(train_index),
                "test_rows": len(test_index),
                "test_spatial_blocks": groups.iloc[test_index].nunique(),
                "mae_try_m": mean_absolute_error(actual, fold_prediction),
                "rmse_try_m": mean_squared_error(actual, fold_prediction) ** 0.5,
                "r2": r2_score(actual, fold_prediction),
                "mape": float(np.mean(np.abs((actual - fold_prediction) / actual))),
            }
        )

    fitted = _model(params, seed)
    fitted.fit(x, y)
    metrics = {
        "validation_strategy": f"{split_count}-fold GroupKFold on 12 km projected spatial blocks",
        "rows": len(benchmark),
        "spatial_blocks": int(groups.nunique()),
        "mae_try_m": float(mean_absolute_error(y, predictions)),
        "rmse_try_m": float(mean_squared_error(y, predictions) ** 0.5),
        "r2": float(r2_score(y, predictions)),
        "mape": float(np.mean(np.abs((y - predictions) / y))),
        "target_mean_try_m": float(y.mean()),
        "target_std_try_m": float(y.std()),
    }
    out_of_fold = benchmark[["benchmark_id", "spatial_block", "annual_sales_try_m"]].copy()
    out_of_fold["predicted_sales_try_m"] = np.round(predictions, 4)
    out_of_fold["residual_try_m"] = np.round(
        out_of_fold["annual_sales_try_m"] - out_of_fold["predicted_sales_try_m"],
        4,
    )
    return ModelResult(fitted, metrics, out_of_fold, pd.DataFrame(fold_rows))


def predict_candidates(
    model: RandomForestRegressor,
    candidates: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Predict candidate demand with tree intervals and SHAP factor contributions."""

    x = candidates[MODEL_FEATURES].astype(float)
    tree_predictions = np.vstack([tree.predict(x.to_numpy()) for tree in model.estimators_])
    point_prediction = tree_predictions.mean(axis=0)
    result = candidates.copy()
    result["predicted_sales_try_m"] = np.round(point_prediction, 3)
    result["sales_p10_try_m"] = np.round(np.quantile(tree_predictions, 0.10, axis=0), 3)
    result["sales_p90_try_m"] = np.round(np.quantile(tree_predictions, 0.90, axis=0), 3)
    result["prediction_interval_width_try_m"] = np.round(
        result["sales_p90_try_m"] - result["sales_p10_try_m"],
        3,
    )

    explainer = shap.TreeExplainer(model)
    shap_values = np.asarray(explainer.shap_values(x))
    contribution_rows: list[dict[str, float | str]] = []
    for row_index, candidate_id in enumerate(result["candidate_id"].astype(str)):
        for feature_index, feature in enumerate(MODEL_FEATURES):
            contribution_rows.append(
                {
                    "candidate_id": candidate_id,
                    "feature": feature,
                    "feature_value": float(x.iloc[row_index, feature_index]),
                    "shap_contribution_try_m": float(shap_values[row_index, feature_index]),
                    "direction": (
                        "positive"
                        if shap_values[row_index, feature_index] > 0
                        else "negative"
                        if shap_values[row_index, feature_index] < 0
                        else "neutral"
                    ),
                }
            )
    contributions = pd.DataFrame(contribution_rows)
    result["shap_base_value_try_m"] = round(
        float(np.asarray(explainer.expected_value).reshape(-1)[0]), 4
    )
    return result, contributions


def save_model(
    model: RandomForestRegressor,
    metrics: dict[str, Any],
    path: str | Path,
) -> None:
    """Persist a versioned model bundle."""

    joblib.dump(
        {
            "model": model,
            "features": MODEL_FEATURES,
            "metrics": metrics,
            "schema_version": "1.0.0",
        },
        Path(path),
    )


def load_model(path: str | Path) -> dict[str, Any]:
    """Load a persisted model bundle."""

    return joblib.load(Path(path))
