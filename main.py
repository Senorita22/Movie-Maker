from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from db import favorites_collection
from motor.motor_asyncio import AsyncIOMotorClient
import httpx


app = FastAPI()

@app.get("/")
def get_home():
    return {"message": "Welcome to the Movie finder"}

class FavoriteMovie(BaseModel):
    title: str
    year: str
    genre: str
    imdbID: str
    user_rating: float


@app.get("/movie/{title}")
async def search_movie(title: str):
    """Search a movie by title using the OMDb API."""
    omdb_url = f"http://www.omdbapi.com/?t={title}&apikey={"8701355c"}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(omdb_url)
        movie_data = response.json()
        
        if movie_data.get("Response") == "False":
            raise HTTPException(status_code=404, detail=f"Movie '{title}' not found.")
        
        return {
            "title": movie_data.get("Title"),
            "year": movie_data.get("Year"),
            "genre": movie_data.get("Genre"),
            "imdbID": movie_data.get("imdbID")
        }

@app.post("/favorites", status_code= status.HTTP_201_CREATED)
async def save_favorite_movie(movie: FavoriteMovie):
    """
    Save a movie to your favorites list.
    Only allows movies that exist on the external API.
    """
    # 1. Check if the movie already exists in the database to prevent duplicates
    existing_movie = await favorites_collection.find_one({"imdbID": movie.imdbID})
    if existing_movie:
        raise HTTPException(status_code=409, detail="Movie is already in favorites.")

    # 2. Add a new check: Verify the movie exists on the external API
    omdb_url = f"http://www.omdbapi.com/?i={movie.imdbID}&apikey={"8701355c"}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(omdb_url)
            response.raise_for_status() # Raise error for 4xx or 5xx status codes
            movie_data = response.json()
            
            if movie_data.get("Response") == "False":
                raise HTTPException(status_code=404, detail=f"Movie with IMDb ID '{movie.imdbID}' not found on the external API.")

    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Could not connect to the external API: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during API validation: {exc}")

    # 3. If validation passes, save the movie to the database
    await favorites_collection.insert_one(movie.model_dump())
    return {"message": "Movie saved successfully!"}

# --- The GET /favorites endpoints remain unchanged ---
@app.get("/favorites")
async def get_all_favorite_movies():
    """List all saved movies from the database."""
    movies = await favorites_collection.find().to_list(100)
    
    for movie in movies:
        movie['_id'] = str(movie['_id'])
    
    return movies