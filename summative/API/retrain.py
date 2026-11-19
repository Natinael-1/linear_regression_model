import io

import joblib
import pandas as pd
from fastapi import HTTPException
from sklearn.metrics import mean_squared_error


def retrain_model_from_csv(
    model_pipeline,
    contents: bytes,
    model_path: str,
    feature_columns: list[str],
    target_column: str,
):
    try:
        new_df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV file: {str(exc)}")

    required_cols = feature_columns + [target_column]
    missing_cols = [col for col in required_cols if col not in new_df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded CSV is missing required columns: {missing_cols}",
        )

    new_df["Parent_Education_Level"] = new_df["Parent_Education_Level"].fillna("None")
    new_df = new_df.dropna(subset=required_cols)

    if len(new_df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV contains 0 valid rows after cleaning.")

    X_new = new_df[feature_columns].copy()
    y_new = new_df[target_column].copy()

    try:
        preprocessor = model_pipeline.named_steps["preprocessor"]
        regressor = model_pipeline.named_steps["regressor"]
        X_new_transformed = preprocessor.transform(X_new)
        regressor.partial_fit(X_new_transformed, y_new)
        updated_preds = model_pipeline.predict(X_new)
        new_batch_mse = float(mean_squared_error(y_new, updated_preds))
        joblib.dump(model_pipeline, model_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(exc)}")

    return model_pipeline, {
        "status": "success",
        "message": "Model updated via partial_fit, saved to best_model.pkl.",
        "new_rows_uploaded": len(new_df),
        "mse_on_uploaded_batch": round(new_batch_mse, 4),
    }