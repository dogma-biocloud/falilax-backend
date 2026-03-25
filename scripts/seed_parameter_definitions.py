from __future__ import annotations

from app.db.session import SessionLocal
from app.models.parameter_definition import ParameterDefinition

from scripts.parameter_seed.physical import PHYSICAL_PARAMETERS
from scripts.parameter_seed.chemistry import CHEMISTRY_PARAMETERS
from scripts.parameter_seed.nutrients import NUTRIENT_PARAMETERS
from scripts.parameter_seed.nutrient_species import NUTRIENT_SPECIES_PARAMETERS
from scripts.parameter_seed.ions import ION_PARAMETERS
from scripts.parameter_seed.heavy_metals import HEAVY_METAL_PARAMETERS
from scripts.parameter_seed.microbiology import MICROBIOLOGY_PARAMETERS
from scripts.parameter_seed.disinfectants import DISINFECTANT_PARAMETERS
from scripts.parameter_seed.organics import ORGANIC_CONTAMINANT_PARAMETERS
from scripts.parameter_seed.pesticides import PESTICIDE_PARAMETERS
from scripts.parameter_seed.pfas import PFAS_PARAMETERS
from scripts.parameter_seed.radioactivity import RADIOACTIVITY_PARAMETERS
from scripts.parameter_seed.industrial_chemicals import INDUSTRIAL_CHEMICAL_PARAMETERS
from scripts.parameter_seed.emerging_contaminants import EMERGING_CONTAMINANT_PARAMETERS
from scripts.parameter_seed.operational import OPERATIONAL_PARAMETERS
from scripts.parameter_seed.microbial_toxins import MICROBIAL_TOXIN_PARAMETERS
from scripts.parameter_seed.secondary_standards import SECONDARY_STANDARD_PARAMETERS


PARAMETER_SEED = (
    PHYSICAL_PARAMETERS
    + CHEMISTRY_PARAMETERS
    + NUTRIENT_PARAMETERS
    + NUTRIENT_SPECIES_PARAMETERS
    + ION_PARAMETERS
    + HEAVY_METAL_PARAMETERS
    + MICROBIOLOGY_PARAMETERS
    + DISINFECTANT_PARAMETERS
    + ORGANIC_CONTAMINANT_PARAMETERS
    + PESTICIDE_PARAMETERS
    + PFAS_PARAMETERS
    + RADIOACTIVITY_PARAMETERS
    + INDUSTRIAL_CHEMICAL_PARAMETERS
    + EMERGING_CONTAMINANT_PARAMETERS
    + OPERATIONAL_PARAMETERS
    + MICROBIAL_TOXIN_PARAMETERS
    + SECONDARY_STANDARD_PARAMETERS
)


def seed_parameter_definitions() -> None:
    db = SessionLocal()
    try:
        for item in PARAMETER_SEED:
            existing = (
                db.query(ParameterDefinition)
                .filter(ParameterDefinition.parameter_code == item["parameter_code"])
                .first()
            )

            if existing:
                existing.display_name = item["display_name"]
                existing.category = item["category"]
                existing.expected_unit = item["expected_unit"]
                existing.description = item["description"]
                existing.threshold_profile = item["threshold_profile"]
                existing.regulatory_source = item["regulatory_source"]
                existing.warn_min = item["warn_min"]
                existing.warn_max = item["warn_max"]
                existing.critical_min = item["critical_min"]
                existing.critical_max = item["critical_max"]
                existing.alerts_enabled = item["alerts_enabled"]
                existing.is_active = item["is_active"]
            else:
                db.add(ParameterDefinition(**item))

        db.commit()
        print(f"Seeded/updated {len(PARAMETER_SEED)} parameter definitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_parameter_definitions()