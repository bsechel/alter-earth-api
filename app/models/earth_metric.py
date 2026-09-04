"""
Earth Health Dashboard models: cited data sources, metric definitions,
and the historical readings that back each metric's graph.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class DataSource(Base):
    """A cited publisher/dataset backing one or more metric readings."""
    __tablename__ = "data_sources"
    __table_args__ = {"schema": "alter_earth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    organization = Column(String(200), nullable=False)
    url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    readings = relationship("EarthMetricReading", back_populates="source")

    def __repr__(self):
        return f"<DataSource(name='{self.name}', organization='{self.organization}')>"


class EarthMetric(Base):
    """Static metadata for one Earth Health Dashboard card."""
    __tablename__ = "earth_metrics"
    __table_args__ = {"schema": "alter_earth"}

    id = Column(String(100), primary_key=True)  # slug, e.g. 'co2-level'
    category = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    simplified_name = Column(String(200), nullable=False)
    icon = Column(String(10), nullable=False)
    unit = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=False)
    target_description = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    action_info = Column(Text, nullable=False)

    higher_is_worse = Column(Boolean, nullable=False)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)

    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    readings = relationship("EarthMetricReading", back_populates="metric", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EarthMetric(id='{self.id}', name='{self.name}')>"


class EarthMetricReading(Base):
    """One historical data point for a metric."""
    __tablename__ = "earth_metric_readings"
    __table_args__ = (
        UniqueConstraint('metric_id', 'reading_date', name='unique_metric_reading_date'),
        {"schema": "alter_earth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(String(100), ForeignKey('alter_earth.earth_metrics.id', ondelete='CASCADE'), nullable=False, index=True)
    reading_date = Column(Date, nullable=False)
    value = Column(Float, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.data_sources.id', ondelete='RESTRICT'), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    metric = relationship("EarthMetric", back_populates="readings")
    source = relationship("DataSource", back_populates="readings")

    def __repr__(self):
        return f"<EarthMetricReading(metric_id='{self.metric_id}', date={self.reading_date}, value={self.value})>"
