from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {
        "access_token": "token123",
        "refresh_token": "refresh123",
        "token_type": "bearer",
        "role": "patient",
        "email": form_data.username
    }

@app.get("/patient/profile")
async def patient_profile():
    return {
        "surname": "Петров",
        "name": "Александр",
        "patronim": "Иванович",
        "birth_date": "1980-01-01",
        "gender": "м",
        "height": 175,
        "weight": 80,
        "email": "Петров.Александр.Иванович@mail.ru",
        "phone": "+7 (999) 123-45-67"
    }

@app.get("/patient/measurements")
async def patient_measurements():
    return []

@app.post("/patient/measurements")
async def add_measurement():
    return {"status": "ok"}

@app.get("/patient/prescriptions")
async def patient_prescriptions():
    return []

@app.get("/patient/complaints")
async def patient_complaints():
    return []

@app.post("/patient/complaints")
async def add_complaint():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("api:app", port=5000)