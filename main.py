from fastapi import FastAPI, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError

from db import get_db, engine, Base
from models import Location, Visitor

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

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ DB ready")
    except OperationalError as e:
        print("❌ DB error:", e)

# ✅ AUTO STORE IP ON VISIT
@app.get("/")
async def visit(request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    db.add(Visitor(ip_address=ip))
    db.commit()
    return {"status": "ok"}

# 🔴 SAVE LOCATION (optional: also stores IP with location row)
@app.post("/save-location")
async def save_location(
    request: Request,
    uid: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)

    db.add(Location(user_id=uid, lat=lat, lng=lng, ip_address=ip))
    db.commit()
    return {"status": "ok"}

# 🟢 FETCH: latest locations + ALL visited IPs
@app.get("/fetch-locations")
async def fetch_locations(db: Session = Depends(get_db)):
    # latest location per user
    loc_rows = (
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

    locations = [
        {
            "user_id": r[0],
            "lat": r[1],
            "lng": r[2],
            "last_ip": r[3],
            "time": r[4],
        }
        for r in loc_rows
    ]

    # all visitors IPs (latest first)
    vis_rows = (
        db.query(Visitor.ip_address, Visitor.time)
        .order_by(desc(Visitor.id))
        .all()
    )

    visitors = [{"ip_address": v[0], "time": v[1]} for v in vis_rows]

    return {
        "locations": locations,
        "visitors": visitors
    }
