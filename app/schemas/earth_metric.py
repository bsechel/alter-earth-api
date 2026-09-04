"""
Pydantic schemas for the Earth Health Dashboard.
"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date


class DataSourceOut(BaseModel):
    """A cited source, returned alongside metric data for transparency."""
    name: str
    organization: str
    url: str
    retrieved_at: str

    class Config:
        from_attributes = True


class EarthMetricOut(BaseModel):
    """One metric card: metadata + latest reading + derived trend/status."""
    id: str
    category: str
    name: str
    simplified_name: str
    icon: str
    unit: str
    target_value: float
    target_description: str
    description: str
    action_info: str

    current_value: Optional[float] = None
    latest_reading_date: Optional[str] = None
    trend: Literal['worsening', 'stable', 'improving', 'unknown'] = 'unknown'
    trend_direction: Literal['up', 'down', 'stable', 'unknown'] = 'unknown'
    status: Literal['critical', 'warning', 'good', 'unknown'] = 'unknown'
    earliest_reading_date: Optional[str] = None
    reading_count: int = 0
    source: Optional[DataSourceOut] = None


class EarthHealthResponse(BaseModel):
    """Response for GET /earth-metrics - mirrors the frontend's existing shape."""
    last_updated: str
    metrics: list[EarthMetricOut]


class EarthMetricReadingOut(BaseModel):
    """One point in a metric's history graph."""
    date: date
    value: float


class EarthMetricHistoryResponse(BaseModel):
    """Response for GET /earth-metrics/{id}/history."""
    metric_id: str
    unit: str
    readings: list[EarthMetricReadingOut]
    source: Optional[DataSourceOut] = None
