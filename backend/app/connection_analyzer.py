from .models import FlightLeg
from datetime import datetime

def analyze_connection(arrival_flight: FlightLeg, departure_flight: FlightLeg) -> dict:
    """
    Analyze connection safety between two flights.
    
    Returns:
    - connection_time_minutes: Time between arrival and next departure
    - connection_risk: Low/Medium/High based on connection time
    - is_safe: Boolean indicating if connection is feasible
    """
    
    try:
        # Parse times - handle both formats
        arr_str = arrival_flight.scheduled_arrival
        dep_str = departure_flight.scheduled_departure
        
        if not arr_str or not dep_str:
            return {
                "connection_time_minutes": 120,
                "connection_risk": "Medium",
                "is_safe": True
            }
        
        # Try parsing with Z suffix
        if arr_str.endswith('Z'):
            arr_time = datetime.fromisoformat(arr_str.replace('Z', '+00:00'))
        else:
            arr_time = datetime.fromisoformat(arr_str)
            
        if dep_str.endswith('Z'):
            dep_time = datetime.fromisoformat(dep_str.replace('Z', '+00:00'))
        else:
            dep_time = datetime.fromisoformat(dep_str)
        
        # Calculate connection time in minutes
        connection_time = (dep_time - arr_time).total_seconds() / 60
        
        # Determine risk level
        if connection_time < 180:  # Less than 3 hours
            risk = "Low"
            is_safe = True
        elif connection_time < 300:  # 3-5 hours
            risk = "Medium"
            is_safe = True
        else:  # More than 5 hours
            risk = "High"
            is_safe = False
        
        return {
            "connection_time_minutes": int(connection_time),
            "connection_risk": risk,
            "is_safe": is_safe
        }
    except Exception as e:
        print(f"Connection analysis error: {e}")
        return {
            "connection_time_minutes": 120,
            "connection_risk": "Medium",
            "is_safe": True
        }


def calculate_itinerary_risk(flights: list, individual_risks: list) -> dict:
    """
    Calculate overall itinerary risk based on:
    - Individual flight risks
    - Connection safety
    
    Returns overall risk level and reliability score
    """
    
    if not flights or not individual_risks:
        return {"risk_level": "Unknown", "reliability_score": 0}
    
    # Average individual flight risks
    avg_disruption_prob = sum(r["disruption_probability"] for r in individual_risks) / len(individual_risks)
    
    # Check connections
    connection_risks = []
    for i in range(len(flights) - 1):
        conn = analyze_connection(flights[i], flights[i + 1])
        connection_risks.append(conn)
    
    # Increase risk if any connection is risky
    if connection_risks:
        risky_connections = sum(1 for c in connection_risks if c["connection_risk"] == "High")
        avg_disruption_prob += (risky_connections * 0.2)  # Add 20% per risky connection
    
    # Cap at 1.0
    avg_disruption_prob = min(avg_disruption_prob, 1.0)
    
    # Determine overall risk level
    if avg_disruption_prob < 0.3:
        level = "Low"
    elif avg_disruption_prob < 0.6:
        level = "Medium"
    else:
        level = "High"
    
    reliability = int((1 - avg_disruption_prob) * 100)
    
    return {
        "risk_level": level,
        "reliability_score": reliability,
        "disruption_probability": round(avg_disruption_prob, 2),
        "connections": connection_risks
    }
