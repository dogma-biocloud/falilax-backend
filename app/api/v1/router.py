from fastapi import APIRouter

# -------------------------------
# Core system routes
# -------------------------------
from app.api.v1.routes.routes import router as test_router
from app.api.v1.routes.water_sample import router as water_sample_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.measurement import router as measurement_router
from app.api.v1.routes.parameter_definition import router as parameter_definition_router

# -------------------------------
# Alerts system
# -------------------------------
from app.api.v1.alert_ingest import router as alert_ingest_router
from app.api.v1.alert_dashboard import router as alert_dashboard_router
from app.api.v1.alerts import router as alerts_router

# -------------------------------
# Data ingestion pipeline
# -------------------------------
from app.api.v1.data_sources import router as data_sources_router
from app.api.v1.ingestion_uploads import router as ingestion_uploads_router
from app.api.v1.normalization import router as normalization_router
from app.api.v1.normalized_records import router as normalized_records_router
from app.api.v1.measurement_bridge import router as measurement_bridge_router
from app.api.v1.sensor_ingest import router as sensor_ingest_router

# -------------------------------
# Frontend / dashboard APIs
# -------------------------------
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.alerts_map import router as alerts_map_router
from app.api.v1.system_status import router as system_status_router
from app.api.v1.alerts_timeline import router as alerts_timeline_router
from app.api.v1.source_attribution import router as source_attribution_router
from app.api.v1.simulation import router as simulation_router

# -------------------------------
# GIS map endpoints
# -------------------------------
from app.api.v1.map import router as map_router
from app.api.v1.map_live import router as map_live_router
from app.api.v1.contamination_spread import router as contamination_spread_router
from app.api.v1.contamination_prediction import router as contamination_prediction_router
from app.api.v1.community_alert_escalation import router as community_alert_escalation_router
from app.api.v1.water_intelligence import router as water_intelligence_router
from app.api.v1.central_systems import router as central_systems_router
from app.api.v1.distribution_lines import router as distribution_lines_router
from app.api.v1.alert_dispatch import router as alert_dispatch_router
from app.api.v1.alert_dispatch import router as alert_dispatch_router
from app.api.v1.alert_dispatch import router as alert_dispatch_router

api_router = APIRouter()

# -------------------------------
# Core system routes
# -------------------------------
api_router.include_router(test_router)
api_router.include_router(water_sample_router)
api_router.include_router(health_router)
api_router.include_router(measurement_router)
api_router.include_router(parameter_definition_router)

# -------------------------------
# Alert ingestion + alert APIs
# -------------------------------
api_router.include_router(alert_ingest_router)
api_router.include_router(alerts_router)
api_router.include_router(alert_dashboard_router)
api_router.include_router(sensor_ingest_router)

# -------------------------------
# Data ingestion pipeline
# -------------------------------
api_router.include_router(data_sources_router)
api_router.include_router(ingestion_uploads_router)
api_router.include_router(normalization_router)
api_router.include_router(normalized_records_router)
api_router.include_router(measurement_bridge_router)

# -------------------------------
# Frontend dashboard endpoints
# -------------------------------
api_router.include_router(dashboard_router)
api_router.include_router(alerts_map_router)
api_router.include_router(system_status_router)
api_router.include_router(alerts_timeline_router)
api_router.include_router(source_attribution_router)
api_router.include_router(simulation_router)

# -------------------------------
# GIS / Community Map endpoints
# -------------------------------
api_router.include_router(map_router)
api_router.include_router(map_live_router)
api_router.include_router(contamination_spread_router)
api_router.include_router(contamination_prediction_router)
api_router.include_router(community_alert_escalation_router)
api_router.include_router(water_intelligence_router)
api_router.include_router(central_systems_router)
api_router.include_router(distribution_lines_router)
api_router.include_router(alert_dispatch_router)
api_router.include_router(alert_dispatch_router)
api_router.include_router(alert_dispatch_router)