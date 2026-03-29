"""
Alternative routing suggestions engine.
Generates safer alternative routes when a selected itinerary is high-risk.
"""

from typing import List, Dict, Tuple
from .models import FlightLeg
from .risk_calculator import compute_risk
from datetime import datetime, timedelta
import random


def find_alternative_routes(
    origin: str,
    destination: str,
    date: str,
    current_risk_level: str,
    available_flights: List[FlightLeg],
    max_alternatives: int = 3
) -> List[Dict]:
    """
    Find alternative routes that are safer than the current high-risk itinerary.
    
    Strategies:
    1. Direct flights (if available) - lowest risk
    2. Different airlines - may have better reliability
    3. Different connection airports - avoid congested hubs
    4. Different departure times - avoid peak hours
    """
    
    alternatives = []
    
    # Strategy 1: Prioritize direct flights
    direct_flights = [f for f in available_flights if f.origin == origin and f.destination == destination]
    direct_flights_sorted = sorted(
        direct_flights,
        key=lambda f: compute_risk(f)[0]  # Sort by disruption probability (lower is better)
    )
    
    for flight in direct_flights_sorted[:2]:
        prob, reliability, level = compute_risk(flight)
        if level.lower() != current_risk_level.lower():  # Only if different risk level
            alternatives.append({
                "type": "direct",
                "flights": [flight],
                "reason": "Direct flight with better reliability",
                "disruption_probability": prob,
                "reliability_score": reliability,
                "risk_level": level,
                "total_duration_minutes": calculate_duration(flight.scheduled_departure, flight.scheduled_arrival)
            })
    
    # Strategy 2: Different airlines (if current is high-risk)
    if current_risk_level.lower() == "high":
        airline_groups = {}
        for flight in available_flights:
            airline = flight.airline
            if airline not in airline_groups:
                airline_groups[airline] = []
            airline_groups[airline].append(flight)
        
        # Get best flight from each airline
        for airline, flights in airline_groups.items():
            best_flight = min(flights, key=lambda f: compute_risk(f)[0])
            prob, reliability, level = compute_risk(best_flight)
            
            if level.lower() in ["low", "medium"]:  # Only suggest if better
                alternatives.append({
                    "type": "different_airline",
                    "flights": [best_flight],
                    "reason": f"Try {airline} - better on-time performance",
                    "disruption_probability": prob,
                    "reliability_score": reliability,
                    "risk_level": level,
                    "total_duration_minutes": calculate_duration(best_flight.scheduled_departure, best_flight.scheduled_arrival)
                })
    
    # Strategy 3: Different departure times (avoid peak hours)
    if current_risk_level.lower() in ["high", "medium"]:
        # Group flights by departure hour
        time_groups = {}
        for flight in available_flights:
            try:
                dep_time = datetime.fromisoformat(flight.scheduled_departure.replace('Z', '+00:00'))
                hour = dep_time.hour
                if hour not in time_groups:
                    time_groups[hour] = []
                time_groups[hour].append(flight)
            except:
                continue
        
        # Find off-peak hours (early morning or late evening)
        off_peak_hours = [6, 7, 8, 19, 20, 21, 22]
        for hour in off_peak_hours:
            if hour in time_groups:
                best_flight = min(time_groups[hour], key=lambda f: compute_risk(f)[0])
                prob, reliability, level = compute_risk(best_flight)
                
                if level.lower() in ["low", "medium"]:
                    dep_time = datetime.fromisoformat(best_flight.scheduled_departure.replace('Z', '+00:00'))
                    alternatives.append({
                        "type": "different_time",
                        "flights": [best_flight],
                        "reason": f"Off-peak departure at {dep_time.strftime('%H:%M')} - typically more reliable",
                        "disruption_probability": prob,
                        "reliability_score": reliability,
                        "risk_level": level,
                        "total_duration_minutes": calculate_duration(best_flight.scheduled_departure, best_flight.scheduled_arrival)
                    })
                    break
    
    # Sort alternatives by reliability score (highest first)
    alternatives.sort(key=lambda x: x["reliability_score"], reverse=True)
    
    # Return top N alternatives
    return alternatives[:max_alternatives]


def calculate_duration(dep_time_str: str, arr_time_str: str) -> int:
    """Calculate flight duration in minutes."""
    try:
        dep = datetime.fromisoformat(dep_time_str.replace('Z', '+00:00'))
        arr = datetime.fromisoformat(arr_time_str.replace('Z', '+00:00'))
        duration = (arr - dep).total_seconds() / 60
        return int(duration)
    except:
        return 0


def get_route_recommendations(
    origin: str,
    destination: str,
    date: str,
    available_flights: List[FlightLeg]
) -> Dict:
    """
    Get comprehensive route recommendations including:
    - Best overall itinerary
    - Cheapest option (if price data available)
    - Fastest option
    - Most reliable option
    """
    
    if not available_flights:
        return {}
    
    recommendations = {}
    
    # Most reliable
    most_reliable = min(available_flights, key=lambda f: compute_risk(f)[0])
    prob, reliability, level = compute_risk(most_reliable)
    recommendations["most_reliable"] = {
        "flight": most_reliable,
        "reason": "Highest reliability score based on historical data",
        "disruption_probability": prob,
        "reliability_score": reliability,
        "risk_level": level
    }
    
    # Fastest
    fastest = min(
        available_flights,
        key=lambda f: calculate_duration(f.scheduled_departure, f.scheduled_arrival)
    )
    prob, reliability, level = compute_risk(fastest)
    recommendations["fastest"] = {
        "flight": fastest,
        "reason": "Shortest total travel time",
        "disruption_probability": prob,
        "reliability_score": reliability,
        "risk_level": level,
        "duration_minutes": calculate_duration(fastest.scheduled_departure, fastest.scheduled_arrival)
    }
    
    # Best balance (reliability + speed)
    best_balance = min(
        available_flights,
        key=lambda f: (
            compute_risk(f)[0] * 0.6 +  # 60% weight on reliability
            (calculate_duration(f.scheduled_departure, f.scheduled_arrival) / 1000) * 0.4  # 40% weight on speed
        )
    )
    prob, reliability, level = compute_risk(best_balance)
    recommendations["best_balance"] = {
        "flight": best_balance,
        "reason": "Best balance between reliability and travel time",
        "disruption_probability": prob,
        "reliability_score": reliability,
        "risk_level": level,
        "duration_minutes": calculate_duration(best_balance.scheduled_departure, best_balance.scheduled_arrival)
    }
    
    return recommendations
