import os
import requests
from dotenv import load_dotenv
from typing import List
from .models import FlightLeg
from datetime import datetime, timedelta

load_dotenv()
FLIGHTLABS_KEY = os.getenv("FLIGHTLABS_KEY")

BASE_URL = "https://api.flightlabs.io/v1/flights"

def fetch_flights(origin: str, destination: str, date: str) -> List[FlightLeg]:
    """
    Fetch real flights from FlightLabs API.
    """
    
    flights: List[FlightLeg] = []
    
    if not FLIGHTLABS_KEY:
        raise RuntimeError("FLIGHTLABS_KEY not set in environment")
    
    # Parse the date
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    try:
        # Query FlightLabs API
        params = {
            "access_key": FLIGHTLABS_KEY,
            "dep_iata": origin,
            "arr_iata": destination,
            "flight_date": date
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        raw_flights = data.get("data", []) or []
        
        if not raw_flights:
            return flights
        
        # Extract flight information
        for flight in raw_flights:
            flight_number = flight.get("flight_number") or flight.get("flight_iata") or "N/A"
            airline_name = flight.get("airline_name") or "Unknown"
            
            # Get times
            scheduled_dep = flight.get("departure_scheduled")
            actual_dep = flight.get("departure_actual")
            scheduled_arr = flight.get("arrival_scheduled")
            actual_arr = flight.get("arrival_actual")
            
            # Get status and delay
            status = flight.get("flight_status") or "scheduled"
            delay_minutes = flight.get("departure_delay")
            
            flights.append(
                FlightLeg(
                    flight_number=flight_number,
                    airline=airline_name,
                    origin=origin,
                    destination=destination,
                    scheduled_departure=scheduled_dep,
                    scheduled_arrival=scheduled_arr,
                    actual_departure=actual_dep,
                    actual_arrival=actual_arr,
                    delay_minutes=delay_minutes,
                    status=status,
                )
            )
        
        return flights[:10]  # Limit to 10 flights
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"FlightLabs API error: {str(e)}")
