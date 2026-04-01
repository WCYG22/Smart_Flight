"""
Itinerary Manager (F011, F012)
Handles itinerary summary views and save/export functionality
"""

from typing import Dict, List
from datetime import datetime
import json
import base64


def generate_itinerary_summary(itinerary: Dict) -> Dict:
    """
    Generate a comprehensive summary for an itinerary (F011).
    Includes all relevant details for display and export.
    """
    
    flights = itinerary.get("flights", [])
    connections = itinerary.get("connections", [])
    
    # Calculate total journey details
    total_duration = itinerary.get("journey_duration_minutes", 0)
    hours = total_duration // 60
    minutes = total_duration % 60
    
    # Build flight segments
    flight_segments = []
    for idx, flight in enumerate(flights):
        segment = {
            "leg": idx + 1,
            "flight_number": flight.get("flight_number"),
            "airline": flight.get("airline"),
            "origin": flight.get("origin"),
            "destination": flight.get("destination"),
            "departure": flight.get("scheduled_departure"),
            "arrival": flight.get("scheduled_arrival"),
            "status": flight.get("status"),
            "delay_minutes": flight.get("delay_minutes", 0),
            "risk_level": flight.get("risk_level"),
            "reliability_score": flight.get("reliability_score"),
            "disruption_probability": flight.get("disruption_probability")
        }
        flight_segments.append(segment)
    
    # Build connection details
    connection_details = []
    for idx, conn in enumerate(connections):
        connection_details.append({
            "between_legs": f"{idx + 1} → {idx + 2}",
            "connection_time_minutes": conn.get("connection_time_minutes"),
            "connection_risk": conn.get("connection_risk"),
            "is_safe": conn.get("is_safe")
        })
    
    summary = {
        "rank": itinerary.get("rank"),
        "rank_label": itinerary.get("rank_label"),
        "ranking_score": itinerary.get("ranking_score"),
        "overall_risk_level": itinerary.get("overall_risk_level"),
        "overall_reliability_score": itinerary.get("overall_reliability_score"),
        "overall_disruption_probability": itinerary.get("overall_disruption_probability"),
        "journey_duration": f"{hours}h {minutes}m",
        "journey_duration_minutes": total_duration,
        "num_stops": itinerary.get("num_stops", 0),
        "flights": flight_segments,
        "connections": connection_details,
        "generated_at": datetime.now().isoformat()
    }
    
    return summary


def export_itinerary_json(itinerary: Dict) -> str:
    """Export itinerary as JSON string (F012)."""
    summary = generate_itinerary_summary(itinerary)
    return json.dumps(summary, indent=2)


def export_itinerary_csv(itinerary: Dict) -> str:
    """Export itinerary as CSV format (F012)."""
    summary = generate_itinerary_summary(itinerary)
    
    csv_lines = []
    csv_lines.append("SmartFlight Itinerary Export")
    csv_lines.append(f"Generated: {summary['generated_at']}")
    csv_lines.append("")
    
    csv_lines.append("ITINERARY SUMMARY")
    csv_lines.append(f"Rank,{summary['rank']} - {summary['rank_label']}")
    csv_lines.append(f"Overall Risk,{summary['overall_risk_level']}")
    csv_lines.append(f"Reliability Score,{summary['overall_reliability_score']}%")
    csv_lines.append(f"Disruption Probability,{summary['overall_disruption_probability'] * 100:.1f}%")
    csv_lines.append(f"Journey Duration,{summary['journey_duration']}")
    csv_lines.append(f"Number of Stops,{summary['num_stops']}")
    csv_lines.append("")
    
    csv_lines.append("FLIGHT SEGMENTS")
    csv_lines.append("Leg,Flight,Airline,Origin,Destination,Departure,Arrival,Risk Level,Reliability,Disruption %")
    for flight in summary['flights']:
        csv_lines.append(
            f"{flight['leg']},{flight['flight_number']},{flight['airline']},"
            f"{flight['origin']},{flight['destination']},"
            f"{flight['departure']},{flight['arrival']},"
            f"{flight['risk_level']},{flight['reliability_score']}%,"
            f"{flight['disruption_probability'] * 100:.1f}%"
        )
    
    csv_lines.append("")
    csv_lines.append("CONNECTION DETAILS")
    csv_lines.append("Between Legs,Connection Time (min),Risk,Safe")
    for conn in summary['connections']:
        csv_lines.append(
            f"{conn['between_legs']},{conn['connection_time_minutes']},"
            f"{conn['connection_risk']},{conn['is_safe']}"
        )
    
    return "\n".join(csv_lines)


def export_itinerary_html(itinerary: Dict) -> str:
    """Export itinerary as HTML for email or viewing (F012, F013)."""
    summary = generate_itinerary_summary(itinerary)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #0066cc; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .summary-item {{ display: inline-block; margin-right: 30px; margin-bottom: 10px; }}
            .summary-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .summary-value {{ font-size: 18px; font-weight: bold; color: #0066cc; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th {{ background: #0066cc; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #e0e0e0; }}
            tr:hover {{ background: #f8f9fa; }}
            .risk-low {{ color: #34c759; font-weight: bold; }}
            .risk-medium {{ color: #ff9500; font-weight: bold; }}
            .risk-high {{ color: #ff3b30; font-weight: bold; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SmartFlight Itinerary</h1>
                <p>{summary['rank_label']}</p>
            </div>
            
            <div class="summary">
                <div class="summary-item">
                    <div class="summary-label">Overall Risk</div>
                    <div class="summary-value risk-{summary['overall_risk_level'].lower()}">{summary['overall_risk_level']}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Reliability</div>
                    <div class="summary-value">{summary['overall_reliability_score']}%</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Duration</div>
                    <div class="summary-value">{summary['journey_duration']}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Stops</div>
                    <div class="summary-value">{summary['num_stops']}</div>
                </div>
            </div>
            
            <h2>Flight Segments</h2>
            <table>
                <tr>
                    <th>Leg</th>
                    <th>Flight</th>
                    <th>Route</th>
                    <th>Departure</th>
                    <th>Arrival</th>
                    <th>Risk</th>
                    <th>Reliability</th>
                </tr>
    """
    
    for flight in summary['flights']:
        risk_class = f"risk-{flight['risk_level'].lower()}"
        html += f"""
                <tr>
                    <td>{flight['leg']}</td>
                    <td><strong>{flight['flight_number']}</strong> ({flight['airline']})</td>
                    <td>{flight['origin']} → {flight['destination']}</td>
                    <td>{flight['departure']}</td>
                    <td>{flight['arrival']}</td>
                    <td><span class="{risk_class}">{flight['risk_level']}</span></td>
                    <td>{flight['reliability_score']}%</td>
                </tr>
        """
    
    html += """
            </table>
            
            <h2>Connection Details</h2>
            <table>
                <tr>
                    <th>Between Legs</th>
                    <th>Connection Time</th>
                    <th>Risk</th>
                    <th>Safe</th>
                </tr>
    """
    
    for conn in summary['connections']:
        html += f"""
                <tr>
                    <td>{conn['between_legs']}</td>
                    <td>{conn['connection_time_minutes']} minutes</td>
                    <td>{conn['connection_risk']}</td>
                    <td>{'✓ Yes' if conn['is_safe'] else '✗ No'}</td>
                </tr>
        """
    
    html += f"""
            </table>
            
            <div class="footer">
                <p>Generated on {summary['generated_at']}</p>
                <p>SmartFlight - Flight Disruption Risk Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
