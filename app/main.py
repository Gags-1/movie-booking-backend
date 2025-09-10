from fastapi import FastAPI
from .database import engine
from . import models
from .routers import auth, movies,theaters,showtimes, bookings, payments

app=FastAPI()

#models.Base.metadata.create_all(bind=engine)
@app.get("/")
def health_check():
    return {"message":"check check"}

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(theaters.router, prefix="/theaters", tags=["Theaters"])
app.include_router(showtimes.router, prefix="/showtimes", tags=["Showtimes"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])