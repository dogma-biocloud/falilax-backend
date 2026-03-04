from datetime import datetime
from sqlalchemy.orm import Session

from app.models.water_sample import WaterSample
from app.schemas.water_sample import WaterSampleCreate


def get_all_water_samples(db: Session):
    return db.query(WaterSample).all()


def create_water_sample(db: Session, payload: WaterSampleCreate) -> WaterSample:
    data = payload.model_dump()

    # If collected_at not provided, set it to "now"
    if data.get("collected_at") is None:
        data["collected_at"] = datetime.utcnow()

    sample = WaterSample(**data)
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample