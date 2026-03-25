from dataclasses import dataclass


class MeasurementNormalizationError(ValueError):
    pass


@dataclass
class NormalizedMeasurement:
    raw_parameter: str
    raw_unit: str | None
    raw_value: float

    parameter_code: str
    canonical_unit: str
    normalized_value: float


PARAMETER_ALIASES = {
    "ph": "ph",
    "pH": "ph",

    "temp": "temperature",
    "temperature": "temperature",

    "turbidity": "turbidity",

    "tds": "tds",

    "ec": "electrical_conductivity",
    "electrical conductivity": "electrical_conductivity",
    "conductivity": "electrical_conductivity",

    "lead": "lead",
    "pb": "lead",

    "arsenic": "arsenic",
    "as": "arsenic",

    "fluoride": "fluoride",
    "f": "fluoride",

    "nitrate": "nitrate",
    "no3": "nitrate",
    "no3-": "nitrate",

    "nitrite": "nitrite",
    "no2": "nitrite",
    "no2-": "nitrite",

    "chlorine": "chlorine",
    "free chlorine": "chlorine",
}


CANONICAL_UNITS = {
    "ph": "pH",
    "temperature": "celsius",
    "turbidity": "ntu",
    "tds": "mg/L",
    "electrical_conductivity": "uS/cm",
    "lead": "mg/L",
    "arsenic": "mg/L",
    "fluoride": "mg/L",
    "nitrate": "mg/L",
    "nitrite": "mg/L",
    "chlorine": "mg/L",
}


UNIT_ALIASES = {
    "c": "celsius",
    "°c": "celsius",
    "celsius": "celsius",

    "f": "fahrenheit",
    "°f": "fahrenheit",
    "fahrenheit": "fahrenheit",

    "mg/l": "mg/L",
    "ppm": "mg/L",

    "ug/l": "ug/L",
    "μg/l": "ug/L",
    "mcg/l": "ug/L",

    "ntu": "ntu",

    "us/cm": "uS/cm",
    "µs/cm": "uS/cm",
    "μs/cm": "uS/cm",
    "ms/cm": "mS/cm",
}


def normalize_text(value: str) -> str:
    return value.strip().lower()


def normalize_parameter(parameter: str) -> str:
    key = normalize_text(parameter)

    if key in PARAMETER_ALIASES:
        return PARAMETER_ALIASES[key]

    raise MeasurementNormalizationError(f"Unsupported parameter: {parameter}")


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None

    key = normalize_text(unit)

    if key in UNIT_ALIASES:
        return UNIT_ALIASES[key]

    raise MeasurementNormalizationError(f"Unsupported unit: {unit}")


def convert_temperature(value: float, unit: str) -> float:
    if unit == "celsius":
        return value

    if unit == "fahrenheit":
        return (value - 32) * 5 / 9

    raise MeasurementNormalizationError(f"Unsupported temperature unit: {unit}")


def convert_concentration_to_mg_per_l(value: float, unit: str) -> float:
    if unit == "mg/L":
        return value

    if unit == "ug/L":
        return value / 1000.0

    raise MeasurementNormalizationError(f"Unsupported concentration unit: {unit}")


def convert_conductivity(value: float, unit: str) -> float:
    if unit == "uS/cm":
        return value

    if unit == "mS/cm":
        return value * 1000.0

    raise MeasurementNormalizationError(f"Unsupported conductivity unit: {unit}")


def normalize_measurement(
    parameter: str,
    value: float,
    unit: str | None,
) -> NormalizedMeasurement:
    parameter_code = normalize_parameter(parameter)
    normalized_unit = normalize_unit(unit)
    canonical_unit = CANONICAL_UNITS[parameter_code]

    if parameter_code == "ph":
        normalized_value = value

    elif parameter_code == "temperature":
        if normalized_unit is None:
            raise MeasurementNormalizationError("Temperature requires a unit")
        normalized_value = convert_temperature(value, normalized_unit)

    elif parameter_code == "turbidity":
        if normalized_unit != "ntu":
            raise MeasurementNormalizationError("Turbidity must be in NTU")
        normalized_value = value

    elif parameter_code == "electrical_conductivity":
        if normalized_unit is None:
            raise MeasurementNormalizationError("Electrical conductivity requires a unit")
        normalized_value = convert_conductivity(value, normalized_unit)

    elif parameter_code in {
        "tds",
        "lead",
        "arsenic",
        "fluoride",
        "nitrate",
        "nitrite",
        "chlorine",
    }:
        if normalized_unit is None:
            raise MeasurementNormalizationError(f"{parameter_code} requires a unit")
        normalized_value = convert_concentration_to_mg_per_l(value, normalized_unit)

    else:
        raise MeasurementNormalizationError(f"No normalization rule for {parameter_code}")

    return NormalizedMeasurement(
        raw_parameter=parameter,
        raw_unit=unit,
        raw_value=value,
        parameter_code=parameter_code,
        canonical_unit=canonical_unit,
        normalized_value=normalized_value,
    )