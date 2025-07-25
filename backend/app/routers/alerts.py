"""
Alerts router for alert management and notifications.

This router handles:
- Alert rule management
- Alert lifecycle management
- Notification configuration
- Alert statistics and bulk operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID, uuid4

from ..dependencies import get_db, get_current_user
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User

router = APIRouter(tags=["Alerts"])

# In-memory stub store for alert rules
ALERT_RULES = {}
VALID_CONDITIONS = {"greater_than", "less_than", "equal_to"}

@router.get("/rules")
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    device_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    rules = list(ALERT_RULES.values())
    # Filtering
    if device_id:
        rules = [r for r in rules if r.get("device_id") == device_id]
    if sensor_type:
        rules = [r for r in rules if r.get("sensor_type") == sensor_type]
    if is_active is not None:
        rules = [r for r in rules if r.get("is_active") == is_active]
    total = len(rules)
    start = (page - 1) * per_page
    end = start + per_page
    paged_rules = rules[start:end]
    return {"rules": paged_rules, "total": total, "page": page, "per_page": per_page, "size": len(paged_rules)}

@router.post("/rules", status_code=201)
async def create_alert_rule(
    rule: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Basic validation
    if not rule.get("name") or not rule.get("device_id"):
        raise HTTPException(status_code=422, detail="Missing required fields")
    if rule.get("condition") not in VALID_CONDITIONS:
        raise HTTPException(status_code=422, detail="Invalid condition")
    try:
        device_id = UUID(rule["device_id"])
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid device_id")
    rule_id = uuid4()
    new_rule = {"id": str(rule_id), **rule}
    ALERT_RULES[str(rule_id)] = new_rule
    return new_rule

@router.get("/rules/{rule_id}")
async def get_alert_rule(rule_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        uuid_obj = UUID(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    rule = ALERT_RULES.get(str(uuid_obj))
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule

@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    update: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        uuid_obj = UUID(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    rule = ALERT_RULES.get(str(uuid_obj))
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    if "condition" in update and update["condition"] not in VALID_CONDITIONS:
        raise HTTPException(status_code=422, detail="Invalid condition")
    rule.update(update)
    ALERT_RULES[str(uuid_obj)] = rule
    return rule

@router.delete("/rules/{rule_id}", status_code=200)
async def delete_alert_rule(rule_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        uuid_obj = UUID(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    if str(uuid_obj) not in ALERT_RULES:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    del ALERT_RULES[str(uuid_obj)]
    return {"deleted": True, "message": "Alert rule deleted"}

@router.get("")
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List alert history."""
    # TODO: Implement alert history listing
    return {"alerts": "Not implemented"}

@router.get("/active")
async def list_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List currently active alerts."""
    # TODO: Implement active alerts listing
    return {"active_alerts": "Not implemented"}

@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert (mark as seen)."""
    # TODO: Implement alert acknowledge
    return {"acknowledged": "Not implemented"} 