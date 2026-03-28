from dataclasses import dataclass
from typing import Optional

@dataclass
class FlightLeg:
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
