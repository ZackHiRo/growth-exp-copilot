from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Metric(BaseModel):
    name: str
    type: Literal["rate", "mean"]
    event: str
    property: Optional[str] = None
    description: Optional[str] = None

class ExperimentSpec(BaseModel):
    key: str
    hypothesis: str
    variants: List[str] = ["control", "treatment"]
    primary_metric: Metric
    secondary_metrics: List[Metric] = []
    segment_filters: dict = {}
    mde: float = Field(0.05, description="minimum detectable effect, relative")
    alpha: float = 0.05
    power: float = 0.8
    min_sample_size: int = 2000
    max_duration_days: int = 21
    flag_key: Optional[str] = None
    repo_paths: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    status: Literal["draft", "approved", "running", "completed", "stopped"] = "draft"
    decision: Optional[Literal["ship_treatment", "ship_control", "extend", "stop"]] = None

class TrackingPlan(BaseModel):
    events: List[dict]
    guardrails: dict
    experiment_key: str

class ExperimentStatus(BaseModel):
    experiment_key: str
    status: str
    current_sample_size: int
    decision: Optional[str] = None
    confidence: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)
