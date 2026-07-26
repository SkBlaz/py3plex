"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


class UploadResponse(BaseModel):
    graph_id: str
    filename: str
    message: str


class GraphSummary(BaseModel):
    graph_id: str
    nodes: int
    edges: int
    layers: List[str]
    attributes: List[str]


class FilterSpec(BaseModel):
    attribute: Optional[str] = None
    min_degree: Optional[int] = None
    max_degree: Optional[int] = None
    layers: Optional[List[str]] = None
    communities: Optional[List[int]] = None


class FilterResponse(BaseModel):
    subgraph_id: str
    original_graph_id: str
    nodes: int
    edges: int


class LayoutAlgorithm(str, Enum):
    spring = "spring"
    force_atlas = "force_atlas"
    kamada_kawai = "kamada_kawai"
    circular = "circular"
    random = "random"


class LayoutRequest(BaseModel):
    algorithm: LayoutAlgorithm = LayoutAlgorithm.spring
    seed: Optional[int] = 42
    dimensions: int = Field(default=2, ge=2, le=3)
    iterations: Optional[int] = 50


class LayoutResponse(BaseModel):
    job_id: str
    status: str = "queued"


class CentralityMetric(str, Enum):
    degree = "degree"
    betweenness = "betweenness"
    closeness = "closeness"
    eigenvector = "eigenvector"
    pagerank = "pagerank"


class CentralityRequest(BaseModel):
    metrics: List[CentralityMetric]
    layers: Optional[List[str]] = None


class CommunityAlgorithm(str, Enum):
    louvain = "louvain"
    label_propagation = "label_propagation"
    greedy_modularity = "greedy_modularity"


class CommunityRequest(BaseModel):
    algorithm: CommunityAlgorithm = CommunityAlgorithm.louvain
    resolution: float = 1.0
    seed: Optional[int] = 42


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[int] = None
    phase: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    artifacts: Optional[List[str]] = None


class NodePosition(BaseModel):
    node_id: str
    x: float
    y: float
    z: Optional[float] = None
    layer: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    layer: Optional[str] = None


class GraphPositions(BaseModel):
    graph_id: str
    positions: List[NodePosition]
    edges: List[GraphEdge] = []


class WorkspaceSaveRequest(BaseModel):
    name: str
    graph_id: str
    view_state: Optional[Dict[str, Any]] = None


class WorkspaceSaveResponse(BaseModel):
    workspace_id: str
    filename: str
    message: str


class WorkspaceLoadResponse(BaseModel):
    graph_id: str
    view_state: Optional[Dict[str, Any]] = None
    message: str
