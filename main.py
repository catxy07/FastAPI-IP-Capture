from fastapi import FastAPI, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db import get_db, engine, Base
from models import Location

app = FastAPI(title="Live Location Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.post("/")
async def visit(request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)

    # Store as a location row with dummy values OR create a separate visitors table (better)
    loc = Location(user_id="visitor", lat=0.0, lng=0.0, ip_address=ip)
    db.add(loc)
    db.commit()
    return {"status": "ok", "ip": ip}


def get_client_ip(request: Request) -> str:
    # If behind proxy (nginx/cloudflare), x-forwarded-for may exist
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@app.post("/save-location")
async def save_location(
    request: Request,
    uid: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)

    loc = Location(user_id=uid, lat=lat, lng=lng, ip_address=ip)
    db.add(loc)
    db.commit()
    return {"status": "ok", "ip": ip}

@app.get("/fetch-locations")
async def fetch_locations(db: Session = Depends(get_db)):
    rows = (
        db.query(Location.user_id, Location.lat, Location.lng, Location.ip_address)
        .distinct(Location.user_id)
        .order_by(Location.user_id, desc(Location.id))
        .all()
    )
    return [
        {"user_id": r[0], "lat": r[1], "lng": r[2], "ip_address": r[3]}
        for r in rows
    ]
