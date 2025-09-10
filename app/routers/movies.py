from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..database import get_db
from ..dependencies import get_current_admin_user

router = APIRouter(prefix="/movies", tags=["Movies"])

# Public endpoints
@router.get("/", response_model=List[schemas.Movie])
def get_movies(
    skip: int = 0, 
    limit: int = 100, 
    genre: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Movie)
    if genre:
        query = query.filter(models.Movie.genre.ilike(f"%{genre}%"))
    movies = query.offset(skip).limit(limit).all()
    return movies

@router.get("/{movie_id}", response_model=schemas.Movie)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# Admin only endpoints
@router.post("/", response_model=schemas.Movie)
def create_movie(
    movie: schemas.MovieCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_movie = models.Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.put("/{movie_id}", response_model=schemas.Movie)
def update_movie(
    movie_id: int,
    movie: schemas.MovieCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    for key, value in movie.dict().items():
        setattr(db_movie, key, value)
    
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.delete("/{movie_id}")
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    db.delete(movie)
    db.commit()
    return {"message": "Movie deleted successfully"}