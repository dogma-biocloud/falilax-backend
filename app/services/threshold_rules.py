DEFAULT_THRESHOLDS = {
    "turbidity": {
        "warn_max": 5.0,
        "critical_max": 10.0,
    },
    "ph": {
        "warn_min": 6.5,
        "warn_max": 8.5,
        "critical_min": 6.0,
        "critical_max": 9.0,
    },
    "lead_ppb": {
        "warn_max": 10.0,
        "critical_max": 15.0,
    }
}

def evaluate_measurement(parameter_code: str, value: float):
    rules = DEFAULT_THRESHOLDS.get(parameter_code)

    if not rules:
        return "normal"

    # Critical first
    if "critical_min" in rules and value < rules["critical_min"]:
        return "critical"
    if "critical_max" in rules and value > rules["critical_max"]:
        return "critical"

    # Warning level
    if "warn_min" in rules and value < rules["warn_min"]:
        return "attention"
    if "warn_max" in rules and value > rules["warn_max"]:
        return "attention"

    return "normal"