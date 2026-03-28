import os
import requests
from dotenv import load_dotenv
from typing import List
from .models import FlightLeg
from datetime import datetime, timedelta
import random

load_dotenv()

def fetch_flights(origin: str, destination: str, date: str) -> List[FlightLeg]:
    """
    Generate realistic sample flights for Phase 2 multi-leg itineraries.
    """
    
    flights: List[FlightLeg] = []
    
    # Parse the date
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    # Generate 5-8 realistic sample flights for this route
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
        
        actual_dep = None
        actual_arr = None
        
        flights.append(
            FlightLeg(
                flight_number=flight_number,
                airline=f"{airline} Airlines",
                origin=origin,
                destination=destination,
                scheduled_departure=scheduled_dep,
                scheduled_arrival=scheduled_arr,
                actual_departure=actual_dep,
                actual_arrival=actual_arr,
                delay_minutes=delay,
                status=status,
            )
        )
    
    return flights
