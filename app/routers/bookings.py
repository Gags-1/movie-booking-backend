from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from .. import schemas, models
from ..database import get_db
from ..dependencies import get_current_active_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/", response_model=List[schemas.BookingWithDetails])
def get_user_bookings(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return bookings

@router.get("/{booking_id}", response_model=schemas.BookingWithDetails)
def get_booking(
    booking_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking

@router.post("/", response_model=schemas.Booking)
def create_booking(
    booking: schemas.BookingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Check if showtime exists
    showtime = db.query(models.Showtime).filter(models.Showtime.id == booking.showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Parse requested seats
    try:
        requested_seats = json.loads(booking.seats_booked)
        if not isinstance(requested_seats, list) or not requested_seats:
            raise ValueError("Seats must be a non-empty list")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid seats format: {str(e)}")
    
    # Get all booked seats for this showtime
    booked_seats = []
    for existing_booking in showtime.bookings:
        if existing_booking.status != models.BookingStatus.CANCELLED:
            try:
                booked_seats.extend(json.loads(existing_booking.seats_booked))
            except json.JSONDecodeError:
                continue
    
    # Check if all requested seats are available
    for seat in requested_seats:
        if seat in booked_seats:
            raise HTTPException(
                status_code=400, 
                detail=f"Seat {seat} is not available"
            )
    
    # Calculate total price
    total_price = len(requested_seats) * showtime.price_per_seat
    
    # Create booking
    db_booking = models.Booking(
        user_id=current_user.id,
        showtime_id=booking.showtime_id,
        seats_booked=booking.seats_booked,
        total_price=total_price,
        status=models.BookingStatus.PENDING
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return db_booking

@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status == models.BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking is already cancelled")
    
    # Check if payment was made and handle refund logic if needed
    if booking.payment and booking.payment.payment_status == models.PaymentStatus.SUCCESS:
        # In a real application, you would integrate with a payment gateway for refunds
        booking.payment.payment_status = models.PaymentStatus.PENDING  # Mark for refund
    
    booking.status = models.BookingStatus.CANCELLED
    db.commit()
    
    return {"message": "Booking cancelled successfully"}