"""Input validation utilities."""
import re
from datetime import datetime
from typing import Optional
from fastapi import HTTPException


def validate_date_format(date_str: str) -> datetime:
    """Validate and parse ISO date string.

    Args:
        date_str: ISO format date string

    Returns:
        Parsed datetime object

    Raises:
        HTTPException: If date format is invalid
    """
    try:
        # Remove timezone info for parsing
        clean_date = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_date)
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use ISO format (e.g., 2024-01-01T00:00:00)"
        )


def validate_period(period: str) -> int:
    """Validate period string and convert to days.

    Args:
        period: Period string (e.g., "30d", "7d")

    Returns:
        Number of days

    Raises:
        HTTPException: If period format is invalid
    """
    if not period or not period.endswith("d"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format: {period}. Use format like '30d'"
        )
    
    try:
        days = int(period[:-1])
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="Period must be between 1 and 365 days"
            )
        return days
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format: {period}. Use format like '30d'"
        )


def validate_bonus_percent(percent: float) -> float:
    """Validate bonus percentage.

    Args:
        percent: Bonus percentage

    Returns:
        Validated percentage

    Raises:
        HTTPException: If percentage is invalid
    """
    if percent < 0 or percent > 100:
        raise HTTPException(
            status_code=400,
            detail="Bonus percentage must be between 0 and 100"
        )
    return percent


def validate_category(category: str) -> str:
    """Validate spending category.

    Args:
        category: Category name

    Returns:
        Validated category

    Raises:
        HTTPException: If category is invalid
    """
    if not category:
        raise HTTPException(status_code=400, detail="Category is required")
    
    # Allow alphanumeric and common characters
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', category):
        raise HTTPException(
            status_code=400,
            detail="Invalid category format"
        )
    
    if len(category) > 50:
        raise HTTPException(status_code=400, detail="Category name too long")
    
    return category.lower().strip()

