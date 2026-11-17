import io
import os
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.metrics import mean_squared_error

# Use paths relative to this script so Render and local execution both find the files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model.pkl")


app = FastAPI(
    title="Student Academic Performance and Early Warning System",
    description=(
        "Multivariate regression API that predicts a student's "
        "Total_Score (0-100) using mid-semester academic performance and "
        "socioeconomic indicators. "
        "The goal of the system is to track students' progress and help those"
        "who are left behind, or need assistance."
    ),
    version="1.0.0",
)


# CORS MIDDLEWARE CONFIGURATION)
#Allow only my own deployed API page and local debug addresses.
# Restrict all other websites, so random sites cannot call the API from a browser.
# Methods and headers are limited to what the app needs.
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://performance-checker-service.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)


# Feature definitions and Pydantic validation schemas.
# column names expected by trained scikit-learn Pipeline in best_model.pkl
NUMERIC_FEATURES = [
    "Attendance (%)",
    "Midterm_Score",
    "Assignments_Avg",
    "Quizzes_Avg",
    "Projects_Score",
]

CATEGORICAL_FEATURES = [
    "Internet_Access_at_Home",
    "Family_Income_Level",
    "Parent_Education_Level",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "Total_Score"


class StudentPredictionInput(BaseModel):
    """
    Pydantic schema enforcing strict data types,percentage bounds (0.0 to 100.0),
    and allowed categorical values for all 8 input features.
    """

    attendance: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Student class attendance percentage (0.0 to 100.0)",
        examples=[85.5],
    )
    midterm_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Mid-semester examination score (0.0 to 100.0)",
        examples=[78.0],
    )
    assignments_avg: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average score across weekly homework assignments (0.0 to 100.0)",
        examples=[82.0],
    )
    quizzes_avg: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average score across classroom quizzes (0.0 to 100.0)",
        examples=[76.5],
    )
    projects_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Practical coursework projects score (0.0 to 100.0)",
        examples=[88.0],
    )
    internet_access_at_home: Literal["Yes", "No"] = Field(
        ...,
        description="Whether the student has internet connectivity at home ('Yes' or 'No')",
        examples=["Yes"],
    )
    family_income_level: Literal["Low", "Medium", "High"] = Field(
        ...,
        description="Household socioeconomic ('Low', 'Medium', or 'High')",
        examples=["Low"],
    )
    parent_education_level: Literal["None", "High School", "Bachelor's", "Master's", "PhD"] = Field(
        ...,
        description="Highest formal education level by parents",
        examples=["High School"],
    )


class PredictionResponse(BaseModel):
    """Schema for the JSON response returned by POST /predict."""

    predicted_total_score: float
    risk_status: str
    message: str


# Model loading and prediction function
def load_model_pipeline(path: str = MODEL_PATH):
    """Loads the serialized scikit-learn Pipeline (preprocessor + regressor) from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model file not found at '{path}'. Please run multivariate.ipynb first to generate best_model.pkl."
        )
    return joblib.load(path)


# Load the trained pipeline into memory at server startup
try:
    model_pipeline = load_model_pipeline()
except Exception as e:
    print(f"WARNING: Could not load model at startup: {e}")
    model_pipeline = None


def predict_single_student(input_data: dict, pipeline=None) -> float:
    """
    prediction function that accepts a dictionary of
    8 raw student features, transforms them via the Pipeline, and returns Total_Score.
    """
    active_pipeline = pipeline if pipeline is not None else load_model_pipeline()
    input_df = pd.DataFrame([input_data])
    raw_prediction = active_pipeline.predict(input_df)[0]
    clamped_prediction = float(np.clip(raw_prediction, 0.0, 100.0))
    return round(clamped_prediction, 2)



# (GET /) & (POST /predict)
@app.get("/", tags=["Check If Active"])
def root():
    """check endpoint verifying that the API service and model pipeline are active."""
    model_loaded = model_pipeline is not None
    regressor_name = (
        type(model_pipeline.named_steps["regressor"]).__name__
        if model_loaded and hasattr(model_pipeline, "named_steps")
        else "Not Loaded"
    )
    return {
        "status": "online",
        "service": "Educational Equity Early Warning System API",
        "model_loaded": model_loaded,
        "active_model_class": regressor_name,
        "docs_url": "/docs",
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict_score(student: StudentPredictionInput):
    """
    Predicts a student's Total_Score (0.0 - 100.0) from 8 mid-semester
    academic and socioeconomic features.
    """
    global model_pipeline

    if model_pipeline is None:
        try:
            model_pipeline = load_model_pipeline()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Model pipeline unavailable: {str(exc)}")

    # Map clean snake_case Pydantic fields back to the CSV column names expected by the Pipeline
    feature_row = {
        "Attendance (%)": student.attendance,
        "Midterm_Score": student.midterm_score,
        "Assignments_Avg": student.assignments_avg,
        "Quizzes_Avg": student.quizzes_avg,
        "Projects_Score": student.projects_score,
        "Internet_Access_at_Home": student.internet_access_at_home,
        "Family_Income_Level": student.family_income_level,
        "Parent_Education_Level": student.parent_education_level,
    }

    try:
        predicted_score = predict_single_student(feature_row, pipeline=model_pipeline)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}")

    if predicted_score < 60.0:
        risk_status = "High Risk"
        message = "Immediate academic tutoring and socioeconomic support recommended before final exams."
    elif predicted_score < 75.0:
        risk_status = "Moderate Risk"
        message = "Monitor coursework closely and check in on study resources."
    else:
        risk_status = "On Track"
        message = "Student is progressing well toward a strong final cumulative score."

    return PredictionResponse(
        predicted_total_score=predicted_score,
        risk_status=risk_status,
        message=message,
    )

@app.post("/retrain", tags=["Retraining"])
async def retrain_model(file: UploadFile = File(..., description="CSV file containing new student records")):
    """
    Accepts an uploaded CSV file with student records, validates required columns,
    updates the regression model (using partial_fit for SGDRegressor or full Pipeline
    refitting on combined data for closed-form/tree models), saves best_model.pkl
    """
    global model_pipeline

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file.")

    if model_pipeline is None:
        try:
            model_pipeline = load_model_pipeline()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Cannot load existing pipeline: {str(exc)}")

    # Read the uploaded CSV bytes into a pandas DataFrame
    try:
        contents = await file.read()
        new_df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV file: {str(exc)}")

    # Verify all 8 feature columns and the target column (Total_Score) exist in the uploaded CSV
    required_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_cols = [col for col in required_cols if col not in new_df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded CSV is missing required columns: {missing_cols}",
        )

    # Clean the uploaded data (restore 'None' in Parent_Education_Level and drop incomplete rows)
    new_df["Parent_Education_Level"] = new_df["Parent_Education_Level"].fillna("None")
    new_df = new_df.dropna(subset=required_cols)

    if len(new_df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV contains 0 valid rows after cleaning.")

    X_new = new_df[FEATURE_COLUMNS].copy()
    y_new = new_df[TARGET_COLUMN].copy()

    # Update the model based on whether the active estimator supports incremental learning (partial_fit)
    try:
        preprocessor = model_pipeline.named_steps["preprocessor"]
        regressor = model_pipeline.named_steps["regressor"]
        X_new_transformed = preprocessor.transform(X_new)
        regressor.partial_fit(X_new_transformed, y_new)
        updated_preds = model_pipeline.predict(X_new)
        new_batch_mse = float(mean_squared_error(y_new, updated_preds))
        joblib.dump(model_pipeline, MODEL_PATH)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(exc)}")

    return {
        "status": "success",
        "message": "Model updated via partial_fit, saved to best_model.pkl.",
        "new_rows_uploaded": len(new_df),
        "mse_on_uploaded_batch": round(new_batch_mse, 4),
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("prediction:app", host="0.0.0.0", port=port, reload=True)