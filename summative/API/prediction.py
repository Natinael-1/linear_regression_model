import os
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from retrain import retrain_model_from_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model.pkl")

app = FastAPI(
    title="Student Academic Performance and Early Warning System",
    description=(
        "Multivariate regression API that predicts a student's "
        "Total_Score (0-100) using mid-semester academic performance and "
        "socioeconomic indicators. "
        "The goal of the system is to track students' progress and help those "
        "who are left behind, or need assistance."
    ),
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://student-academic-performance-checker.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

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
    predicted_total_score: float
    risk_status: str
    message: str


def load_model_pipeline(path: str = MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model file not found at '{path}'. Please run multivariate.ipynb first to generate best_model.pkl."
        )
    return joblib.load(path)


try:
    model_pipeline = load_model_pipeline()
except Exception as e:
    print(f"WARNING: Could not load model at startup: {e}")
    model_pipeline = None


def predict_single_student(input_data: dict, pipeline=None) -> float:
    active_pipeline = pipeline if pipeline is not None else load_model_pipeline()
    input_df = pd.DataFrame([input_data])
    raw_prediction = active_pipeline.predict(input_df)[0]
    clamped_prediction = float(np.clip(raw_prediction, 0.0, 100.0))
    return round(clamped_prediction, 2)


@app.get("/", tags=["Check If Active"])
def root():
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
    global model_pipeline

    if model_pipeline is None:
        try:
            model_pipeline = load_model_pipeline()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Model pipeline unavailable: {str(exc)}")

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
        message = ("This student needs academic tutoring and socioeconomic support before final exams to be able succeed. "
                   "NGOs, Scholarship Providers, and School Adminstratives should support this student."
                   
                   )
    elif predicted_score < 75.0:
        risk_status = "Moderate Risk"
        message = ("Studying more time, checking  courseworks, and other study materials is recommended to do better. "
                   "School should provide enough study materials, longer library access, and other resources for this student "
                   "to succeed in final exam."
                   )
    else:
        risk_status = "On Track"
        message = ("Student is doing well, and to keep this good progress up, better to take more study hours and read study materials."
                   "School should work closely with this student so that he can support his peers, team work and others"
                   )

    return PredictionResponse(
        predicted_total_score=predicted_score,
        risk_status=risk_status,
        message=message,
    )


@app.post("/retrain", tags=["Retraining"])
async def retrain_model(file: UploadFile = File(..., description="CSV file containing new student records")):
    global model_pipeline

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file.")

    if model_pipeline is None:
        try:
            model_pipeline = load_model_pipeline()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Cannot load existing pipeline: {str(exc)}")

    contents = await file.read()
    model_pipeline, result = retrain_model_from_csv(
        model_pipeline=model_pipeline,
        contents=contents,
        model_path=MODEL_PATH,
        feature_columns=FEATURE_COLUMNS,
        target_column=TARGET_COLUMN,
    )
    return result


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("prediction:app", host="0.0.0.0", port=port, reload=True)