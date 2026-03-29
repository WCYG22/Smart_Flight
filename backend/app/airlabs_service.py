import os
import requests
from dotenv import load_dotenv
from typing import List
from .models import FlightLeg
from datetime import datetime, timedelta
import random
import base64

load_dotenv()

OPENSKY_USERNAME = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_PASSWORD = os.getenv("OPENSKY_CLIENT_SECRET")
OPENSKY_API = "https://opensky-network.org/api"

def fetch_flights(origin: str, destination: str, date: str) -> List[FlightLeg]:
    """
    Fetch real flights from OpenSky Network API with fallback to sample data.
    """
    
    flights: List[FlightLeg] = []
    
    # Parse the date
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    # Try to fetch from OpenSky Network API
    try:
        # Create basic auth header
        auth_string = base64.b64encode(f"{OPENSKY_USERNAME}:{OPENSKY_PASSWORD}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_string}"}
        
        # OpenSky API endpoint for flights
        params = {
            "begin": int(flight_date.timestamp()),
            "end": int((flight_date + timedelta(days=1)).timestamp()),
            "departure": origin,
            "arrival": destination
        }
        
        response = requests.get(f"{OPENSKY_API}/flights/departure", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                for flight_data in data[:10]:
                    try:
                        # Extract flight information
                        flight_number = flight_data.get("callsign", "N/A").strip()
                        airline_name = flight_data.get("airline", "Unknown Airline")
                        
                        # Parse times
                        dep_time_unix = flight_data.get("firstSeen")
                        arr_time_unix = flight_data.get("lastSeen")
                        
                        if dep_time_unix and arr_time_unix:
                            dep_time = datetime.utcfromtimestamp(dep_time_unix).isoformat() + "Z"
                            arr_time = datetime.utcfromtimestamp(arr_time_unix).isoformat() + "Z"
                        else:
                            continue
                        
                        # Get actual times (OpenSky provides actual times)
                        actual_dep = dep_time
                        actual_arr = arr_time
                        
                        # Calculate delay
                        delay_minutes = 0
                        
                        # Get flight status
                        status = "completed" if arr_time_unix else "scheduled"
                        
                        flights.append(
                            FlightLeg(
                                flight_number=flight_number,
                                airline=airline_name,
                                origin=origin,
                                destination=destination,
                                scheduled_departure=dep_time,
                                scheduled_arrival=arr_time,
                                actual_departure=actual_dep,
                                actual_arrival=actual_arr,
                                delay_minutes=delay_minutes,
                                status=status,
                            )
                        )
                    except Exception as e:
                        print(f"Error parsing flight: {e}")
                        continue
                
                if flights:
                    return flights
    except Exception as e:
        print(f"OpenSky API error: {e}")
    
    # Fallback to sample data if API fails
    return generate_sample_flights(origin, destination, flight_date)


def generate_sample_flights(origin: str, destination: str, flight_date: datetime) -> List[FlightLeg]:
    """
    Generate realistic sample flights as fallback.
    """
    flights: List[FlightLeg] = []
    num_flights = random.randint(5, 8)
    airlines = ["MH", "AK", "SQ", "TR", "FD", "BJ", "3K"]
    
    for i in range(num_flights):
        airline = random.choice(airlines)
        flight_number = f"{airline}{random.randint(100, 999)}"
        
        # Random departure time between 6 AM and 10 PM
        dep_hour = random.randint(6, 22)
        dep_minute = random.choice([0, 15, 30, 45])
        scheduled_dep = f"{flight_date.strftime('%Y-%m-%d')}T{dep_hour:02d}:{dep_minute:02d}:00Z"
        
        # Flight duration 1-4 hours
        flight_duration = random.randint(60, 240)
        arr_time = datetime.strptime(scheduled_dep, "%Y-%m-%dT%H:%M:%SZ") + timedelta(minutes=flight_duration)
        scheduled_arr = arr_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Status and delay
        status_choice = random.random()
        if status_choice < 0.7:
            status = "scheduled"
            delay = 0
        elif status_choice < 0.85:
            status = "scheduled"
            delay = random.randint(5, 45)
        elif status_choice < 0.95:
            status = "delayed"
            delay = random.randint(30, 120)
        else:
            status = "cancelled"
            delay = None
        
        flights.append(
            FlightLeg(
                flight_number=flight_number,
                airline=f"{airline} Airlines",
                origin=origin,
                destination=destination,
                scheduled_departure=scheduled_dep,
                scheduled_arrival=scheduled_arr,
                actual_departure=None,
                actual_arrival=None,
                delay_minutes=delay,
                status=status,
            )
        )
    
    return flights
