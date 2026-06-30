# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

RAW_DATA_PATH = "data/raw/patients_raw.csv"
ANON_DATA_PATH = "data/processed/patients_anonymized.csv"


# --- ENDPOINT 1: Chỉ admin được đọc raw PII ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về 10 records raw đầu tiên (chỉ admin)."""
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        return JSONResponse(content=df.head(10).to_dict(orient="records"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found. Run generate_data.py first.")


# --- ENDPOINT 2: ml_engineer và admin được đọc anonymized data ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về anonymized patient data."""
    try:
        # Dùng cached anonymized data nếu có
        try:
            df = pd.read_csv(ANON_DATA_PATH)
        except FileNotFoundError:
            # Anonymize on-the-fly
            raw_df = pd.read_csv(RAW_DATA_PATH)
            df = anonymizer.anonymize_dataframe(raw_df)
            df.to_csv(ANON_DATA_PATH, index=False)

        return JSONResponse(content=df.head(10).to_dict(orient="records"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found. Run generate_data.py first.")


# --- ENDPOINT 3: data_analyst, ml_engineer, admin đọc aggregated metrics ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Trả về aggregated metrics không chứa PII."""
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        metrics = {
            "total_patients": int(len(df)),
            "benh_distribution": df["benh"].value_counts().to_dict(),
            "avg_ket_qua_xet_nghiem": round(float(df["ket_qua_xet_nghiem"].mean()), 2),
            "min_ket_qua": round(float(df["ket_qua_xet_nghiem"].min()), 2),
            "max_ket_qua": round(float(df["ket_qua_xet_nghiem"].max()), 2),
        }
        return JSONResponse(content=metrics)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found. Run generate_data.py first.")


# --- ENDPOINT 4: Chỉ admin được xóa patient ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Xóa patient record (chỉ admin). Các role khác nhận 403."""
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        if patient_id not in df["patient_id"].values:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

        df = df[df["patient_id"] != patient_id]
        df.to_csv(RAW_DATA_PATH, index=False)
        return {"message": f"Patient {patient_id} deleted", "deleted_by": current_user["username"]}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found.")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
