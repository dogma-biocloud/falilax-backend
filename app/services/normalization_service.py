from __future__ import annotations

from typing import Any


BASE_PARAMETER_MAPPINGS = {
    "lead": ["lead", "lead_ppb", "lead (ppb)", "pb", "pb_ppb", "lead result"],
    "copper": ["copper", "copper_ppm", "copper (ppm)", "cu", "copper result"],
    "chlorine": ["chlorine", "chlorine_ppm", "chlorine (ppm)", "free chlorine"],
    "ph": ["ph", "pH"],
    "turbidity": ["turbidity", "turbidity_ntu", "turbidity (ntu)", "ntu"],
}

PARSER_PARAMETER_OVERRIDES = {
    "school_water_csv": {
        "lead": ["lead result", "lead fountain", "lead outlet"],
        "copper": ["copper result"],
    },
    "utility_lab_csv": {
        "lead": ["pb", "pb result", "lead ug/l"],
        "chlorine": ["free chlorine residual", "chlorine residual"],
    },
}

DEFAULT_UNITS = {
    "lead": "mg/L",
    "copper": "mg/L",
    "chlorine": "mg/L",
    "ph": "",
    "turbidity": "NTU",
}


def normalize_key(value: str) -> str:
    return value.strip().lower().replace("_", " ")


def merge_parameter_mappings(parser_type: str | None) -> dict[str, list[str]]:
    merged = {k: list(v) for k, v in BASE_PARAMETER_MAPPINGS.items()}

    if parser_type and parser_type in PARSER_PARAMETER_OVERRIDES:
        for parameter_code, aliases in PARSER_PARAMETER_OVERRIDES[parser_type].items():
            merged.setdefault(parameter_code, [])
            merged[parameter_code].extend(aliases)

    return merged


def detect_unit_from_key(raw_key: str, parameter_code: str) -> str:
    key = normalize_key(raw_key)

    if parameter_code == "lead":
        if "ug/l" in key or "µg/l" in key or "μg/l" in key:
            return "ug/L"
        if "ppb" in key:
            return "ppb"
        if "mg/l" in key:
            return "mg/L"

    if parameter_code in {"copper", "chlorine"}:
        if "mg/l" in key:
            return "mg/L"
        if "ppm" in key:
            return "ppm"
        if "ug/l" in key or "µg/l" in key or "μg/l" in key:
            return "ug/L"

    if parameter_code == "turbidity":
        return "NTU"

    if parameter_code == "ph":
        return ""

    return DEFAULT_UNITS.get(parameter_code, "")


def convert_to_standard_unit(parameter_code: str, value: float, unit: str) -> tuple[float, str]:
    unit_norm = unit.strip().lower()

    if parameter_code == "lead":
        if unit_norm in {"ug/l", "µg/l", "μg/l", "ppb"}:
            return value / 1000.0, "mg/L"
        if unit_norm == "mg/l":
            return value, "mg/L"

    if parameter_code in {"copper", "chlorine"}:
        if unit_norm in {"mg/l", "ppm"}:
            return value, "mg/L"
        if unit_norm in {"ug/l", "µg/l", "μg/l"}:
            return value / 1000.0, "mg/L"

    if parameter_code == "turbidity":
        return value, "NTU"

    if parameter_code == "ph":
        return value, ""

    return value, DEFAULT_UNITS.get(parameter_code, unit)


def find_parameter_matches(
    raw_row: dict[str, Any],
    parser_type: str | None = None,
) -> list[tuple[str, str, Any]]:
    mappings = merge_parameter_mappings(parser_type)
    matches: list[tuple[str, str, Any]] = []

    normalized_row = {
        normalize_key(str(key)): (str(key), value)
        for key, value in raw_row.items()
    }

    for parameter_code, aliases in mappings.items():
        alias_set = {normalize_key(alias) for alias in aliases}

        for normalized_key, (original_key, value) in normalized_row.items():
            if normalized_key in alias_set:
                matches.append((parameter_code, original_key, value))

    return matches


def find_location_name(raw_row: dict[str, Any]) -> str:
    for key in raw_row.keys():
        key_norm = normalize_key(str(key))
        if key_norm in {
            "sample location",
            "location",
            "site",
            "site name",
            "sampling point",
            "facility",
            "facility name",
            "outlet",
        }:
            return str(raw_row[key])

    return "Unknown Location"


def find_sample_date(raw_row: dict[str, Any]) -> str | None:
    for key in raw_row.keys():
        key_norm = normalize_key(str(key))
        if key_norm in {
            "collection date",
            "sample date",
            "date",
            "sampling date",
            "date collected",
        }:
            value = raw_row[key]
            if value is None:
                return None
            return str(value)

    return None


def to_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).strip())
    except Exception:
        return None


def normalize_raw_row(
    raw_row: dict[str, Any],
    parser_type: str | None = None,
) -> list[dict[str, Any]]:
    location_name = find_location_name(raw_row)
    sample_date = find_sample_date(raw_row)
    parameter_matches = find_parameter_matches(raw_row, parser_type=parser_type)

    normalized_records: list[dict[str, Any]] = []

    for parameter_code, original_key, raw_value in parameter_matches:
        measured_value = to_float(raw_value)
        if measured_value is None:
            continue

        detected_unit = detect_unit_from_key(original_key, parameter_code)
        standard_value, standard_unit = convert_to_standard_unit(
            parameter_code,
            measured_value,
            detected_unit,
        )

        normalized_records.append(
            {
                "location_name": location_name,
                "parameter_code": parameter_code,
                "parameter_name": parameter_code.capitalize(),
                "measured_value": standard_value,
                "original_value": measured_value,
                "original_unit": detected_unit,
                "unit": standard_unit,
                "sample_date": sample_date,
            }
        )

    return normalized_records