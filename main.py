from fastapi import FastAPI, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError

from db import get_db, engine, Base
from models import Location

app = FastAPI(title="Live Location Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ✅ Create tables safely
@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ DB ready")
    except OperationalError as e:
        print("❌ DB error:", e)

# ✅ AUTO STORE IP ON VISIT (NO IP SHOWN)
@app.get("/")
async def visit(request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)

    db.add(Location(
        user_id="visitor",
        lat=0.0,
        lng=0.0,
        ip_address=ip
    ))
    db.commit()

    return {"status": "ok"}

# 🔴 SAVE LOCATION (IP STORED, NOT SHOWN)
@app.post("/save-location")
async def save_location(
    request: Request,
    uid: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)

    db.add(Location(
        user_id=uid,
        lat=lat,
        lng=lng,
        ip_address=ip
    ))
    db.commit()

    return {"status": "ok"}

# 🟢 FETCH LATEST LOCATION OF ALL USERS + ALL IPS
@app.get("/fetch-locations")
async def fetch_locations(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Location.user_id,
            Location.lat,
            Location.lng,
            Location.ip_address,
            Location.time
        )
        .distinct(Location.user_id)
        .order_by(Location.user_id, desc(Location.id))
        .all()
    )

    return [
        {
            "user_id": r[0],
            "lat": r[1],
            "lng": r[2],
            "ip_address": r[3],
            "time": r[4],
        }
        for r in rows
    ]
