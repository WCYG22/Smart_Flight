from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from schemas import SearchRequest, SearchResponse, FlightLegSchema
from airlabs_service import fetch_flights
from risk_calculator import compute_risk

app = FastAPI(title="SmartFlight – Phase 1 Prototype")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search", response_model=SearchResponse)
def search_flights(req: SearchRequest):
    try:
        legs = fetch_flights(req.origin, req.destination, req.date)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AviationStack error: {e}")

    flights: List[FlightLegSchema] = []

    for leg in legs[:10]:  # limit for demo
        prob, reliability, level = compute_risk(leg)

        flights.append(
            FlightLegSchema(
                flight_number=leg.flight_number,
                airline=leg.airline,
                origin=leg.origin,
                destination=leg.destination,
                scheduled_departure=leg.scheduled_departure,
                scheduled_arrival=leg.scheduled_arrival,
                actual_departure=leg.actual_departure,
                actual_arrival=leg.actual_arrival,
                delay_minutes=leg.delay_minutes,
                status=leg.status,
                disruption_probability=prob,
                reliability_score=reliability,
                risk_level=level,
            )
        )

    return SearchResponse(
        origin=req.origin,
        destination=req.destination,
        date=req.date,
        flights=flights
    )
