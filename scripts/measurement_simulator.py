import random
import time
from datetime import datetime, timezone
from typing import Any

import requests

API_URL = "http://127.0.0.1:8001/api/v1/measurements"

USER_ID = 1
SAMPLE_ID = 1

PARAMETER_CONFIGS: dict[str, dict[str, Any]] = {
    "turbidity": {
        "unit": "NTU",
        "method": "sensor_simulator",
        "normal_range": (1.0, 4.5),
        "warning_range": (5.5, 9.5),
        "critical_range": (10.5, 15.0),
    },
    "ph": {
        "unit": "pH",
        "method": "sensor_simulator",
        "normal_range": (6.8, 8.2),
        "warning_range_low": (6.1, 6.4),
        "warning_range_high": (8.6, 8.9),
        "critical_range_low": (5.4, 5.9),
        "critical_range_high": (9.1, 9.6),
    },
    "lead_ppb": {
        "unit": "ppb",
        "method": "sensor_simulator",
        "normal_range": (0.5, 8.0),
        "warning_range": (10.5, 14.5),
        "critical_range": (15.5, 25.0),
    },
}


def build_payload(
    *,
    sample_id: int,
    parameter_code: str,
    value: float,
    unit: str,
    method: str,
    source_type: str = "sensor",
    quality_flag: str = "valid",
) -> dict[str, Any]:
    return {
        "user_id": USER_ID,
        "sample_id": sample_id,
        "parameter_code": parameter_code,
        "value": round(value, 3),
        "unit": unit,
        "qualifier": None,
        "method": method,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "source_type": source_type,
        "quality_flag": quality_flag,
    }


def post_measurement(payload: dict[str, Any]) -> None:
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(
            f"[{payload['parameter_code']}] "
            f"value={payload['value']} {payload['unit']} "
            f"status={response.status_code}"
        )
        if response.status_code >= 400:
            print(response.text)
    except requests.RequestException as exc:
        print(f"Request failed for {payload['parameter_code']}: {exc}")


def random_in_range(low: float, high: float) -> float:
    return random.uniform(low, high)


def generate_turbidity_value(mode: str) -> float:
    cfg = PARAMETER_CONFIGS["turbidity"]
    if mode == "normal":
        return random_in_range(*cfg["normal_range"])
    if mode == "warning":
        return random_in_range(*cfg["warning_range"])
    return random_in_range(*cfg["critical_range"])


def generate_lead_value(mode: str) -> float:
    cfg = PARAMETER_CONFIGS["lead_ppb"]
    if mode == "normal":
        return random_in_range(*cfg["normal_range"])
    if mode == "warning":
        return random_in_range(*cfg["warning_range"])
    return random_in_range(*cfg["critical_range"])


def generate_ph_value(mode: str) -> float:
    cfg = PARAMETER_CONFIGS["ph"]
    if mode == "normal":
        return random_in_range(*cfg["normal_range"])

    if mode == "warning":
        side = random.choice(["low", "high"])
        if side == "low":
            return random_in_range(*cfg["warning_range_low"])
        return random_in_range(*cfg["warning_range_high"])

    side = random.choice(["low", "high"])
    if side == "low":
        return random_in_range(*cfg["critical_range_low"])
    return random_in_range(*cfg["critical_range_high"])


def choose_mode(cycle_number: int) -> str:
    """
    Simulates realistic phases:
    - mostly normal
    - occasional warning windows
    - rare critical spikes
    """
    if cycle_number % 15 == 0:
        return "critical"
    if cycle_number % 5 == 0:
        return "warning"
    return "normal"


def generate_parameter_payloads(sample_id: int, cycle_number: int) -> list[dict[str, Any]]:
    mode = choose_mode(cycle_number)

    turbidity_cfg = PARAMETER_CONFIGS["turbidity"]
    ph_cfg = PARAMETER_CONFIGS["ph"]
    lead_cfg = PARAMETER_CONFIGS["lead_ppb"]

    payloads = [
        build_payload(
            sample_id=sample_id,
            parameter_code="turbidity",
            value=generate_turbidity_value(mode),
            unit=turbidity_cfg["unit"],
            method=turbidity_cfg["method"],
        ),
        build_payload(
            sample_id=sample_id,
            parameter_code="ph",
            value=generate_ph_value(mode),
            unit=ph_cfg["unit"],
            method=ph_cfg["method"],
        ),
        build_payload(
            sample_id=sample_id,
            parameter_code="lead_ppb",
            value=generate_lead_value(mode),
            unit=lead_cfg["unit"],
            method=lead_cfg["method"],
        ),
    ]

    return payloads


def main() -> None:
    print("Starting FalilaX realistic measurement simulator...")
    print("Posting measurements to:", API_URL)
    print("Press Ctrl+C to stop.\n")

    cycle = 1

    try:
        while True:
            print(f"\n--- Cycle {cycle} ---")
            payloads = generate_parameter_payloads(SAMPLE_ID, cycle)

            for payload in payloads:
                post_measurement(payload)
                time.sleep(1)

            cycle += 1
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()