from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    origin: str        # IATA
    destination: str   # IATA
    date: str          # YYYY-MM-DD

class FlightLegSchema(BaseModel):
    flight_number: str
    airline: str
    origin: str
    destination: str
    scheduled_departure: Optional[str]
    scheduled_arrival: Optional[str]
    actual_departure: Optional[str]
    actual_arrival: Optional[str]
    delay_minutes: Optional[int]
    status: Optional[str]
    disruption_probability: float
    reliability_score: int
    risk_level: str

class SearchResponse(BaseModel):
    origin: str
    destination: str
    date: str
    flights: List[FlightLegSchema]
