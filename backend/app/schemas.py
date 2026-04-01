from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    origin: str        # IATA
    destination: str   # IATA
    date: str          # YYYY-MM-DD

class MultiLegSearchRequest(BaseModel):
    legs: List[dict]   # [{"origin": "KUL", "destination": "SIN"}, ...]
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

class ConnectionSchema(BaseModel):
    connection_time_minutes: int
    connection_risk: str
    is_safe: bool

class ItinerarySchema(BaseModel):
    flights: List[FlightLegSchema]
    connections: List[ConnectionSchema]
    overall_risk_level: str
    overall_reliability_score: int
    overall_disruption_probability: float
    rank: Optional[int] = None
    rank_label: Optional[str] = None
    ranking_score: Optional[float] = None
    journey_duration_minutes: Optional[int] = None
    num_stops: Optional[int] = None

class SearchResponse(BaseModel):
    origin: str
    destination: str
    date: str
    flights: List[FlightLegSchema]

class MultiLegSearchResponse(BaseModel):
    itineraries: List[ItinerarySchema]

