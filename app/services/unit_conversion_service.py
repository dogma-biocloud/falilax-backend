from __future__ import annotations


def normalize_unit_text(unit: str | None) -> str:
    if not unit:
        return ""
    return unit.strip().lower().replace("μ", "u").replace("µ", "u")


def convert_value(
    *,
    value: float,
    from_unit: str | None,
    to_unit: str | None,
) -> tuple[float, str, bool]:
    """
    Returns:
        (converted_value, normalized_target_unit, converted_flag)

    Rules implemented:
    - identical units => no conversion needed
    - mg/L <-> ug/L <-> ng/L <-> g/L
    - ug/L <-> ppb   (water assumption)
    - mg/L <-> ppb   (water assumption)
    - mg/L <-> ppm   (water assumption)
    - uS/cm <-> mS/cm
    - C <-> F
    - CFU/mL <-> CFU/100mL
    - % <-> fraction
    """

    src = normalize_unit_text(from_unit)
    dst = normalize_unit_text(to_unit)

    if not dst:
        return value, dst, False

    if src == dst:
        return value, dst, False

    aliases = {
        "ug/l": "ug/l",
        "ng/l": "ng/l",
        "mg/l": "mg/l",
        "g/l": "g/l",
        "ppb": "ppb",
        "ppm": "ppm",
        "c": "c",
        "f": "f",
        "ntu": "ntu",
        "ph": "ph",
        "cfu/100ml": "cfu/100ml",
        "cfu/ml": "cfu/ml",
        "count/l": "count/l",
        "pci/l": "pci/l",
        "psi": "psi",
        "%": "%",
        "percent": "%",
        "fraction": "fraction",
        "l/min": "l/min",
        "us/cm": "us/cm",
        "ms/cm": "ms/cm",
        "mv": "mv",
        "ppt": "ppt",
        "pt-co": "pt-co",
        "score": "score",
        "hr": "hr",
        "min": "min",
        "m": "m",
        "kwh": "kwh",
    }

    src = aliases.get(src, src)
    dst = aliases.get(dst, dst)

    # Concentration conversions (water assumptions where noted)
    if src == "mg/l" and dst == "ug/l":
        return value * 1000.0, dst, True

    if src == "ug/l" and dst == "mg/l":
        return value / 1000.0, dst, True

    if src == "ug/l" and dst == "ng/l":
        return value * 1000.0, dst, True

    if src == "ng/l" and dst == "ug/l":
        return value / 1000.0, dst, True

    if src == "mg/l" and dst == "ng/l":
        return value * 1_000_000.0, dst, True

    if src == "ng/l" and dst == "mg/l":
        return value / 1_000_000.0, dst, True

    if src == "g/l" and dst == "mg/l":
        return value * 1000.0, dst, True

    if src == "mg/l" and dst == "g/l":
        return value / 1000.0, dst, True

    if src == "g/l" and dst == "ug/l":
        return value * 1_000_000.0, dst, True

    if src == "ug/l" and dst == "g/l":
        return value / 1_000_000.0, dst, True

    if src == "ug/l" and dst == "ppb":
        return value, dst, True

    if src == "ppb" and dst == "ug/l":
        return value, dst, True

    if src == "mg/l" and dst == "ppb":
        return value * 1000.0, dst, True

    if src == "ppb" and dst == "mg/l":
        return value / 1000.0, dst, True

    if src == "mg/l" and dst == "ppm":
        return value, dst, True

    if src == "ppm" and dst == "mg/l":
        return value, dst, True

    if src == "ug/l" and dst == "ppm":
        return value / 1000.0, dst, True

    if src == "ppm" and dst == "ug/l":
        return value * 1000.0, dst, True

    # Conductivity
    if src == "us/cm" and dst == "ms/cm":
        return value / 1000.0, dst, True

    if src == "ms/cm" and dst == "us/cm":
        return value * 1000.0, dst, True

    # Temperature
    if src == "f" and dst == "c":
        return (value - 32.0) * 5.0 / 9.0, dst, True

    if src == "c" and dst == "f":
        return (value * 9.0 / 5.0) + 32.0, dst, True

    # Microbiology counts
    if src == "cfu/ml" and dst == "cfu/100ml":
        return value * 100.0, dst, True

    if src == "cfu/100ml" and dst == "cfu/ml":
        return value / 100.0, dst, True

    # Percent/fraction
    if src == "%" and dst == "fraction":
        return value / 100.0, dst, True

    if src == "fraction" and dst == "%":
        return value * 100.0, dst, True

    # No supported conversion
    return value, dst, False