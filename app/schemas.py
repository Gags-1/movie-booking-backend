from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from .models import UserRole, BookingStatus, PaymentStatus

# Authentication schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Movie schemas
class MovieBase(BaseModel):
    title: str
    genre: str
    language: str
    duration: int
    rating: Optional[float] = None
    poster_url: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int

    class Config:
        from_attributes = True

# Theater schemas
class TheaterBase(BaseModel):
    name: str
    location: str

class TheaterCreate(TheaterBase):
    pass

class Theater(TheaterBase):
    id: int

    class Config:
        from_attributes = True

# Screen schemas
class ScreenBase(BaseModel):
    theater_id: int
    screen_number: int
    seat_layout: str

class ScreenCreate(ScreenBase):
    pass

class Screen(ScreenBase):
    id: int

    class Config:
        from_attributes = True

# Showtime schemas
class ShowtimeBase(BaseModel):
    movie_id: int
    screen_id: int
    start_time: datetime
    price_per_seat: float

class ShowtimeCreate(ShowtimeBase):
    pass

class Showtime(ShowtimeBase):
    id: int

    class Config:
        from_attributes = True

# Extended showtime with details
class ShowtimeWithDetails(Showtime):
    movie: Movie
    screen: Screen
    theater: Optional[Theater] = None

    class Config:
        from_attributes = True

# Booking schemas
class BookingBase(BaseModel):
    showtime_id: int
    seats_booked: str  # JSON string

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    user_id: int
    total_price: float
    status: BookingStatus

    class Config:
        from_attributes = True

# Extended booking with details
class BookingWithDetails(Booking):
    showtime: ShowtimeWithDetails
    user: Optional[User] = None

    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    booking_id: int
    amount: float

class Payment(PaymentBase):
    id: int
    payment_status: PaymentStatus

    class Config:
        from_attributes = True


class PaymentWithDetails(Payment):
    booking: Optional[Booking] = None
    
    class Config:
        from_attributes = True