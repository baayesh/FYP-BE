from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_parent_user
from app.schemas.common import APIResponse
from app.models.user import User
from app.models.calendar_event import ParentChildRelationship
from app.services.parent import ParentStatsService

router = APIRouter()

# Dashboard endpoints
@router.get("/dashboard", response_model=APIResponse)
async def get_parent_dashboard(
    parent_id: str = Query(..., description="UUID of the parent"),
    db: Session = Depends(get_db)
):
    """Get parent dashboard with children's information, grades, and notifications"""
    try:
        # Fetch dashboard data from database
        dashboard_data = ParentStatsService.get_dashboard_stats(parent_id, db)
        
        return APIResponse(
            success=True,
            data=dashboard_data,
            message="Parent dashboard retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Child management endpoints
@router.get("/children", response_model=APIResponse)
async def get_children(
    parent_id: str = Query(..., description="UUID of the parent"),
    db: Session = Depends(get_db)
):
    """Get all children associated with the parent"""
    try:
        # Get children relationships
        relationships = db.query(ParentChildRelationship).filter(
            ParentChildRelationship.parent_id == parent_id,
            ParentChildRelationship.verified == True
        ).all()
        
        children = []
        for rel in relationships:
            child = db.query(User).filter(User.id == rel.child_id).first()
            if child:
                children.append({
                    "id": child.id,
                    "name": child.full_name,
                    "grade": "10th Grade",
                    "school": "School"
                })
        
        return APIResponse(success=True, data=children)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/children/{child_id}/grades", response_model=APIResponse)
async def get_child_grades(
    child_id: str,
    db: Session = Depends(get_db)
):
    """Get specific child's grades by subject with teacher feedback"""
    try:
        grades_data = ParentStatsService.get_child_grades(child_id, db)
        
        return APIResponse(
            success=True,
            data=grades_data,
            message="Grades retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
