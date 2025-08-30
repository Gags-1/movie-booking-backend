from sqlalchemy import String, Integer, ForeignKey, Float, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from datetime import datetime
from .database import Base



class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(50))
    duration: Mapped[int] = mapped_column(Integer)  # in minutes
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    poster_url: Mapped[str] = mapped_column(String(255), nullable=True)

    showtimes: Mapped[list["Showtime"]] = relationship(back_populates="movie")


class Theater(Base):
    __tablename__ = "theaters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(200))

    screens: Mapped[list["Screen"]] = relationship(back_populates="theater")



class Screen(Base):
    __tablename__ = "screens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    theater_id: Mapped[int] = mapped_column(ForeignKey("theaters.id"))
    screen_number: Mapped[int] = mapped_column(Integer)
    seat_layout: Mapped[str] = mapped_column(Text)

    theater: Mapped["Theater"] = relationship(back_populates="screens")
    showtimes: Mapped[list["Showtime"]] = relationship(back_populates="screen")



class Showtime(Base):
    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    price_per_seat: Mapped[float] = mapped_column(Float)

    movie: Mapped["Movie"] = relationship(back_populates="showtimes")
    screen: Mapped["Screen"] = relationship(back_populates="showtimes")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="showtime")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"))
    seats_booked: Mapped[str] = mapped_column(Text)  # JSON string of booked seats
    total_price: Mapped[float] = mapped_column(Float)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING)

    user: Mapped["User"] = relationship(back_populates="bookings")
    showtime: Mapped["Showtime"] = relationship(back_populates="bookings")
    payment: Mapped["Payment"] = relationship(back_populates="booking", uselist=False)



class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    amount: Mapped[float] = mapped_column(Float)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    booking: Mapped["Booking"] = relationship(back_populates="payment")
