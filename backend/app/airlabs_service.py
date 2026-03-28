import os
import requests
from dotenv import load_dotenv
from typing import List
from .models import FlightLeg
from datetime import datetime, timedelta

load_dotenv()
FLIGHTLABS_KEY = os.getenv("FLIGHTLABS_KEY")

BASE_URL = "https://app.goflightlabs.com/advanced-flights-schedules"

def fetch_flights(origin: str, destination: str, date: str) -> List[FlightLeg]:
    """
    Fetch real flights from FlightLabs API.
    """
    
    flights: List[FlightLeg] = []
    
    if not FLIGHTLABS_KEY:
        raise RuntimeError("FLIGHTLABS_KEY not set in environment")
    
    try:
        # Query FlightLabs API for departure airport schedules
        params = {
            "access_key": FLIGHTLABS_KEY,
            "iataCode": origin,
            "type": "departure",
            "date": date
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        raw_flights = data.get("data", []) or []
        
        if not raw_flights:
            return flights
        
        # Filter flights by destination and extract information
        for flight in raw_flights:
            # Check if destination matches
            arr_iata = flight.get("arr_iata")
            if arr_iata != destination:
                continue
            
            flight_number = flight.get("flight_iata") or flight.get("flight_number") or "N/A"
            airline_name = flight.get("airline_name") or "Unknown"
            
            # Get times
            scheduled_dep = flight.get("dep_time")
            actual_dep = flight.get("dep_actual")
            scheduled_arr = flight.get("arr_time")
            actual_arr = flight.get("arr_actual")
            
            # Get status and delay
            status = flight.get("status") or "scheduled"
            delay_minutes = flight.get("dep_delayed")
            
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
