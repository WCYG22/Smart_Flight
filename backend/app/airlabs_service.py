import os
import requests
from dotenv import load_dotenv
from typing import List
from .models import FlightLeg
from datetime import datetime, timedelta
import random

load_dotenv()

FLIGHTLABS_KEY = os.getenv("FLIGHTLABS_KEY")
FLIGHTLABS_API = "https://app.goflightlabs.com/advanced-flights-schedules"

def fetch_flights(origin: str, destination: str, date: str) -> List[FlightLeg]:
    """
    Fetch real flights from FlightLabs API with fallback to sample data.
    """
    
    flights: List[FlightLeg] = []
    
    # Parse the date
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    # Try to fetch from FlightLabs API
    try:
        params = {
            "api_key": FLIGHTLABS_KEY,
            "dep_iata": origin,
            "arr_iata": destination,
            "flight_date": date
        }
        
        response = requests.get(FLIGHTLABS_API, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success") and data.get("data"):
                for flight_data in data.get("data", [])[:10]:
                    try:
                        # Extract flight information
                        flight_number = flight_data.get("flight_iata", "N/A")
                        airline_name = flight_data.get("airline_name", "Unknown Airline")
                        
                        # Parse times
                        dep_time = flight_data.get("departure", {}).get("scheduled")
                        arr_time = flight_data.get("arrival", {}).get("scheduled")
                        
                        # Get actual times if available
                        actual_dep = flight_data.get("departure", {}).get("actual")
                        actual_arr = flight_data.get("arrival", {}).get("actual")
                        
                        # Calculate delay if actual time exists
                        delay_minutes = None
                        if actual_dep and dep_time:
                            try:
                                dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
                                actual_dep_dt = datetime.fromisoformat(actual_dep.replace('Z', '+00:00'))
                                delay_minutes = int((actual_dep_dt - dep_dt).total_seconds() / 60)
                            except:
                                pass
                        
                        # Get flight status
                        status = flight_data.get("status", "scheduled")
                        
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
        print(f"FlightLabs API error: {e}")
    
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
