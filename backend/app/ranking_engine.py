"""
Itinerary Ranking Engine (F007)
Orders itineraries using weighted scoring that balances:
- Reliability (disruption + connection risks)
- Total journey time
- Number of stops
"""

from typing import List, Dict
from datetime import datetime


def calculate_ranking_score(itinerary: Dict) -> float:
    """
    Calculate a composite ranking score for an itinerary.
    
    Weights:
    - Reliability: 50% (most important)
    - Journey Time: 30% (shorter is better)
    - Number of Stops: 20% (fewer is better)
    
    Returns a score between 0-100 (higher is better)
    """
    
    reliability_score = itinerary.get("overall_reliability_score", 50)
    disruption_prob = itinerary.get("overall_disruption_probability", 0.5)
    
    # Calculate reliability component (0-100)
    # Higher reliability score = higher ranking
    reliability_component = reliability_score * 0.5
    
    # Calculate journey time component (0-100)
    # Normalize based on typical flight duration (assume 24 hours max)
    journey_minutes = calculate_journey_duration(itinerary)
    journey_hours = journey_minutes / 60
    max_hours = 24
    time_component = max(0, (1 - (journey_hours / max_hours)) * 100) * 0.3
    
    # Calculate stops component (0-100)
    # Fewer stops = higher score
    num_stops = len(itinerary.get("flights", [])) - 1
    max_stops = 3
    stops_component = max(0, (1 - (num_stops / max_stops)) * 100) * 0.2
    
    # Composite score
    total_score = reliability_component + time_component + stops_component
    
    return round(total_score, 2)


def calculate_journey_duration(itinerary: Dict) -> int:
    """Calculate total journey duration in minutes."""
    try:
        flights = itinerary.get("flights", [])
        if not flights:
            return 0
        
        first_flight = flights[0]
        last_flight = flights[-1]
        
        dep_time = datetime.fromisoformat(
            first_flight.get("scheduled_departure", "").replace('Z', '+00:00')
        )
        arr_time = datetime.fromisoformat(
            last_flight.get("scheduled_arrival", "").replace('Z', '+00:00')
        )
        
        duration = (arr_time - dep_time).total_seconds() / 60
        return int(duration)
    except:
        return 0


def rank_itineraries(itineraries: List[Dict]) -> List[Dict]:
    """
    Rank itineraries by composite score and add ranking metadata.
    
    Returns itineraries sorted by score (highest first) with ranking info.
    """
    
    # Calculate scores for each itinerary
    scored_itineraries = []
    for idx, itinerary in enumerate(itineraries):
        score = calculate_ranking_score(itinerary)
        journey_duration = calculate_journey_duration(itinerary)
        num_stops = len(itinerary.get("flights", [])) - 1
        
        scored_itineraries.append({
            **itinerary,
            "ranking_score": score,
            "journey_duration_minutes": journey_duration,
            "num_stops": num_stops,
            "original_index": idx
        })
    
    # Sort by ranking score (highest first)
    ranked = sorted(scored_itineraries, key=lambda x: x["ranking_score"], reverse=True)
    
    # Add rank position
    for rank, itinerary in enumerate(ranked, 1):
        itinerary["rank"] = rank
        itinerary["rank_label"] = get_rank_label(rank)
    
    return ranked


def get_rank_label(rank: int) -> str:
    """Get a descriptive label for the rank position."""
    if rank == 1:
        return "🏆 Best Option"
    elif rank == 2:
        return "⭐ Great Choice"
    elif rank == 3:
        return "✨ Good Option"
    else:
        return f"#{rank}"
