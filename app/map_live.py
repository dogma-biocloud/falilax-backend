from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.map import MapNetworkResponse

router = APIRouter(prefix="/map", tags=["Map"])


def build_demo_map_network() -> MapNetworkResponse:
    return MapNetworkResponse(
        nodes=[
            {
                "id": "source",
                "label": "Central Source",
                "x": 10,
                "y": 48,
                "status": "safe",
                "type": "source",
                "detail": "Source water stable",
                "response": "Continue routine monitoring and maintain baseline source testing.",
            },
            {
                "id": "line-a",
                "label": "Distribution Line A",
                "x": 30,
                "y": 48,
                "status": "moderate",
                "type": "distribution",
                "detail": "Minor shared-line disturbance",
                "response": "Inspect line pressure behavior and test adjacent downstream nodes.",
            },
            {
                "id": "district-5",
                "label": "District 5",
                "x": 50,
                "y": 48,
                "status": "moderate",
                "type": "distribution",
                "detail": "Monitoring active",
                "response": "Increase local sampling frequency and compare with nearby district branches.",
            },
            {
                "id": "school",
                "label": "Lincoln Elementary",
                "x": 74,
                "y": 28,
                "status": "critical",
                "type": "school",
                "detail": "Highest endpoint concern",
                "response": "Escalate response immediately, isolate affected fixtures, and confirm with certified testing.",
            },
            {
                "id": "hospital",
                "label": "Hospital Zone",
                "x": 74,
                "y": 50,
                "status": "moderate",
                "type": "hospital",
                "detail": "Precautionary monitoring",
                "response": "Maintain precautionary surveillance and prioritize patient-facing fixtures.",
            },
            {
                "id": "homes",
                "label": "Residential Cluster",
                "x": 74,
                "y": 72,
                "status": "safe",
                "type": "residential",
                "detail": "No elevated risk detected",
                "response": "Maintain standard observation and compare against district-level shifts.",
            },
        ],
        edges=[
            {"from": "source", "to": "line-a", "severity": "safe"},
            {"from": "line-a", "to": "district-5", "severity": "moderate"},
            {"from": "district-5", "to": "school", "severity": "critical"},
            {"from": "district-5", "to": "hospital", "severity": "moderate"},
            {"from": "district-5", "to": "homes", "severity": "safe"},
        ],
    )


@router.websocket("/live")
async def map_live_socket(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            payload = build_demo_map_network().model_dump(by_alias=True)
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return