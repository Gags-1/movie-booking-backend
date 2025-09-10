from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .. import schemas, models
from ..database import get_db
from ..dependencies import get_current_admin_user

router = APIRouter(prefix="/showtimes", tags=["Showtimes"])

# Public endpoints
@router.get("/", response_model=List[schemas.ShowtimeWithDetails])
def get_showtimes(
    skip: int = 0, 
    limit: int = 100, 
    movie_id: int = None,
    theater_id: int = None,
    date: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Showtime).join(models.Showtime.movie).join(models.Showtime.screen)
    
    if movie_id:
        query = query.filter(models.Showtime.movie_id == movie_id)
    
    if theater_id:
        query = query.filter(models.Screen.theater_id == theater_id)
    
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(db.func.date(models.Showtime.start_time) == date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    showtimes = query.offset(skip).limit(limit).all()
    return showtimes

@router.get("/{showtime_id}", response_model=schemas.ShowtimeWithDetails)
def get_showtime(showtime_id: int, db: Session = Depends(get_db)):
    showtime = db.query(models.Showtime).filter(models.Showtime.id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    return showtime

@router.get("/{showtime_id}/available-seats")
def get_available_seats(showtime_id: int, db: Session = Depends(get_db)):
    showtime = db.query(models.Showtime).filter(models.Showtime.id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Get all booked seats for this showtime
    booked_seats = []
    for booking in showtime.bookings:
        if booking.status != models.BookingStatus.CANCELLED:
            # Assuming seats_booked is a JSON string like '["A1", "A2", "B3"]'
            import json
            try:
                booked_seats.extend(json.loads(booking.seats_booked))
            except json.JSONDecodeError:
                continue
    
    # Get all possible seats from screen layout
    import json
    try:
        all_seats = json.loads(showtime.screen.seat_layout)
    except json.JSONDecodeError:
        all_seats = []
    
    # Calculate available seats
    available_seats = [seat for seat in all_seats if seat not in booked_seats]
    
    return {
        "showtime_id": showtime_id,
        "total_seats": len(all_seats),
        "booked_seats": booked_seats,
        "available_seats": available_seats,
        "available_count": len(available_seats)
    }

# Admin endpoints
@router.post("/", response_model=schemas.Showtime)
def create_showtime(
    showtime: schemas.ShowtimeCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    # Check if movie exists
    movie = db.query(models.Movie).filter(models.Movie.id == showtime.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if screen exists
    screen = db.query(models.Screen).filter(models.Screen.id == showtime.screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Check for time conflicts
    conflicting_showtime = db.query(models.Showtime).filter(
        models.Showtime.screen_id == showtime.screen_id,
        models.Showtime.start_time == showtime.start_time
    ).first()
    
    if conflicting_showtime:
        raise HTTPException(
            status_code=400, 
            detail="Another showtime is already scheduled for this screen at the same time"
        )
    
    db_showtime = models.Showtime(**showtime.dict())
    db.add(db_showtime)
    db.commit()
    db.refresh(db_showtime)
    return db_showtime

@router.put("/{showtime_id}", response_model=schemas.Showtime)
def update_showtime(
    showtime_id: int,
    showtime: schemas.ShowtimeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_showtime = db.query(models.Showtime).filter(models.Showtime.id == showtime_id).first()
    if not db_showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    for key, value in showtime.dict().items():
        setattr(db_showtime, key, value)
    
    db.commit()
    db.refresh(db_showtime)
    return db_showtime

@router.delete("/{showtime_id}")
def delete_showtime(
    showtime_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    showtime = db.query(models.Showtime).filter(models.Showtime.id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    db.delete(showtime)
    db.commit()
    return {"message": "Showtime deleted successfully"}