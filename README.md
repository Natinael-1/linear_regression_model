# Student Academic Performance Checker and Early Warning System

## 1. Mission and Problem

Nowadays, education is expensive and schools are non-inclusive. My mission is to provide quality education and make it accessible to every student in primary and secondary schools regardless of student's background and socioeconomic status in my community. So I developed this Student Academic Performance Tracker and Early Warning System helps to track students performance after mid-term to predict their final cumulative score and provide necessary support like scholarship opportunities, NGO and school admnistration support. 

---

## 2. Dataset Description and Source

This project uses the **Student Performance & Behavior Dataset** (5,000 student records), sourced from Kaggle:

- **Source:** [Student Performance & Behavior Dataset on Kaggle](https://www.kaggle.com/datasets/mahmoudelhemaly/students-grading-dataset)

The regression pipeline predicts a student's final cumulative score (`Total_Score`, bounded between `0.0` and `100.0`) from 8 mid-semester features:

| Feature Column | Type | Allowed Values / Range | Description |
| :--- | :--- | :--- | :--- |
| `Attendance (%)` | Numeric | `0.0` to `100.0` | Class attendance percentage |
| `Midterm_Score` | Numeric | `0.0` to `100.0` | Mid-semester exam score |
| `Assignments_Avg` | Numeric | `0.0` to `100.0` | Average score across assignments |
| `Quizzes_Avg` | Numeric | `0.0` to `100.0` | Average score across quizzes |
| `Projects_Score` | Numeric | `0.0` to `100.0` | Practical projects score |
| `Internet_Access_at_Home` | Categorical | `Yes`, `No` | Home internet availability |
| `Family_Income_Level` | Categorical | `Low`, `Medium`, `High` | Household socioeconomic tier |
| `Parent_Education_Level` | Categorical | `None`, `High School`, `Bachelor's`, `Master's`, `PhD` | Highest formal parental education |

---

## 3. Public API and Swagger UI Documentation

- **Swagger UI:** https://student-academic-performance-checker.onrender.com/docs
- **Base API URL:** https://student-academic-performance-checker.onrender.com

*Note: This API is hosted on Render's free tier and sleeps after 15 minutes of inactivity. The first request after an idle period can take up to 60 seconds while the server wakes up.*

### Available Endpoints

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/` | Health check confirming the API is online and `best_model.pkl` is loaded. |
| `POST` | `/predict` | Accepts a single student's 8 features as JSON and returns the predicted `Total_Score`, risk classification, and advisory message. |
| `POST` | `/retrain` | Accepts a `.csv` file upload of new student records, incrementally updates the `SGDRegressor` model via `partial_fit`, and returns the updated batch MSE. |

### How to Use the Endpoints in Swagger UI

#### 1. Check Service Status (`GET /`)
1. Open the Swagger UI link above, expand **`GET /`**, click **Try it out**, and click **Execute**.
2. A healthy server returns HTTP `200` with `"status": "online"`, `"model_loaded": true`, and `"active_model_class": "SGDRegressor"`.

#### 2. Predict a Student's Final Score (`POST /predict`)
1. Expand **`POST /predict`** and click **Try it out**.
2. Edit the JSON request body (all numeric scores must be between `0.0` and `100.0`, and categorical strings must match the allowed values exactly):
   ```json
   {
     "attendance": 85.5,
     "midterm_score": 78.0,
     "assignments_avg": 82.0,
     "quizzes_avg": 76.5,
     "projects_score": 88.0,
     "internet_access_at_home": "Yes",
     "family_income_level": "Low",
     "parent_education_level": "High School"
   }
   ```
3. Click **Execute**. FastAPI validates the payload using Pydantic (`StudentPredictionInput`), transforms the features through the saved scikit-learn `Pipeline`, clamps the output to `0.0–100.0`, and returns HTTP `200`:
   ```json
   {
     "predicted_total_score": 78.45,
     "risk_status": "On Track",
     "message": "Student is progressing well toward a strong final cumulative score."
   }
   ```
4. **Risk Classification Rules:**
   - **High Risk:** Predicted score below `60.0`
   - **Moderate Risk:** Predicted score from `60.0` up to `74.99`
   - **On Track:** Predicted score of `75.0` or higher
5. **Validation Behavior:** Submitting out-of-range numbers (e.g., `-5` or `120`) or invalid category names returns HTTP `422 Unprocessable Entity`.

#### 3. Retrain the Model (`POST /retrain`)
1. Prepare a `.csv` file containing raw (unscaled) student records with the 8 feature column headers listed in Section 2 plus `Total_Score`:
   ```csv
   Attendance (%),Midterm_Score,Assignments_Avg,Quizzes_Avg,Projects_Score,Internet_Access_at_Home,Family_Income_Level,Parent_Education_Level,Total_Score
   92.0,85.5,88.0,84.0,91.0,Yes,High,Master's,88.5
   64.5,58.0,61.0,55.5,63.0,No,Low,None,59.2
   ```
   *(Extra columns from the original dataset are safely ignored, and blank `Parent_Education_Level` cells are automatically filled with `"None"`.)*
2. Expand **`POST /retrain`**, click **Try it out**, click **Choose File**, select your `.csv` file, and click **Execute**.
3. The backend parses the file, transforms the new rows with the fitted preprocessor, calls `partial_fit` on `SGDRegressor`, saves `best_model.pkl`, and hot-swaps the active model in memory. A successful call returns HTTP `200`:
   ```json
   {
     "status": "success",
     "message": "Model updated via partial_fit, saved to best_model.pkl.",
     "new_rows_uploaded": 2,
     "mse_on_uploaded_batch": 12.4518
   }
   ```
4. **Validation Behavior:** Uploading a non-`.csv` file or a CSV missing any of the 9 required columns returns HTTP `400 Bad Request`.
5. *Persistence Note:* Because Render's free tier uses an ephemeral filesystem, retrained weights remain active while the server is awake and reset to the committed `best_model.pkl` when the container restarts.

---

## 4. Video Demo

- **YouTube Demo:** [https://youtu.be/_ik5hgd9pe4]

---

## 5. How to Run the Mobile App

### Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) installed and configured in your system `PATH`
- Android Studio or VSC  with an Android Virtual Device (AVD), or a physical Android/iOS device with USB debugging enabled
- Git

### Steps

1. Clone the repository and move into the Flutter app folder:
   ```bash
   git clone [https://github.com/](https://github.com/)<your-github-username>/linear_regression_model.git
   cd linear_regression_model/summative/FlutterApp
   ```

2. Fetch the required Dart and Flutter dependencies:
   ```bash
   flutter pub get
   ```

3. Start your Android emulator (or connect a physical device) and verify that Flutter recognizes it:
   ```bash
   flutter devices
   ```

4. Selec the device and run the application:
   ```bash
   flutter run -d device_name
   ```

6. Enter the student's 5 numeric scores (`0–100`), choose the 3 socioeconomic dropdown options, and tap **Predict Final Score**. Use the top-right refresh button to reset the form for a new prediction.

---

## 6. Repository Structure and Essential Files

```text
linear_regression_model/
├── README.md
└── summative/
    ├── pyproject.toml
    ├── uv.lock
    ├── linear_regression/
    │   └── multivariate.ipynb
    ├── API/
    │   ├── prediction.py
    │   ├── retrain.py
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   └── best_model.pkl
    └── FlutterApp/
        ├── pubspec.yaml
        └── lib/
            └── main.dart
```

### Key File Descriptions

- **`summative/linear_regression/multivariate.ipynb`**: Data exploration, preprocessing pipeline construction (`ColumnTransformer` with scaling and encoding), model training and comparison across regression algorithms, evaluation plots, and serialization of the best-performing `SGDRegressor` pipeline to `best_model.pkl`.
- **`summative/API/prediction.py`**: Main FastAPI application defining CORS rules, Pydantic request/response schemas (`StudentPredictionInput`, `PredictionResponse`), model loading, and the `GET /`, `POST /predict`, and `POST /retrain` endpoints.
- **`summative/API/retrain.py`**: Modular retraining helper imported by `prediction.py` that validates uploaded CSV columns, cleans missing values, updates `SGDRegressor` incrementally via `partial_fit`, computes batch MSE, and saves the updated pipeline to `best_model.pkl`.
- **`summative/API/best_model.pkl`**: Serialized scikit-learn `Pipeline` (`preprocessor` + trained `SGDRegressor`) loaded into memory at API startup.
- **`summative/pyproject.toml` & `summative/uv.lock`**: `uv` dependency manifest and lockfile for the data science notebook environment.
- **`summative/API/pyproject.toml` & `summative/API/uv.lock`**: Isolated `uv` dependency manifest and lockfile used by Render (`summative/API` root directory) to install only the runtime packages needed by the API.
- **`summative/FlutterApp/lib/main.dart`**: Complete Flutter mobile frontend containing input validation (`0.0–100.0`), HTTP `POST` integration with the FastAPI `/predict` endpoint, loading/error states, and color-coded risk cards.

---

## 7. Running the API Locally (Optional)

To run the FastAPI server locally using `uv`:

```bash
cd summative/API
uv sync --locked
uv run uvicorn prediction:app --host 0.0.0.0 --port 8000 --reload
```

Then open `http://127.0.0.1:8000/docs` in your browser to test the endpoints locally.