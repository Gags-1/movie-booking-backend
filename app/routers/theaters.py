from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..database import get_db
from ..dependencies import get_current_admin_user

router = APIRouter(prefix="/theaters", tags=["Theaters"])

# Public endpoints
@router.get("/", response_model=List[schemas.Theater])
def get_theaters(
    skip: int = 0, 
    limit: int = 100, 
    location: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Theater)
    if location:
        query = query.filter(models.Theater.location.ilike(f"%{location}%"))
    theaters = query.offset(skip).limit(limit).all()
    return theaters

@router.get("/{theater_id}", response_model=schemas.Theater)
def get_theater(theater_id: int, db: Session = Depends(get_db)):
    theater = db.query(models.Theater).filter(models.Theater.id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    return theater

@router.get("/{theater_id}/screens", response_model=List[schemas.Screen])
def get_theater_screens(theater_id: int, db: Session = Depends(get_db)):
    theater = db.query(models.Theater).filter(models.Theater.id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    return theater.screens

# Admin endpoints
@router.post("/", response_model=schemas.Theater)
def create_theater(
    theater: schemas.TheaterCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_theater = models.Theater(**theater.dict())
    db.add(db_theater)
    db.commit()
    db.refresh(db_theater)
    return db_theater

@router.post("/{theater_id}/screens", response_model=schemas.Screen)
def create_screen(
    theater_id: int,
    screen: schemas.ScreenCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    # Check if theater exists
    theater = db.query(models.Theater).filter(models.Theater.id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    # Check if screen number already exists in this theater
    existing_screen = db.query(models.Screen).filter(
        models.Screen.theater_id == theater_id,
        models.Screen.screen_number == screen.screen_number
    ).first()
    
    if existing_screen:
        raise HTTPException(
            status_code=400, 
            detail=f"Screen number {screen.screen_number} already exists in this theater"
        )
    
    db_screen = models.Screen(**screen.dict(), theater_id=theater_id)
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    return db_screen

@router.put("/{theater_id}", response_model=schemas.Theater)
def update_theater(
    theater_id: int,
    theater: schemas.TheaterCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_theater = db.query(models.Theater).filter(models.Theater.id == theater_id).first()
    if not db_theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    for key, value in theater.dict().items():
        setattr(db_theater, key, value)
    
    db.commit()
    db.refresh(db_theater)
    return db_theater

@router.delete("/{theater_id}")
def delete_theater(
    theater_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    theater = db.query(models.Theater).filter(models.Theater.id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    db.delete(theater)
    db.commit()
    return {"message": "Theater deleted successfully"}