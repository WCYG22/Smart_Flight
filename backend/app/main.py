from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .schemas import SearchRequest, SearchResponse, FlightLegSchema, MultiLegSearchRequest, MultiLegSearchResponse, ItinerarySchema, ConnectionSchema
from .airlabs_service import fetch_flights
from .risk_calculator import compute_risk
from .connection_analyzer import analyze_connection, calculate_itinerary_risk

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
    """
    try:
        if len(req.legs) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 legs allowed")
        
        itineraries: List[ItinerarySchema] = []
        
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
            
            itineraries.append(
                ItinerarySchema(
                    flights=all_flights,
                    connections=connections,
                    overall_risk_level=itinerary_risk["risk_level"],
                    overall_reliability_score=itinerary_risk["reliability_score"],
                    overall_disruption_probability=itinerary_risk["disruption_probability"]
                )
            )
        
        return MultiLegSearchResponse(itineraries=itineraries)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")

