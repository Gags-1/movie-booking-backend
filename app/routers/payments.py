from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..dependencies import get_current_active_user

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/{booking_id}/initiate")
def initiate_payment(
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
        raise HTTPException(status_code=400, detail="Cannot pay for a cancelled booking")
    
    # Check if payment already exists
    if booking.payment:
        if booking.payment.payment_status == models.PaymentStatus.SUCCESS:
            raise HTTPException(status_code=400, detail="Payment already completed")
        # Return existing payment details
        return {
            "payment_id": booking.payment.id,
            "amount": booking.payment.amount,
            "status": booking.payment.payment_status.value
        }
    
    # Create new payment
    payment = models.Payment(
        booking_id=booking_id,
        amount=booking.total_price,
        payment_status=models.PaymentStatus.PENDING
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    #add payment gateway integration here in real application
    
    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.payment_status.value,
        "message": "Payment initiated. Integrate with your payment gateway in production."
    }

@router.post("/{payment_id}/confirm")
def confirm_payment(
    payment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check if user owns this payment
    if payment.booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this payment")
    
    # In a real application, you would verify the payment with your payment gateway
    # For demo purposes, we'll just mark it as successful
    
    payment.payment_status = models.PaymentStatus.SUCCESS
    payment.booking.status = models.BookingStatus.CONFIRMED
    
    db.commit()
    
    return {
        "message": "Payment confirmed successfully", 
        "status": "success",
        "booking_id": payment.booking_id,
        "booking_status": payment.booking.status.value
    }

@router.get("/{payment_id}", response_model=schemas.PaymentWithDetails)
def get_payment(
    payment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check if user owns this payment
    if payment.booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this payment")
    
    return payment