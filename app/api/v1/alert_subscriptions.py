from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert_subscription import AlertSubscription
from app.schemas.alert_subscription import (
    AlertSubscriptionCreate,
    AlertSubscriptionRead,
    AlertSubscriptionUpdate,
)

router = APIRouter(prefix="/alert-subscriptions", tags=["alert-subscriptions"])


@router.post(
    "/",
    response_model=AlertSubscriptionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_alert_subscription(
    payload: AlertSubscriptionCreate,
    db: Session = Depends(get_db),
) -> AlertSubscription:
    subscription = AlertSubscription(
        subscriber_type=payload.subscriber_type,
        subscriber_id=payload.subscriber_id,
        scope_type=payload.scope_type,
        scope_code=payload.scope_code,
        delivery_channel=payload.delivery_channel,
        recipient=payload.recipient,
        is_enabled=payload.is_enabled,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("/", response_model=list[AlertSubscriptionRead])
def list_alert_subscriptions(
    subscriber_type: str | None = Query(default=None),
    subscriber_id: int | None = Query(default=None),
    scope_type: str | None = Query(default=None),
    scope_code: str | None = Query(default=None),
    is_enabled: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AlertSubscription]:
    stmt = select(AlertSubscription).order_by(AlertSubscription.id.desc()).limit(limit)

    if subscriber_type:
        stmt = stmt.where(AlertSubscription.subscriber_type == subscriber_type)

    if subscriber_id is not None:
        stmt = stmt.where(AlertSubscription.subscriber_id == subscriber_id)

    if scope_type:
        stmt = stmt.where(AlertSubscription.scope_type == scope_type)

    if scope_code:
        stmt = stmt.where(AlertSubscription.scope_code == scope_code)

    if is_enabled is not None:
        stmt = stmt.where(AlertSubscription.is_enabled == is_enabled)

    return list(db.execute(stmt).scalars().all())


@router.get("/{subscription_id}", response_model=AlertSubscriptionRead)
def get_alert_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
) -> AlertSubscription:
    subscription = db.get(AlertSubscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert subscription not found",
        )
    return subscription


@router.patch("/{subscription_id}", response_model=AlertSubscriptionRead)
def update_alert_subscription(
    subscription_id: int,
    payload: AlertSubscriptionUpdate,
    db: Session = Depends(get_db),
) -> AlertSubscription:
    subscription = db.get(AlertSubscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert subscription not found",
        )

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(subscription, key, value)

    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
) -> None:
    subscription = db.get(AlertSubscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert subscription not found",
        )

    db.delete(subscription)
    db.commit()