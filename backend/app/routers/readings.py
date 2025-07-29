"""
Readings router for sensor data operations.

This router handles all sensor reading operations including:
- Data ingestion from devices
- Historical data retrieval
- Data aggregation and statistics
- Data export functionality
- Real-time data streaming
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from ..dependencies import get_db, get_current_user
from ..schemas.reading import (
    ReadingResponse,
    ReadingListResponse,
    ReadingQueryParams,
    ReadingAggregationResponse,
    ReadingExportRequest,
    ReadingStatsResponse
)
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..models.reading import Reading
from ..models.device import Device
from ..exceptions import (
    DeviceNotFoundException,
    AccessDeniedException,
    ValidationException
)

router = APIRouter(tags=["Data Ingestion"])

@router.get("", response_model=ReadingListResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def get_readings(
    params: ReadingQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sensor readings across all devices.
    
    Returns a paginated list of sensor readings with filtering options.
    Supports filtering by device, sensor type, time range, and organization.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Get readings with filters
    readings = Reading.get_readings(
        db=db,
        organization_id=organization_id,
        device_id=params.device_id,
        sensor_type=params.sensor_type,
        start_time=params.start_time,
        end_time=params.end_time,
        limit=params.limit,
        offset=params.offset
    )
    
    # Get total count
    total = Reading.count_readings(
        db=db,
        organization_id=organization_id,
        device_id=params.device_id,
        sensor_type=params.sensor_type,
        start_time=params.start_time,
        end_time=params.end_time
    )
    
    return ReadingListResponse(
        readings=[ReadingResponse.from_model(reading) for reading in readings],
        total=total,
        device_id=params.device_id,
        size=len(readings)
    )

@router.get("/latest", response_model=List[ReadingResponse], responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def get_latest_readings(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get latest sensor readings.
    
    Returns the most recent sensor readings from all devices or a specific device.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Get latest readings
    readings = Reading.get_latest_readings(
        db=db,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type
    )
    
    return [ReadingResponse.from_model(reading) for reading in readings]

@router.get("/stats", response_model=ReadingStatsResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def get_reading_stats(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time for statistics"),
    end_time: Optional[datetime] = Query(None, description="End time for statistics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reading statistics.
    
    Returns statistical information about sensor readings including counts,
    averages, min/max values, and data quality metrics.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Get statistics
    stats = Reading.get_reading_stats(
        db=db,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return ReadingStatsResponse(**stats)

@router.get("/aggregation", response_model=ReadingAggregationResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def get_reading_aggregation(
    aggregation_type: str = Query(..., description="Type of aggregation (hourly, daily, weekly, monthly)"),
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time for aggregation"),
    end_time: Optional[datetime] = Query(None, description="End time for aggregation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated reading data.
    
    Returns time-series aggregated data for analysis and visualization.
    Supports hourly, daily, weekly, and monthly aggregations.
    """
    # Validate aggregation type
    valid_types = ["hourly", "daily", "weekly", "monthly"]
    if aggregation_type not in valid_types:
        raise ValidationException(detail=f"Invalid aggregation type. Must be one of: {valid_types}")
    
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Get aggregated data
    aggregation = Reading.get_aggregated_readings(
        db=db,
        aggregation_type=aggregation_type,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return ReadingAggregationResponse(
        aggregation_type=aggregation_type,
        data=aggregation,
        device_id=device_id,
        sensor_type=sensor_type
    )

@router.post("/export", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def export_readings(
    export_request: ReadingExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export reading data.
    
    Exports sensor readings in various formats (CSV, JSON, Excel) for analysis.
    Returns a download link or initiates a background export job.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Validate export format
    valid_formats = ["csv", "json", "excel"]
    if export_request.format not in valid_formats:
        raise ValidationException(detail=f"Invalid export format. Must be one of: {valid_formats}")
    
    # TODO: Implement background export job
    # For now, return success message
    return BaseResponse(
        message=f"Export job started for {export_request.format} format",
        success=True
    )

@router.get("/quality", response_model=dict, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def get_data_quality(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time for quality analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for quality analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get data quality metrics.
    
    Returns data quality indicators including completeness, accuracy,
    and consistency metrics for sensor readings.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Get quality metrics
    quality_metrics = Reading.get_data_quality(
        db=db,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return quality_metrics

@router.get("/trends", response_model=dict, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def get_reading_trends(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    trend_period: str = Query("7d", description="Trend period (1d, 7d, 30d, 90d)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reading trends.
    
    Returns trend analysis for sensor readings including moving averages,
    trend direction, and seasonal patterns.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Validate trend period
    valid_periods = ["1d", "7d", "30d", "90d"]
    if trend_period not in valid_periods:
        raise ValidationException(detail=f"Invalid trend period. Must be one of: {valid_periods}")
    
    # Calculate end time based on trend period
    end_time = datetime.utcnow()
    if trend_period == "1d":
        start_time = end_time - timedelta(days=1)
    elif trend_period == "7d":
        start_time = end_time - timedelta(days=7)
    elif trend_period == "30d":
        start_time = end_time - timedelta(days=30)
    else:  # 90d
        start_time = end_time - timedelta(days=90)
    
    # Get trends
    trends = Reading.get_reading_trends(
        db=db,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return trends

@router.delete("/{reading_id}", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def delete_reading(
    reading_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific reading.
    
    Removes a single sensor reading from the database.
    This action cannot be undone.
    """
    reading = Reading.get_reading(db, reading_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found"
        )
    
    # Check organization access
    if not current_user.has_access_to_device(reading.device):
        raise AccessDeniedException(detail="Access denied to this reading")
    
    # Delete reading
    Reading.delete_reading(db, reading_id)
    
    return BaseResponse(
        message="Reading successfully deleted",
        success=True
    )

@router.post("/bulk-delete", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def bulk_delete_readings(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time for deletion"),
    end_time: Optional[datetime] = Query(None, description="End time for deletion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk delete readings.
    
    Deletes multiple sensor readings based on filters.
    This action cannot be undone.
    """
    # Get user's organization
    organization_id = current_user.organization_id
    
    # Validate that at least one filter is provided
    if not any([device_id, sensor_type, start_time, end_time]):
        raise ValidationException(detail="At least one filter must be provided for bulk deletion")
    
    # Delete readings
    deleted_count = Reading.bulk_delete_readings(
        db=db,
        organization_id=organization_id,
        device_id=device_id,
        sensor_type=sensor_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return BaseResponse(
        message=f"Successfully deleted {deleted_count} readings",
        success=True
    ) 