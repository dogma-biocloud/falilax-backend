from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict


NodeStatus = Literal["safe", "moderate", "critical"]
NodeType = Literal["source", "distribution", "school", "hospital", "residential"]


class MapNode(BaseModel):
    id: str
    label: str
    x: float
    y: float
    status: NodeStatus
    type: NodeType
    detail: str
    response: str


class MapEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    severity: NodeStatus

    model_config = ConfigDict(populate_by_name=True)


class MapNetworkResponse(BaseModel):
    nodes: List[MapNode]
    edges: List[MapEdge]

    model_config = ConfigDict(populate_by_name=True)