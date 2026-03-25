from __future__ import annotations

from sqlalchemy.orm import Session


def create_alert_from_measurement(
    *,
    db: Session,
    user_id: int,
    scope_type: str,
    scope_id: int,
    parameters: dict,
    measurement_id: int,
    source_kind: str = "site",
):
    """
    Core alert creation logic
    """

    # 🔴 Put your real alert logic here
    # Example placeholder:
    print(f"ALERT → user={user_id}, scope={scope_type}:{scope_id}, measurement={measurement_id}")

    return True


# ✅ BACKWARD COMPATIBILITY WRAPPER (VERY IMPORTANT)
class MeasurementAlertService:
    def create_alert_from_measurement(
        self,
        *,
        db: Session,
        user_id: int,
        scope_type: str,
        scope_id: int,
        parameters: dict,
        measurement_id: int,
        source_kind: str = "site",
    ):
        return create_alert_from_measurement(
            db=db,
            user_id=user_id,
            scope_type=scope_type,
            scope_id=scope_id,
            parameters=parameters,
            measurement_id=measurement_id,
            source_kind=source_kind,
        )