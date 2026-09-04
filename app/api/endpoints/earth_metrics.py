"""
API endpoints for the Earth Health Dashboard: metric cards and their
historical reading graphs. Public read, no auth required (same pattern
as comments: encourage browsing, and this data is meant to be citable
and shareable).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.core.database import get_async_session
from app.models.earth_metric import EarthMetric, EarthMetricReading, DataSource
from app.schemas.earth_metric import (
    EarthMetricOut,
    EarthHealthResponse,
    EarthMetricReadingOut,
    EarthMetricHistoryResponse,
    DataSourceOut,
)

router = APIRouter(prefix="/earth-metrics", tags=["earth-metrics"])


def _derive_trend_and_status(metric: EarthMetric, readings: list[EarthMetricReading]):
    """Derive current value, trend, and status from a metric's ordered readings."""
    if not readings:
        return None, None, 'unknown', 'unknown', 'unknown'

    ordered = sorted(readings, key=lambda r: r.reading_date)
    latest = ordered[-1]
    current_value = latest.value

    if len(ordered) <= 6:
        # Sparse/epoch data (e.g. GCRMN's coral reef assessments): the ~10-year
        # lookback below can land on an arbitrary, unrepresentative point given
        # how irregularly these are spaced - e.g. coral reef cover's readings
        # are 1990/1998/2009/2018, and "closest to 10 years before 2018" picks
        # 1998, the mass-bleaching crash year, making a partial recovery from
        # that crash read as "improving" even though cover peaked in 2009 and
        # has been declining since. For sparse series, "did it get better or
        # worse since it was last measured" (the previous reading) is what a
        # reader actually means by trend.
        baseline = ordered[-2] if len(ordered) >= 2 else ordered[0]
    else:
        # Dense annual data: compare against the reading from ~10 years before
        # the latest one (or the earliest available if shorter than that).
        baseline = ordered[0]
        target_year = latest.reading_date.year - 10
        for r in ordered:
            if r.reading_date.year <= target_year:
                baseline = r
            else:
                break

    delta = current_value - baseline.value

    # Measure how significant the change is against the metric's own scale of
    # concern (the gap between its warning and critical thresholds), not as a
    # raw percentage of the value. A percentage-of-value threshold works for
    # something like CO2 (hundreds of ppm) but badly understates metrics that
    # live on a narrow scale far from zero - e.g. ocean pH moving from 8.065
    # to 8.048 is a real, well-documented acidification trend, but it's only
    # a 0.2% change in the raw value, so it used to get misclassified as
    # "stable". Falls back to percent-of-value when thresholds aren't set.
    if metric.critical_threshold is not None and metric.warning_threshold is not None:
        scale = abs(metric.critical_threshold - metric.warning_threshold) or abs(baseline.value) or 1
    else:
        scale = abs(baseline.value) or 1
    significance = abs(delta) / scale

    if significance < 0.05:
        trend_direction = 'stable'
    else:
        trend_direction = 'up' if delta > 0 else 'down'

    if trend_direction == 'stable':
        trend = 'stable'
    else:
        going_up = trend_direction == 'up'
        trend = 'worsening' if going_up == metric.higher_is_worse else 'improving'

    # Status: prefer explicit thresholds, fall back to distance-from-target.
    if metric.critical_threshold is not None and metric.warning_threshold is not None:
        if metric.higher_is_worse:
            if current_value >= metric.critical_threshold:
                status = 'critical'
            elif current_value >= metric.warning_threshold:
                status = 'warning'
            else:
                status = 'good'
        else:
            if current_value <= metric.critical_threshold:
                status = 'critical'
            elif current_value <= metric.warning_threshold:
                status = 'warning'
            else:
                status = 'good'
    else:
        target = metric.target_value
        distance = abs(current_value - target) / abs(target) if target else 0
        past_target = (current_value > target) if metric.higher_is_worse else (current_value < target)
        if not past_target:
            status = 'good'
        elif distance < 0.1:
            status = 'warning'
        else:
            status = 'critical'

    return current_value, latest.reading_date, trend, trend_direction, status


@router.get("", response_model=EarthHealthResponse)
async def list_earth_metrics(session: AsyncSession = Depends(get_async_session)):
    """List all active earth health metrics with their latest reading, trend, and status."""
    query = (
        select(EarthMetric)
        .where(EarthMetric.is_active == True)
        .order_by(EarthMetric.display_order)
        .options(selectinload(EarthMetric.readings).selectinload(EarthMetricReading.source))
    )
    result = await session.execute(query)
    metrics = result.scalars().all()

    out = []
    for metric in metrics:
        current_value, latest_date, trend, trend_direction, status = _derive_trend_and_status(
            metric, metric.readings
        )
        ordered = sorted(metric.readings, key=lambda r: r.reading_date)
        latest_source = ordered[-1].source if ordered else None

        out.append(EarthMetricOut(
            id=metric.id,
            category=metric.category,
            name=metric.name,
            simplified_name=metric.simplified_name,
            icon=metric.icon,
            unit=metric.unit,
            target_value=metric.target_value,
            target_description=metric.target_description,
            description=metric.description,
            action_info=metric.action_info,
            current_value=current_value,
            latest_reading_date=latest_date.isoformat() if latest_date else None,
            trend=trend,
            trend_direction=trend_direction,
            status=status,
            earliest_reading_date=ordered[0].reading_date.isoformat() if ordered else None,
            reading_count=len(ordered),
            source=DataSourceOut(
                name=latest_source.name,
                organization=latest_source.organization,
                url=latest_source.url,
                retrieved_at=latest_source.retrieved_at.isoformat(),
            ) if latest_source else None,
        ))

    return EarthHealthResponse(
        last_updated=datetime.now(timezone.utc).isoformat(),
        metrics=out,
    )


@router.get("/{metric_id}/history", response_model=EarthMetricHistoryResponse)
async def get_earth_metric_history(metric_id: str, session: AsyncSession = Depends(get_async_session)):
    """Full historical time series for one metric, for charting."""
    query = (
        select(EarthMetric)
        .where(EarthMetric.id == metric_id)
        .options(selectinload(EarthMetric.readings).selectinload(EarthMetricReading.source))
    )
    result = await session.execute(query)
    metric = result.scalar_one_or_none()

    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    ordered = sorted(metric.readings, key=lambda r: r.reading_date)
    latest_source = ordered[-1].source if ordered else None

    return EarthMetricHistoryResponse(
        metric_id=metric.id,
        unit=metric.unit,
        readings=[EarthMetricReadingOut(date=r.reading_date, value=r.value) for r in ordered],
        source=DataSourceOut(
            name=latest_source.name,
            organization=latest_source.organization,
            url=latest_source.url,
            retrieved_at=latest_source.retrieved_at.isoformat(),
        ) if latest_source else None,
    )
