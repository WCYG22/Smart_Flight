from models import FlightLeg

def compute_risk(leg: FlightLeg) -> tuple[float, int, str]:
    """
    Simple Phase 1 heuristic:
    - If status says 'cancelled' or 'diverted' => very high risk.
    - If delayed minutes is large => higher risk.
    - Otherwise low/medium.
    """

    status = (leg.status or "").lower()
    delay = leg.delay_minutes

    # Base on status
    if status in ("cancelled", "diverted"):
        p = 0.95
    elif status == "delayed":
        p = 0.7
    elif status in ("active", "scheduled", "landed"):
        # refine with delay if available
        if delay is None:
            p = 0.3
        elif delay <= 10:
            p = 0.2
        elif delay <= 30:
            p = 0.5
        else:
            p = 0.8
    else:
        # unknown status
        p = 0.4

    reliability = int((1 - p) * 100)

    if p < 0.3:
        level = "Low"
    elif p < 0.6:
        level = "Medium"
    else:
        level = "High"

    return round(p, 2), reliability, level
