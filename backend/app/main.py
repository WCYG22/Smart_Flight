from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from .schemas import SearchRequest, SearchResponse, FlightLegSchema, MultiLegSearchRequest, MultiLegSearchResponse, ItinerarySchema, ConnectionSchema
from .airlabs_service import fetch_flights
from .risk_calculator import compute_risk
from .connection_analyzer import analyze_connection, calculate_itinerary_risk
from .alternative_routes import find_alternative_routes, get_route_recommendations
from .ranking_engine import rank_itineraries
from .itinerary_manager import generate_itinerary_summary, export_itinerary_json, export_itinerary_csv, export_itinerary_html
from .email_service import send_itinerary_email

app = FastAPI(title="SmartFlight – Phase 2 Multi-Leg")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search", response_model=SearchResponse)
def search_flights(req: SearchRequest):
    try:
        legs = fetch_flights(req.origin, req.destination, req.date)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")

    flights: List[FlightLegSchema] = []

    for leg in legs[:10]:
        prob, reliability, level = compute_risk(leg)

        flights.append(
            FlightLegSchema(
                flight_number=leg.flight_number,
                airline=leg.airline,
                origin=leg.origin,
                destination=leg.destination,
                scheduled_departure=leg.scheduled_departure,
                scheduled_arrival=leg.scheduled_arrival,
                actual_departure=leg.actual_departure,
                actual_arrival=leg.actual_arrival,
                delay_minutes=leg.delay_minutes,
                status=leg.status,
                disruption_probability=prob,
                reliability_score=reliability,
                risk_level=level,
            )
        )

    return SearchResponse(
        origin=req.origin,
        destination=req.destination,
        date=req.date,
        flights=flights
    )


@app.post("/search-itinerary", response_model=MultiLegSearchResponse)
def search_multi_leg(req: MultiLegSearchRequest):
    """
    Search for multi-leg itineraries with connection risk analysis.
    F007: Itinerary Ranking Engine - Results are ranked by composite score
    F008: Ranked Results Display - Best options appear at top
    """
    try:
        if len(req.legs) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 legs allowed")
        
        itineraries_data: List[Dict] = []
        
        # Generate 3-5 sample itineraries
        num_itineraries = 4
        
        for _ in range(num_itineraries):
            all_flights: List[FlightLegSchema] = []
            all_flight_legs: List = []
            individual_risks = []
            
            # Fetch flights for each leg
            for leg_idx, leg in enumerate(req.legs):
                leg_flights = fetch_flights(leg["origin"], leg["destination"], req.date)
                
                if not leg_flights:
                    continue
                
                # Pick first flight for this leg
                selected_flight = leg_flights[0]
                all_flight_legs.append(selected_flight)
                
                prob, reliability, level = compute_risk(selected_flight)
                individual_risks.append({
                    "disruption_probability": prob,
                    "reliability_score": reliability,
                    "risk_level": level
                })
                
                all_flights.append(
                    FlightLegSchema(
                        flight_number=selected_flight.flight_number,
                        airline=selected_flight.airline,
                        origin=selected_flight.origin,
                        destination=selected_flight.destination,
                        scheduled_departure=selected_flight.scheduled_departure,
                        scheduled_arrival=selected_flight.scheduled_arrival,
                        actual_departure=selected_flight.actual_departure,
                        actual_arrival=selected_flight.actual_arrival,
                        delay_minutes=selected_flight.delay_minutes,
                        status=selected_flight.status,
                        disruption_probability=prob,
                        reliability_score=reliability,
                        risk_level=level,
                    )
                )
            
            # Calculate itinerary risk
            itinerary_risk = calculate_itinerary_risk(all_flight_legs, individual_risks)
            
            # Build connection schemas
            connections: List[ConnectionSchema] = []
            for conn in itinerary_risk.get("connections", []):
                connections.append(
                    ConnectionSchema(
                        connection_time_minutes=conn["connection_time_minutes"],
                        connection_risk=conn["connection_risk"],
                        is_safe=conn["is_safe"]
                    )
                )
            
            itinerary_dict = {
                "flights": [f.dict() for f in all_flights],
                "connections": [c.dict() for c in connections],
                "overall_risk_level": itinerary_risk["risk_level"],
                "overall_reliability_score": itinerary_risk["reliability_score"],
                "overall_disruption_probability": itinerary_risk["disruption_probability"]
            }
            
            itineraries_data.append(itinerary_dict)
        
        # F007: Rank itineraries by composite score
        ranked_itineraries = rank_itineraries(itineraries_data)
        
        # Convert to response format
        itineraries: List[ItinerarySchema] = []
        for ranked_item in ranked_itineraries:
            flights_list = []
            for flight_data in ranked_item["flights"]:
                flights_list.append(FlightLegSchema(**flight_data))
            
            connections_list = []
            for conn_data in ranked_item["connections"]:
                connections_list.append(ConnectionSchema(**conn_data))
            
            itineraries.append(
                ItinerarySchema(
                    flights=flights_list,
                    connections=connections_list,
                    overall_risk_level=ranked_item["overall_risk_level"],
                    overall_reliability_score=ranked_item["overall_reliability_score"],
                    overall_disruption_probability=ranked_item["overall_disruption_probability"],
                    rank=ranked_item.get("rank"),
                    rank_label=ranked_item.get("rank_label"),
                    ranking_score=ranked_item.get("ranking_score"),
                    journey_duration_minutes=ranked_item.get("journey_duration_minutes"),
                    num_stops=ranked_item.get("num_stops")
                )
            )
        
        return MultiLegSearchResponse(itineraries=itineraries)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")


@app.post("/alternatives")
def get_alternatives(req: SearchRequest):
    """
    Get alternative route suggestions for a high-risk itinerary.
    UC004: View Alternative Itineraries
    """
    try:
        # Fetch all available flights for this route
        all_flights = fetch_flights(req.origin, req.destination, req.date)
        
        if not all_flights:
            raise HTTPException(status_code=404, detail="No flights found for this route")
        
        # Determine current risk level (assume high-risk if user is asking for alternatives)
        current_risk = "high"
        
        # Find alternatives
        alternatives = find_alternative_routes(
            req.origin,
            req.destination,
            req.date,
            current_risk,
            all_flights,
            max_alternatives=3
        )
        
        # Convert to response format
        alternative_flights = []
        for alt in alternatives:
            flight = alt["flights"][0]
            alternative_flights.append({
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "scheduled_departure": flight.scheduled_departure,
                "scheduled_arrival": flight.scheduled_arrival,
                "status": flight.status,
                "delay_minutes": flight.delay_minutes,
                "disruption_probability": alt["disruption_probability"],
                "reliability_score": alt["reliability_score"],
                "risk_level": alt["risk_level"],
                "reason": alt["reason"],
                "type": alt["type"],
                "duration_minutes": alt.get("total_duration_minutes", 0)
            })
        
        return {
            "origin": req.origin,
            "destination": req.destination,
            "date": req.date,
            "alternatives": alternative_flights,
            "count": len(alternative_flights)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")


@app.post("/recommendations")
def get_recommendations(req: SearchRequest):
    """
    Get route recommendations (best overall, fastest, most reliable).
    Helps users make informed decisions.
    """
    try:
        # Fetch all available flights
        all_flights = fetch_flights(req.origin, req.destination, req.date)
        
        if not all_flights:
            raise HTTPException(status_code=404, detail="No flights found for this route")
        
        # Get recommendations
        recommendations = get_route_recommendations(
            req.origin,
            req.destination,
            req.date,
            all_flights
        )
        
        # Convert to response format
        result = {}
        for rec_type, rec_data in recommendations.items():
            flight = rec_data["flight"]
            result[rec_type] = {
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "scheduled_departure": flight.scheduled_departure,
                "scheduled_arrival": flight.scheduled_arrival,
                "status": flight.status,
                "delay_minutes": flight.delay_minutes,
                "disruption_probability": rec_data["disruption_probability"],
                "reliability_score": rec_data["reliability_score"],
                "risk_level": rec_data["risk_level"],
                "reason": rec_data["reason"],
                "duration_minutes": rec_data.get("duration_minutes", 0)
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")



@app.post("/itinerary-summary")
def get_itinerary_summary(itinerary_data: Dict):
    """
    Get detailed summary for an itinerary (F011).
    """
    try:
        summary = generate_itinerary_summary(itinerary_data)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")


@app.post("/export-itinerary")
def export_itinerary(request: Dict):
    """
    Export itinerary in requested format (F012).
    Formats: json, csv, html
    """
    try:
        itinerary = request.get("itinerary")
        format_type = request.get("format", "json").lower()
        
        if format_type == "json":
            content = export_itinerary_json(itinerary)
            return {
                "success": True,
                "format": "json",
                "content": content,
                "filename": "itinerary.json"
            }
        elif format_type == "csv":
            content = export_itinerary_csv(itinerary)
            return {
                "success": True,
                "format": "csv",
                "content": content,
                "filename": "itinerary.csv"
            }
        elif format_type == "html":
            content = export_itinerary_html(itinerary)
            return {
                "success": True,
                "format": "html",
                "content": content,
                "filename": "itinerary.html"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: json, csv, or html")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")


@app.post("/send-itinerary-email")
def send_itinerary_via_email(request: Dict):
    """
    Send itinerary summary via email (F013).
    """
    try:
        email = request.get("email")
        itinerary = request.get("itinerary")
        subject = request.get("subject", "Your SmartFlight Itinerary")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email address required")
        
        result = send_itinerary_email(email, itinerary, subject)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")


@app.post("/filter-itineraries")
def filter_itineraries(request: Dict):
    """
    Filter and sort itineraries (F010).
    Supports filtering by: risk_level, min_reliability, max_duration, departure_time
    Supports sorting by: reliability, duration, risk, rank
    """
    try:
        itineraries = request.get("itineraries", [])
        filters = request.get("filters", {})
        sort_by = request.get("sort_by", "rank")
        sort_order = request.get("sort_order", "asc")  # asc or desc
        
        # Apply filters
        filtered = itineraries
        
        # Filter by risk level
        if "risk_level" in filters:
            risk_level = filters["risk_level"].lower()
            filtered = [it for it in filtered if it.get("overall_risk_level", "").lower() == risk_level]
        
        # Filter by minimum reliability
        if "min_reliability" in filters:
            min_rel = filters["min_reliability"]
            filtered = [it for it in filtered if it.get("overall_reliability_score", 0) >= min_rel]
        
        # Filter by maximum duration
        if "max_duration_minutes" in filters:
            max_dur = filters["max_duration_minutes"]
            filtered = [it for it in filtered if it.get("journey_duration_minutes", 0) <= max_dur]
        
        # Filter by number of stops
        if "max_stops" in filters:
            max_stops = filters["max_stops"]
            filtered = [it for it in filtered if it.get("num_stops", 0) <= max_stops]
        
        # Apply sorting
        sort_key_map = {
            "rank": lambda x: x.get("rank", 999),
            "reliability": lambda x: x.get("overall_reliability_score", 0),
            "duration": lambda x: x.get("journey_duration_minutes", 0),
            "risk": lambda x: {"low": 0, "medium": 1, "high": 2}.get(x.get("overall_risk_level", "high").lower(), 2),
            "disruption": lambda x: x.get("overall_disruption_probability", 1)
        }
        
        sort_key = sort_key_map.get(sort_by, sort_key_map["rank"])
        reverse = sort_order.lower() == "desc"
        
        filtered.sort(key=sort_key, reverse=reverse)
        
        return {
            "success": True,
            "total_before": len(itineraries),
            "total_after": len(filtered),
            "itineraries": filtered
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
