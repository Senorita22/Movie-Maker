import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

mongo_client = AsyncIOMotorClient(os.getenv("FILM_URI"))
film_manager_db = mongo_client["film_manager_db"]
# film_collection is the "movie" collection
film_collection = film_manager_db["movie"]
# favorites_collection is the "favorites" collection
favorites_collection = film_manager_db["favorites"]