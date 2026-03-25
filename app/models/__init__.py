# app/models/__init__.py
"""
Register all SQLAlchemy models so that Base.metadata
knows about every table when the application starts.

This avoids errors like:
    NoReferencedTableError: could not find table 'users'

Models should still be imported directly where needed, e.g.:
    from app.models.alert import Alert
"""

from app.models.base import Base

# ------------------------------
# CORE MODELS
# ------------------------------
from app.models.user import User
from app.models.location import Location
from app.models.water_sample import WaterSample
from app.models.measurement import Measurement
from app.models.risk_assessment import RiskAssessment
from app.models.notification_preference import NotificationPreference
from app.models.alert import Alert
from app.models.parameter_definition import ParameterDefinition

# ------------------------------
# INGESTION PIPELINE (🔥 CRITICAL)
# ------------------------------
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.raw_water_record import RawWaterRecord

# ------------------------------
# INFRASTRUCTURE LAYER (FalilaX)
# ------------------------------
from app.models.central_system import CentralSystem
from app.models.distribution_line import DistributionLine
from app.models.alert_delivery_log import AlertDeliveryLog

# ------------------------------
# IMPORTANT:
# We do NOT expose models to avoid circular imports.
# But importing them ensures SQLAlchemy registers them.
# ------------------------------

__all__ = ["Base"]