from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.map_service import build_demo_map_network

router = APIRouter(prefix="/map", tags=["Map"])


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